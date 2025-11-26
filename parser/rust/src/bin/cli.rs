use adf::{parse_file, Result};
use std::env;
use std::process;

fn main() {
    if let Err(e) = run() {
        eprintln!("Error: {}", e);
        process::exit(1);
    }
}

fn run() -> Result<()> {
    let args: Vec<String> = env::args().collect();

    if args.len() < 2 {
        print_usage();
        process::exit(1);
    }

    let command = &args[1];

    match command.as_str() {
        "parse" | "check" => {
            if args.len() < 3 {
                eprintln!("Error: Missing file path");
                print_usage();
                process::exit(1);
            }
            check_file(&args[2])?;
        }
        "to-json" => {
            if args.len() < 3 {
                eprintln!("Error: Missing file path");
                print_usage();
                process::exit(1);
            }
            to_json(&args[2])?;
        }
        "--help" | "-h" => {
            print_help();
        }
        "--version" | "-v" => {
            println!("adf-parser {}", env!("CARGO_PKG_VERSION"));
        }
        _ => {
            eprintln!("Error: Unknown command '{}'", command);
            print_usage();
            process::exit(1);
        }
    }

    Ok(())
}

fn check_file(path: &str) -> Result<()> {
    let doc = parse_file(path)?;
    println!("✓ Valid ADF document");
    println!("  {} keys in root", doc.as_map().len());
    Ok(())
}

#[cfg(feature = "serde")]
fn to_json(path: &str) -> Result<()> {
    let doc = parse_file(path)?;
    let json = doc.to_json()?;
    println!("{}", json);
    Ok(())
}

#[cfg(not(feature = "serde"))]
fn to_json(_path: &str) -> Result<()> {
    eprintln!("Error: JSON support requires the 'serde' feature");
    eprintln!("Rebuild with: cargo build --features serde");
    process::exit(1);
}

fn print_usage() {
    println!("Usage: adf <command> [args]");
    println!();
    println!("Commands:");
    println!("  parse <file>     Parse and validate an ADF file");
    println!("  check <file>     Alias for parse");
    println!("  to-json <file>   Convert ADF to JSON");
    println!("  --help, -h       Show this help message");
    println!("  --version, -v    Show version");
}

fn print_help() {
    println!("ADF Parser - Rust implementation");
    println!();
    print_usage();
    println!();
    println!("Examples:");
    println!("  adf parse config.adf");
    println!("  adf to-json config.adf > config.json");
    println!();
    println!("For more information, visit: https://github.com/Solifugus/ADF");
}
