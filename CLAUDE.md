# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Augmentable Data Format (ADF)** is a specification for a minimal, human-friendly, AI-friendly data notation designed for representing and augmenting hierarchical data. It is an alternative to JSON, YAML, and XML that emphasizes simplicity and progressive augmentation.

This is a **specification and documentation project** — not a software implementation. The repository contains the formal specification and examples but currently has empty parser directories.

## Core ADF Concepts

### Section Types
- **Absolute sections** (anchored at root): Headers beginning with `#`, e.g., `# person.name:`
- **Relative sections** (relocatable fragments): Headers without `#`, e.g., `upgrade.stats:`
  - Relative sections enable patches, overlays, and modular configuration

### Data Structures
- **Objects**: Represented with `key = value` pairs under a section
- **Arrays of scalars**: Non-empty lines without `=` in a section
- **Arrays of objects**: Blocks of `key = value` pairs separated by blank lines
- **Multiline values**: Use repeated quotes as delimiters, e.g., `""" ... """`
- **Constraints**: Optional annotations in parentheses after values, e.g., `age = 54 (>= 0)`

### Augmentation
Multiple ADF documents or sections can merge into one structure:
- Later definitions can extend or override earlier ones
- Relative sections can be attached to different parent paths
- This design supports version upgrades, configuration layers, and AI-generated updates

## File Structure

```
├── README.md              # Project introduction with quick examples
├── SPEC.md                # Formal specification (authoritative reference)
├── SYNTAX.md              # Technical parsing notes for implementers
├── HOWTO_BY_EXAMPLE.md    # Gentle walkthrough with annotated examples
├── examples/              # Example ADF documents
│   ├── basicadf          # Basic object structure
│   ├── arraysadf         # Scalar and object arrays
│   ├── multiline.adf     # Multiline strings
│   ├── constraints.adf   # Constraint annotations
│   ├── config_full.adf   # Full application config example
│   ├── game_state.adf    # Game state representation
│   ├── agent_memory.adf  # AI agent memory structure
│   ├── upgrade_patch.adf # Relative sections as patches
│   └── docs_mixed.adf    # Mixed documentation + data
└── parser/                # Empty directories for future implementations
    ├── python/
    ├── javascript/
    ├── rust/
    ├── c/
    ├── c++/
    ├── golang/
    └── zig/
```

## Documentation Organization

1. **README.md** — Start here for quick overview and basic examples
2. **SPEC.md** — The authoritative formal specification
3. **SYNTAX.md** — Implementation details, parsing algorithms, and edge cases
4. **HOWTO_BY_EXAMPLE.md** — Tutorial-style guide with annotated examples

When making changes to ADF behavior or syntax, SPEC.md is the source of truth.

## Key Design Principles

- **Zero braces, brackets, or commas** — Structure emerges from lines and whitespace
- **Dot-notation paths** — Replace nested braces with intuitive hierarchical addressing
- **Progressive augmentation** — Documents can be layered and merged
- **Human and AI friendly** — Easy to read, write, and generate
- **Relocatable fragments** — Relative sections enable modular composition
- **Minimal syntax** — Fewer constructs to learn and implement

## Use Cases Highlighted in Examples

- Human-edited configuration (config_full.adf)
- Game state persistence (game_state.adf)
- AI agent memory structures (agent_memory.adf)
- Data merging and upgrades (upgrade_patch.adf)
- Documentation with embedded data (docs_mixed.adf)

## Development Context

This is a specification project in early stage (v0). No parser implementations exist yet in the parser/ directories. Future work may include:

- Reference parser implementations in various languages
- Conformance test suites
- Tooling for validation and visualization
- Standard constraint keyword libraries
