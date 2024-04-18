use std::collections::BTreeMap;
use std::convert::TryFrom;

use crate::errors::ConverterError;

#[derive(Debug)]
pub enum Type {
    Integer(i64),
    ByteString(String),
    // Bytes(PyBytes),
    List(Vec<Type>),
    Dictionary(BTreeMap<String, Type>),
}

impl TryFrom<Type> for String {
    type Error = ConverterError;

    fn try_from(value: Type) -> Result<Self, Self::Error> {
        match value {
            Type::ByteString(s) => Ok(s),
            _ => Err(ConverterError::InvalidString),
        }
    }
}

impl TryFrom<&Type> for String {
    type Error = ConverterError;

    fn try_from(value: &Type) -> Result<Self, Self::Error> {
        match value {
            Type::ByteString(s) => Ok(s.to_string()),
            _ => Err(ConverterError::InvalidString),
        }
    }
}

impl TryFrom<Type> for i64 {
    type Error = ConverterError;

    fn try_from(value: Type) -> Result<Self, Self::Error> {
        match value {
            Type::Integer(i) => Ok(i),
            _ => Err(ConverterError::InvalidInteger),
        }
    }
}

impl Type {
    pub fn get(&self, key: String) -> Result<&Type, ConverterError> {
        match self {
            Type::Dictionary(d) => match d.get(&key) {
                Some(t) => Ok(t),
                None => Err(ConverterError::InvalidDictionary),
            },
            _ => Err(ConverterError::InvalidDictionary),
        }
    }
}
