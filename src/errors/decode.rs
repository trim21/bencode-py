use std::fmt::Debug;
use thiserror::Error;


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
