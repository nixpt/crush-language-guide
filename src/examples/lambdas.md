# Lambdas & the Pipeline Operator

## The pipeline operator

`x |> f` calls `f(x)`; `x |> f(y)` calls `f(x, y)`. Chains read left to right and
bind more loosely than any other operator. The right-hand side must be a
user-defined function (or a call to one).

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

> **Not yet implemented.** Anonymous functions, functions as values, and closures
> all fail to compile today. The lexer reads a bare `|` as an identifier, so the
> `|params| body` parser is unreachable — crush-ast **CRUSH-75**, open (the same
> bug is GitHub issue #78). The forms below are what the design intends; they are
> kept here, marked, so they can be switched on when CRUSH-75 lands.

<!-- check: nyi CRUSH-75 -->
```crush
let add = |a, b| {
    return a + b
}
print(add(1, 2))
```

<!-- check: nyi CRUSH-75 -->
```crush
let mul = |x, y| => x * y
print(mul(4, 5))
```

Passing a function by name (`apply(double, 21)`) fails for the same reason: a
function name is not a value. Until then, use named functions and `|>`.
