# Functions

Functions are first-class values in Crush. This chapter covers function definition, calling, parameters, and return values.

## Function Definition

### Basic Function

```crush
fn greet() {
    @io.print("Hello!");
}
```

### With Parameters

```crush
fn greet(name: String) {
    @io.print("Hello, " + name + "!");
}
```

### With Return Value

```crush
fn add(a: Int, b: Int) -> Int {
    return a + b;
}
```

### Multiple Parameters

```crush
fn calculate(x: Int, y: Int, operation: String) -> Int {
    if operation == "add" {
        return x + y;
    } else if operation == "multiply" {
        return x * y;
    }
    return 0;
}
```

## Function Calls

```crush
// No arguments
greet();

// With arguments
greet("Alice");

// Storing result
let sum = add(5, 3);

// Nested calls
let result = calculate(add(2, 3), 4, "multiply");
```

## Return Values

### Explicit Return

```crush
fn get_value() -> Int {
    return 42;
}
```

### Multiple Return Points

```crush
fn check_sign(x: Int) -> String {
    if x > 0 {
        return "positive";
    } else if x < 0 {
        return "negative";
    }
    return "zero";
}
```

### Void Functions

Functions without return values:

```crush
fn log_message(msg: String) {
    @io.print("[LOG] " + msg);
    // No return statement
}
```

## Parameters

### Positional Parameters

```crush
fn create_user(name: String, age: Int, active: Bool) {
    // ...
}

create_user("Alice", 30, true);
```

### Default Parameters (Future Feature)

```crush
fn greet(name: String = "Guest") {
    @io.print("Hello, " + name);
}

greet();         // "Hello, Guest"
greet("Alice");  // "Hello, Alice"
```

## Recursion

```crush
fn factorial(n: Int) -> Int {
    if n <= 1 {
        return 1;
    }
    return n * factorial(n - 1);
}

fn main() {
    let result = factorial(5);  // 120
    @io.print(result);
}
```

## Higher-Order Functions

Functions are first-class values and can be passed as arguments:

```crush
fn apply(f: Function, x: Int) -> Int {
    return f(x);
}

fn double(n: Int) -> Int {
    return n * 2;
}

fn main() {
    let result = apply(double, 21);  // 42
}
```

## Lambdas and Closures

Anonymous functions use the `|params| { body }` syntax (the `Lambda` AST node):

```crush
let double = |x| { return x * 2; };
let result = double(21);  // 42

// Single-expression form
let square = |x| => x * x;
```

Closures capture variables from the enclosing scope:

```crush
fn make_adder(x: Int) -> Function {
    return |y| { return x + y; };
}

fn main() {
    let add_five = make_adder(5);
    let result = add_five(10);  // 15
}
```

## Async Functions

Use `async`/`await` for asynchronous operations. `spawn` launches a task concurrently:

```crush
async fn fetch_data(url: String) -> String {
    let response = await @net.get(url);
    return response;
}

fn main() {
    let task = spawn fetch_data("https://api.example.com/data");
    let result = await task;
    @io.print(result);
}
```

## Best Practices

### 1. Use Type Hints

```crush
// Good
fn calculate(x: Int, y: Int) -> Int {
    return x + y;
}

// Less clear
fn calculate(x, y) {
    return x + y;
}
```

### 2. Keep Functions Focused

```crush
// Good: Single responsibility
fn validate_email(email: String) -> Bool {
    // ...
}

fn send_email(to: String, subject: String, body: String) {
    // ...
}
```

### 3. Use Descriptive Names

```crush
// Good
fn calculate_total_price(items: Array, tax_rate: Float) -> Float {
    // ...
}

// Avoid
fn calc(x, y) {
    // ...
}
```

## Next Steps

- **[Capability System](capabilities.md)**: Secure I/O operations
- **[Polyglot Programming](polyglot.md)**: Embed multiple languages
