# Augmentable Data Format (ADF) — Syntax and Parsing Notes

This document gives a slightly more technical view of ADF, suitable for
implementers. It complements, but does not replace, the core rules in
**SPEC.md**.

ADF is intentionally line-oriented and forgiving. A simple parser can
handle most use cases without complex lexing or lookahead.

---

## 1. High-level Structure

An ADF document is a sequence of **sections**:

```text
document := section*
section  := header content*
header   := absolute_header | relative_header
```

- An **absolute header** begins with `#` and anchors to the root.
- A **relative header** omits `#` and represents a relocatable fragment.
- Each header line ends with a colon `:`.
- Content lines belong to the current section until the next header
  or end-of-file.

If the document begins without any header, an implementation MAY treat it
as if it had an implicit absolute `#:` header (root section).

---

## 2. Paths and Keys

A **path** is a dot-separated sequence of keys:

```text
path := key ("." key)*
key  := [A-Za-z0-9_]+
```

Section headers use paths to identify where values go:

- In absolute sections, paths are anchored at the root.
- In relative sections, paths describe a subtree that can be attached
  by the embedding system.

Within content lines, keys before `=` may also use dot-notation:

```text
user.name = Matthew
user.address.city = Fayetteville
```

The **effective path** for a `key = value` line is:

```text
effective_path = header_path + "." + key_path
```

where `header_path` is the path from the section header (absolute or
relative), and `key_path` is the key (possibly containing dots).

---

## 3. Recognizing Headers

A line is a **header** if:

- it contains a colon `:` that terminates the path, and
- the text before the colon consists of a valid path optionally preceded
  by `#`.

Examples:

```text
#:
# person:
# system.settings.ui.theme:
my.data.fragment:
upgrade.stats:
```

Classification:

- Lines beginning with `#` (after optional leading whitespace) are
  **absolute headers**.
- Lines that do not begin with `#` but match `path:` are
  **relative headers**.

The colon is required to disambiguate headers from content lines.

---

## 4. Recognizing Key/Value Pairs

Within a section, a line is treated as a `key = value` pair if:

- it contains an `=` character, and
- the `=` is not part of a quote-block delimiter.

A simple rule is to find the first `=` that occurs before the start of
any detected quote-block delimiter. Everything before that is the key,
everything after is the raw value.

Basic parsing:

```python
raw_key, raw_value = line.split("=", 1)
key   = raw_key.strip()
value = raw_value.lstrip()
```

If no `=` is found, the line is either:

- part of a scalar array, or
- empty (blank), or
- a malformed line (implementation choice).

---

## 5. Scalar Arrays vs Object Arrays vs Plain Objects

Inside a section:

- If **no** non-empty lines contain `=`, treat non-empty lines as entries
  of a **scalar array**.
- If lines contain `key = value` pairs, and there are **blank lines**
  separating groups of them, treat them as an **array of objects**.
- If lines contain `key = value` pairs and there are no blank lines used
  to separate logical blocks, treat the section as a **plain object**.

Implementers may use a simple two-pass approach per section:

1. Scan lines to see if any contain `=`.
2. If not, parse as scalar array.
3. Otherwise, decide whether blank lines should be interpreted as
   object-array separators or ignored, based on conventions or a
   configuration flag.

---

## 6. Multiline Quote Blocks

A value begins a multiline block if it starts with one or more `"`:

```text
value := quote_block | simple_value
```

To parse a quote block:

1. After reading `key =`, examine the next non-whitespace characters.
2. Count how many consecutive `"` appear. Let this be N (`N >= 1`).
3. If N > 0, this is the opening delimiter.
4. The remainder of the line after the opening delimiter (if any) is
   part of the content.
5. Then, repeatedly read subsequent lines until a line is found whose
   **end** contains exactly N consecutive `"` (ignoring trailing spaces).
6. The content of the quote block is everything between the opening
   delimiter and the closing delimiter (excluding both).

Example:

```text
bio = """
Line one.
Line two with "quotes".
"""
```

Implementations MUST preserve newlines exactly as they appear between
the delimiters.

---

## 7. Constraints

Constraints follow a value and are enclosed in parentheses:

```text
value ( constraint_text )
```

Simplest approach:

1. After parsing the value (simple or quote block), look for the first
   `(` that:
   - is preceded by whitespace, and
   - is not inside the quote block.
2. If found, parse forward to the matching `)` (e.g., the last closing
   parenthesis on the line).
3. Treat everything inside as `constraint_text`.

Example:

```text
age = 54 (>= 0)
status = pending (enum pending,paid,canceled)
description = """
Some text.
""" (maxlen 1024, nonempty)
```

The **constraint_text** is stored as a raw string. ADF itself does not
prescribe a constraint language.

---

## 8. Building the Data Tree

A simple strategy for building the final data tree from absolute sections:

1. Maintain a current absolute section path (default: root).
2. For each absolute header, update the current section path.
3. For each content line in that section:
   - If scalar array section → append value to array.
   - If object array section → accumulate key/value pairs into a temporary
     object until a blank line; then append the object to the array.
   - If plain object section → assign key/value under the effective path.
4. When the same path is assigned multiple times:
   - For objects: merge fields (later assignments override scalars).
   - For arrays: append, unless an implementation defines otherwise.

For relative sections:

- Parse them using the same rules to produce a subtree rooted at the
  relative path.
- Defer the decision of where to attach or how to merge to the embedding
  application (e.g., attach under a specific parent, use as an override,
  or treat as a reusable template).

This supports **augmentation**: later files or sections can extend or
override earlier ones, and relative fragments can be applied flexibly.

---

## 9. Reserved and Undefined Behavior

The following are intentionally left unspecified at the core level:

- Comment syntax (if any)
- Detailed constraint semantics
- Exact type inference rules
- Treatment of mixing scalar and object-style lines in one section
- Conflict resolution for deeply nested merges
- Policies for attaching relative sections

Implementations may define profiles or modes to handle these aspects
consistently within a given ecosystem.

---

## 10. Example Parsing Walkthrough

Given:

```adf
# person:
name = Matthew
age = 54 (>= 0)

# person.hobbies:
reading
physics
coding

# person.pets:

name = Luna
species = mouse

name = Ember
species = chicken

upgrade.stats:
strength = 12
agility = 9
```

A conforming implementation will construct at least the rooted structure:

```json
{
  "person": {
    "name": "Matthew",
    "age": 54,
    "hobbies": ["reading", "physics", "coding"],
    "pets": [
      { "name": "Luna", "species": "mouse" },
      { "name": "Ember", "species": "chicken" }
    ]
  }
}
```

and will additionally parse the relative fragment:

```json
{
  "upgrade": {
    "stats": {
      "strength": 12,
      "agility": 9
    }
  }
}
```

How and where that fragment is attached or applied is up to the
embedding application.

See the `examples/` folder for additional documents demonstrating the
syntax.
