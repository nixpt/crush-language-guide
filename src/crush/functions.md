# Functions

> Verified against crush-ast `c1cc21fb` (2026-10-30).

This chapter covers defining and calling functions. Named functions are
top-level declarations, and they are also **values**: you can store one in a
variable, pass it as an argument and return it. Lambdas and closures have their
own chapter, [Closures and Function Values](closures.md).

## Defining functions

```crush
fn greet(name: String) {
    print("Hello, " + name + "!")
}

fn add(a: Int, b: Int) -> Int {
    return a + b
}

greet("Alice")
print(add(5, 3))
```

<!-- check: output -->
```text
Hello, Alice!
8
```

- Parameter and return **type hints are optional**. When present they are checked
  at compile time at call sites (`add("x", 1)` is a compile error).
- The number of arguments is checked at compile time: `add(1)` →
  `Function 'add' expects 2 arguments, found 1`.
- There are no default parameter values (`fn f(x = 1)` is a parse error) and no
  variadic parameters.
- A function may be called before its definition appears in the file.

## Returning values

Return with `return`. A function that falls off the end — or uses a bare
`return` — yields `null`. A final expression is **not** an implicit return:

```crush
fn check_sign(x: Int) -> String {
    if x > 0 {
        return "positive"
    } else if x < 0 {
        return "negative"
    }
    return "zero"
}

fn log_message(msg: String) {
    print("[LOG] " + msg)
}

print(check_sign(5))
print(check_sign(-2))
print(check_sign(0))
log_message("done")
print(log_message("again"))
```

<!-- check: output -->
```text
positive
negative
zero
[LOG] done
[LOG] again
null
```

The return-type hint is not checked against what the body actually returns
today: `fn f() -> Int { return "s" }` compiles.

## Recursion

```crush
fn factorial(n: Int) -> Int {
    if n <= 1 {
        return 1
    }
    return n * factorial(n - 1)
}

fn fib(n) {
    if n < 2 {
        return n
    }
    return fib(n - 1) + fib(n - 2)
}

print(factorial(5))
print(fib(15))
```

<!-- check: output -->
```text
120
610
```

Mutual recursion works too. Recursion depth is capped by the VM's call-depth
quota — **256 frames by default** (`--max-call-depth N` on `crush-run`); exceeding
it ends the program with `call depth quota exceeded`. The other default quotas are
1,000,000 instructions (`--max-steps`), a 4096-slot stack (`--max-stack`), 1 MiB of
output (`--max-output`), and a 30-second wall-clock limit per polyglot block.

<!-- check: runfail call depth quota exceeded -->
```crush
fn d(n) {
    return d(n - 1)
}
print(d(1))
```

## Higher-order functions and lambdas

A function name is a value. Store it, pass it, call it through the variable:

```crush
fn double(n) {
    return n * 2
}
fn apply(f, x) {
    return f(x)
}
let f = double
print(f(21))
print(apply(double, 4))
```

<!-- check: output -->
```text
42
8
```

Anonymous functions are written `|params| expression` or `|params| { block }`:

```crush
let double = |x| { return x * 2 }
let add = |a, b| a + b
print(double(21))
print(add(2, 3))
```

<!-- check: output -->
```text
42
5
```

They capture variables from where they are written; that, and the rules for
calling function values, is in [Closures and Function Values](closures.md). The
built-ins `print` and `len` are not values (`let g = len` is a compile error that
says so, crush-ast [#257](https://github.com/nixpt/crush-ast/issues/257)); wrap them:
`|x| len(x)`.

The pipeline operator (`x |> f`) takes a function name or a variable holding one:

```crush
fn double(n) {
    return n * 2
}
fn inc(n) {
    return n + 1
}
print(5 |> double |> inc)
```

<!-- check: output -->
```text
11
```

## Concurrency: `spawn`, `yield`, `async`, `await`

`spawn f(args)` starts a green task, `yield` lets other tasks run, and `await h`
waits for a task and returns its result. They are covered in
[Concurrency](concurrency.md). In short:

```crush
fn worker() {
    print("worker")
}
spawn worker()
yield
print("main")
```

<!-- check: output -->
```text
worker
main
```

## Best practices

- Keep functions small and give parameters type hints — they document the
  interface and catch mistakes at compile time.
- Pass data in as parameters: named functions cannot see top-level variables
  ([Variables](variables.md#module-level-variables-are-not-visible-inside-functions));
  a top-level lambda can.
- Prefer descriptive names (`calculate_total_price`, not `calc`).

## Next Steps

- **[Closures and Function Values](closures.md)**
- **[Capability System](capabilities.md)**
- **[Polyglot Programming](polyglot.md)**
