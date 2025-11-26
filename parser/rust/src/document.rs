use crate::error::{AdfError, Result};
use crate::value::Value;
use std::collections::HashMap;

/// Represents a parsed ADF document
#[derive(Debug, Clone, PartialEq)]
pub struct Document {
    root: HashMap<String, Value>,
    relative_sections: HashMap<String, Value>,
}

impl Document {
    /// Create a new empty document
    pub fn new() -> Self {
        Document {
            root: HashMap::new(),
            relative_sections: HashMap::new(),
        }
    }

    /// Get a value by dot-notation path (returns clone)
    pub fn get(&self, path: &str) -> Option<Value> {
        if path.is_empty() {
            return Some(Value::Object(self.root.clone()));
        }

        let parts = Self::parse_path(path);
        let mut current = Value::Object(self.root.clone());

        for part in parts {
            match current {
                Value::Object(map) => {
                    current = map.get(&part)?.clone();
                }
                _ => return None,
            }
        }

        Some(current)
    }

    /// Set a value by dot-notation path
    pub fn set(&mut self, path: &str, value: Value) -> Result<()> {
        if path.is_empty() {
            if let Value::Object(obj) = value {
                self.root = obj;
            }
            return Ok(());
        }

        let parts = Self::parse_path(path);
        let mut current = &mut self.root;

        for (i, part) in parts.iter().enumerate() {
            if i == parts.len() - 1 {
                // Last part - set the value
                current.insert(part.clone(), value);
                return Ok(());
            }

            // Navigate or create intermediate objects
            current = current
                .entry(part.clone())
                .or_insert_with(|| Value::Object(HashMap::new()))
                .as_object_mut()
                .ok_or_else(|| {
                    AdfError::validation_error(
                        path,
                        format!("Cannot set nested value: '{}' is not an object", part),
                    )
                })?;
        }

        Ok(())
    }

    /// Merge another document into this one
    pub fn merge(&mut self, other: &Document) {
        self.root = Self::deep_merge_objects(&self.root, &other.root);
    }

    /// Merge data at a specific path
    pub fn merge_at_path(&mut self, path: &str, value: Value) -> Result<()> {
        if let Some(existing) = self.get(path) {
            if let (Value::Object(existing_obj), Value::Object(new_obj)) =
                (&existing, &value)
            {
                let merged = Self::deep_merge_objects(existing_obj, new_obj);
                self.set(path, Value::Object(merged))?;
                return Ok(());
            }
        }
        self.set(path, value)
    }

    /// Get relative sections
    pub fn relative_sections(&self) -> &HashMap<String, Value> {
        &self.relative_sections
    }

    /// Add a relative section
    pub fn add_relative_section(&mut self, path: &str, value: Value) {
        let parts = Self::parse_path(path);
        let mut current = &mut self.relative_sections;

        for (i, part) in parts.iter().enumerate() {
            if i == parts.len() - 1 {
                current.insert(part.clone(), value);
                return;
            }

            current = current
                .entry(part.clone())
                .or_insert_with(|| Value::Object(HashMap::new()))
                .as_object_mut()
                .expect("Should be object");
        }
    }

    /// Convert to HashMap (consuming self)
    pub fn into_map(self) -> HashMap<String, Value> {
        self.root
    }

    /// Get reference to root map
    pub fn as_map(&self) -> &HashMap<String, Value> {
        &self.root
    }

    /// Convert to JSON string (requires serde feature)
    #[cfg(feature = "serde")]
    pub fn to_json(&self) -> Result<String> {
        serde_json::to_string_pretty(&self.root).map_err(|e| AdfError::Other(e.to_string()))
    }

    /// Parse a dot-notation path into parts
    fn parse_path(path: &str) -> Vec<String> {
        let mut parts = Vec::new();
        let mut current = String::new();
        let mut in_quotes = false;

        for ch in path.chars() {
            match ch {
                '"' => {
                    in_quotes = !in_quotes;
                    current.push(ch);
                }
                '.' if !in_quotes => {
                    if !current.is_empty() {
                        parts.push(Self::unquote_key(&current));
                        current.clear();
                    }
                }
                _ => current.push(ch),
            }
        }

        if !current.is_empty() {
            parts.push(Self::unquote_key(&current));
        }

        parts
    }

    /// Remove quotes from a quoted key
    fn unquote_key(key: &str) -> String {
        if key.starts_with('"') && key.ends_with('"') && key.len() >= 2 {
            key[1..key.len() - 1].to_string()
        } else {
            key.to_string()
        }
    }

    /// Deep merge two objects
    fn deep_merge_objects(
        base: &HashMap<String, Value>,
        overlay: &HashMap<String, Value>,
    ) -> HashMap<String, Value> {
        let mut result = base.clone();

        for (key, overlay_val) in overlay {
            if let Some(base_val) = result.get(key) {
                if let (Value::Object(base_obj), Value::Object(overlay_obj)) =
                    (base_val, overlay_val)
                {
                    result.insert(key.clone(), Value::Object(Self::deep_merge_objects(base_obj, overlay_obj)));
                    continue;
                }
            }
            result.insert(key.clone(), overlay_val.clone());
        }

        result
    }
}

impl Default for Document {
    fn default() -> Self {
        Self::new()
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
