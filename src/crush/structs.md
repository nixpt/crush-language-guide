# Structs, Methods and Kinds

> Verified against crush-ast `aa07413` (2026-10-16). New since the 0.3 line:
> `impl`, `trait`, `@kind` and struct patterns (crush-ast CRUSH-zorro-41/43, the
> COSM object model).

A `struct` declares a record type. `impl` blocks give it methods, `trait`s give
several structs a shared interface with default methods, and `@kind(...)`
chooses its object semantics (reference or value, how `self` is bound, how
lookup works). Under the hood each struct is a **Kind** of COSM, the Crush Object
Semantic Model that crush-ast also uses to lower other languages' classes; see
crush-ast's `docs/design/object-model.md`.

## Declaring and building

Write the fields on **one line** (a struct body spread over several lines is a
parse error today, gap `GAP-STRUCT-MULTILINE`). Build one with a literal that
names **every** field, or with `new Name()` and assign the fields later:

```crush
struct Point { x: Int, y: Int }
let p = Point { y: 2, x: 1 }
print(p)
print(p.x + p.y)
p.x = 10
print(p)
let q = new Point()
print(q)
q.y = 5
print(q)
print(q.x)
```

<!-- check: output -->
```text
{y: 2, x: 1}
3
{y: 2, x: 10}
{}
{y: 5}
null
```

An instance prints like a map, its fields in the order they were first set. A
field not yet set reads as `null`. Field type hints are not checked at run time.

A literal that misses a field or names an unknown one is a compile error:

<!-- check: error -->
```crush
struct Point { x: Int, y: Int }
let p = Point { x: 1, z: 2 }
```

```text
[compile] Parse errors: Unexpected token at line 2, column 15: struct Point has no field `z` (fields: x, y), Unexpected token at line 2, column 15: missing field(s) `y` in Point { ... }
```

## Structs are sealed

Writing a field the struct does not declare stops the program, on every engine:

<!-- check: runfail `P` is sealed: it has no field `z` (fields: x) -->
```crush
struct P { x: Int }
let p = P { x: 1 }
print(p)
p.z = 2
print("not reached")
```

```text
{x: 1}
[runtime] `P` is sealed: it has no field `z` (fields: x)
```

