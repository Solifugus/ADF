# Augmentable Data Format (ADF) — Specification (v0)

**ADF** is a simple, human-friendly notation for representing and *augmenting*
hierarchical data. It is designed to be easy for humans and AI models to read
and write, while remaining straightforward for software to parse.

ADF intentionally avoids braces, brackets, commas, and rigid typing. Instead,
it uses:

- `#` and dot-notation paths for hierarchy
- `key = value` for associative mappings
- natural line and blank-line structure for arrays
- repeated quotes for multiline strings
- optional constraints in parentheses after values
- progressive augmentation: multiple documents can merge into one structure
- both absolute and relative sections for rooted and relocatable data

This document defines the core notation. Future extensions must remain
compatible with these rules.

---

## 1. Sections and Paths

An ADF document is divided into **sections**. Each section begins with a
header line that ends with a colon `:`:

```text
# path.to.location:
path.to.location:
```

There are two kinds of sections:

- **Absolute sections**: headers that begin with `#`
- **Relative sections**: headers that do not begin with `#`

### 1.1 Absolute sections

An absolute section header has the form:

```text
# path.to.location:
```

Rules:

- The line must start with `#`.
- It is followed immediately or after a space by a **path**.
- The path is a dot-separated sequence of simple keys.
- The line ends with a colon `:`.

The path identifies where in the **root** data tree subsequent content
will be written.

Special case:

- `#:` refers to the **root object**.

Examples:

```text
#:
# person:
# system.settings.ui.theme:
```

All non-header lines after an absolute header apply to that section
until the next header or end of file.

### 1.2 Relative sections

A relative section header has the form:

```text
path.to.location:
```

without a leading `#`.

Rules:

- The line begins with a path (no `#` prefix).
- The path is a dot-separated sequence of simple keys.
- The line ends with a colon `:`.

A relative section defines a **relocatable subtree** whose interpretation
depends on the embedding environment. For example:

```text
upgrade.stats:
strength = 12
agility = 9
```

represents a fragment that could be merged under any parent path, such as
`player.` to yield `player.upgrade.stats` or used to override
`player.stats`.

Relative sections are a key part of ADF's augmentable design, enabling
patches, overlays, and modular data fragments.

---

## 2. Keys and Values

Within a section, the most common construct is a **key/value pair**:

```text
key = value
```

Rules:

- There must be exactly one `=` character used as the separator.
- Whitespace around the key and around `=` is ignored.
- The key is taken from the text before `=`.
- The value is taken from the text after `=`, subject to the rules for
  simple values, quoted blocks, and constraints (see below).

### 2.1 Dot-notation keys

Keys may themselves contain dot-notation, which addresses deeper
paths relative to the section path:

```text
#:

user.name = Matthew
user.address.city = Fayetteville
user.address.state = NY
```

If the section path is `# person:`, then:

```text
# person:
name = Matthew
address.city = Fayetteville
```

is equivalent to writing those fields under `person.name` and
`person.address.city` in the root.

Implementations MUST treat section paths and key paths as a unified
hierarchical addressing mechanism.

---

## 3. Arrays

ADF supports arrays without requiring `[]` or commas. Arrays are defined
by the **structure of lines inside a section**.

### 3.1 Arrays of scalars

If a section contains non-empty lines **none of which contain `=`**, the
section is interpreted as an array of scalar values:

```text
# hobbies:
reading
physics
coding
```

This corresponds to:

```json
{
  "hobbies": ["reading", "physics", "coding"]
}
```

### 3.2 Arrays of objects

If a section contains one or more blocks of `key = value` pairs,
separated by **blank lines**, then the section is interpreted as an
array of objects:

```text
# users:

name = Alice
age = 22

name = Bob
age = 30
```

This corresponds to:

```json
{
  "users": [
    { "name": "Alice", "age": 22 },
    { "name": "Bob", "age": 30 }
  ]
}
```

Rules:

- A **block** is a consecutive run of one or more `key = value` lines,
  separated from other blocks by one or more blank lines.
- Each block becomes an object.
- The order of blocks determines the order of array elements.

### 3.3 Mixed content

It is recommended that implementations treat a section as **either**:

- a scalar array section (no `=` in any non-empty line), or
- an object array section (one or more blocks of `key = value`), or
- a plain object (only `key = value` and no blank-line separation semantics)

Mixing bare values and `key = value` lines in the same section should
be treated as an error or left undefined.

---

## 4. Multiline Values

A value may be a **multiline string** using repeated-quote delimiters.

