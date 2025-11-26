use crate::error::Result;

#[derive(Debug, Clone, PartialEq)]
pub enum TokenType {
    BlankLine,
    AbsoluteHeader,
    RelativeHeader,
    KeyValue,
    ScalarValue,
    MultilineStart,
    MultilineContent,
    MultilineEnd,
}

#[derive(Debug, Clone)]
pub struct Token {
    pub token_type: TokenType,
    pub line_number: usize,
    pub raw_line: String,
    pub path: Option<String>,
    pub is_absolute: Option<bool>,
    pub key: Option<String>,
    pub value: Option<String>,
    pub constraint: Option<String>,
    pub quote_count: Option<usize>,
}

impl Token {
    fn new(token_type: TokenType, line_number: usize, raw_line: String) -> Self {
        Token {
            token_type,
            line_number,
            raw_line,
            path: None,
            is_absolute: None,
            key: None,
            value: None,
            constraint: None,
            quote_count: None,
        }
    }
}

pub struct Lexer {
    in_multiline: bool,
    multiline_quote_count: usize,
}

impl Lexer {
    pub fn new() -> Self {
        Lexer {
            in_multiline: false,
            multiline_quote_count: 0,
        }
    }

    pub fn tokenize(&mut self, text: &str) -> Result<Vec<Token>> {
        let mut tokens = Vec::new();

        for (i, line) in text.lines().enumerate() {
            let line_number = i + 1;
            if let Some(token) = self.tokenize_line(line, line_number)? {
                tokens.push(token);
            }
        }

        Ok(tokens)
    }

    fn tokenize_line(&mut self, line: &str, line_number: usize) -> Result<Option<Token>> {
        // Handle multiline continuation
        if self.in_multiline {
            return Ok(Some(self.handle_multiline_continuation(
                line,
                line_number,
            )));
        }

        // Blank line
        if line.trim().is_empty() {
            return Ok(Some(Token::new(
                TokenType::BlankLine,
                line_number,
                line.to_string(),
            )));
        }

        // Try to parse header
        if let Some(token) = self.try_parse_header(line, line_number)? {
            return Ok(Some(token));
        }

        // Key-value pair
        if line.contains('=') {
            return Ok(Some(self.parse_key_value(line, line_number)?));
        }

        // Scalar value
        Ok(Some(Token {
            token_type: TokenType::ScalarValue,
            line_number,
            raw_line: line.to_string(),
            value: Some(line.trim().to_string()),
            ..Token::new(TokenType::ScalarValue, line_number, line.to_string())
        }))
    }

    fn try_parse_header(&self, line: &str, line_number: usize) -> Result<Option<Token>> {
        let stripped = line.trim();

        if !stripped.ends_with(':') {
            return Ok(None);
        }

        let mut path_part = stripped[..stripped.len() - 1].trim().to_string();
        let is_absolute = path_part.starts_with('#');

        if is_absolute {
            path_part = path_part[1..].trim().to_string();
        }

        // Root section
        if path_part.is_empty() && is_absolute {
            return Ok(Some(Token {
                token_type: TokenType::AbsoluteHeader,
                line_number,
                raw_line: line.to_string(),
                path: Some(String::new()),
                is_absolute: Some(true),
                ..Token::new(TokenType::AbsoluteHeader, line_number, line.to_string())
            }));
        }

        if path_part.is_empty() {
            return Ok(None);
        }

        if !Self::is_valid_path(&path_part) {
            return Ok(None);
        }

        Ok(Some(Token {
            token_type: if is_absolute {
                TokenType::AbsoluteHeader
            } else {
                TokenType::RelativeHeader
            },
            line_number,
            raw_line: line.to_string(),
            path: Some(path_part),
            is_absolute: Some(is_absolute),
            ..Token::new(
                if is_absolute {
                    TokenType::AbsoluteHeader
                } else {
                    TokenType::RelativeHeader
                },
                line_number,
                line.to_string(),
            )
        }))
    }

