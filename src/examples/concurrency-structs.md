# Concurrency & Structs

> Source: `tests/language/concurrency_structs.crush`

Struct instantiation with field access, plus `spawn`/`yield` for cooperative multitasking.

```crush
// Struct instantiation
let p = new Point();
p.x = 10;
p.y = 20;
print("Point x: " + p.x);
print("Point y: " + p.y);

// Spawn a concurrent task
print("Main starting spawn");
spawn worker();

print("Main yielding 1");
yield;

print("Main yielding 2");
yield;

print("Main resumed");

fn worker() {
    print("Worker running");
    yield;
    print("Worker finishing");
}
```

**What this shows:**
- `new StructName()` instantiates a struct
- Field assignment and access via `.` operator
- `spawn fn()` — launches a function as a cooperative task
- `yield` — suspends the current task and switches to another ready task
- `spawn`/`yield` implement M:1 cooperative concurrency (no preemption)

The tree-sitter grammar also supports struct definitions with typed fields:

```crush
struct Point {
    x: Float,
    y: Float
}

let p = Point { x: 10.0, y: 20.0 };
print(p.x);
```
