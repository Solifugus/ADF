use crate::document::Document;
use crate::error::{AdfError, Result};
use crate::lexer::{Lexer, Token, TokenType};
use crate::value::Value;
use std::collections::HashMap;

pub struct Parser {
    infer_types: bool,
    strict: bool,
}

#[derive(Debug, Clone)]
pub struct ParseOptions {
    pub infer_types: bool,
    pub strict: bool,
}

impl Default for ParseOptions {
    fn default() -> Self {
        ParseOptions {
            infer_types: true,
            strict: false,
        }
    }
}

impl Parser {
    pub fn new(options: ParseOptions) -> Self {
        Parser {
            infer_types: options.infer_types,
            strict: options.strict,
        }
    }

    pub fn parse(&self, text: &str) -> Result<Document> {
        let mut lexer = Lexer::new();
        let tokens = lexer.tokenize(text)?;

        let mut document = Document::new();
        self.parse_tokens(&tokens, &mut document)?;

        Ok(document)
    }

    fn parse_tokens(&self, tokens: &[Token], document: &mut Document) -> Result<()> {
        let mut i = 0;
        let mut current_section_path = String::new();
        let mut current_is_absolute = true;
        let mut section_start = 0;

        while i < tokens.len() {
            let token = &tokens[i];

            match token.token_type {
                TokenType::AbsoluteHeader | TokenType::RelativeHeader => {
                    // Process previous section
                    if i > section_start {
                        let section_tokens = &tokens[section_start..i];
                        self.process_section(
                            section_tokens,
                            &current_section_path,
                            current_is_absolute,
                            document,
                        )?;
                    }

                    // Start new section
                    current_section_path = token.path.clone().unwrap_or_default();
                    current_is_absolute = token.is_absolute.unwrap_or(false);
                    section_start = i + 1;
                }
                _ => {}
            }

            i += 1;
        }

        // Process final section
        if section_start < tokens.len() {
            let section_tokens = &tokens[section_start..];
            self.process_section(
                section_tokens,
                &current_section_path,
                current_is_absolute,
                document,
            )?;
        }

        Ok(())
    }

    fn process_section(
        &self,
        tokens: &[Token],
        section_path: &str,
        is_absolute: bool,
        document: &mut Document,
    ) -> Result<()> {
        if tokens.is_empty() {
            return Ok(());
        }

        // Filter out blank lines for analysis
        let content_tokens: Vec<&Token> = tokens
            .iter()
            .filter(|t| t.token_type != TokenType::BlankLine)
            .collect();

        if content_tokens.is_empty() {
            return Ok(());
        }

        // Determine section type
        let has_key_value = content_tokens.iter().any(|t| {
            matches!(
                t.token_type,
                TokenType::KeyValue | TokenType::MultilineStart
            )
        });

        if !has_key_value {
            // Scalar array
            let values: Vec<Value> = content_tokens
                .iter()
                .filter_map(|t| t.value.as_ref())
                .map(|v| self.infer_type(v))
                .collect();

            if is_absolute {
                document.set(section_path, Value::Array(values))?;
            } else {
                document.add_relative_section(section_path, Value::Array(values));
            }
        } else {
            // Check for object array (blank line separators)
            if self.has_blank_line_separators(tokens) {
                let objects = self.parse_object_array(tokens)?;
                if is_absolute {
                    document.set(section_path, Value::Array(objects))?;
                } else {
                    document.add_relative_section(section_path, Value::Array(objects));
                }
            } else {
                // Plain object
                let obj = self.parse_object(tokens)?;
                if is_absolute {
                    for (key, value) in obj {
                        let full_path = if section_path.is_empty() {
                            key
                        } else {
                            format!("{}.{}", section_path, key)
                        };
                        document.merge_at_path(&full_path, value)?;
                    }
                } else {
                    document.add_relative_section(section_path, Value::Object(obj));
                }
            }
        }

        Ok(())
    }

    fn has_blank_line_separators(&self, tokens: &[Token]) -> bool {
        let mut has_blank = false;
        let mut has_content_after_blank = false;
        let mut found_content = false;

        for token in tokens {
            if token.token_type == TokenType::BlankLine {
                if found_content {
                    has_blank = true;
                    found_content = false;
                }
            } else if matches!(
                token.token_type,
                TokenType::KeyValue | TokenType::MultilineStart
            ) {
                if has_blank {
                    has_content_after_blank = true;
                }
                found_content = true;
            }
        }

        has_blank && has_content_after_blank
    }

