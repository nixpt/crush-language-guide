# Arrays & Loops

> Source: `tests/language/arrays_and_loops.crush`

Array creation, indexed access, for-in iteration, and loop control.

```crush
let arr = [10, 20, 30, 40, 50];
print("Array created: " + arr);

let size = len(arr);
print("Array length: " + size);

// Indexed access
print(arr[0]);   // 10
print(arr[2]);   // 30

// Iterate all elements
for x in arr {
    print("Item: " + x);
}

// break — stop at 30
for x in arr {
    if x == 30 {
        break;
    }
    print("Item: " + x);
}

// continue — skip 30
for x in arr {
    if x == 30 {
        continue;
    }
    print("Item: " + x);
}
```

**What this shows:**
- Array literal `[v1, v2, ...]` and `len()` built-in
- `arr[i]` zero-based integer indexing
- `for x in iterable { }` — iterates arrays and ranges
- `break` exits the loop immediately; `continue` skips to next iteration

String characters are also indexable:

```crush
let s = "hello";
print(s[0]);   // "h"
print(s[4]);   // "o"
```

Range iteration with `..`:

```crush
for i in 0..10 {
    print(i);   // 0 through 9
}
```
