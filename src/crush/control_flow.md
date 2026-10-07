# Control Flow

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

`a..b` is half-open (excludes `b`). There is no inclusive `..=` and no `range()`
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

<!-- check: error -->
```crush
for i in 1..=3 {
    print(i)
}
```

Iterating directly over a map (`for k in obj`) is not supported — see
[Types](types.md#objects-maps).

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

Supported patterns: integer, string and bool literals, `_`, and a bare
identifier that binds the scrutinee (`n => "got " + n`). Arm bodies can be an
expression or a `{ ... }` block whose last expression is the value:

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

Current limitations (alpha):

- **Not used as a statement.** `match v { 1 => print("one"), _ => print("other") }`
  on its own fails at run time with `stack underflow`; the arms must produce
  values and the result must be bound with `let` (or use `if` for side effects).
- **`return match ...` returns `null`.** Bind first, then return:

```crush
fn name(v) {
    let r = match v {
        0 => "zero",
        _ => "other"
    }
    return r
}
print(name(0))
print(name(3))
```

<!-- check: output -->
```text
zero
other
```

- A `match` with no matching arm evaluates to `null` — there is no
  exhaustiveness error.
- No guards (`x if x > 3 => ...`) and no range patterns (`0..3 => ...`).

(These are crush-ast gaps without a ticket yet; see `GAP-MATCH-STATEMENT` and
`GAP-MATCH-RETURN` in the GUIDE-3 notes.)

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
