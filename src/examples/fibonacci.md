# Fibonacci & Functions

The canonical recursion example, with typed function signatures. Run it with
`crush run fib.crush`.

```crush
fn fib(n: Int) -> Int {
    if n <= 1 {
        return n
    }
    return fib(n - 1) + fib(n - 2)
}

fn factorial(n: Int) -> Int {
    if n <= 1 {
        return 1
    }
    return n * factorial(n - 1)
}

fn main() {
    for i in 0..10 {
        print("fib(" + i + ") = " + fib(i))
    }
    print("10! = " + factorial(10))
}
```

<!-- check: output -->
```text
fib(0) = 0
fib(1) = 1
fib(2) = 1
fib(3) = 2
fib(4) = 3
fib(5) = 5
fib(6) = 8
fib(7) = 13
fib(8) = 21
fib(9) = 34
10! = 3628800
```

**What this shows:**

- `fn name(param: Type) -> ReturnType` — a typed signature (hints are checked at
  call sites)
- Recursion needs no special annotation; the default call-depth limit is 256
  frames, which is far more than this needs
- `return` is explicit — there is no implicit last-expression return
- `"text" + number` converts the number, so `print` can build a line
- A program may have both top-level statements and `fn main()`; the top-level
  statements run first, then `main`
