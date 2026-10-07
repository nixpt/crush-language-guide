# Data Types

Crush is dynamically typed at run time, with a **static checker** that catches
obvious mismatches at compile time when you add type annotations. This chapter
covers the values you can build today.

## Primitive types

| Type | Literal | Notes |
|------|---------|-------|
| Int | `42`, `-7` | 64-bit signed. Decimal literals only |
| Float | `3.14` | 64-bit IEEE 754. No exponent literals (`1.5e3` is a parse error) |
| String | `"hello"` | double quotes only; `len` counts **bytes** |
| Bool | `true`, `false` | |
| Null | `null` | absence of a value |

```crush
let count = 42
let pi = 3.14
let name = "Alice"
let active = true
let nothing = null
print(count)
print(pi)
print(name)
print(active)
print(nothing)
```

<!-- check: output -->
```text
42
3.14
Alice
true
null
```

### Numbers

`+ - * / %` work on `Int` and `Float`. Mixing the two promotes to `Float`.
`/` on two `Int`s is **integer division**:

```crush
print(10 / 4)
print(10.0 / 4)
print(1 + 2.5)
print(7 % 3)
```

<!-- check: output -->
```text
2
2.5
3.5
1
```

Dividing by zero is a **runtime error** (`[runtime] division by zero`). It is
raised by the VM rather than thrown as a Crush value, so `try`/`catch` does not
intercept it.

> **Alpha caveat.** Integer arithmetic that overflows `i64` in a *constant
> expression* currently panics the compiler's optimizer instead of reporting an
> error. Keep literals within range.

### Strings

Concatenate with `+`. Adding a number to a string converts the number:

```crush
let first = "Ada"
let last = "Lovelace"
print(first + " " + last)
print("Count: " + 42)
print("Pi is " + 3.14)
```

<!-- check: output -->
```text
Ada Lovelace
Count: 42
Pi is 3.14
```

`len(s)` is the byte length and `s[i]` yields a one-character string. With
`--stdlib`, the `str.*` capabilities add `str.split`, `str.trim`,
`str.to_upper`, `str.substring` and friends — see [Standard Library](stdlib.md).

```crush
let s = "hello"
print(len(s))
print(s[1])
print(str.to_upper(s))
```

<!-- check: output -->
```text
5
e
HELLO
```

## Collections

### Arrays

Ordered, mixed-type, zero-indexed. Index, assign by index, and `len`:

```crush
let numbers = [10, 20, 30]
print(numbers[0])
numbers[1] = 99
print(numbers)
print(len(numbers))

let nested = [[1, 2], [3]]
print(nested[0][1])
```

<!-- check: output -->
```text
10
[10, 99, 30]
3
2
```

Append with `array.push(arr, value)` or the method form `arr.push(value)`; `+`
joins two arrays:

```crush
let a = [1, 2]
a.push(3)
array.push(a, 4)
print(a)
print([1] + [2])
```

<!-- check: output -->
```text
[1, 2, 3, 4]
[1, 2]
```

Iterate with `for`:

```crush
for item in ["a", "b"] {
    print(item)
}
```

<!-- check: output -->
```text
a
b
```

`array.pop(a)` removes and returns the last element, `a.append(v)` is an alias for
`push`, and slices work:

```crush
let a = [1, 2, 3, 4]
let last = array.pop(a)
print(last)
print(a)
print(a[0:2])
```

<!-- check: output -->
```text
4
[1, 2, 3]
[1, 2]
```

Reading past the end is a runtime error (`array index out of range`). The
method form `a.pop()` is **not** available (`unknown capability: pop`); call
`array.pop(a)`. Array mutation still has open gaps — see crush-ast **CRUSH-7**.

### Objects (maps)

Key–value pairs written `{"key": value}`. Keys may be bare identifiers or
strings. Read and write fields with **dot notation**:

```crush
let person = {"name": "Alice", "age": 30}
print(person.name)
person.age = 31
person.email = "alice@example.com"
print(person.age)
print(person.email)
```

<!-- check: output -->
```text
Alice
31
alice@example.com
```

