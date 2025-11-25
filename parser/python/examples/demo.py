#!/usr/bin/env python3
"""
Demo script showing ADF parser capabilities
"""

from adf import parse, parse_file

# Example 1: Simple parsing
print("=" * 60)
print("Example 1: Simple key-value pairs")
print("=" * 60)

text1 = """
# person:
name = Matthew
age = 54
city = Fayetteville
"""

doc1 = parse(text1)
print(f"Name: {doc1.get('person.name')}")
print(f"Age: {doc1.get('person.age')}")
print(f"City: {doc1.get('person.city')}")
print(f"\nFull structure: {doc1.to_dict()}")

# Example 2: Arrays
print("\n" + "=" * 60)
print("Example 2: Scalar and Object Arrays")
print("=" * 60)

text2 = """
# hobbies:
reading
physics
coding

# users:

name = Alice
age = 22

name = Bob
age = 30
"""

doc2 = parse(text2)
print(f"Hobbies: {doc2.get('hobbies')}")
print(f"Users: {doc2.get('users')}")

# Example 3: Multiline values
print("\n" + "=" * 60)
print("Example 3: Multiline strings")
print("=" * 60)

text3 = '''
# article:
title = My Article
body = """
This is a multiline body.
It can contain multiple lines.
And even "quotes" inside.
"""
'''

doc3 = parse(text3)
print(f"Title: {doc3.get('article.title')}")
print(f"Body:\n{doc3.get('article.body')}")

# Example 4: Type inference
print("\n" + "=" * 60)
print("Example 4: Type inference")
print("=" * 60)

text4 = """
#:
count = 42
ratio = 3.14
enabled = true
disabled = false
name = Matthew
"""

doc4 = parse(text4)
print(f"count = {doc4.get('count')} (type: {type(doc4.get('count')).__name__})")
print(f"ratio = {doc4.get('ratio')} (type: {type(doc4.get('ratio')).__name__})")
print(f"enabled = {doc4.get('enabled')} (type: {type(doc4.get('enabled')).__name__})")
print(f"name = {doc4.get('name')} (type: {type(doc4.get('name')).__name__})")

# Example 5: Parsing a file
print("\n" + "=" * 60)
print("Example 5: Parsing from file")
print("=" * 60)

try:
    doc5 = parse_file("../../../examples/config_full.adf")
    print(f"App name: {doc5.get('app.name')}")
    print(f"App version: {doc5.get('app.version')}")
    print(f"Theme: {doc5.get('app.ui.theme')}")
    print(f"Features: {doc5.get('app.features')}")
    print(f"Server port: {doc5.get('app.server.port')}")
except FileNotFoundError:
    print("Example file not found (expected if running from different directory)")

# Example 6: Serialization
print("\n" + "=" * 60)
print("Example 6: Round-trip serialization")
print("=" * 60)

text6 = """
# config:
name = MyApp
version = 1.0

# config.features:
feature1
feature2
"""

doc6 = parse(text6)
print("Original parsed:")
print(doc6.to_dict())

serialized = doc6.serialize()
print("\nSerialized back to ADF:")
print(serialized)

# Example 7: Relative sections
print("\n" + "=" * 60)
print("Example 7: Relative sections (relocatable fragments)")
print("=" * 60)

text7 = """
upgrade.stats:
strength = 12
agility = 9
"""

doc7 = parse(text7)
print("Relative sections:")
print(doc7.get_relative_sections())

print("\n" + "=" * 60)
print("Demo complete!")
print("=" * 60)
