# ADF Parser (TypeScript/JavaScript)

TypeScript/JavaScript implementation of the Augmentable Data Format (ADF) parser.

## Installation

```bash
npm install adf-parser
```

## Quick Start

```typescript
import { parse } from 'adf-parser';

const text = `
# person:
name = Matthew
age = 54

# person.hobbies:
reading
physics
coding
`;

const doc = parse(text);
console.log(doc.get('person.name')); // "Matthew"
console.log(doc.get('person.age'));  // 54
console.log(doc.get('person.hobbies')); // ["reading", "physics", "coding"]
```

## Features

- ✅ Full ADF specification compliance
- ✅ TypeScript with full type definitions
- ✅ Works in Node.js and browsers
- ✅ Absolute and relative sections
- ✅ Scalar and object arrays
- ✅ Multiline values
- ✅ Type inference
- ✅ Constraint parsing
- ✅ Document merging
- ✅ JSON export
- ✅ CLI tool included

## API

### Parsing

```typescript
import { parse, parseFile, Document } from 'adf-parser';

// Parse from string
const doc = parse(text);

// Parse from file (Node.js only)
const doc = parseFile('config.adf');

// Parse with options
const doc = parse(text, {
  inferTypes: true,
  strict: false
});
```

### Document Methods

```typescript
// Get values by path
const value = doc.get('person.name');
const defaultValue = doc.get('missing.path', 'default');

// Set values
doc.set('person.age', 55);

// Merge documents
doc.merge(otherDoc);

// Export
const obj = doc.toObject();
const json = doc.toJSON();
const adf = doc.serialize();

// Access relative sections
const relative = doc.getRelativeSections();
```

## CLI Tool

```bash
# Install globally
npm install -g adf-parser

# Parse and validate
adf parse config.adf

# Convert to JSON
adf to-json config.adf

# Format ADF file
adf format config.adf

# Show help
adf --help
```

## Browser Usage

```html
<script src="https://unpkg.com/adf-parser"></script>
<script>
  const doc = ADF.parse(text);
  console.log(doc.get('key'));
</script>
```

Or with ES modules:

```javascript
import { parse } from 'https://unpkg.com/adf-parser?module';
```

## TypeScript Types

Full TypeScript support with type definitions:

```typescript
import { Document, Value, ParseOptions } from 'adf-parser';

const options: ParseOptions = {
  inferTypes: true,
  strict: false
};

const doc: Document = parse(text, options);
const value: Value | undefined = doc.get('path');
```

## Development

```bash
# Install dependencies
npm install

# Build
npm run build

# Test
npm test

# Test with coverage
npm run test:coverage

# Lint
npm run lint

# Format
npm run format
```

## License

MIT License - See LICENSE file for details
