# Concurrency

> Verified against crush-ast `cb655f3` (2026-10-16). New since the 0.3 line
> (crush-ast #161, #174/#177, #175, CRUSH-251 step 5).

Crush has two kinds of concurrency:

- **Green tasks**: `spawn`, `yield`, `await` and `async fn`. Tasks run inside one
  VM, take turns at `yield` / `await`, and share the variables they capture.
- **`parallel_map(items, f)`**: real parallelism for pure computation. Each item
  runs in its own share-nothing VM (a thread on the native VM).

## `spawn`, `yield`, `await`

`spawn f(args)` starts a task and returns a handle; `await h` waits for the task
and gives its return value; `yield` lets the other tasks run.

```crush
fn worker(name, n) {
    let i = 0
    while i < n {
        print(name + " step " + i)
        yield
        i = i + 1
    }
    return name + " done"
}
fn main() {
    let a = spawn worker("a", 2)
    let b = spawn worker("b", 2)
    print(await a)
    print(await b)
}
```

<!-- check: output -->
```text
a step 0
b step 0
a step 1
b step 1
a done
b done
```

`spawn` takes any function value, including a closure. A spawned closure shares
the variables it captured with the function that made it, so the main task sees
its writes:

```crush
fn main() {
    let n = 0
    let inc = || {
        n = n + 1
        return n
    }
    let h = spawn inc()
    await h
    print(n)
}
```

<!-- check: output -->
```text
1
```

An `async fn` runs as a task when called; `await` its result:

```crush
async fn sub(a, b) {
    return a - b
}
fn main() {
    let r = await sub(10, 3)
    print(r)
}
```

<!-- check: output -->
```text
7
```

Calling it without `await` gives the handle itself (it prints as `<handle 1>`).

### When the program ends

The program ends when the main task ends, as in Go: a spawned task that has not
run by then is abandoned. Give it a chance with `yield`, or `await` it.

```crush
fn worker() {
    print("worker")
}
fn main() {
    spawn worker()
    print("main ends")
}
```

<!-- check: output -->
```text
main ends
```

`await` on a value that is not a task handle gives the value back, as in JavaScript:
`let v = await 5` sets `v` to `5`. (crush-ast builds before
[#265](https://github.com/nixpt/crush-ast/pull/265) gave `null`; see
[#251](https://github.com/nixpt/crush-ast/issues/251).)

## `parallel_map`

`parallel_map(items, f)` calls `f` on every item, each in its own VM, and returns
the results in input order. Anything the workers print also comes out in input
order:

```crush
fn fib(n) {
    if n < 2 {
        return n
    }
    return fib(n - 1) + fib(n - 2)
}
fn main() {
    print(parallel_map([1, 2, 3, 4], |n| n * n))
    print(parallel_map([10, 15, 20], fib))
    let k = 10
    let r = parallel_map([3, 1, 2], |x| {
        print("item " + x)
        return x * k
    })
    print(r)
}
```

<!-- check: output -->
```text
[1, 4, 9, 16]
[55, 610, 6765]
item 3
item 1
item 2
[30, 10, 20]
```

Workers **share nothing**: each gets its own copy of the item and of anything it
captured. A worker may read a captured variable but not change it, because the
change would be lost, so that is an error:

<!-- check: runfail the function changed something it captured -->
```crush
fn main() {
    let total = 0
    parallel_map([1, 2], |x| {
        total = total + x
        return x
    })
    print(total)
}
```

```text
[runtime] parallel_map: item 0: parallel_map: the function changed something it captured (a variable it or a function it calls captured, or a captured array/map); a parallel_map worker shares nothing, so the change would be lost — return the value instead
```

If several items fail, the first failing item *in input order* is reported:

<!-- check: runfail parallel_map: item 1: division by zero -->
```crush
fn main() {
    print(parallel_map([2, 0, 1, 0], |x| 10 / x))
}
```

## Engines

The native VM (`crush run`) runs tasks and `parallel_map` workers; the portable
VM (the browser build) runs the same programs with the same output, running
`parallel_map` items one after another. The AOT backends refuse `spawn` by name
instead of dropping it: `` `spawn` (green tasks) isn't supported on the Rust AOT
backend yet (#161) ``. See [Engines and AOT](engines.md).

## Next Steps

- **[Closures and Function Values](closures.md)**
- **[Engines and AOT](engines.md)**
