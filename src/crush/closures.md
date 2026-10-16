# Closures and Function Values

> Verified against crush-ast `aa07413` (2026-10-16). New since the 0.3 line
> (crush-ast CRUSH-251).

Functions in Crush are values. A named function can be stored, passed and
returned; a **lambda** is a function written inline; and a lambda **captures** the
variables around it, which makes it a closure.

## Function values

A function's name, used without calling it, is a value:

```crush
fn double(n) { return n * 2 }
fn apply(f, x) { return f(x) }
fn twice(f) {
    return |x| f(f(x))
}

let g = double
print(g(5))
print(apply(double, 21))
let quad = twice(double)
print(quad(3))
```

<!-- check: output -->
```text
10
42
12
```

Function values go in arrays and maps like anything else, and they print as
`<fn name>`:

```crush
fn double(n) { return n * 2 }
let fs = [double, |n| n - 1]
let first = fs[0]
let second = fs[1]
print(first(10))
print(second(10))
print(first)
```

<!-- check: output -->
```text
20
9
<fn double>
```

## Lambdas

A lambda is `|params| expression`, or `|params| { ... }` with a block that uses
`return`. `||` is a lambda with no parameters.

```crush
let sq = |x| x * x
let add = |a, b| a + b
let clamp = |v| {
    if v > 10 {
        return 10
    }
    return v
}
let hello = || "no params"
print(sq(4))
print(add(2, 3))
print(clamp(42))
print(hello())
```

<!-- check: output -->
```text
16
5
10
no params
```

A `let`-bound lambda can call itself by name:

```crush
let fact = |n| {
    if n <= 1 {
        return 1
    }
    return n * fact(n - 1)
}
print(fact(6))
```

<!-- check: output -->
```text
720
```

## Capture

A lambda captures the variables it uses from the function (or top-level script)
around it. Capture is **by reference**: the closure and its surroundings share
the variable.

```crush
fn make_adder(a) {
    return |b| a + b
}
let add3 = make_adder(3)
let add10 = make_adder(10)
print(add3(4))
print(add10(4))
```

<!-- check: output -->
```text
7
14
```

Because the variable is shared, a closure can keep state, and each call of the
factory makes a new variable:

```crush
fn make_counter() {
    let c = 0
    return || {
        c = c + 1
        return c
    }
}
let a = make_counter()
let b = make_counter()
print(a())
print(a())
print(b())
print(a())
```

<!-- check: output -->
```text
1
2
1
3
```

Writes go both ways: the function sees what the closure wrote, and the closure
sees later writes by the function.

```crush
fn main() {
    let x = 1
    let get = || x
    let set = |v| {
        x = v
    }
    x = 5
    print(get())
    set(9)
    print(x)
    print(get())
}
```

<!-- check: output -->
```text
5
9
9
```

A top-level lambda captures top-level variables the same way. (A *named*
function can't see top-level variables at all; see
[Variables](variables.md#module-level-variables-are-not-visible-inside-functions).)

```crush
let k = 3
let mul = |x| x * k
print(mul(2))
k = 10
print(mul(2))
```

<!-- check: output -->
```text
6
20
```

### Closures made in a loop

A loop variable is **one** variable, so closures that capture it all see its last
value (Python's late binding). A `let` in the loop body is a fresh binding each
time round, so capture that when you want each closure to keep its own value:

```crush
fn main() {
    let late = []
    let fresh = []
    let i = 0
    while i < 3 {
        late.push(|| i)
        let j = i
        fresh.push(|| j)
        i = i + 1
    }
    let l0 = late[0]
    let f0 = fresh[0]
    let f2 = fresh[2]
    print(l0())
    print(f0())
    print(f2())
}
```

<!-- check: output -->
```text
3
0
2
```

## Calling a function value

Only a **name** can be called. `fs[0](1)` and `make()(2)` are parse errors today
(crush-ast CRUSH-zorro-24); bind the value to a name first, as the examples above
do.

<!-- check: error -->
```crush
let fs = [|x| x + 1]
print(fs[0](1))
```

```text
[compile] Parse errors: Unexpected token at line 2, column 15: Cannot call non-function
```

The built-ins `print` and `len` are not function values: `let g = len` compiles
but fails when it runs (`load from uninitialised slot`, crush-ast
[#257](https://github.com/nixpt/crush-ast/issues/257)). Wrap them in a lambda:

```crush
let size = |x| len(x)
print(size([1, 2, 3]))
```

<!-- check: output -->
```text
3
```

## With the pipeline, `spawn` and `parallel_map`

The pipeline operator takes any function value bound to a name, and so do
[`spawn` and `parallel_map`](concurrency.md):

```crush
let inc = |n| n + 1
print(3 |> inc |> inc)
print(parallel_map([1, 2, 3], |n| n * n))
```

<!-- check: output -->
```text
5
[1, 4, 9]
```

## Engines

Closures run on the CVM1 VM (`crush run`) and in the browser build. The AOT
backends refuse them by name rather than miscompiling them: `crush-aotc` reports
`` the Rust AOT backend cannot compile: `make_closure` ``. See
[Engines and AOT](engines.md).

## Next Steps

- **[Structs, Methods and Kinds](structs.md)**: methods as values (`bound_self`)
- **[Concurrency](concurrency.md)**