Nested objects chain:

```crush
let cfg = {"db": {"port": 5432}}
print(cfg.db.port)
cfg.db.port = 5433
print(cfg.db.port)
```

<!-- check: output -->
```text
5432
5433
```

> **Not yet implemented.** String-key subscripts (`person["name"]`) fail at run
> time with `array index must be int, got str`; `len(map)` and `for k in map`
> are rejected (`expected array or string, got map`); and `.keys()` is not
> available. Use dot access. (Reported against crush-ast; no ticket yet — see
> the GUIDE-3 ticket.)

<!-- check: nyi GAP-MAP-SUBSCRIPT -->
```crush
let person = {"name": "Alice"}
print(person["name"])
```

## Structs

Declare a struct with its field names (optionally with type hints) **on one line**,
create it
with `new Name()` — **no constructor arguments** — and assign fields
individually:

```crush
struct Point { x: Float, y: Float }

let p = new Point()
p.x = 1.5
p.y = 2.5
print(p.x + p.y)
```

<!-- check: output -->
```text
4.0
```

Assigning to a field the struct doesn't declare is a compile error
(`Struct 'Point' has no field 'z'`). Field type hints are **not enforced** at
run time today, and an unassigned field reads as `null`.

`Point { x: 1.0, y: 2.0 }` literals and `new Point(1.0, 2.0)` are rejected by the
parser. A struct body that spans several lines is also rejected today — the parser
doesn't skip newlines inside `struct { ... }` (see the GUIDE-3 ticket, gap
`GAP-STRUCT-MULTILINE`):

<!-- check: nyi GAP-STRUCT-MULTILINE -->
```crush
struct Point {
    x: Float,
    y: Float
}
```

## Type annotations

You may annotate variables, parameters and return types with `Int`, `Float`,
`String`, `Bool`, or `Any`. The compiler checks them statically:

```crush
fn double(n: Int) -> Int {
    return n * 2
}
let label: String = "answer"
print(label)
print(double(21))
```

<!-- check: output -->
```text
answer
42
```

Mismatches are rejected at compile time:

<!-- check: error -->
```crush
let x: Int = "not a number"
```

<!-- check: error -->
```crush
fn double(n: Int) -> Int {
    return n * 2
}
print(double("seven"))
```

Annotations are optional. Not available: generic forms (`Array<Int>`), array
shorthand (`Int[]`), nullable `T?`, and `Function`/`Array`/`Map` as hint names —
all fail with a parse or `Unknown type` error.

## Conversion and inspection

With `--stdlib`, the `conv.*` capabilities convert between types and report
them:

```crush
print(conv.to_int("42") + 1)
print(conv.to_str(5) + "x")
print(conv.to_float(2))
print(conv.type_of([1]))
print(conv.type_of(null))
```

<!-- check: output -->
```text
43
5x
2.0
array
null
```

`conv.type_of` returns `int`, `float`, `string`, `bool`, `null`, `array` or
`map`. There is no `type.of`.

## Conditions must be Bool

`if` and `while` conditions are type-checked: an `Int` or `String` is **not**
silently truthy. Compare explicitly (`x != 0`, `s != ""`).

<!-- check: error -->
```crush
if 1 {
    print("yes")
}
```

## Comparison

`==`/`!=` compare values of the same type; comparing a string to an int is a
compile error (`Cannot compare types string and int`). `1 == 1.0` is `true`.

## Not available yet

| Feature | Status |
|---|---|
| `Bytes` literals (`b"..."`), `Error(...)` values | not parsed / undefined |
| Optional types `T?`, `??` | not parsed |
| Enums, type aliases, generics | not in the grammar |
| Lambdas / `Function` values | crush-ast **CRUSH-75** (open) — see [Functions](functions.md) |

## Next Steps

- **[Variables](variables.md)**: scope and mutation
- **[Operators](operators.md)**: the operator reference
- **[Functions](functions.md)**: calls, recursion, hints
- **[Control Flow](control_flow.md)**: loops, `match`, `try`/`catch`
