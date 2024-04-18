use std::fmt::Debug;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum ConverterError {
    #[error("invalid string")]
    InvalidString,
    #[error("invalid integer")]
    InvalidInteger,
    #[error("invalid list")]
    InvalidList,
    #[error("invalid dictionary")]
    InvalidDictionary,
}
