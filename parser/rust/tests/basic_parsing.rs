use adf::{parse, Value};

#[test]
fn test_simple_key_value() {
    let text = r#"
# person:
name = Matthew
age = 54
"#;

    let doc = parse(text).unwrap();
    assert_eq!(doc.get("person.name").unwrap().as_str().unwrap(), "Matthew");
    assert_eq!(doc.get("person.age").unwrap().as_i64().unwrap(), 54);
}

#[test]
fn test_nested_paths() {
    let text = r#"
# person.address:
city = Fayetteville
state = NY
"#;

    let doc = parse(text).unwrap();
    assert_eq!(
        doc.get("person.address.city").unwrap().as_str().unwrap(),
        "Fayetteville"
    );
    assert_eq!(
        doc.get("person.address.state").unwrap().as_str().unwrap(),
        "NY"
    );
}

#[test]
fn test_root_section() {
    let text = r#"
#:
name = ADF
version = 0.1
"#;

    let doc = parse(text).unwrap();
    assert_eq!(doc.get("name").unwrap().as_str().unwrap(), "ADF");
    assert_eq!(doc.get("version").unwrap().as_f64().unwrap(), 0.1);
}

#[test]
fn test_scalar_array() {
    let text = r#"
# hobbies:
reading
physics
coding
"#;

    let doc = parse(text).unwrap();
    let hobbies_value = doc.get("hobbies").unwrap();
    let hobbies = hobbies_value.as_array().unwrap();
    assert_eq!(hobbies.len(), 3);
    assert_eq!(hobbies[0].as_str().unwrap(), "reading");
    assert_eq!(hobbies[1].as_str().unwrap(), "physics");
    assert_eq!(hobbies[2].as_str().unwrap(), "coding");
}

#[test]
fn test_object_array() {
    let text = r#"
# users:

name = Alice
age = 22

name = Bob
age = 30
"#;

    let doc = parse(text).unwrap();
    let users_value = doc.get("users").unwrap();
    let users = users_value.as_array().unwrap();
    assert_eq!(users.len(), 2);

    let alice = users[0].as_object().unwrap();
    assert_eq!(alice.get("name").unwrap().as_str().unwrap(), "Alice");
    assert_eq!(alice.get("age").unwrap().as_i64().unwrap(), 22);

    let bob = users[1].as_object().unwrap();
    assert_eq!(bob.get("name").unwrap().as_str().unwrap(), "Bob");
    assert_eq!(bob.get("age").unwrap().as_i64().unwrap(), 30);
}

#[test]
fn test_multiline_value() {
    let text = r#"
# article:
body = """
This is line one.
This is line two.
"""
"#;

    let doc = parse(text).unwrap();
    let body_value = doc.get("article.body").unwrap();
    let body = body_value.as_str().unwrap();
    assert!(body.contains("line one"));
    assert!(body.contains("line two"));
    assert_eq!(body, "This is line one.\nThis is line two.");
}

#[test]
fn test_type_inference_integers() {
    let text = r#"
#:
count = 42
negative = -10
"#;

    let doc = parse(text).unwrap();
    assert_eq!(doc.get("count").unwrap().as_i64().unwrap(), 42);
    assert_eq!(doc.get("negative").unwrap().as_i64().unwrap(), -10);
}

#[test]
fn test_type_inference_floats() {
    let text = r#"
#:
pi = 3.14159
ratio = 0.5
"#;

    let doc = parse(text).unwrap();
    assert_eq!(doc.get("pi").unwrap().as_f64().unwrap(), 3.14159);
    assert_eq!(doc.get("ratio").unwrap().as_f64().unwrap(), 0.5);
}

#[test]
fn test_type_inference_booleans() {
    let text = r#"
#:
enabled = true
disabled = false
"#;

    let doc = parse(text).unwrap();
    assert_eq!(doc.get("enabled").unwrap().as_bool().unwrap(), true);
    assert_eq!(doc.get("disabled").unwrap().as_bool().unwrap(), false);
}

#[test]
fn test_multiple_sections_same_path() {
    let text = r#"
# config:
name = MyApp

# config:
version = 1.0
"#;

    let doc = parse(text).unwrap();
    assert_eq!(doc.get("config.name").unwrap().as_str().unwrap(), "MyApp");
    assert_eq!(doc.get("config.version").unwrap().as_f64().unwrap(), 1.0);
}

#[test]
fn test_relative_section() {
    let text = r#"
upgrade.stats:
strength = 12
agility = 9
"#;

    let doc = parse(text).unwrap();
    let relative = doc.relative_sections();
    assert!(relative.contains_key("upgrade"));
}

#[test]
fn test_empty_document() {
    let doc = parse("").unwrap();
    assert_eq!(doc.as_map().len(), 0);
}

#[test]
fn test_dot_notation_in_keys() {
    let text = r#"
# server:
host.primary = localhost
host.backup = backup.example.com
"#;

    let doc = parse(text).unwrap();
    assert_eq!(
        doc.get("server.host.primary")
            .unwrap()
            .as_str()
            .unwrap(),
        "localhost"
    );
    assert_eq!(
        doc.get("server.host.backup").unwrap().as_str().unwrap(),
        "backup.example.com"
    );
}

#[test]
#[cfg(feature = "serde")]
fn test_to_json() {
    let text = r#"
# person:
name = Matthew
age = 54
"#;

    let doc = parse(text).unwrap();
    let json = doc.to_json().unwrap();
    assert!(json.contains("\"name\": \"Matthew\""));
    assert!(json.contains("\"age\": 54"));
}