If the value begins with **N adjacent double quotes** (`"`), where
`N >= 1`, then the value is considered a quoted block and continues
until a line whose trailing characters include the same sequence
of N quotes.

Example with triple quotes:

```text
bio = """
This is a multiline block.
It may contain "quotes" freely.
"""
```

- The opening delimiter is the sequence `"""` immediately after `=`.
- The content of the value includes all lines after the opening
  delimiter, up to but not including the line with the closing
  delimiter.
- The closing delimiter is `"""` at the **end of a line**.
- Any shorter sequence of `"` inside the block is treated as
  plain content and does not terminate the block.

Longer delimiters allow quoting inside quoting:

```text
example = """"This string contains """quoted""" text""""
```

Here:

- The outer delimiter is `""""` (four quotes).
- The inner `"""quoted"""` is part of the content.

Implementations MUST treat the content of a multiline block as raw text
with newlines preserved.

---

## 5. Optional Constraints

A value may be followed by a pair of parentheses containing an
optional **constraint annotation**:

```text
age = 54 (>= 0)
status = pending (enum pending,paid,canceled)
ratio = 0.32 (0 <= value <= 1)
```

Rules:

- A constraint, if present, MUST follow the value after at least one
  space.
- The constraint begins with `(` and ends with the matching `)`.
- The text inside parentheses is captured verbatim as the constraint.
- The ADF core specification does **not** interpret constraint content.
  Tools may use it for validation, documentation, or hints.

Examples are intentionally informal and may use operators or keywords
(e.g., `>=`, `enum`, `pattern`, `min`, `max`, etc.), but these are not
standardized at the notation level.

Constraints may also appear after multiline values:

```text
description = """
Long text...
""" (maxlen 2048, nonempty)
```

---

## 6. Whitespace Rules

- Leading and trailing whitespace on header lines and `key = value`
  lines (outside values and constraints) SHOULD be ignored.
- Blank lines:
  - separate object-array entries in a section intended as an array
    of objects,
  - are otherwise insignificant and may be ignored.
- Indentation at the beginning of a line is allowed but is not
  semantically meaningful in core ADF.

Within multiline values, all whitespace is preserved exactly.

---

## 7. Augmentation and Merging

Multiple ADF documents (or multiple sections within a document) can
**augment** the same paths.

### 7.1 Augmenting absolute sections

When two absolute sections address the same path:

```text
# player.stats:
strength = 10

# player.stats:
agility = 7
```

an implementation that merges these sections SHOULD produce:

```json
{
  "player": {
    "stats": {
      "strength": 10,
      "agility": 7
    }
  }
}
```

Later definitions at the same path MAY override earlier scalar values:

```text
# config:
mode = basic

# config:
mode = advanced
```

Here `config.mode` is expected to become `"advanced"` after merging.

### 7.2 Merging relative sections

Relative sections define subtrees that can be attached anywhere. For example:

```text
upgrade.stats:
strength = 12
agility = 9
```

This fragment might be interpreted as:

- `player.upgrade.stats` (attached under `player`), or
- a replacement for `player.stats`, or
- a library of reusable upgrades.

Exact merge semantics (where to attach, override vs merge) are left to
the embedding application, but ADF is intended to support progressive
enhancement, patching, and modular composition of hierarchical data.

---

## 8. Data Model

ADF maps conceptually onto a tree of:

- **objects** (maps / dictionaries)
- **arrays** (lists)
- **scalars**: strings, numbers, booleans, null (if supported)

The core notation does not enforce or prescribe a specific type system.
Parsers MAY:

- treat all values as strings, or
- attempt simple inference (e.g., `true`/`false` → booleans,
  numeric literals → numbers), according to their use case.

---

## 9. Error Handling

ADF aims to be easy to write by hand and generate from AI systems.

Implementations MAY choose one of two broad strategies:

- **Lenient mode**:
  - skip malformed lines where possible,
  - collect best-effort structure,
  - log or report non-fatal parsing issues.

- **Strict mode**:
  - treat malformed constructs as errors,
  - reject documents that violate structure rules.

Examples of malformed constructs include:

- headers without a trailing colon,
- `key = value` lines with no key or no value,
- unterminated multiline quote blocks.

---

## 10. Forward Compatibility

Future extensions to ADF may introduce:

- comments,
- metadata sections,
- richer constraint conventions,
- references or links between paths,
- optional typing annotations.

Such extensions MUST NOT break the core syntax defined in this document
and SHOULD be designed so that older parsers can safely ignore
unrecognized constructs.
