# Variables and Scoping

This chapter covers variable declaration, assignment, scoping rules, and variable management in Crush.

## Variable Declaration

### Basic Declaration

```crush
let x = 42;
let name = "Alice";
let active = true;
```

### With Type Hints

```crush
let age: Int = 30;
let score: Float = 95.5;
let message: String = "Hello";
let flag: Bool = true;
```

## Assignment and Reassignment

Variables are mutable by default:

```crush
let counter = 0;
counter = 1;
counter = counter + 1;  // counter is now 2
```

### Compound Assignment (Future Feature)

```crush
counter += 1;   // counter = counter + 1
counter -= 1;   // counter = counter - 1
counter *= 2;   // counter = counter * 2
counter /= 2;   // counter = counter / 2
```

## Scoping Rules

### Function Scope

Variables declared in a function are local to that function:

```crush
fn example() {
    let x = 10;  // Local to example()
    @io.print(x);
}

fn main() {
    example();
    // @io.print(x);  // Error: x not in scope
}
```

### Block Scope

Variables declared in a block are local to that block:

```crush
fn main() {
    let x = 10;
    
    if true {
        let y = 20;  // Local to if block
        @io.print(x);  // Can access outer x
        @io.print(y);
    }
    
    @io.print(x);  // OK
    // @io.print(y);  // Error: y not in scope
}
```

### Global Scope (Module Level)

Variables at module level are accessible throughout the module:

```crush
let GLOBAL_CONFIG = "production";

fn get_config() -> String {
    return GLOBAL_CONFIG;
}

fn main() {
    @io.print(GLOBAL_CONFIG);
}
```

## Variable Shadowing

Inner scopes can shadow outer variables:

```crush
fn main() {
    let x = 10;
    @io.print(x);  // 10
    
    {
        let x = 20;  // Shadows outer x
        @io.print(x);  // 20
    }
    
    @io.print(x);  // 10 (outer x restored)
}
```

## Export and Import

### Exporting Variables

```crush
// capsule_a.crush
export result = calculate();
export config = {"mode": "production"};
```

### Importing Variables

```crush
// capsule_b.crush
let data = @import.var("capsule_a", "result");
let cfg = @import.var("capsule_a", "config");
```

## Constants (Future Feature)

```crush
const PI = 3.14159;
const MAX_SIZE = 100;

// PI = 3.14;  // Error: cannot reassign constant
```

## Variable Lifetime

Variables live until their scope ends:

```crush
fn main() {
    let x = allocate_resource();
    // x is alive
    
    if condition {
        let y = another_resource();
        // Both x and y are alive
    }  // y is destroyed here
    
    // Only x is alive
}  // x is destroyed here
```

## Best Practices

### 1. Declare Variables Close to Use

```crush
// Good
fn process() {
    let data = fetch_data();
    transform(data);
}

// Less ideal
fn process() {
    let data;
    // ... many lines ...
    data = fetch_data();
    transform(data);
}
```

### 2. Use Meaningful Names

```crush
// Good
let user_count = 100;
let temperature_celsius = 25.5;

// Avoid
let x = 100;
let temp = 25.5;
```

### 3. Minimize Scope

```crush
// Good: Narrow scope
if needs_processing {
    let temp_data = process();
    use(temp_data);
}

// Less ideal: Wider scope
let temp_data;
if needs_processing {
    temp_data = process();
    use(temp_data);
}
```

### 4. Initialize Variables

```crush
// Good
let counter = 0;

// Avoid (future: may require initialization)
// let counter;
// counter = 0;
```

## Next Steps

- **[Operators](operators.md)**: Learn about operators
- **[Control Flow](control_flow.md)**: If, while, for loops
- **[Functions](functions.md)**: Function parameters and returns