    fn parse_key_value(&mut self, line: &str, line_number: usize) -> Result<Token> {
        let equals_pos = line.find('=').unwrap();
        let raw_key = line[..equals_pos].trim();
        let raw_value = &line[equals_pos + 1..].trim_start();

        let key = raw_key.to_string();

        // Check for multiline value
        let quote_count = Self::count_leading_quotes(raw_value);
        if quote_count > 0 {
            self.in_multiline = true;
            self.multiline_quote_count = quote_count;

            // Check if it ends on same line
            if raw_value.len() > quote_count * 2
                && Self::ends_with_quotes(raw_value, quote_count)
            {
                // Single-line quoted value
                self.in_multiline = false;
                let value = Self::extract_quoted_value(raw_value, quote_count);
                let constraint = Self::extract_constraint_after_quotes(raw_value, quote_count);

                return Ok(Token {
                    token_type: TokenType::KeyValue,
                    line_number,
                    raw_line: line.to_string(),
                    key: Some(key),
                    value: Some(value),
                    constraint,
                    ..Token::new(TokenType::KeyValue, line_number, line.to_string())
                });
            } else {
                // Multiline start
                let content = if raw_value.len() > quote_count {
                    raw_value[quote_count..].to_string()
                } else {
                    String::new()
                };

                return Ok(Token {
                    token_type: TokenType::MultilineStart,
                    line_number,
                    raw_line: line.to_string(),
                    key: Some(key),
                    value: Some(content),
                    quote_count: Some(quote_count),
                    ..Token::new(TokenType::MultilineStart, line_number, line.to_string())
                });
            }
        }

        // Simple value
        let (value, constraint) = Self::parse_value_and_constraint(raw_value);

        Ok(Token {
            token_type: TokenType::KeyValue,
            line_number,
            raw_line: line.to_string(),
            key: Some(key),
            value: Some(value),
            constraint,
            ..Token::new(TokenType::KeyValue, line_number, line.to_string())
        })
    }

    fn handle_multiline_continuation(&mut self, line: &str, line_number: usize) -> Token {
        if Self::ends_with_quotes(line, self.multiline_quote_count) {
            self.in_multiline = false;
            let content = if line.len() >= self.multiline_quote_count {
                line[..line.len() - self.multiline_quote_count]
                    .trim_end()
                    .to_string()
            } else {
                String::new()
            };
            let constraint = Self::extract_constraint_after_line(line, self.multiline_quote_count);

            Token {
                token_type: TokenType::MultilineEnd,
                line_number,
                raw_line: line.to_string(),
                value: Some(content),
                constraint,
                ..Token::new(TokenType::MultilineEnd, line_number, line.to_string())
            }
        } else {
            Token {
                token_type: TokenType::MultilineContent,
                line_number,
                raw_line: line.to_string(),
                value: Some(line.to_string()),
                ..Token::new(TokenType::MultilineContent, line_number, line.to_string())
            }
        }
    }

    fn is_valid_path(path: &str) -> bool {
        if path.is_empty() {
            return true;
        }

        for part in path.split('.') {
            if part.starts_with('"') && part.ends_with('"') {
                continue; // Quoted key
            }
            if !part
                .chars()
                .all(|c| c.is_alphanumeric() || c == '_')
            {
                return false;
            }
        }
        true
    }

    fn count_leading_quotes(s: &str) -> usize {
        s.chars().take_while(|&c| c == '"').count()
    }

    fn ends_with_quotes(s: &str, count: usize) -> bool {
        if s.len() < count {
            return false;
        }
        s.chars().rev().take(count).all(|c| c == '"')
    }

    fn extract_quoted_value(s: &str, quote_count: usize) -> String {
        if s.len() < quote_count * 2 {
            return String::new();
        }
        s[quote_count..s.len() - quote_count].to_string()
    }

    fn extract_constraint_after_quotes(s: &str, quote_count: usize) -> Option<String> {
        if s.len() <= quote_count * 2 {
            return None;
        }
        let after = &s[s.len() - quote_count..];
        Self::parse_constraint(after)
    }

    fn extract_constraint_after_line(line: &str, quote_count: usize) -> Option<String> {
        if line.len() < quote_count {
            return None;
        }
        let after = &line[line.len() - quote_count..];
        Self::parse_constraint(after)
    }

    fn parse_value_and_constraint(s: &str) -> (String, Option<String>) {
        let constraint = Self::parse_constraint(s);
        if let Some(_) = &constraint {
            if let Some(paren_pos) = s.rfind('(') {
                let value = s[..paren_pos].trim_end().to_string();
                return (value, constraint);
            }
        }
        (s.trim().to_string(), None)
    }

    fn parse_constraint(s: &str) -> Option<String> {
        let trimmed = s.trim();
        if trimmed.is_empty() {
            return None;
        }

        let open_paren = trimmed.rfind('(')?;
        let close_paren = trimmed.rfind(')')?;

        if close_paren < open_paren {
            return None;
        }

        let constraint = trimmed[open_paren + 1..close_paren].trim();
        if constraint.is_empty() {
            None
        } else {
            Some(constraint.to_string())
        }
    }
}

impl Default for Lexer {
    fn default() -> Self {
        Self::new()
    }
}
