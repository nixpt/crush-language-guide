# Fibonacci & Functions

> Source: `crates/core/crush-lang/tests/fixtures/fibonacci.crush`

The canonical recursion example — also validates type-hinted function signatures.

```crush
fn fib(n: Int) -> Int {
    if n <= 1 {
        return n
    }
    return fib(n - 1) + fib(n - 2)
}

fn main() {
    let result = fib(10)
    return result
}
```

**What this shows:**
- `fn name(param: Type) -> ReturnType` — typed function signature
- Recursive calls work without any special annotation
- `return` is explicit; there is no implicit last-expression return

A simpler function that doubles its argument (from `function_call.crush`):

```crush
fn double(n: Int) {
    return n * 2
}

double(21)
```

Functions without a `-> Type` annotation implicitly return `Void`.
