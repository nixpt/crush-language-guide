# Structs (and Concurrency)

A struct is declared once, created with `new Name()`, and filled in by assigning
fields. Structs are passed by reference.

```crush
struct Point { x: Float, y: Float }

fn dist2(a, b) {
    let dx = a.x - b.x
    let dy = a.y - b.y
    return dx * dx + dy * dy
}

let p = new Point()
p.x = 1.0
p.y = 2.0
let q = new Point()
q.x = 4.0
q.y = 6.0

print("p = (" + p.x + ", " + p.y + ")")
print("squared distance: " + dist2(p, q))
```

<!-- check: output -->
```text
p = (1.0, 2.0)
squared distance: 25.0
```

**What this shows:**

- `struct Point { x: Float, y: Float }` — declare it on **one line**; the parser
  does not yet accept a struct body that spans lines
- `new Point()` takes no arguments; set each field with `p.x = ...`
- Field access works inside functions, including on parameters (`a.x`)
- `Float` arithmetic: `3.0 * 3.0 + 4.0 * 4.0` is `25.0`

## Concurrency

Earlier revisions of this guide demonstrated `spawn worker()` with cooperative
`yield`. That does **not** run today: the compiler emits a `SPAWN` instruction
without its operand and the assembler rejects the program
(`SPAWN takes 1 operand(s), got 0`). The scheduler for green threads exists in
`crush-vm`, but the source-level path is unfinished — crush-ast **CRUSH-34**
(spawn/await/yield execution) is open. A bare `yield` statement compiles and is a
no-op.

<!-- check: nyi CRUSH-34 -->
```crush
fn worker() {
    print("worker running")
    yield
    print("worker finishing")
}

spawn worker()
print("main")
yield
print("main again")
```
