# Syntax and Grammar

This chapter covers the fundamental syntax and grammar rules of the Crush language.

## Lexical Structure

### Comments

```crush
// Single-line comment

/*
 * Multi-line comment
 * Can span multiple lines
 */

fn main() {
    // Comments can appear anywhere
    @io.print("Hello");  // Including after statements
}
```

### Identifiers

Identifiers (variable names, function names) must:
- Start with a letter or underscore
- Contain only letters, digits, and underscores
- Not be a reserved keyword

```crush
// Valid identifiers
let x = 1;
let my_variable = 2;
let _private = 3;
let counter123 = 4;

// Invalid identifiers
// let 123abc = 5;  // Cannot start with digit
// let my-var = 6;  // Hyphens not allowed
```

### Keywords

Reserved keywords in Crush:

```text
fn          let         if          else        while
for         in          return      break       continue
import      export      as          true        false
null        spawn       yield       struct      match
```

### Literals

```crush
// Integer literals
let dec = 42;
let hex = 0x2A;
let bin = 0b101010;

// Float literals
let pi = 3.14159;
let sci = 1.5e-10;

// String literals
let s1 = "Hello";
let s2 = 'World';
let multiline = """
    This is a
    multi-line string
""";

// Boolean literals
let t = true;
let f = false;

// Null literal
let n = null;
```

## Statements vs Expressions

### Statements

Statements perform actions but don't produce values:

```crush
// Variable declaration
let x = 42;

// Function definition
fn greet() {
    @io.print("Hello");
}

// Control flow
if x > 0 {
    @io.print("Positive");
}

// Expression statement
@io.print("Hello");
```

### Expressions

Expressions produce values:

```crush
// Arithmetic expressions
let sum = 5 + 3;

// Function calls
let result = calculate(10);

// Conditionals as expressions (future feature)
// let max = if a > b { a } else { b };
```

## Semicolons

Semicolons are **required** at the end of statements:

```crush
let x = 42;
@io.print(x);
return x;
```

Exception: The last expression in a block doesn't need a semicolon:

```crush
fn add(a: Int, b: Int) -> Int {
    return a + b;  // Semicolon required
}

fn add_implicit(a: Int, b: Int) -> Int {
    a + b  // No semicolon (implicit return, future feature)
}
```

## Blocks

Blocks are delimited by curly braces `{}`:

```crush
{
    let x = 10;
    let y = 20;
    @io.print(x + y);
}

fn main() {
    // Function body is a block
    let message = "Hello";
    @io.print(message);
}

if condition {
    // If body is a block
    @io.print("True");
}
```

## Variable Declaration

```crush
// Basic declaration
let x = 42;

// With type hint
let name: String = "Alice";

// Multiple declarations
let a = 1;
let b = 2;
let c = 3;
```

## Function Definition

```crush
// Basic function
fn greet() {
    @io.print("Hello!");
}

// With parameters
fn add(a: Int, b: Int) {
    return a + b;
}

// With return type
fn multiply(x: Int, y: Int) -> Int {
    return x * y;
}

// With type hints
fn process(data: String, count: Int) -> Bool {
    // ...
    return true;
}
```

## Operators

### Arithmetic

```crush
let sum = a + b;      // Addition
let diff = a - b;     // Subtraction
let prod = a * b;     // Multiplication
let quot = a / b;     // Division
let rem = a % b;      // Modulo
let neg = -a;         // Negation
```

### Comparison

```crush
let eq = a == b;      // Equal
let ne = a != b;      // Not equal
let lt = a < b;       // Less than
let gt = a > b;       // Greater than
let le = a <= b;      // Less or equal
let ge = a >= b;      // Greater or equal
```

### Logical

```crush
let and_result = a and b;   // Logical AND
let or_result = a or b;     // Logical OR
let not_result = not a;     // Logical NOT
```

### String Concatenation

```crush
let greeting = "Hello, " + name + "!";
let message = "Count: " + count;  // Auto-converts to string
```

## Operator Precedence

From highest to lowest:

1. Function calls, field access: `f()`, `obj.field`
2. Unary: `-`, `not`
3. Multiplicative: `*`, `/`, `%`
4. Additive: `+`, `-`
5. Comparison: `<`, `>`, `<=`, `>=`
6. Equality: `==`, `!=`
7. Logical AND: `and`
8. Logical OR: `or`

Use parentheses to override precedence:

```crush
let result = (a + b) * c;
let condition = (x > 0) and (y < 10);
```

## Control Flow Syntax

