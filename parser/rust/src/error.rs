use thiserror::Error;

#[derive(Error, Debug)]
pub enum AdfError {
    #[error("Parse error at line {line}: {message}")]
    ParseError {
        line: usize,
        message: String,
        context: Option<String>,
    },

    #[error("Validation error at path '{path}': {message}")]
    ValidationError { path: String, message: String },

    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),

    #[error("UTF-8 error: {0}")]
    Utf8Error(#[from] std::str::Utf8Error),

    #[error("{0}")]
    Other(String),
}

pub type Result<T> = std::result::Result<T, AdfError>;

impl AdfError {
    pub fn parse_error(line: usize, message: impl Into<String>) -> Self {
        AdfError::ParseError {
            line,
            message: message.into(),
            context: None,
        }
    }

    pub fn parse_error_with_context(
        line: usize,
        message: impl Into<String>,
        context: impl Into<String>,
    ) -> Self {
        AdfError::ParseError {
            line,
            message: message.into(),
            context: Some(context.into()),
        }
    }

    pub fn validation_error(path: impl Into<String>, message: impl Into<String>) -> Self {
        AdfError::ValidationError {
            path: path.into(),
            message: message.into(),
        }
    }
}
