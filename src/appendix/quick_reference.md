# Quick Reference

Quick reference cards for CASM and Crush.

## CASM Instructions Quick Reference

### Stack Operations
| Instruction | Effect | Example |
|-------------|--------|---------|
| `push_int` | `→ int` | `{"op": "push_int", "value": 42}` |
| `push_str` | `→ str` | `{"op": "push_str", "value": "hello"}` |
| `pop` | `value →` | `{"op": "pop"}` |
| `dup` | `a → a, a` | `{"op": "dup"}` |

### Arithmetic
| Instruction | Effect | Example |
|-------------|--------|---------|
| `add` | `a, b → result` | `{"op": "add"}` |
| `sub` | `a, b → result` | `{"op": "sub"}` |
| `mul` | `a, b → result` | `{"op": "mul"}` |
| `div` | `a, b → result` | `{"op": "div"}` |

### Control Flow
| Instruction | Effect | Example |
|-------------|--------|---------|
| `jmp` | Jump | `{"op": "jmp", "target": 10}` |
| `jmp_if` | `cond →` jump if true | `{"op": "jmp_if", "target": 10}` |
| `call` | Call function | `{"op": "call", "function": "add"}` |
| `ret` | Return | `{"op": "ret"}` |

### Capabilities
| Instruction | Effect | Example |
|-------------|--------|---------|
| `cap_call` | Call capability | `{"op": "cap_call", "name": "io.print", "argc": 1}` |

## Crush Syntax Quick Reference

### Variables
```crush
let x = 42;
let name: String = "Alice";
```

### Functions
```crush
fn greet(name: String) {
    @io.print("Hello, " + name);
}

fn add(a: Int, b: Int) -> Int {
    return a + b;
}
```

### Control Flow
```crush
if condition {
    // ...
} else {
    // ...
}

while condition {
    // ...
}

for item in collection {
    // ...
}
```

### Capabilities
```crush
@io.print("Hello");
@fs.read("file.txt");
@net.http("https://api.example.com");
```

### Polyglot
```crush
@python {
    print("Hello from Python")
}

@javascript {
    console.log("Hello from JS");
}

@bash {
    echo "Hello from Bash"
}
```

## Common Patterns

### Read File
```crush
if @fs.exists("file.txt") {
    let content = @fs.read("file.txt");
    @io.print(content);
}
```

### HTTP Request
```crush
let response = @net.get("https://api.example.com/data");
@io.print(response);
```

### Command-Line Args
```crush
let args = @sys.args();
if args.length < 2 {
    @io.eprint("Usage: program <arg>");
    @sys.exit(1);
}
```

## Type Reference

| Type | Example | Description |
|------|---------|-------------|
| `Int` | `42` | 64-bit integer |
| `Float` | `3.14` | 64-bit float |
| `String` | `"hello"` | UTF-8 string |
| `Bool` | `true` | Boolean |
| `Null` | `null` | Null value |
| `Array` | `[1, 2, 3]` | Array |
| `Map` | `{"key": "value"}` | Map/Object |

## Capability Reference

| Capability | Description |
|------------|-------------|
| `io.print` | Print to stdout |
| `io.read` | Read from stdin |
| `fs.read` | Read file |
| `fs.write` | Write file |
| `fs.exists` | Check if file exists |
| `net.http` | HTTP request |
| `sys.exec` | Execute command |
| `sys.args` | Get CLI arguments |
