# Lambdas & the Pipeline Operator

> Source: `crates/core/crush-lang/walkers/tree-sitter-crush/test_lambda.crush`

Two lambda forms and the `|>` pipeline operator.

```crush
// Block-body lambda (multiple statements)
let add = |a, b| {
    return a + b;
};

// Arrow lambda (single expression, no braces or return)
let mul = |x, y| => x * y;

// Call like any function
let sum = add(1, 2);      // 3
let product = mul(4, 5);  // 20
```

## Typed Parameters

```crush
let add_typed = |x: Int, y: Int| => x + y;
```

## The Pipeline Operator

`|>` passes the left value as the first argument to the right function:

```crush
let res = add(1, 2) |> mul(3);
// Equivalent to: mul(add(1, 2), 3) = mul(3, 3) = 9
```

Pipelines chain left-to-right with the lowest operator precedence:

```crush
let result = raw_data
    |> parse
    |> validate
    |> format;
```

## Higher-Order Functions

Functions accept and return other functions:

```crush
fn apply(f: Function, x: Int) -> Int {
    return f(x);
}

fn double(n: Int) -> Int { return n * 2; }

let r = apply(double, 21);   // 42
let r2 = apply(|x| => x * x, 5);  // 25 — lambda passed inline
```

## Closures

Lambdas capture the enclosing scope:

```crush
fn make_adder(x: Int) -> Function {
    return |y| { return x + y; };
}

let add5 = make_adder(5);
let result = add5(10);   // 15
```
