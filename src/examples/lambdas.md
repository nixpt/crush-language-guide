# Lambdas & the Pipeline Operator

> Verified against crush-ast `cb655f3` (2026-10-16).

## The pipeline operator

`x |> f` calls `f(x)`; `x |> f(y)` calls `f(x, y)`. Chains read left to right and
bind more loosely than any other operator. The right-hand side must be a function
name, or a variable holding a function value.

```crush
fn add(a, b) {
    return a + b
}
fn mul(a, b) {
    return a * b
}
fn square(x) {
    return x * x
}

print(add(1, 2) |> mul(3))
print(2 |> square |> square)
let result = 3 |> add(4) |> mul(10)
print(result)
```

<!-- check: output -->
```text
9
16
70
```

`add(1, 2) |> mul(3)` is `mul(add(1, 2), 3)`, i.e. `mul(3, 3)` = 9.

## Lambdas

A lambda is `|params| expression` or `|params| { block }`:

<!-- check: error -->
```crush
let add = |a, b| {
    return a + b
}
let mul = |x, y| x * y
print(add(1, 2))
print(mul(4, 5))
print(6 |> |n| n)
```

That program fails to compile because of its last line: an inline lambda on the
right of `|>` is a parse error (`Pipeline right side must be function`). Bind it
first:

```crush
let add = |a, b| {
    return a + b
}
let mul = |x, y| x * y
let ident = |n| n
print(add(1, 2))
print(mul(4, 5))
print(6 |> ident)
```

<!-- check: output -->
```text
3
20
6
```

## Functions as values, and closures

A function name is a value, and a lambda captures the variables around it:

```crush
fn compose(f, g) {
    return |x| g(f(x))
}
fn make_scaler(k) {
    return |x| x * k
}
let triple = make_scaler(3)
let inc = |x| x + 1
let triple_then_inc = compose(triple, inc)
print(triple_then_inc(5))
print(parallel_map([1, 2, 3], triple))
```

<!-- check: output -->
```text
16
[3, 6, 9]
```

More in [Closures and Function Values](../crush/closures.md).
