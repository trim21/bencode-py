use std::fmt::Debug;
use thiserror::Error;


#[derive(Debug, Error)]
pub enum SerializationError {
    #[error("could not be serialized to json")]
    JsonSerializationError,
    #[error("could not open file")]
    FileError,
    #[error("could not save to .json file")]
    FileSerializationError,
}