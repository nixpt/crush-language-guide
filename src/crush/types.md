# Data Types

> Verified against crush-ast `b1791d8e` (2026-10-29).

Crush is dynamically typed at run time, with a **static checker** that catches
obvious mismatches at compile time when you add type annotations. This chapter
covers the values you can build today.

## Primitive types

| Type | Literal | Notes |
|------|---------|-------|
| Int | `42`, `-7`, `0x2A`, `0b101` | 64-bit signed; overflow is a runtime error |
| Float | `3.14` | 64-bit IEEE 754. No exponent literals (`1.5e3` is a parse error) |
| String | `"hello"`, `'hello'` | `len` counts **bytes** |
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

Dividing by zero is a **runtime error** (`[runtime] division by zero`), for
`Float` too (there is no `inf` or `NaN`). It is raised by the VM rather than thrown
as a Crush value, so `try`/`catch` does not intercept it.

`Int` arithmetic is checked: a result outside `i64` stops the program with
`[runtime] arithmetic overflow`. It never wraps.

<!-- check: runfail arithmetic overflow -->
```crush
let big = 9223372036854775807
print(big + 1)
```

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

`len(s)` is the byte length and `s[i]` yields a one-character string (a negative
index counts from the end). The standard library's `str.*` capabilities add
`str.split`, `str.trim`, `str.to_upper`, `str.substring` and friends — see
[Standard Library](stdlib.md). Strings have no methods: `s.to_upper()` is refused
(`not available in this host: to_upper`); call `str.to_upper(s)`.

```crush
let s = "hello"
print(len(s))
print(s[1])
print(s[-1])
print(str.to_upper(s))
print(str.substring(s, 1, 3))
```

<!-- check: output -->
```text
5
e
o
HELLO
el
```

The slice syntax `s[1:3]` is for arrays only; on a string it compiles but fails
at run time (`expected array, got str`). Use `str.substring`.

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
`push`, and slices `a[start:end]` work (end exclusive):

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

Reading past the end is a runtime error (`array index out of range`), and so is
`a[-1]` on an empty array; `a[-1]` on a non-empty one is the last element. The
method form `a.pop()` is **not** available (the program is refused with `not
available in this host: pop`); call `array.pop(a)`.

Negative slice bounds count from the end, as an index does: with
`let a = [1, 2, 3, 4]`, `a[1:-1]` is `[2, 3]`, `a[-3:]` is `[2, 3, 4]` and
`a[:-1]` is `[1, 2, 3]`. (Before crush-ast
[#254](https://github.com/nixpt/crush-ast/issues/254) they were silently clamped.)

### Objects (maps)

Key–value pairs written `{"key": value}`. Keys may be bare identifiers or
strings. Read and write fields with **dot notation** or a **string subscript**:

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

Objects keep **insertion order**: printing, `for k in obj` and
`collections.keys(obj)` all list keys in the order they were first set.

```crush
let person = {"name": "Alice"}
person["age"] = 30
let field = "name"
print(person[field])
print(person)
for k in person {
    print(k)
}
```

<!-- check: output -->
```text
Alice
{name: Alice, age: 30}
name
age
```

Reading a key that isn't there is a runtime error (`expected present map key, got
absent key`), not `null`. `len(obj)` is rejected (`expected array or string, got
map`); count `collections.keys(obj)` instead.

## Structs

Declare a struct with its field names (optionally with type hints) **on one
line**, then build one with a literal that names every field, or with
`new Name()` and assign fields individually:

```crush
struct Point { x: Float, y: Float }

let a = Point { x: 1.0, y: 2.0 }
let p = new Point()
p.x = 1.5
p.y = 2.5
print(a)
print(p.x + p.y)
```

<!-- check: output -->
```text
{x: 1.0, y: 2.0}
4.0
```

Structs are **sealed**: writing a field the struct doesn't declare stops the
program (`` `Point` is sealed: it has no field `z` (fields: x, y) ``), and a
literal with a missing or unknown field is a compile error. Field type hints are
**not enforced** at run time today, and an unassigned field reads as `null`.
Methods, traits, value semantics and `@kind` are in
[Structs, Methods and Kinds](structs.md).

A struct body that spans several lines is still rejected: the parser doesn't skip
newlines inside `struct { ... }` (gap `GAP-STRUCT-MULTILINE`, listed in crush-ast's
CRUSH-192 ticket):

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

The standard library's `conv.*` capabilities convert between types and report
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
| `Bytes` literals (`b"..."`) | refused: `bytes literals (b"...") are not supported yet` |
| `Error(...)` values | undefined |
| Optional types `T?`, `??` | not parsed |
| Enums, type aliases, generics | not in the grammar |
| `Function` as a type hint | `Unknown type` (function values themselves work: [Closures](closures.md)) |

## Next Steps

- **[Variables](variables.md)**: scope and mutation
- **[Operators](operators.md)**: the operator reference
- **[Functions](functions.md)**: calls, recursion, hints
- **[Control Flow](control_flow.md)**: loops, `match`, `try`/`catch`
