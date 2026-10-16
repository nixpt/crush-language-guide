# Variables and Scoping

> Verified against crush-ast `3ae0b4a` (2026-10-16).

This chapter covers declaration, assignment, and the scoping rules the compiler
enforces today.

## Declaration

Every variable is introduced with `let` and **must be initialised**:

```crush
let x = 42
let name = "Alice"
let active = true
print(x)
```

<!-- check: output -->
```text
42
```

A bare `let x` (no value) is a parse error. So is `let mut x = 0` — `mut` is a
reserved word, but it is not accepted in a declaration, and there is no `const`.
Every `let` variable is simply reassignable.

<!-- check: error -->
```crush
let x
```

<!-- check: error -->
```crush
let mut counter = 0
```

### Type hints

```crush
let age: Int = 30
let score: Float = 95.5
let message: String = "Hello"
let flag: Bool = true
print(age)
```

<!-- check: output -->
```text
30
```

The initial value is checked against the hint at compile time
(`let x: Int = "s"` is rejected). The hint is **not** re-checked on later
assignment today.

## Assignment

Reassign with `=`:

```crush
let counter = 0
counter = counter + 1
counter = counter + 1
print(counter)
```

<!-- check: output -->
```text
2
```

Compound assignment (`+=`, `-=`, `*=`, `/=`) and `++`/`--` are **not implemented**:
use `counter = counter + 1`. Assigning to a name that was never declared is a
compile error (`Undefined variable`).

<!-- check: error -->
```crush
counter += 1
```

Variables are dynamically typed at run time, so a `let`-declared name can later
hold a value of a different type (unless the compiler can see the mismatch for a
hinted parameter or initialiser).

## Scoping rules

### Function scope

Variables declared in a function are local to it, and parameters are local copies:

```crush
fn bump(n) {
    n = n + 1
    return n
}

let v = 1
print(bump(v))
print(v)
```

<!-- check: output -->
```text
2
1
```

Arrays and objects are passed **by reference**, so a function can mutate its
argument in place:

```crush
fn add_nine(items) {
    items.push(9)
}

let xs = [1]
add_nine(xs)
print(xs)
```

<!-- check: output -->
```text
[1, 9]
```

Using a function's local outside it is a compile error:

<!-- check: error -->
```crush
fn example() {
    let x = 10
    print(x)
}
example()
print(x)
```

### Module-level variables are not visible inside functions

Top-level statements form the program's entry body, **not** a shared global
scope. A function cannot read a variable declared at the top level — pass it as
an argument:

<!-- check: error -->
```crush
let LEVEL = "production"

fn get_level() {
    return LEVEL
}
print(get_level())
```

```crush
let level = "production"

fn describe(l) {
    return "running in " + l
}
print(describe(level))
```

<!-- check: output -->
```text
running in production
```

(If you need shared state across functions today, thread it through parameters,
or keep it in an object/array you pass around.)

This applies to **named** functions. A lambda written at the top level does see
top-level variables: it captures them (see [Closures](closures.md)).

```crush
let level = "production"
let describe = || "running in " + level
print(describe())
```

<!-- check: output -->
```text
running in production
```

### Block scope

A name first declared inside an `if`, `while` or `for` body is not visible after
the block ends. A `for` loop variable is likewise local to the loop:

<!-- check: error -->
```crush
if true {
    let y = 2
}
print(y)
```

<!-- check: error -->
```crush
for i in 0..3 {
    print(i)
}
print(i)
```

### Shadowing

**Across functions** a local simply hides nothing — each function has its own
variables:

```crush
let x = 10

fn show() {
    let x = 20
    print(x)
}

show()
print(x)
```

<!-- check: output -->
```text
20
10
```

**Within one function**, re-declaring an *outer* name inside a block is not a
shadow limited to that block: after the block, the name `x` means the new
binding for the rest of the function. So this program prints `2`:

```crush
let x = 1
if true {
    let x = 2
}
print(x)
```

<!-- check: output -->
```text
2
```

Each `let` still creates a *fresh* binding, which only shows when a closure
captured the earlier one: it keeps seeing the old variable.

```crush
let x = 1
let get = || x
if true {
    let x = 2
}
print(x)
print(get())
```

<!-- check: output -->
```text
2
1
```

Choose distinct names for inner variables rather than relying on shadowing.

## Exporting a variable

`export name` marks an already-declared variable or function for export. See
[Syntax](syntax.md#imports-and-exports); importing it from another file is not
possible yet (crush-ast **CRUSH-110**).

## Best practices

- Initialise at declaration and keep scopes narrow.
- Pass state explicitly: functions can't see top-level variables.
- Prefer new names over shadowing.

## Next Steps

- **[Operators](operators.md)**
- **[Control Flow](control_flow.md)**
- **[Functions](functions.md)**
