"""
Basic parsing tests for ADF parser
"""

import pytest
from adf import parse, Document


def test_simple_key_value():
    """Test parsing simple key-value pairs"""
    text = """
# person:
name = Matthew
age = 54
"""
    doc = parse(text)
    assert doc.get("person.name") == "Matthew"
    assert doc.get("person.age") == 54


def test_nested_paths():
    """Test nested dot-notation paths"""
    text = """
# person.address:
city = Fayetteville
state = NY
"""
    doc = parse(text)
    assert doc.get("person.address.city") == "Fayetteville"
    assert doc.get("person.address.state") == "NY"


def test_root_section():
    """Test root section (#:)"""
    text = """
#:
name = ADF
version = 0.1
"""
    doc = parse(text)
    assert doc.get("name") == "ADF"
    assert doc.get("version") == 0.1


def test_scalar_array():
    """Test scalar array"""
    text = """
# hobbies:
reading
physics
coding
"""
    doc = parse(text)
    hobbies = doc.get("hobbies")
    assert hobbies == ["reading", "physics", "coding"]


def test_object_array():
    """Test object array with blank line separators"""
    text = """
# users:

name = Alice
age = 22

name = Bob
age = 30
"""
    doc = parse(text)
    users = doc.get("users")
    assert len(users) == 2
    assert users[0] == {"name": "Alice", "age": 22}
    assert users[1] == {"name": "Bob", "age": 30}


def test_multiline_value():
    """Test multiline string with triple quotes"""
    text = '''
# article:
body = """
This is line one.
This is line two.
"""
'''
    doc = parse(text)
    body = doc.get("article.body")
    assert "line one" in body
    assert "line two" in body
    assert body == "This is line one.\nThis is line two."


def test_type_inference_integers():
    """Test type inference for integers"""
    text = """
#:
count = 42
negative = -10
"""
    doc = parse(text)
    assert doc.get("count") == 42
    assert doc.get("negative") == -10
    assert isinstance(doc.get("count"), int)


def test_type_inference_floats():
    """Test type inference for floats"""
    text = """
#:
pi = 3.14159
ratio = 0.5
"""
    doc = parse(text)
    assert doc.get("pi") == 3.14159
    assert doc.get("ratio") == 0.5
    assert isinstance(doc.get("pi"), float)


def test_type_inference_booleans():
    """Test type inference for booleans"""
    text = """
#:
enabled = true
disabled = false
"""
    doc = parse(text)
    assert doc.get("enabled") is True
    assert doc.get("disabled") is False


def test_no_type_inference():
    """Test disabling type inference"""
    text = """
#:
count = 42
enabled = true
"""
    doc = parse(text, infer_types=False)
    assert doc.get("count") == "42"
    assert doc.get("enabled") == "true"


def test_multiple_sections_same_path():
    """Test augmentation with multiple sections at same path"""
    text = """
# config:
name = MyApp

# config:
version = 1.0
"""
    doc = parse(text)
    assert doc.get("config.name") == "MyApp"
    assert doc.get("config.version") == 1.0


def test_relative_section():
    """Test relative section (no # prefix)"""
    text = """
upgrade.stats:
strength = 12
agility = 9
"""
    doc = parse(text)
    relative = doc.get_relative_sections()
    assert "upgrade" in relative
    assert relative["upgrade"]["stats"]["strength"] == 12


def test_empty_document():
    """Test parsing empty document"""
    doc = parse("")
    assert doc.to_dict() == {}


def test_only_comments_and_blank_lines():
    """Test document with only blank lines"""
    text = """


"""
    doc = parse(text)
    assert doc.to_dict() == {}


def test_to_dict():
    """Test converting document to dict"""
    text = """
# person:
name = Matthew
age = 54
"""
    doc = parse(text)
    data = doc.to_dict()
    assert data == {"person": {"name": "Matthew", "age": 54}}


def test_to_json():
    """Test converting document to JSON"""
    text = """
# person:
name = Matthew
age = 54
"""
    doc = parse(text)
    json_str = doc.to_json()
    assert '"name": "Matthew"' in json_str
    assert '"age": 54' in json_str


def test_dot_notation_in_keys():
    """Test dot notation within keys"""
    text = """
# server:
host.primary = localhost
host.backup = backup.example.com
"""
    doc = parse(text)
    assert doc.get("server.host.primary") == "localhost"
    assert doc.get("server.host.backup") == "backup.example.com"
