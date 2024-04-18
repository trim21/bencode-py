#![deny(clippy::implicit_return)]
#![allow(clippy::needless_return)]

mod decode;
mod encode;
mod errors;
mod typ;

use pyo3::prelude::*;

/// A Python module implemented in Rust.
#[pymodule]
fn bencode2(py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(encode::encode, m)?)?;
    m.add_function(wrap_pyfunction!(decode::decode, m)?)?;
    m.add(
        "BencodeEncodeError",
        py.get_type_bound::<encode::BencodeEncodeError>(),
    )?;
    m.add(
        "BencodeDecodeError",
        py.get_type_bound::<decode::BencodeDecodeError>(),
    )?;
    return Ok(());
}
