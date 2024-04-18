mod converter;
mod decode;
mod deserialize;
mod serialize;

pub use converter::ConverterError;

pub type BencodeError = Box<dyn std::error::Error + Send + Sync + 'static>;
pub type BencodeResult<T> = Result<T, BencodeError>;