    fn parse_object_array(&self, tokens: &[Token]) -> Result<Vec<Value>> {
        let mut objects = Vec::new();
        let mut current_object = HashMap::new();

        let mut i = 0;
        while i < tokens.len() {
            let token = &tokens[i];

            match token.token_type {
                TokenType::BlankLine => {
                    if !current_object.is_empty() {
                        objects.push(Value::Object(current_object));
                        current_object = HashMap::new();
                    }
                }
                TokenType::KeyValue => {
                    if let (Some(key), Some(value)) = (&token.key, &token.value) {
                        current_object.insert(key.clone(), self.infer_type(value));
                    }
                }
                TokenType::MultilineStart => {
                    let (value, new_i) = self.collect_multiline(tokens, i)?;
                    if let Some(key) = &token.key {
                        current_object.insert(key.clone(), Value::String(value));
                    }
                    i = new_i;
                }
                _ => {}
            }

            i += 1;
        }

        // Don't forget last object
        if !current_object.is_empty() {
            objects.push(Value::Object(current_object));
        }

        Ok(objects)
    }

    fn parse_object(&self, tokens: &[Token]) -> Result<HashMap<String, Value>> {
        let mut obj = HashMap::new();

        let mut i = 0;
        while i < tokens.len() {
            let token = &tokens[i];

            match token.token_type {
                TokenType::KeyValue => {
                    if let (Some(key), Some(value)) = (&token.key, &token.value) {
                        self.set_nested_value(&mut obj, key, self.infer_type(value))?;
                    }
                }
                TokenType::MultilineStart => {
                    let (value, new_i) = self.collect_multiline(tokens, i)?;
                    if let Some(key) = &token.key {
                        self.set_nested_value(&mut obj, key, Value::String(value))?;
                    }
                    i = new_i;
                }
                _ => {}
            }

            i += 1;
        }

        Ok(obj)
    }

    fn collect_multiline(&self, tokens: &[Token], start_idx: usize) -> Result<(String, usize)> {
        let mut parts = Vec::new();

        // Add initial content
        if let Some(value) = &tokens[start_idx].value {
            if !value.is_empty() {
                parts.push(value.clone());
            }
        }

        let mut i = start_idx + 1;
        while i < tokens.len() {
            let token = &tokens[i];

            match token.token_type {
                TokenType::MultilineContent => {
                    if let Some(value) = &token.value {
                        parts.push(value.clone());
                    }
                }
                TokenType::MultilineEnd => {
                    if let Some(value) = &token.value {
                        if !value.is_empty() {
                            parts.push(value.clone());
                        }
                    }
                    break;
                }
                _ => {}
            }

            i += 1;
        }

        Ok((parts.join("\n"), i))
    }

    fn set_nested_value(
        &self,
        obj: &mut HashMap<String, Value>,
        key: &str,
        value: Value,
    ) -> Result<()> {
        if key.contains('.') {
            let parts: Vec<&str> = key.split('.').collect();
            let mut current = obj;

            for (i, part) in parts.iter().enumerate() {
                if i == parts.len() - 1 {
                    current.insert(part.to_string(), value);
                    return Ok(());
                }

                current = current
                    .entry(part.to_string())
                    .or_insert_with(|| Value::Object(HashMap::new()))
                    .as_object_mut()
                    .ok_or_else(|| {
                        AdfError::parse_error(
                            0,
                            format!("Cannot set nested value: '{}' is not an object", part),
                        )
                    })?;
            }
        } else {
            obj.insert(key.to_string(), value);
        }

        Ok(())
    }

    fn infer_type(&self, value: &str) -> Value {
        if !self.infer_types {
            return Value::String(value.to_string());
        }

        // Try boolean
        match value.to_lowercase().as_str() {
            "true" => return Value::Boolean(true),
            "false" => return Value::Boolean(false),
            _ => {}
        }

        // Try integer
        if let Ok(i) = value.parse::<i64>() {
            return Value::Integer(i);
        }

        // Try float
        if let Ok(f) = value.parse::<f64>() {
            return Value::Float(f);
        }

        // Keep as string
        Value::String(value.to_string())
    }
}

// Helper trait for getting mutable object from Value
trait ValueExt {
    fn as_object_mut(&mut self) -> Option<&mut HashMap<String, Value>>;
}

impl ValueExt for Value {
    fn as_object_mut(&mut self) -> Option<&mut HashMap<String, Value>> {
        match self {
            Value::Object(obj) => Some(obj),
            _ => None,
        }
    }
}

/// Parse ADF text with default options
pub fn parse(text: &str) -> Result<Document> {
    let parser = Parser::new(ParseOptions::default());
    parser.parse(text)
}

/// Parse ADF text with custom options
pub fn parse_with_options(text: &str, options: ParseOptions) -> Result<Document> {
    let parser = Parser::new(options);
    parser.parse(text)
}

/// Parse ADF file with default options
pub fn parse_file(path: &str) -> Result<Document> {
    let text = std::fs::read_to_string(path)?;
    parse(&text)
}
