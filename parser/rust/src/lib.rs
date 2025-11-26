/*!
# ADF Parser

Rust implementation of the Augmentable Data Format (ADF) parser.

## Example

```rust
use adf::parse;

let text = r#"
# person:
name = Matthew
age = 54
"#;

let doc = parse(text).unwrap();
let name_value = doc.get("person.name").unwrap();
println!("Name: {}", name_value.as_str().unwrap());
```
*/

mod document;
mod error;
mod lexer;
mod parser;
mod value;

pub use document::Document;
pub use error::{AdfError, Result};
pub use parser::{parse, parse_file, parse_with_options, ParseOptions};
pub use value::Value;
