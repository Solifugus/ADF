import { parse } from './parser';

describe('ADF Parser', () => {
  describe('basic parsing', () => {
    test('simple key-value pairs', () => {
      const text = `
# person:
name = Matthew
age = 54
`;
      const doc = parse(text);
      expect(doc.get('person.name')).toBe('Matthew');
      expect(doc.get('person.age')).toBe(54);
    });

    test('nested paths', () => {
      const text = `
# person.address:
city = Fayetteville
state = NY
`;
      const doc = parse(text);
      expect(doc.get('person.address.city')).toBe('Fayetteville');
      expect(doc.get('person.address.state')).toBe('NY');
    });

    test('root section', () => {
      const text = `
#:
name = ADF
version = 0.1
`;
      const doc = parse(text);
      expect(doc.get('name')).toBe('ADF');
      expect(doc.get('version')).toBe(0.1);
    });
  });

  describe('arrays', () => {
    test('scalar array', () => {
      const text = `
# hobbies:
reading
physics
coding
`;
      const doc = parse(text);
      const hobbies = doc.get('hobbies');
      expect(Array.isArray(hobbies)).toBe(true);
      expect(hobbies).toEqual(['reading', 'physics', 'coding']);
    });

    test('object array', () => {
      const text = `
# users:

name = Alice
age = 22

name = Bob
age = 30
`;
      const doc = parse(text);
      const users = doc.get('users') as any[];
      expect(users.length).toBe(2);
      expect(users[0]).toEqual({ name: 'Alice', age: 22 });
      expect(users[1]).toEqual({ name: 'Bob', age: 30 });
    });
  });

  describe('multiline values', () => {
    test('triple quotes', () => {
      const text = `
# article:
body = """
This is line one.
This is line two.
"""
`;
      const doc = parse(text);
      const body = doc.get('article.body');
      expect(body).toContain('line one');
      expect(body).toContain('line two');
      expect(body).toBe('This is line one.\nThis is line two.');
    });
  });

  describe('type inference', () => {
    test('integers', () => {
      const text = `
#:
count = 42
negative = -10
`;
      const doc = parse(text);
      expect(doc.get('count')).toBe(42);
      expect(doc.get('negative')).toBe(-10);
      expect(typeof doc.get('count')).toBe('number');
    });

    test('floats', () => {
      const text = `
#:
pi = 3.14159
ratio = 0.5
`;
      const doc = parse(text);
      expect(doc.get('pi')).toBe(3.14159);
      expect(doc.get('ratio')).toBe(0.5);
    });

    test('booleans', () => {
      const text = `
#:
enabled = true
disabled = false
`;
      const doc = parse(text);
      expect(doc.get('enabled')).toBe(true);
      expect(doc.get('disabled')).toBe(false);
    });

    test('no type inference', () => {
      const text = `
#:
count = 42
enabled = true
`;
      const doc = parse(text, { inferTypes: false });
      expect(doc.get('count')).toBe('42');
      expect(doc.get('enabled')).toBe('true');
    });
  });

  describe('augmentation', () => {
    test('multiple sections same path', () => {
      const text = `
# config:
name = MyApp

# config:
version = 1.0
`;
      const doc = parse(text);
      expect(doc.get('config.name')).toBe('MyApp');
      expect(doc.get('config.version')).toBe(1.0);
    });
  });

  describe('relative sections', () => {
    test('relative section', () => {
      const text = `
upgrade.stats:
strength = 12
agility = 9
`;
      const doc = parse(text);
      const relative = doc.getRelativeSections();
      expect(relative).toHaveProperty('upgrade');
    });
  });

  describe('document methods', () => {
    test('empty document', () => {
      const doc = parse('');
      expect(doc.toObject()).toEqual({});
    });

    test('toObject', () => {
      const text = `
# person:
name = Matthew
age = 54
`;
      const doc = parse(text);
      const obj = doc.toObject();
      expect(obj).toEqual({ person: { name: 'Matthew', age: 54 } });
    });

    test('toJSON', () => {
      const text = `
# person:
name = Matthew
age = 54
`;
      const doc = parse(text);
      const json = doc.toJSON();
      expect(json).toContain('"name": "Matthew"');
      expect(json).toContain('"age": 54');
    });
  });

  describe('dot notation in keys', () => {
    test('nested keys', () => {
      const text = `
# server:
host.primary = localhost
host.backup = backup.example.com
`;
      const doc = parse(text);
      expect(doc.get('server.host.primary')).toBe('localhost');
      expect(doc.get('server.host.backup')).toBe('backup.example.com');
    });
  });
});
