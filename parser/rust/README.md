# ADF Rust Parser

High-performance Rust implementation of the Augmentable Data Format (ADF) parser.

## Installation

Add to your `Cargo.toml`:

```toml
[dependencies]
adf-parser = "0.1"
```

## Quick Start

```rust
use adf::parse;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let text = r#"
# person:
name = Matthew
age = 54

# person.hobbies:
reading
physics
coding
"#;

    let doc = parse(text)?;

    println!("Name: {}", doc.get("person.name").unwrap().as_str().unwrap());
    println!("Age: {}", doc.get("person.age").unwrap().as_i64().unwrap());

    Ok(())
}
```

## Features

- ✅ Full ADF specification compliance
- ✅ Zero-copy parsing where possible
- ✅ Strong type safety with Rust's type system
- ✅ Absolute and relative sections
- ✅ Scalar and object arrays
- ✅ Multiline values
- ✅ Type inference
- ✅ Constraint parsing
- ✅ Serde integration (optional)
- ✅ CLI tool included

## API

### Parsing

```rust
use adf::{parse, parse_file, Document};

// Parse from string
let doc = parse(text)?;

// Parse from file
let doc = parse_file("config.adf")?;

// Parse with options
let doc = parse_with_options(text, ParseOptions {
    strict: true,
    infer_types: true,
})?;
```

### Document Access

```rust
// Get values by path
let value = doc.get("person.name");
let name = value.and_then(|v| v.as_str());

// Check value types
if let Some(val) = doc.get("person.age") {
    if val.is_integer() {
        println!("Age: {}", val.as_i64().unwrap());
    }
}

// Export to JSON (requires serde feature)
#[cfg(feature = "serde")]
let json = doc.to_json()?;
```

## CLI Tool

```bash
# Install
cargo install adf-parser

# Parse and validate
adf parse config.adf

# Convert to JSON
adf to-json config.adf

# Format ADF file
adf format config.adf

# Check syntax
adf check config.adf
```

## Performance

The Rust implementation is optimized for performance:

- Fast parsing (~10x faster than Python)
- Low memory footprint
- Zero-copy where possible
- Efficient string handling

See `benches/` for benchmark code.

## Building

```bash
# Build library
cargo build --release

# Build CLI
cargo build --release --bin adf

# Run tests
cargo test

# Run benchmarks
cargo bench
```

## License

MIT License - See LICENSE file for details
