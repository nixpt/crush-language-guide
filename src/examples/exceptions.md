# Exception Handling

`try` / `catch` / `throw` work, including across function calls. Any value can
be thrown.

```crush
print("Starting")

try {
    print("Inside try block")
    throw "Oops"
    print("This should not print")
} catch e {
    print("Caught exception: " + e)
}

print("After catch block")

fn safe_divide(a: Int, b: Int) -> Int {
    if b == 0 {
        throw "division by zero"
    }
    return a / b
}

try {
    print(safe_divide(10, 2))
    print(safe_divide(10, 0))
} catch e {
    print("Error: " + e)
}

// any value can be thrown
try {
    throw {"code": 404, "msg": "not found"}
} catch err {
    print(err.code)
    print(err.msg)
}
```

<!-- check: output -->
```text
Starting
Inside try block
Caught exception: Oops
After catch block
5
Error: division by zero
404
not found
```

**What this shows:**

- `try { ... } catch e { ... }` — the thrown value binds to `e`
- `throw expr` — the rest of the `try` body is skipped
- Output printed before the `throw` is kept (`5` above)
- Thrown values may be strings, numbers, or objects (`err.code`)
- `catch` also handles VM faults such as `1 / 0` and failed capability calls
  (the caught value prints as `error(<message>)`); a crashing polyglot block or an
  exhausted quota still ends the program — see
  [Control Flow](../crush/control_flow.md#what-catch-catches)