### If Statement

```crush
if condition {
    // then block
}

if condition {
    // then block
} else {
    // else block
}

if condition1 {
    // block 1
} else if condition2 {
    // block 2
} else {
    // block 3
}
```

### While Loop

```crush
while condition {
    // loop body
}

while i < 10 {
    @io.print(i);
    i = i + 1;
}
```

### For Loop

```crush
for item in collection {
    // loop body
}

for i in range(0, 10) {
    @io.print(i);
}
```

### Break and Continue

```crush
while true {
    if should_exit {
        break;
    }
    if should_skip {
        continue;
    }
    // ...
}
```

## Capability Calls

Capability calls use the `@` prefix:

```crush
// Basic capability call
@io.print("Hello");

// With multiple arguments
@fs.write("file.txt", "content");

// Storing result
let content = @fs.read("file.txt");

// Chaining (if result is an object)
let data = @net.http("https://api.example.com").json();
```

## Language Blocks

Embed other languages with `@language { ... }`:

```crush
@python {
    print("Hello from Python")
    x = 42
}

@javascript {
    console.log("Hello from JavaScript");
    const y = 100;
}

@bash {
    echo "Hello from Bash"
    ls -la
}
```

## Import Statements

```crush
// Import module
import std.io;

// Import with alias
import std.fs as filesystem;

// Import specific items (future feature)
// import std.io.{print, read};
```

> **Important**: `import` creates **aliases** for capabilities, not direct access. The `@` prefix is still required for all capability calls:
>
> ```crush
> import std.io as console;
> 
> @console.print("Hello");  // ✓ Correct
> // console.print("Hello");  // ✗ Error: missing @
> ```

## Export Statements

```crush
// Export variable for other capsules
export result = calculate();

// Export function
export fn utility() {
    // ...
}
```

## Type Annotations

```crush
// Variable type hints
let name: String = "Alice";
let age: Int = 30;
let score: Float = 95.5;
let active: Bool = true;

// Function parameter and return types
fn calculate(x: Int, y: Int) -> Int {
    return x + y;
}

// Array types (future feature)
// let numbers: Array<Int> = [1, 2, 3];

// Map types (future feature)
// let config: Map<String, Int> = {"key": 42};
```

## Code Organization

### Single File

```crush
// Imports at top
import std.io;
import std.fs;

// Function definitions
fn helper() {
    // ...
}

fn main() {
    // Entry point
}
```

### Multiple Files (future feature)

```crush
// lib.crush
export fn utility() {
    // ...
}

// main.crush
import lib;

fn main() {
    lib.utility();
}
```

## Style Guidelines

### Naming Conventions

```crush
// Functions: snake_case
fn calculate_total() { }

// Variables: snake_case
let user_name = "Alice";

// Constants: SCREAMING_SNAKE_CASE (future feature)
// const MAX_SIZE = 100;

// Types: PascalCase
struct UserData { }
```

### Indentation

Use 4 spaces (not tabs):

```crush
fn main() {
    if condition {
        while loop {
            @io.print("Nested");
        }
    }
}
```

### Line Length

Keep lines under 100 characters when possible.

### Spacing

```crush
// Spaces around operators
let sum = a + b;

// Space after commas
fn call(a, b, c) { }

// No space before semicolon
let x = 42;

// Space after keywords
if condition {
while loop {
```

## Grammar Summary

```ebnf
program         = statement*

statement       = var_decl
                | fn_def
                | if_stmt
                | while_stmt
                | for_stmt
                | return_stmt
                | expr_stmt
                | import_stmt
                | export_stmt

var_decl        = "let" IDENT (":" type)? "=" expression ";"

fn_def          = "fn" IDENT "(" params? ")" ("->" type)? block

if_stmt         = "if" expression block ("else" (if_stmt | block))?

while_stmt      = "while" expression block

for_stmt        = "for" IDENT "in" expression block

return_stmt     = "return" expression? ";"

expr_stmt       = expression ";"

expression      = literal
                | IDENT
                | binary_op
                | unary_op
                | call
                | cap_call
                | lang_block

cap_call        = "@" IDENT "." IDENT "(" args? ")"

lang_block      = "@" IDENT "{" ... "}"

block           = "{" statement* "}"
```

## Next Steps

- **[Data Types](types.md)**: Learn about Crush's type system
- **[Variables](variables.md)**: Variable scoping and management
- **[Control Flow](control_flow.md)**: Detailed control flow guide
- **[Functions](functions.md)**: Function definition and calling
