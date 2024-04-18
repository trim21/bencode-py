use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3::{create_exception, PyResult, Python};
use std::collections::BTreeMap;
use std::fmt::Debug;
use thiserror::Error;

use crate::typ::Type;

create_exception!(bencode2, BencodeDecodeError, pyo3::exceptions::PyException);

#[pyfunction]
pub fn decode<'a>(py: Python<'a>, value: Vec<u8>, str_key: bool) -> PyResult<Bound<'_, PyDict>> {
    let _ctx = Decoder {
        str_key: str_key,
        py: py,
    };

    let b = value;

    let o = PyDict::new_bound(py);

    match _ctx.decode(&mut b.into_iter()) {
        Ok(_) => return Ok(o),
        Err(e) => return Err(BencodeDecodeError::new_err(e.to_string())),
    };
}

#[derive(Debug, Error)]
pub enum DecodeError {
    #[error("empty byte sequence")]
    Empty,
    #[error("invalid start byte")]
    InvalidStartByte,
    #[error("invalid end byte for type: {0}")]
    InvalidEndByte(String),
    #[error("invalid integer")]
    InvalidInteger,
    #[error("negative zero is not allowed")]
    NegativeZeroInteger,
    #[error("integer with leading zeros is not allowed")]
    IntegerWithLeadingZeros,
    #[error("invalid byte string length")]
    InvalidByteStringLength,
    #[error("invalid list")]
    InvalidList,
    #[error("invalid dictionary")]
    InvalidDictionary,
    #[error("invalid type for dictionary key")]
    InvalidDictionaryKey,
    #[error("invalid byte sequence")]
    InvalidByteSequence,
}

pub type DecodeResult = Result<Type, DecodeError>;

struct Decoder<'a> {
    str_key: bool,
    py: Python<'a>,
}

impl<'a> Decoder<'a> {
    fn decode<T>(&self, bytes: &mut T) -> DecodeResult
    where
        T: Iterator<Item = u8>,
    {
        let result = match bytes.next() {
            None => return Err(DecodeError::Empty),
            Some(start_byte) => self.handler(bytes, start_byte),
        };

        if result.is_err() {
            return result;
        }

        match bytes.next() {
            None => result,
            Some(_) => return Err(DecodeError::InvalidByteSequence),
        }
    }

    fn handler<T>(&self, bytes: &mut T, start_byte: u8) -> DecodeResult
    where
        T: Iterator<Item = u8>,
    {
        match start_byte {
            b'i' => self.decode_integer(bytes, start_byte),
            b'l' => self.decode_list(bytes, start_byte),
            b'd' => self.decode_dictionary(bytes, start_byte),
            b'0'..=b'9' => self.decode_binarystring(bytes, start_byte),
            _ => return Err(DecodeError::InvalidStartByte),
        }
    }

    fn decode_integer<T>(&self, bytes: &mut T, _start_byte: u8) -> Result<Type, DecodeError>
    where
        T: Iterator<Item = u8>,
    {
        let mut buff = vec![];
        let mut sign = 1;

        let nxt = match bytes.next() {
            None => return Err(DecodeError::InvalidInteger),
            Some(ch) => ch,
        };

        if nxt == b'-' {
            sign = -1;
        } else if nxt >= b'0' && nxt <= b'9' {
            buff.push(nxt);
        } else {
            return Err(DecodeError::InvalidInteger);
        }

        while let Some(ch) = bytes.next() {
            match ch {
                b'0'..=b'9' => buff.push(ch),
                b'e' => break,
                _ => return Err(DecodeError::InvalidEndByte("integer".to_string())),
            }
        }

        if buff.len() > 1 && buff[0] == b'0' {
            return Err(DecodeError::IntegerWithLeadingZeros);
        }

        let i = bytes_to_int(buff)?;

        if sign == -1 && i == 0 {
            return Err(DecodeError::NegativeZeroInteger);
        }

        Ok(Type::Integer(sign * i))
    }

    fn decode_binarystring<T>(&self, bytes: &mut T, start_byte: u8) -> DecodeResult
    where
        T: Iterator<Item = u8>,
    {
        let mut len_buff = vec![start_byte];
        let mut str_buff = vec![];

        while let Some(ch) = bytes.next() {
            match ch {
                b'0'..=b'9' => len_buff.push(ch),
                b':' => break,
                _ => return Err(DecodeError::InvalidEndByte("byte string".to_string())),
            }
        }

        let len = bytes_to_int(len_buff)?;

        for _ in 0..len {
            match bytes.next() {
                None => return Err(DecodeError::InvalidByteStringLength),
                Some(ch) => str_buff.push(ch),
            }
        }

        Ok(Type::ByteString(bytes_to_str(str_buff)))
    }

    fn decode_list<T>(&self, bytes: &mut T, _start_byte: u8) -> DecodeResult
    where
        T: Iterator<Item = u8>,
    {
        let mut l = vec![];

        loop {
            match bytes.next() {
                None => return Err(DecodeError::InvalidList),
                Some(ch) => match ch {
                    b'e' => break,
                    ch => {
                        let item = self.handler(bytes, ch)?;
                        l.push(item);
                    }
                },
            }
        }

        Ok(Type::List(l))
    }

    fn decode_dictionary<T>(&self, bytes: &mut T, _start_byte: u8) -> DecodeResult
    where
        T: Iterator<Item = u8>,
    {
        let mut d = BTreeMap::new();
        let mut last_key = None;

        loop {
            match bytes.next() {
                None => return Err(DecodeError::InvalidDictionary),
                Some(ch) => match ch {
                    b'e' => break,
                    _ => match last_key {
                        None => {
                            let key = self.decode_binarystring(bytes, ch)?;
                            match key {
                                Type::ByteString(key) => {
                                    last_key = Some(key);
                                }
                                _ => return Err(DecodeError::InvalidDictionaryKey),
                            };
                        }
                        Some(key) => {
                            let value = self.handler(bytes, ch)?;
                            d.insert(key, value);
                            last_key = None;
                        }
                    },
                },
            }
        }

        Ok(Type::Dictionary(d))
    }
}

fn bytes_to_str(bytes: Vec<u8>) -> String {
    bytes.iter().map(|&b| b as char).collect::<String>()
}

fn bytes_to_int(bytes: Vec<u8>) -> Result<i64, DecodeError> {
    let integer_str = bytes_to_str(bytes);

    match integer_str.parse::<i64>() {
        Err(_) => return Err(DecodeError::InvalidInteger),
        Ok(i) => Ok(i),
    }
}
