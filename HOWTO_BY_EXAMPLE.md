# ADF by Example: A Gentle Walkthrough

This guide walks through several example ADF files to show how the notation
works in practice. It assumes you've skimmed `README.md` and have a rough
idea of sections, keys, arrays, multiline values, and constraints.

We will cover:

1. Basic objects and nested paths
2. Arrays of scalars and arrays of objects
3. Multiline text and constraints
4. Agent-style state
5. Relative sections for patches and upgrades
6. Mixed documentation + data

---

## 1. Basic objects and nested paths

File: `examples/basic.adf`

```adf
# person:
name = Matthew
age = 54

# person.location:
city = Fayetteville
state = NY
country = USA
```

### What this means

- `# person:` is an **absolute section**; everything under it goes under `person`.
- `name = Matthew` and `age = 54` are simple key/value pairs.
- `# person.location:` drills further into `person.location`.

In JSON-like form, this is:

```json
{
  "person": {
    "name": "Matthew",
    "age": 54,
    "location": {
      "city": "Fayetteville",
      "state": "NY",
      "country": "USA"
    }
  }
}
```

Key idea: **dot-notation paths** (in headers or keys) replace braces and brackets.

---

## 2. Arrays of scalars and arrays of objects

File: `examples/arrays.adf`

```adf
# hobbies:
reading
physics
coding

# users:

name = Alice
age = 22

name = Bob
age = 30
```

### Scalar array section

The `# hobbies:` section has non-empty lines with no `=`. That means:

```adf
# hobbies:
reading
physics
coding
```

is interpreted as:

```json
"hobbies": ["reading", "physics", "coding"]
```

### Array of objects section

The `# users:` section has **blocks** of `key = value` lines separated by blank lines:

```adf
# users:

name = Alice
age = 22

name = Bob
age = 30
```

This becomes:

```json
"users": [
  { "name": "Alice", "age": 22 },
  { "name": "Bob", "age": 30 }
]
```

Key idea: **arrays emerge from line and blank-line structure**, not from `[]` and commas.

---

## 3. Multiline text and constraints

File: `examples/multiline.adf`

```adf
# article:
title = "On Augmentable Data Formats"

body = """ 
An augmentable data format allows multiple documents
to extend or refine the same structure without
introducing conflicts in syntax.

This makes it suitable for configuration overlays,
AI-generated updates, and progressive system evolution.
""" 
```

### Multiline `body`

- The value after `body =` starts with `"""` (three quotes).
- The content continues until a line whose end has `"""`.
- Everything in between (including newlines) is part of the string.

This is especially useful for:

- paragraphs
- logs
- prompts
- documentation

File: `examples/constraints.adf` shows constraints:

```adf
# metrics:
requests_per_second = 124.8 (>= 0)
error_rate = 0.012 (0 <= value <= 1)
status = healthy (enum healthy,degraded,down)
```

Constraints:

- live in parentheses after the value,
- are **not** interpreted by ADF itself,
- can be used by tools for validation, docs, or hints.

Key idea: **constraints are annotations, not syntax rules**.

---

## 4. Agent-style state

File: `examples/agent_memory.adf`

This example shows how ADF can represent an AI agent's memory / state:

```adf
# agent:
id = "assistant-001"
role = "research_helper"
version = 2

# agent.profile:
display_name = "Nova"
primary_language = en
fallback_language = en
max_context_tokens = 16000 (>= 0)
```

Nested profile fields under `agent.profile`:

```json
"agent": {
  "id": "assistant-001",
  "role": "research_helper",
  "version": 2,
  "profile": {
    "display_name": "Nova",
    "primary_language": "en",
    "fallback_language": "en",
    "max_context_tokens": 16000
  }
}
```

### Arrays of domains

```adf
# agent.knowledge:
domains:
ai
philosophy
physics
writing
```

This yields:

