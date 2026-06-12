# Exception Handling

> Source: `tests/language/exception_test.crush`

`try`/`catch`/`throw` are fully implemented — not a future feature.

```crush
print("Starting Exception Test")

try {
    print("Inside try block")
    throw "Oops"
    print("This should not print")
} catch e {
    print("Caught exception: " + e)
}

print("After catch block")
```

Output:
```
Starting Exception Test
Inside try block
Caught exception: Oops
After catch block
```

**What this shows:**
- `try { ... } catch e { ... }` — the caught value binds to `e`
- `throw expr` — throws any value as an exception (string, Int, Map, etc.)
- Execution after `throw` inside the `try` block is skipped
- Execution after the `catch` block continues normally

The compiler emits `enter_try` / `exit_try` / `throw` CASM instructions.

## Defensive Pattern

```crush
fn safe_divide(a: Int, b: Int) -> Int {
    if b == 0 {
        throw "division by zero";
    }
    return a / b;
}

try {
    let result = safe_divide(10, 0);
    print(result);
} catch e {
    print("Error: " + e);
}
```
