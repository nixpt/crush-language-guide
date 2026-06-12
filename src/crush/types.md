# Data Types

Crush has a simple, dynamic type system with optional type hints. This chapter covers all built-in types and their usage.

## Primitive Types

### Int

Integer numbers (64-bit signed):

```crush
let count = 42;
let negative = -100;
let hex = 0xFF;
let binary = 0b1010;

// Type hint
let age: Int = 30;
```

**Range:** -9,223,372,036,854,775,808 to 9,223,372,036,854,775,807

### Float

Floating-point numbers (64-bit IEEE 754):

```crush
let pi = 3.14159;
let scientific = 1.5e-10;
let negative = -2.5;

// Type hint
let temperature: Float = 98.6;
```

### String

UTF-8 encoded text:

```crush
let name = "Alice";
let greeting = 'Hello';
let multiline = """
    This is a
    multi-line string
""";

// Type hint
let message: String = "Hello, World!";
```

**String Operations:**

```crush
// Concatenation
let full_name = first + " " + last;

// Length (via capability)
let len = @str.length(name);

// Substring (via capability)
let sub = @str.substring(text, 0, 5);
```

### Bool

Boolean values:

```crush
let is_active = true;
let is_complete = false;

// Type hint
let flag: Bool = true;

// From comparisons
let result = x > 10;  // Bool
```

### Null

Represents absence of a value:

```crush
let empty = null;

// Type hint
let optional: String? = null;  // Future feature

// Checking for null
if value == null {
    @io.print("No value");
}
```

## Collection Types

### Array

Ordered collection of values:

```crush
// Array literal
let numbers = [1, 2, 3, 4, 5];
let mixed = [1, "two", 3.0, true];  // Mixed types allowed

// Type hint (future feature)
// let scores: Array<Int> = [90, 85, 95];

// Empty array
let empty = [];
```

**Array Operations:**

```crush
// Access by index
let first = numbers[0];
let last = numbers[4];

// Length
let len = @array.length(numbers);

// Append
@array.push(numbers, 6);

// Remove last
let popped = @array.pop(numbers);

// Iterate
for item in numbers {
    @io.print(item);
}
```

### Map (Object)

Key-value pairs:

```crush
// Map literal
let person = {
    "name": "Alice",
    "age": 30,
    "active": true
};

// Type hint (future feature)
// let config: Map<String, Int> = {"max": 100};

// Empty map
let empty = {};
```

**Map Operations:**

```crush
// Access by key
let name = person["name"];
let age = person.age;  // Dot notation

// Set value
person["email"] = "alice@example.com";
person.phone = "555-1234";

// Check key exists
if @map.has_key(person, "email") {
    @io.print("Email exists");
}

// Iterate
for key in @map.keys(person) {
    let value = person[key];
    @io.print(key + ": " + value);
}
```

## Type Conversion

### Explicit Conversion

```crush
// Int to String
let str = @convert.to_string(42);

// String to Int
let num = @convert.to_int("42");

// Float to Int
let rounded = @convert.to_int(3.14);

// Int to Float
let decimal = @convert.to_float(42);
```

### Implicit Conversion

String concatenation auto-converts:

```crush
let message = "Count: " + 42;  // "Count: 42"
let result = "Pi is " + 3.14;  // "Pi is 3.14"
```

## Type Checking

### Runtime Type Checking

```crush
let value = 42;

// Check type
let type_name = @type.of(value);  // "Int"

if type_name == "Int" {
    @io.print("It's an integer");
}
```

### Type Hints

Type hints are optional annotations:

```crush
// Variable type hints
let name: String = "Alice";
let age: Int = 30;
let score: Float = 95.5;
let active: Bool = true;

// Function parameter types
fn greet(name: String, age: Int) {
    @io.print("Hello, " + name);
}

// Function return type
fn calculate(x: Int, y: Int) -> Int {
    return x + y;
}
```

**Note:** Type hints are currently for documentation only. Runtime type checking is dynamic.

## Structs (Future Feature)

Custom data structures:

```crush
struct Point {
    x: Float,
    y: Float
}

fn main() {
    let p = Point { x: 10.0, y: 20.0 };
    @io.print(p.x);
}
```

## Enums (Future Feature)

Enumerated types:

```crush
enum Status {
    Pending,
    Active,
    Complete
}

fn main() {
    let status = Status.Active;
}
```

## Type Aliases (Future Feature)

```crush
type UserId = Int;
type Callback = Function(Int) -> Bool;

fn process(id: UserId, cb: Callback) {
    // ...
}
```

## Nullable Types (Future Feature)

```crush
let name: String? = null;  // Nullable string

if name != null {
    @io.print(name);
}

// Unwrap with default
let display_name = name ?? "Unknown";
```

## Type Inference

Crush infers types from values:

```crush
let x = 42;           // Inferred as Int
let pi = 3.14;        // Inferred as Float
let name = "Alice";   // Inferred as String
let flag = true;      // Inferred as Bool
let items = [1, 2];   // Inferred as Array
```

## Type Compatibility

### Numeric Types

```crush
let i: Int = 42;
let f: Float = 3.14;

// Int can be used where Float expected (auto-promotion)
let sum: Float = i + f;  // 45.14

// Float to Int requires explicit conversion
let rounded: Int = @convert.to_int(f);
```

### String Concatenation

Any type can be concatenated with String:

```crush
let message = "Count: " + 42;
let info = "Pi is " + 3.14;
let status = "Active: " + true;
```

## Type System Summary

| Type | Example | Mutable | Nullable |
|------|---------|---------|----------|
| `Int` | `42` | ✓ | ✗ |
| `Float` | `3.14` | ✓ | ✗ |
| `String` | `"Hello"` | ✓ | ✗ |
| `Bool` | `true` | ✓ | ✗ |
| `Null` | `null` | ✗ | N/A |
| `Array` | `[1, 2, 3]` | ✓ | ✗ |
| `Map` | `{"key": "value"}` | ✓ | ✗ |

## Best Practices

### 1. Use Type Hints for Function Signatures

```crush
// Good: Clear interface
fn calculate(x: Int, y: Int) -> Int {
    return x + y;
}

// Okay: Less clear
fn calculate(x, y) {
    return x + y;
}
```

### 2. Be Consistent with Types

```crush
// Good: Consistent types
let numbers = [1, 2, 3, 4, 5];

// Avoid: Mixed types (unless necessary)
let mixed = [1, "two", 3.0];
```

### 3. Check for Null

```crush
if value != null {
    // Safe to use value
    @io.print(value);
}
```

### 4. Use Meaningful Type Names

```crush
// Good
let user_count: Int = 100;
let temperature: Float = 98.6;

// Less clear
let x: Int = 100;
let y: Float = 98.6;
```

## Type Errors

Common type-related errors:

```crush
// Division by zero
let result = 10 / 0;  // Runtime error

// Invalid conversion
let num = @convert.to_int("abc");  // Runtime error

// Null access
let value = null;
@io.print(value.field);  // Runtime error
```

## Next Steps

- **[Variables](variables.md)**: Variable scoping and management
- **[Operators](operators.md)**: Detailed operator reference
- **[Functions](functions.md)**: Working with functions
- **[Control Flow](control_flow.md)**: If, while, for loops
