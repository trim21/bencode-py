use std::borrow::Cow;

use bytes::{BufMut, Bytes, BytesMut};
use pyo3::{
    create_exception,
    exceptions::{PyException, PyTypeError},
    ffi::{
        PyBool_Check, PyBytes_Check, PyDict_Check, PyList_Check, PyLong_Check, PyTuple_Check,
        PyUnicode_Check, Py_TYPE,
    },
    prelude::*,
    types::{PyBytes, PyDict, PyString, PyType},
};
use smallvec::SmallVec;

create_exception!(bencode2, BencodeEncodeError, pyo3::exceptions::PyException);

#[pyfunction]
pub fn encode(value: PyObject, py: Python<'_>) -> PyResult<Cow<'_, [u8]>> {
    let mut buf: BytesMut = BytesMut::with_capacity(1024);

    _encode(value, py, &mut buf)?;

    return Ok(buf.to_vec().into());
}

pub fn _encode(value: PyObject, py: Python<'_>, buf: &mut BytesMut) -> PyResult<()> {
    let o = value.as_ptr();

    unsafe {
        if PyLong_Check(o) == 1 {
            return _encode_int(value.extract(py)?, buf);
        } else if PyBool_Check(o) == 1 {
            buf.put(&b"bool"[..]);
            buf.put(&b"i"[..]);

            if value.is_truthy(py)? {
                buf.put(&b"1"[..]);
            } else {
                buf.put(&b"0"[..]);
            }

            buf.put(&b"e"[..]);
            return Ok(());
        } else if (PyList_Check(o) == 1) || (PyTuple_Check(o) == 1) {
            let v: Vec<PyObject> = value.extract(py)?;
            buf.put(&b"l"[..]);
            for x in v {
                _encode(x, py, buf)?;
            }
            buf.put(&b"e"[..]);
            return Ok(());
        } else if PyDict_Check(o) == 1 {
            if let Ok(d) = value.extract::<&PyDict>(py) {
                return _encode_dict(d, py, buf);
            } else {
                return Err(PyException::new_err(
                    "unexpected error, failed to extract dict".to_string(),
                ));
            }
        } else if PyUnicode_Check(o) == 1 {
            return _encode_str(value.extract(py)?, buf);
        } else if PyBytes_Check(o) == 1 {
            let v: Cow<[u8]> = value.extract(py)?;
            // buf.put(&b"[bytes]"[..]);
            return _encode_bytes(v, buf);
        }
    }

    return Err(BencodeEncodeError::new_err("Unsupported type".to_string()));
}

fn _encode_dict(v: &PyDict, py: Python<'_>, buf: &mut BytesMut) -> PyResult<()> {
    buf.put(&b"d"[..]);

    let mut sv: SmallVec<[(String, PyObject); 8]> = SmallVec::with_capacity(v.len());

    for item in v.items().iter() {
        let (key, value): (PyObject, PyObject) = item.extract()?;

        if let Ok(d) = key.extract::<&PyString>(py) {
            let bb = d.to_string();
            sv.push((bb, value));
        } else if let Ok(d) = key.extract::<&PyBytes>(py) {
            sv.push((String::from_utf8(d.as_bytes().into())?, value));
        } else {
            unsafe {
                let typ = Py_TYPE(key.as_ptr());

                let bb = PyType::from_borrowed_type_ptr(py, typ);
                let name = bb.qualname()?;

                return Err(PyTypeError::new_err(format!(
                    "Unsupported type {name} as dict keys"
                )));
            }
        }
    }

    sv.sort_unstable_by(|a, b| a.0.cmp(&b.0));

    let mut last_key: Option<String> = None;
    for (key, _) in sv.clone() {
        if let Some(lk) = last_key {
            if lk == key {
                return Err(BencodeEncodeError::new_err(format!(
                    "Duplicated keys {key}"
                )));
            }
        }

        last_key = Some(key);
    }

    for (key, value) in sv {
        _encode_str(key, buf)?;
        _encode(value, py, buf)?;
    }

    buf.put(&b"e"[..]);

    return Ok(());
}

fn _encode_int(v: i128, buf: &mut BytesMut) -> PyResult<()> {
    let mut buffer = itoa::Buffer::new();
    let printed = buffer.format(v);

    buf.put(&b"i"[..]);
    buf.put(printed.as_bytes());
    buf.put(&b"e"[..]);

    return Ok(());
}

fn _encode_str<'py>(v: String, buf: &mut BytesMut) -> PyResult<()> {
    let mut buffer = itoa::Buffer::new();
    let printed = buffer.format(v.len());

    buf.put(printed.as_bytes());
    buf.put(&b":"[..]);
    buf.put(v.as_bytes());

    return Ok(());
}

fn _encode_bytes(v: Cow<[u8]>, buf: &mut BytesMut) -> PyResult<()> {
    let mut buffer = itoa::Buffer::new();
    let printed = buffer.format(v.len());

    buf.put(printed.as_bytes());
    buf.put(&b":"[..]);
    buf.put(Bytes::from(v.to_vec()));

    return Ok(());
}
