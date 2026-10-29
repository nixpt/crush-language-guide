# Control Flow

> Verified against crush-ast `b1791d8e` (2026-10-29).

Crush has `if`/`else`, `while`, `for`, `break`/`continue`, a `match` expression,
and `try`/`catch`/`throw`. Conditions are type-checked and must be `Bool`.

## If

```crush
let score = 85

if score >= 90 {
    print("A")
} else if score >= 80 {
    print("B")
} else {
    print("C or below")
}
```

<!-- check: output -->
```text
B
```

`if` is a statement, not an expression: `let y = if c { 1 } else { 2 }` is a
parse error. Use a function or `match` to select a value.

## While

```crush
let i = 0
while i < 3 {
    print(i)
    i = i + 1
}
```

<!-- check: output -->
```text
0
1
2
```

### Loop with `break`

```crush
let counter = 0
while true {
    if counter >= 3 {
        break
    }
    counter = counter + 1
}
print(counter)
```

<!-- check: output -->
```text
3
```

## For

### Over an array

```crush
for n in [10, 20, 30] {
    print(n)
}
```

<!-- check: output -->
```text
10
20
30
```

### Over a range

`a..b` is half-open (excludes `b`); `a..=b` includes `b`. There is no `range()`
function:

```crush
for i in 0..3 {
    print(i)
}

let items = ["x", "y"]
for i in 0..len(items) {
    print(items[i])
}
```

<!-- check: output -->
```text
0
1
2
x
y
```

```crush
for i in 1..=3 {
    print(i)
}
```

<!-- check: output -->
```text
1
2
3
```

### Over a string or a map

A string yields its characters; a map yields its keys, in insertion order:

```crush
for c in "abc" {
    print(c)
}
let ages = {"ada": 36, "alan": 41}
for name in ages {
    print(name + " is " + ages[name])
}
```

<!-- check: output -->
```text
a
b
c
ada is 36
alan is 41
```

The loop variable is a local like any `let`, so methods work on it:
`for s in shapes { print(s.area()) }`, or `row.push(x)` on each row of an array of
arrays. (Before crush-ast [#256](https://github.com/nixpt/crush-ast/issues/256)
such a call was compiled as a capability named `s.area` and the program was
refused.)

## Break and continue

`continue` skips to the next iteration; `break` leaves the innermost loop:

```crush
for i in 0..5 {
    if i % 2 == 0 {
        continue
    }
    print(i)
}

for i in 0..10 {
    if i == 3 {
        break
    }
}
```

<!-- check: output -->
```text
1
3
```

## Match

`match` selects among arms by comparing a value to literal patterns, with `_` as
the wildcard. It is an **expression**: bind its result with `let`.

```crush
let v = 2
let word = match v {
    1 => "one",
    2 => "two",
    _ => "many"
}
print(word)
```

<!-- check: output -->
```text
two
```

Supported patterns: integer, string and bool literals, `_`, a bare identifier
that binds the scrutinee (`n => "got " + n`), and **struct patterns** that test a
value's struct type and bind or compare its fields (`Point { x: 0, y: y } => ...`,
see [Structs, Methods and Kinds](structs.md#struct-patterns-in-match)). Arm bodies
can be an expression or a `{ ... }` block whose last expression is the value:

```crush
let n = 5
let msg = match n {
    0 => "zero",
    other => "got " + other
}
print(msg)
```

<!-- check: output -->
```text
got 5
```

`match` also works as a statement, with arms that only have side effects:

```crush
let v = 2
match v {
    1 => print("one")
    2 => { print("two"); print("still two") }
    _ => print("other")
}
```

<!-- check: output -->
```text
two
still two
```

A `match` can be returned directly (before crush-ast
[#253](https://github.com/nixpt/crush-ast/issues/253), `return match ...` silently
returned `null`):

```crush
fn name(v) {
    return match v {
        0 => "zero",
        _ => "other"
    }
}
print(name(0))
print(name(3))
```

<!-- check: output -->
```text
zero
other
```

Current limitations (alpha):

- A `match` with no matching arm evaluates to `null`; there is no
  exhaustiveness error.
- No guards (`x if x > 3 => ...`), no range patterns (`0..3 => ...`), no
  alternatives (`1 | 2 => ...`), no negative or float literal patterns, and no
  comma after a `{ ... }` arm body (`2 => { 7 }, _ => 0` is a parse error; the
  last three are listed in crush-ast's CRUSH-192 ticket).

## Errors: `try` / `catch` / `throw`

`throw` raises any value; `catch name { ... }` receives it. There is no
`finally`, and the parenthesised form `catch (e)` is not accepted.

```crush
fn divide(a, b) {
    if b == 0 {
        throw "division by zero"
    }
    return a / b
}

try {
    print(divide(4, 2))
    print(divide(1, 0))
    print("not reached")
} catch err {
    print("Error: " + err)
}
print("done")
```

<!-- check: output -->
```text
2
Error: division by zero
done
```

A `throw` crosses function-call boundaries (fixed in crush-ast **CRUSH-126**),
`catch` can rethrow, and thrown values can be any type:

```crush
try {
    try {
        throw "inner"
    } catch e {
        throw "re-" + e
    }
} catch outer {
    print(outer)
}

try {
    throw {"code": 7}
} catch e {
    print(e.code)
}
```

<!-- check: output -->
```text
re-inner
7
```

An uncaught `throw` ends the program with `[runtime] uncaught error: <value>`.

### What `catch` does *not* catch

`try`/`catch` handles values raised with `throw`. **Runtime faults from the VM or
a host capability are not catchable**: division by zero, an out-of-range array
index, a failing `fs.read`, or a polyglot block that raises all abort the
program with a `[runtime]` error instead of reaching your `catch`.

<!-- check: nyi GAP-CATCH-RUNTIME-FAULTS -->
```crush
try {
    print(1 / 0)
} catch e {
    print("caught")
}
```

## Next Steps

- **[Functions](functions.md)**
- **[Capability System](capabilities.md)**
