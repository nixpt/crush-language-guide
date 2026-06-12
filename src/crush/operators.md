# Operators

Crush provides a comprehensive set of operators for arithmetic, comparison, logical operations, and more.

## Arithmetic Operators

### Basic Arithmetic

```crush
let sum = 5 + 3;        // 8
let diff = 10 - 4;      // 6
let product = 6 * 7;    // 42
let quotient = 20 / 4;  // 5
let remainder = 17 % 5; // 2
```

### Negation

```crush
let x = 42;
let neg = -x;  // -42
```

### String Concatenation

The `+` operator concatenates strings:

```crush
let greeting = "Hello, " + "World!";
let message = "Count: " + 42;  // Auto-converts to string
```

## Comparison Operators

```crush
let a = 10;
let b = 20;

let equal = a == b;          // false
let not_equal = a != b;      // true
let less = a < b;            // true
let greater = a > b;          // false
let less_equal = a <= b;     // true
let greater_equal = a >= b;  // false
```

## Logical Operators

### AND

```crush
let result = true and false;  // false
let check = (x > 0) and (x < 100);
```

### OR

```crush
let result = true or false;  // true
let check = (x < 0) or (x > 100);
```

### NOT

```crush
let result = not true;  // false
let check = not (x == 0);
```

## Operator Precedence

From highest to lowest:

| Precedence | Operators | Description |
|------------|-----------|-------------|
| 1 | `()`, `.`, `[]` | Grouping, field access, indexing |
| 2 | `-`, `not` | Unary negation, logical NOT |
| 3 | `*`, `/`, `%` | Multiplication, division, modulo |
| 4 | `+`, `-` | Addition, subtraction |
| 5 | `<`, `>`, `<=`, `>=` | Comparison |
| 6 | `==`, `!=` | Equality |
| 7 | `and` | Logical AND |
| 8 | `or` | Logical OR |

### Examples

```crush
let result = 2 + 3 * 4;        // 14 (not 20)
let result = (2 + 3) * 4;      // 20
let check = x > 0 and x < 100; // Comparison before AND
```

## Next Steps

- **[Control Flow](control_flow.md)**: Use operators in conditions
- **[Functions](functions.md)**: Function definitions
