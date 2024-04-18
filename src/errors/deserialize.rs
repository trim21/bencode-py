use std::fmt::Debug;
use thiserror::Error;


#[derive(Debug, Error)]
pub enum DeserializationError {
    #[error("could not be serialized to json")]
    JsonDeserializationError,
    #[error("could not open file")]
    FileError,
}