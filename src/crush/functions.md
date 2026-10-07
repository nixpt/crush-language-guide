# Functions

This chapter covers defining and calling functions. Crush functions are named,
top-level declarations. **Functions are not first-class values yet** — you can
call one by name, but you can't store it in a variable or pass it as an argument
(see [Higher-order functions](#higher-order-functions-and-lambdas)).

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

> **Not yet implemented.** Passing a function by name (`apply(double, 21)`),
> storing one in a variable (`let f = double`), and anonymous functions
> (`|x| { ... }`, `|x| => x * 2`) all fail to compile. The lexer reads a bare `|`
> as an identifier, so the lambda parser is unreachable (crush-ast **CRUSH-75**,
> open); closures that capture variables are a separate, larger gap. Until then,
> write ordinary named functions and call them directly, or use the
> pipeline operator (`x |> f`), which does accept a function **name**:

<!-- check: nyi CRUSH-75 -->
```crush
fn double(n) {
    return n * 2
}
let f = double
print(f(21))
```

<!-- check: nyi CRUSH-75 -->
```crush
let double = |x| { return x * 2 }
print(double(21))
```

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

These keywords are in the grammar, but the end-to-end path is incomplete: a
program that contains `spawn f()`, `async fn`, or `await` is rejected by the
assembler (`SPAWN takes 1 operand(s), got 0`). The AI/concurrency opcodes are
tracked under crush-ast **CRUSH-1** / **CRUSH-34**. A bare `yield` statement
compiles and runs (it is a no-op without a spawned task).

<!-- check: nyi CRUSH-34 -->
```crush
fn worker() {
    print("worker")
}
spawn worker()
yield
print("main")
```

## Best practices

- Keep functions small and give parameters type hints — they document the
  interface and catch mistakes at compile time.
- Pass data in as parameters: functions cannot see top-level variables
  ([Variables](variables.md#module-level-variables-are-not-visible-inside-functions)).
- Prefer descriptive names (`calculate_total_price`, not `calc`).

## Next Steps

- **[Capability System](capabilities.md)**
- **[Polyglot Programming](polyglot.md)**
