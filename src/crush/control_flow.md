# Control Flow

Crush provides standard control flow structures: if/else, while loops, and for loops.

## If Statements

### Basic If

```crush
if condition {
    @io.print("Condition is true");
}
```

### If-Else

```crush
if x > 0 {
    @io.print("Positive");
} else {
    @io.print("Non-positive");
}
```

### If-Else If-Else

```crush
if score >= 90 {
    @io.print("A");
} else if score >= 80 {
    @io.print("B");
} else if score >= 70 {
    @io.print("C");
} else {
    @io.print("F");
}
```

## While Loops

### Basic While

```crush
let i = 0;
while i < 5 {
    @io.print(i);
    i = i + 1;
}
```

### Infinite Loop with Break

```crush
let counter = 0;
while true {
    if counter >= 10 {
        break;
    }
    @io.print(counter);
    counter = counter + 1;
}
```

## For Loops

### Iterating Over Arrays

```crush
let numbers = [1, 2, 3, 4, 5];
for num in numbers {
    @io.print(num);
}
```

### Range Iteration (Future Feature)

```crush
for i in range(0, 10) {
    @io.print(i);
}
```

## Break and Continue

### Break

Exit the loop immediately:

```crush
while true {
    if should_exit {
        break;
    }
    // ...
}
```

### Continue

Skip to next iteration:

```crush
for i in numbers {
    if i % 2 == 0 {
        continue;  // Skip even numbers
    }
    @io.print(i);
}
```

## Pattern Matching (Future Feature)

```crush
match value {
    0 => @io.print("Zero"),
    1 => @io.print("One"),
    _ => @io.print("Other")
}
```

## Next Steps

- **[Functions](functions.md)**: Define and call functions
- **[Capabilities](capabilities.md)**: Secure I/O operations