```json
"agent": {
  "knowledge": {
    "domains": ["ai", "philosophy", "physics", "writing"]
  }
}
```

Note that here `domains:` is a nested header under `agent.knowledge:`.

### Sessions as object arrays

```adf
# agent.sessions:

id = "session-abc"
user_id = "user-123"
last_active = 2025-11-24T20:10:00Z
summary = """ 
Discussed Augmentable Data Format (ADF) and how to design
a human- and AI-friendly notation for hierarchical data.
"""

id = "session-def"
user_id = "user-123"
last_active = 2025-11-24T21:02:00Z
summary = """ 
Explored ways to represent constraints and relative sections
for modular configuration and upgrades.
"""
```

Each block becomes a session object in an array.

Key idea: ADF is **well-suited for agent logs, configs, and memories**.

---

## 5. Relative sections as patches and upgrades

File: `examples/upgrade_patch.adf`

```adf
# This file illustrates relative sections used as a patch / upgrade.
# It intentionally avoids leading '#' on headers so it can be merged
# into different roots (e.g., game., player., config., etc.).

balance.upgrades.stats:
health_max = 120 (>= 1)
mana_max = 80 (>= 1)

balance.upgrades.items:
"Essence Shard".stack = 10 (>= 0)

ui.overrides:
theme = "high-contrast"
font_size = 16 (>= 8)

agent.tuning:
detail_level = "high"
tone = "precise"
```

Here:

- There are **no `#`-prefixed headers**.
- Each header like `balance.upgrades.stats:` is a **relative section**.
- These fragments can be attached wherever you want:

Examples of use:

- As `game.balance.upgrades.stats` in a game.
- As `player.balance.upgrades.stats` for a specific character.
- As `config.ui.overrides` in an application.

Key idea: **ADF lets you define relocatable fragments** that can be merged into
different roots or contexts, which is perfect for upgrades, patches, and modular
configuration.

---

## 6. Mixing documentation and data

File: `examples/docs_mixed.adf`

```adf
# project:
name = "Augmentable Data Format"
short_name = "ADF"
status = "experimental"

# project.authors:

name = "Matthew"
role = "originator"

name = "Contributors"
role = "community"
```

Here `project.authors` is an array of objects.

The description uses a multiline value:

```adf
# project.description = """ 
Augmentable Data Format (ADF) is a simple, line-oriented notation
for hierarchical data that is easy for both humans and AI to read
and write.

Key properties:

- Uses dot-notation paths instead of braces or brackets
- Supports absolute (rooted) and relative (relocatable) sections
- Represents arrays using natural line and blank-line structure
- Provides intuitive multiline strings with repeated quotes
- Allows optional constraints to annotate values
- Enables progressive augmentation and patching of data
"""
```

And there’s a simple todo list as an array of objects:

```adf
# project.todo:

item = """ 
Define a standard library of constraint keywords (e.g., min, max, enum).
"""
priority = high

item = """ 
Provide a reference parser implementation and conformance tests.
"""
priority = medium

item = """ 
Explore tooling for visualizing and editing ADF trees.
"""
priority = medium
```

This is a good example of how ADF can be used for:

- documentation with structure,
- project metadata,
- planning data,
- all in a single readable file.

---

## 7. Putting it all together

Across these examples, you can see the core ADF ideas in action:

- **Sections**: `# path:` (absolute) and `path:` (relative, relocatable)
- **Objects**: `key = value` under a section
- **Arrays**:
  - scalar arrays → bare lines
  - object arrays → blocks of `key = value` separated by blank lines
- **Multiline values** → repeated quotes (`""" ... """`)
- **Constraints** → `( ... )` after a value
- **Augmentation** → multiple sections merging into a single structure

ADF aims to keep all of this **intuitive for humans** and **easy for AI
to generate**, while giving enough structure for tools to parse and merge
documents reliably.

For a deeper view of the rules, see `SPEC.md` and `SYNTAX.md`.