(`@kind(storage: open_dict)` makes a struct that accepts extra fields; see
[the table below](#kind-choosing-object-semantics).)

## Methods: `impl`

An `impl` block attaches methods. `self` is an explicit first parameter. A
method without `self` is called through the type, `Type::name(...)`, which is the
convention for constructors; `Type::method(value)` also calls an instance method
as a plain function.

```crush
struct Point { x: Int, y: Int }
impl Point {
    fn new(x, y) { return Point { x: x, y: y } }
    fn norm2(self) { return self.x * self.x + self.y * self.y }
    fn shift(self, d) {
        self.x = self.x + d
        return self
    }
}
let p = Point::new(3, 4)
print(p.norm2())
p.shift(1)
print(p.x)
print(Point::norm2(p))
```

<!-- check: output -->
```text
25
4
32
```

`p.shift(1)` changed `p` itself: by default `self` is the instance, not a copy.

`value.method(...)` always resolves on the receiver's struct, never on a global
function or capability. Calling a method the struct doesn't have is a run-time
error:

<!-- check: runfail `T` has no method `size` -->
```crush
struct S { n: Int }
impl S { fn size(self) { return self.n } }
struct T { n: Int }
let s = S { n: 3 }
print(s.size())
let t = T { n: 1 }
print(t.size())
```

```text
3
[runtime] `T` has no method `size`
```

Two current limits:

- The receiver must be a name. `S { n: 3 }.size()` is a parse error (`Cannot call
  non-function`); bind the value with `let` first.
- A method call on a **`for` loop variable** is mistaken for a capability call
  and the program is refused (`not available in this host: s.area`; crush-ast
  [#256](https://github.com/nixpt/crush-ast/issues/256)). Loop over indexes and
  bind `let s = items[i]`.

## Traits

A `trait` lists method signatures, and may give some of them a default body.
`impl Trait for Struct` supplies the rest:

```crush
struct Square { side: Int }
struct Circle { r: Int }
trait Shape {
    fn area(self);
    fn describe(self) { return "a shape with area " + self.area() }
}
impl Shape for Square { fn area(self) { return self.side * self.side } }
impl Shape for Circle {
    fn area(self) { return 3 * self.r * self.r }
    fn describe(self) { return "a circle" }
}
let sq = Square { side: 2 }
let c = Circle { r: 1 }
print(sq.describe())
print(c.describe())
```

<!-- check: output -->
```text
a shape with area 4
a circle
```

Leaving out a method that has no default is a compile error:

<!-- check: error -->
```crush
trait T { fn need(self); }
struct S { }
impl T for S { }
```

```text
[compile] line 3, col 1: `impl T for S` is missing `need`: trait `T` declares it without a default body
```

`impl` and `trait` are only allowed at the top level of a file.

## Equality

`==` on structs compares **fields** (structural equality). It does not compare
the struct type: two different structs with equal fields are `==`, and so is a
plain map with the same entries. `@kind(equality: identity)` makes `==` mean "the
same instance".

```crush
struct A { x: Int }
struct B { x: Int }
let a = A { x: 1 }
print(a == A { x: 1 })
print(a == A { x: 2 })
print(a == B { x: 1 })
print(a == {"x": 1})
```

<!-- check: output -->
```text
true
false
true
true
```

To ask *which* struct a value is, use a [struct pattern](#struct-patterns-in-match).
(`conv.type_of` reports `map` for any struct instance.)

## Reference and value semantics

By default a struct is a **reference**: assignment and argument passing share one
instance. `@kind(semantics: value(copy))` makes a value type that is copied on
assignment, argument passing and return. `x.clone()` deep-copies either kind.

```crush
@kind(semantics: value(copy))
struct V { x: Int }
struct R { x: Int }
fn bump(v) {
    v.x = v.x + 1
    return v
}
let a = V { x: 1 }
let b = a
b.x = 2
print(a.x)
let r = R { x: 1 }
let s = r
s.x = 2
print(r.x)
bump(a)
print(a.x)
bump(r)
print(r.x)
let t = r.clone()
t.x = 99
print(r.x)
```

<!-- check: output -->
```text
1
2
1
3
3
```

## Struct patterns in `match`

A struct pattern tests the value's struct type first, then compares or binds its
fields. Write `field: pattern` (there is no `{ x }` shorthand); patterns nest:

```crush
struct P { x: Int }
struct Q { x: Int }
struct Wrap { inner: Int }
fn describe(v) {
    match v {
        Wrap { inner: P { x: a } } => { return "wrap of P " + a }
        P { x: 1 } => { return "P one" }
        P { x: a } => { return "P " + a }
        Q { x: b } => { return "Q " + b }
        _ => { return "something else" }
    }
}
print(describe(P { x: 1 }))
print(describe(P { x: 5 }))
print(describe(Q { x: 5 }))
print(describe(Wrap { inner: P { x: 2 } }))
print(describe(42))
```

<!-- check: output -->
```text
P one
P 5
Q 5
wrap of P 2
something else
```

So unlike `==`, a pattern does distinguish `P { x: 5 }` from `Q { x: 5 }`. A
pattern naming a struct that isn't declared is a compile error (`no struct `Nope`
is declared, so no value can match it`).

## `@kind`: choosing object semantics

`@kind(key: value, ...)` written directly before a `struct` picks a strategy for
each aspect of the type. Unset keys keep Crush's defaults (in bold). An unknown
key or value is a compile error that lists the valid ones.

| Key | Values | What it controls |
|---|---|---|
| `storage` | **`sealed`**, `open_dict`, `open_dict_with_slots` | whether undeclared fields may be added |
| `semantics` | **`reference`**, `value(copy)`, `value(move)`, `value(clone_explicit)` | sharing vs copying on assignment |
| `receiver` | `dynamic_this`, `bound_self`, `bound_cls`, `explicit_value`, **`explicit_ref`**, `explicit_ref_mut` | what `self` is, and what `obj.method` (unbound) gives |
| `construct` | **`literal`**, `ctor(f)`, `js_new(f)`, `py_new_init(init)` / `py_new_init(new, init)` | what `Name(args)` does |
| `resolution` | **`none`**, `single`, `c3`, `prototype_chain`, `embedding_promotion` | how methods are looked up through `parents` |
| `parents` | a list of structs, `[Base, Mixin]` | the inheritance graph for `resolution` |
| `equality` | `identity`, **`structural`** | what `==` compares |

These are the object models of the languages crush-ast lowers (Python classes,
JS objects, Rust and Go values), which Crush can write directly. Strategies no
engine runs yet are refused at compile time rather than half-implemented:
`resolution: prototype_chain` gives `` struct `Z` declares
`@kind(resolution: prototype_chain)`, which no engine runs yet ``.

A constructor (`construct: ctor(init)`) runs `init` on a new instance when the
struct is called like a function. (`crush run` handles this; `crushc` and
`crush build` wrongly reject it with `Undefined function: Acc`, crush-ast
[#260](https://github.com/nixpt/crush-ast/issues/260).)

<!-- check: nocrushc crush-ast #260 -->
```crush
@kind(construct: ctor(init))
struct Acc { total: Int }
impl Acc {
    fn init(self, start) { self.total = start }
    fn add(self, n) {
        self.total = self.total + n
        return self
    }
}
let a = Acc(10)
a.add(5)
print(a.total)
print(a)
```

<!-- check: output -->
```text
15
{total: 15}
```

Multiple inheritance with a C3 method resolution order (Python's):

```crush
@kind(resolution: c3)
struct Base { }
impl Base {
    fn who(self) { return "base" }
    fn hello(self) { return "hello from base" }
}
@kind(resolution: c3, parents: [Base])
struct Left { }
impl Left { fn who(self) { return "left" } }
@kind(resolution: c3, parents: [Base])
struct Right { }
impl Right {
    fn who(self) { return "right" }
    fn only_right(self) { return "right only" }
}
@kind(resolution: c3, parents: [Left, Right])
struct Bottom { }
let b = Bottom { }
print(b.who())
print(b.only_right())
print(b.hello())
```

<!-- check: output -->
```text
left
right only
hello from base
```

Bound methods: with `receiver: bound_self`, reading `c.inc` (without calling it)
gives a function value bound to `c`. With the default receiver it gives the plain
function, which takes the instance as its first argument:

```crush
@kind(receiver: bound_self)
struct Counter { n: Int }
impl Counter {
    fn inc(self) {
        self.n = self.n + 1
        return self.n
    }
}
struct P { x: Int }
impl P { fn get(self) { return self.x } }
let c = Counter { n: 0 }
let f = c.inc
print(f())
print(f())
print(c.n)
let p = P { x: 7 }
let g = p.get
print(g(p))
```

<!-- check: output -->
```text
1
2
2
7
```

Open storage accepts fields the struct doesn't declare:

```crush
@kind(storage: open_dict)
struct O { x: Int }
let o = O { x: 1 }
o.extra = 2
print(o)
```

<!-- check: output -->
```text
{x: 1, extra: 2}
```

## Engines

Structs, `impl`, traits and every `@kind` above run on the CVM1 VM (`crush run`,
the portable VM and the browser build). The AOT backends build sealed structs
(and enforce the seal) but refuse method calls by name, e.g. `` the Rust AOT
backend cannot compile: `call_member` ``; see [Engines and AOT](engines.md).

## Next Steps

- **[Control Flow](control_flow.md)**: `match`
- **[Closures and Function Values](closures.md)**
