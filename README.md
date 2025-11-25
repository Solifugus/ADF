# Augmentable Data Format (ADF)

**ADF** is a minimal, human-friendly, AI-friendly data notation designed for representing
and *augmenting* hierarchical data without the complexity of JSON, YAML, or XML.

ADF emphasizes:

- **Dot-notation paths** for clear hierarchy
- **Associative mappings** with `key = value`
- **Arrays** created naturally from line structure
- **Intuitive multiline strings** using repeated-quote delimiters
- **Optional constraints** that follow values in parentheses
- **Progressive augmentation** — multiple ADF documents can merge into one structure
- **Zero braces, brackets, or commas**
- **Absolute and relative sections** — data can be rooted or relocatable

ADF is ideal for:

- human-edited configuration  
- AI-generated structured output  
- data merging and upgrades  
- hierarchical state for agents  
- editable persistent memory structures  
- documentation mixed with structured content  

---

## Example (absolute sections)

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

# person.bio = """
Grew up in a cabin without electricity.
Writes about AI and builds experimental devices.
"""
```

This corresponds to hierarchical data equivalent to JSON:

```json
{
  "person": {
    "name": "Matthew",
    "age": 54,
    "hobbies": ["reading","physics","coding"],
    "pets": [
      {"name": "Luna", "species": "mouse"},
      {"name": "Ember", "species": "chicken"}
    ],
    "bio": "Grew up in a cabin without electricity.\nWrites about AI and builds experimental devices.\n"
  }
}
```

---

## Absolute vs Relative Sections

ADF supports both **absolute** and **relative** sections.

### Absolute sections (anchored at root)

A header that begins with `#` writes data relative to the document root:

```adf
# player.stats:
strength = 10
agility = 7
```

This anchors data under `player.stats` in the root structure.

### Relative sections (relocatable fragments)

A header that does **not** begin with `#` defines a *relocatable* subtree:

```adf
upgrade.stats:
strength = 12
agility = 9
```

This fragment can be merged under any parent path by the embedding system, e.g.:

```json
{
  "player": {
    "stats": {
      "strength": 12,
      "agility": 9
    }
  }
}
```

Relative sections are useful for:

- patches and upgrades  
- modular configuration fragments  
- AI-generated “diffs” or overlays  
- reusable building blocks of state  

---

## Why “Augmentable”?

ADF allows multiple documents to *extend*, *override*, or *add to* the same structure simply
by restating sections:

```adf
# player.stats:
strength = 10

# player.stats:
agility = 7
```

These seamlessly merge into:

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

This makes ADF extremely powerful for:

- version upgrades  
- compiled additions  
- layered configuration  
- AI incremental updates  
- dynamic state evolution  

---

## Documentation

- **SPEC.md** — The formal specification  
- **SYNTAX.md** — Syntax rules and parsing behavior  
- **examples/** — Example ADF documents  

A reference parser implementation may be provided in Python, JavaScript, or Rust.

---

## License

MIT License (recommended)
