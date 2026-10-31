# Structs (and Concurrency)

> Verified against crush-ast `bad81048` (v0.9.0, 2026-10-31).

A struct is declared once (on one line), built with a literal, and given methods
in an `impl` block. Structs are passed by reference.

```crush
struct Point { x: Float, y: Float }
impl Point {
    fn new(x, y) { return Point { x: x, y: y } }
    fn dist2(self, other) {
        let dx = self.x - other.x
        let dy = self.y - other.y
        return dx * dx + dy * dy
    }
    fn label(self) { return "(" + self.x + ", " + self.y + ")" }
}

let p = Point::new(1.0, 2.0)
let q = Point { x: 4.0, y: 6.0 }

print("p = " + p.label())
print("squared distance: " + p.dist2(q))
```

<!-- check: output -->
```text
p = (1.0, 2.0)
squared distance: 25.0
```

**What this shows:**

- `struct Point { x: Float, y: Float }`: declare it on **one line**; the parser
  does not yet accept a struct body that spans lines
- `Point { x: 4.0, y: 6.0 }` names every field; `Point::new(...)` is a method
  without `self`, called through the type
- `p.dist2(q)` resolves `dist2` on `p`'s struct; `self` is `p`
- `Float` arithmetic: `3.0 * 3.0 + 4.0 * 4.0` is `25.0`

More in [Structs, Methods and Kinds](../crush/structs.md).

## Concurrency

`spawn` starts a green task; tasks take turns at `yield`, and `await` collects a
task's result. The workers below share one captured counter:

```crush
fn main() {
    let done = 0
    let worker = |name| {
        print(name + " running")
        yield
        print(name + " finishing")
        done = done + 1
        return name
    }
    let a = spawn worker("a")
    let b = spawn worker("b")
    print("main")
    print(await a)
    print(await b)
    print("finished: " + done)
}
```

<!-- check: output -->
```text
main
a running
b running
a finishing
b finishing
a
b
finished: 2
```

More in [Concurrency](../crush/concurrency.md).
