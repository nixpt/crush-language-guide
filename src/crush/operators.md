# Operators

Crush's operators are deliberately few. Everything in this chapter is verified
against the current compiler.

## Arithmetic

| Operator | Meaning | Example |
|---|---|---|
| `+` | add / string concatenation | `5 + 3`, `"a" + "b"` |
| `-` | subtract / unary negate | `10 - 4`, `-x` |
| `*` | multiply | `6 * 7` |
| `/` | divide (`Int / Int` truncates toward zero) | `20 / 4`, `-7 / 2` |
| `%` | remainder | `17 % 5` |

```crush
print(5 + 3)
print(10 - 4)
print(6 * 7)
print(20 / 4)
print(17 % 5)
print(-7 / 2)
print(-(3 + 2))
```

<!-- check: output -->
```text
8
6
42
5
2
-3
-5
```

Mixing `Int` and `Float` promotes to `Float` (`1 + 2.5` is `3.5`). `+` between a
string and a number concatenates (`"n=" + 5` is `"n=5"`); `*` on a string does
**not** repeat it.

There is no exponent operator (`**`), floor-division (`//`), or compound
assignment (`+=`, `-=`, …) — use `math.pow(a, b)` (with `--stdlib`) and
`x = x + 1`. See [Variables](variables.md).

## Comparison

`==`, `!=`, `<`, `>`, `<=`, `>=` return `Bool`. Operands must be of compatible
types; comparing a string with an int is a compile error. Strings compare
lexicographically; arrays compare element-wise with `==`.

```crush
let a = 10
let b = 20
print(a == b)
print(a != b)
print(a < b)
print(a >= b)
print("apple" < "banana")
print([1, 2] == [1, 2])
print(1 == 1.0)
```

<!-- check: output -->
```text
false
true
true
false
true
true
true
```

## Logical

Logic uses **symbols**: `&&`, `||`, `!`. The words `and`, `or` and `not` are not
operators. `&&` and `||` short-circuit (crush-ast **CRUSH-125**):

```crush
fn noisy() {
    print("evaluated")
    return true
}

print(false && noisy())
print(true || noisy())
print(!(1 > 2))
```

<!-- check: output -->
```text
false
true
true
```

<!-- check: error -->
```crush
print(true and false)
```

Conditions in `if`/`while` must be `Bool` — see [Types](types.md#conditions-must-be-bool).

## Range

`a..b` is a half-open range (`a` inclusive, `b` exclusive). It is used by `for`,
and also evaluates to an array of the integers in the range:

```crush
for i in 2..5 {
    print(i)
}
let r = 1..5
print(r)
```

<!-- check: output -->
```text
2
3
4
[1, 2, 3, 4]
```

An empty or reversed range (`5..2`) produces no iterations. Both bounds may be
expressions: `for i in 0..len(items)`. There is no `range()` function.

## Pipeline

`x |> f` calls `f(x)`; `x |> f(y)` calls `f(x, y)`. Chains read left to right.
The right side must be a user-defined function (or a call to one):

```crush
fn inc(x) {
    return x + 1
}
fn dbl(x) {
    return x * 2
}
fn add(a, b) {
    return a + b
}

print(3 |> inc |> dbl)
print(3 |> add(4))
```

<!-- check: output -->
```text
8
7
```

Piping into a **capability** such as `str.trim` or `conv.to_str` is rejected
(`Pipeline right side must be function`); wrap it in a function first:

<!-- check: error -->
```crush
print("  hi  " |> str.trim)
```

## Not available

Bitwise operators (`&`, `|`, `^`, `~`, `<<`, `>>`) are **not** part of the
Crush language today — the lexer rejects them — even though CASM has `bit_*`
opcodes ([CASM reference](../casm/instructions.md)). There is no ternary
`a ? b : c`, no null-coalescing `??`, and no `**`.

## Precedence (high → low)

| Level | Operators |
|---|---|
| 1 | `()`, `.`, `[]` — call, field access, indexing |
| 2 | unary `-`, `!` |
| 3 | `*` `/` `%` |
| 4 | `+` `-` |
| 5 | `<` `>` `<=` `>=` |
| 6 | `==` `!=` |
| 7 | `&&` |
| 8 | `\|\|` |
| 9 | `\|>` |

```crush
print(2 + 3 * 4)
print((2 + 3) * 4)
print(1 + 1 == 2 && 2 * 2 == 4)
```

<!-- check: output -->
```text
14
20
true
```

## Next Steps

- **[Control Flow](control_flow.md)**
- **[Functions](functions.md)**
