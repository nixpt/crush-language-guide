# Polyglot Programming

Crush's killer feature: **embed multiple programming languages in a single program**. Write Python for data science, JavaScript for JSON, Bash for system tasks, and Rust for performance - all seamlessly integrated.

## Language Blocks

Use `@language { ... }` syntax to embed code:

```crush
fn main() {
    @python {
        print("Hello from Python!")
    }
    
    @javascript {
        console.log("Hello from JavaScript!");
    }
    
    @bash {
        echo "Hello from Bash!"
    }
}
```

## Walker Implementation Status

Each language needs a **walker** — a compiler component that parses source code and emits CAST.
Walkers vary in completeness:

| Language | Syntax | Walker status | Supported constructs |
|----------|--------|---------------|----------------------|
| JavaScript/TypeScript | `@javascript { }` | Complete | Dual-backend (`swc` primary, `boa` optional). Full JS + TS + JSX/TSX |
| Python | `@python { }` | Complete | Native frontend via `rustpython-parser` |
| Rust | `@rust { }` | Complete | Native frontend via `syn` |
| Bash | `@bash { }` | Complete | Full AST parsing via `brush-parser` |
| C / C++ | `@c { }` | Mature | Tree-sitter-c and tree-sitter-cpp |
| Go | `@go { }` | Mature | Tree-sitter-based walker |
| Zig | `@zig { }` | Mature | Tree-sitter-based walker |
| Wasm | `@wasm { }` | Mature | Integration tested with `.wat` and WASI |

## Polyglot Execution Model

Each polyglot block executes inside a **WebAssembly (WASM) sandbox** using the **WASI capability model**:

```text
┌─────────────────────────────────────────────────────┐
│                  Crush Runtime                       │
│  ┌───────────────────────────────────────────────┐  │
│  │           Wasmtime / Wasmer Runtime           │  │
│  │  ┌─────────────────────────────────────────┐  │  │
│  │  │        Language WASM Modules            │  │  │
│  │  │  • Python (RustPython/Pyodide)          │  │  │
│  │  │  • JavaScript (QuickJS-wasm)            │  │  │
│  │  │  • Rust (wasm32-wasi)                   │  │  │
│  │  │  • C/Go (Emscripten/TinyGo)             │  │  │
│  │  └─────────────────────────────────────────┘  │  │
│  │                 WASI ABI                      │  │
│  └───────────────────────────────────────────────┘  │
│                        │                             │
│                        ▼                             │
│            Crush Capability Bridge                   │
│     (Maps WASI pre-opens → Crush capabilities)      │
└─────────────────────────────────────────────────────┘
```

### Why WASI?

- **Cross-platform**: Same security on Linux, macOS, Windows
- **Built-in capability model**: No custom sandboxing per language
- **Pre-opened directories**: WASM modules only access granted paths
- **Industry standard**: Used by Cloudflare Workers, Fastly, etc.

### Execution Properties

- **Isolated**: Each capsule has its own memory space
- **Capability-controlled**: Capsules only receive explicitly granted capabilities
- **Type-safe**: Values are marshaled through CASM-compatible types
- **Sandboxed**: Cannot escape the capsule boundary or access host system directly

### Example

[![Run in Codebucket (Codespaces)](https://img.shields.io/badge/Run_in-Codebucket_(Codespaces)-blue?logo=github)](https://codespaces.new/nixpt/crush-website)

```crush
fn main() {
    @python {
        # This capsule has ONLY io.print capability
        # Cannot access fs.write, net.http, etc.
        print("Hello from isolated Python capsule")
    }
}
```

## Variable Sharing

Variables are shared **when representable in CASM's core type system**.

### Shareable Types

| CASM Type | Python | JavaScript | Bash | Rust | C | Go |
|-----------|--------|------------|------|------|---|----|
| Int | `int` | `number` | `$VAR` | `i64` | `int64_t` | `int64` |
| Float | `float` | `number` | `$VAR` | `f64` | `double` | `float64` |
| String | `str` | `string` | `$VAR` | `String` | `char*` | `string` |
| Bool | `bool` | `boolean` | `true/false` | `bool` | `bool` | `bool` |
| Array | `list` | `Array` | `array` | `Vec` | `array` | `[]` |
| Map | `dict` | `Object` | `assoc` | `HashMap` | `struct` | `map` |

### Language-Specific Objects Stay Local

Python classes, JavaScript Promises, Rust structs, and other language-specific objects **remain local to their capsule**.

```crush
fn main() {
    let x = 42;  // ✓ Shareable: Int
    
    @python {
        # x is available as Python int
        result = x * 2  # ✓ Shareable: becomes Crush Int
        
        class MyClass:  # ✗ Not shareable: Python-specific
            pass
        
        obj = MyClass()  # ✗ Not shareable
    }
    
    io.print(result);  // ✓ Works: result is Int
    // io.print(obj);  // ✗ Error: obj not CASM-compatible
}
```

### How It Works

1. Crush variables are **marshaled** to language blocks as native types
2. Language blocks can read and modify shareable values
3. Changes are **marshaled back** to Crush after block execution
4. Non-shareable objects are discarded when the capsule exits

## Library Availability

Because polyglot blocks run in WASM, **not all libraries are available**:

### ✅ Allowed (Pure Computation)
- Math, string manipulation, algorithms
- JSON, YAML, TOML parsing
- Regex, compression, crypto (pure implementations)
- Data structures, collections

### ✅ Allowed (Via Capabilities)
- File I/O → requires `fs.*` capability
- Network → requires `net.*` capability
- Stdout/stdin → requires `io.*` capability

### ❌ Blocked (By Design)
- Raw syscalls, FFI to host
- Process spawning (`subprocess`, `os.system`)
- Arbitrary file access (`os.open`, `std::fs`)
- Dynamic library loading

> **Key insight**: Libraries that perform I/O work **only if** Crush grants the corresponding capability.

## Python Integration

### Basic Python

```crush
@python {
    import math  # Pure computation - allowed
    result = math.sqrt(16)
    print(f"Square root: {result}")
}
```

### JSON Processing

```crush
@python {
    import json  # Pure library - allowed
    
    data = '{"name": "Alice", "age": 30}'
    parsed = json.loads(data)
    print(parsed["name"])
}
```

> **Note**: Libraries like `pandas`, `numpy`, and `sklearn` require WASM-compatible builds. Pure computation libraries (`math`, `json`, `re`) work out of the box.

## JavaScript Integration

### JSON Processing

```crush
@javascript {
    const data = {
        name: "Alice",
        age: 30,
        scores: [90, 85, 95]
    };
    
    const json = JSON.stringify(data, null, 2);
    console.log(json);
}
```

### Async Operations

```crush
@javascript {
    async function fetchData() {
        const response = await fetch('https://api.example.com/data');
        const data = await response.json();
        return data;
    }
    
    const result = await fetchData();
}
```

## Bash Integration

Bash blocks execute in a **restricted shell environment** with only capability-backed commands:

### Using Capabilities

```crush
@bash {
    # These map to Crush capabilities
    crush_print "Hello from Bash"
    
    # File operations require fs.* capabilities
    contents=$(crush_read "./data/file.txt")
    crush_print "$contents"
}
```

> **Note**: Direct system commands (`apt-get`, `systemctl`, etc.) are not available. Bash blocks use capability-backed builtins.

## Rust Integration

### Performance-Critical Code

```crush
@rust {
    fn fibonacci(n: u64) -> u64 {
        match n {
            0 => 0,
            1 => 1,
            _ => fibonacci(n - 1) + fibonacci(n - 2)
        }
    }
    
    let result = fibonacci(20);
}

io.print("Fibonacci: " + result);
```

### Capability Calls from Rust

Rust capsules **cannot access host `std` directly**. They must use capability calls:

```crush
@rust {
    // ✗ Invalid: Direct host access bypasses capabilities
    // use std::fs::File;
    // let file = File::create("output.txt")?;
    
    // ✓ Correct: Use capability calls
    extern "C" {
        fn fs_write(path: *const u8, data: *const u8, len: usize);
    }
    
    let data = b"Hello from Rust!";
    unsafe {
        fs_write(
            b"output.txt\0".as_ptr(),
            data.as_ptr(),
            data.len()
        );
    }
}
```

> **Security Note**: Rust capsules are sandboxed like all other language capsules. They cannot access the host filesystem, network, or system calls without explicit capability grants.

## C Integration

### Low-Level Operations

```crush
@c {
    #include <stdio.h>
    #include <stdlib.h>
    
    int* allocate_array(int size) {
        return (int*)malloc(size * sizeof(int));
    }
    
    int sum = 0;
    for (int i = 0; i < 10; i++) {
        sum += i;
    }
}

io.print("Sum: " + sum);
```

## Go Integration

### Concurrency

```crush
@go {
    package main
    
    import (
        "fmt"
        "sync"
    )
    
    func worker(id int, wg *sync.WaitGroup) {
        defer wg.Done()
        fmt.Printf("Worker %d done\n", id)
    }
    
    var wg sync.WaitGroup
    for i := 0; i < 5; i++ {
        wg.Add(1)
        go worker(i, &wg)
    }
    wg.Wait()
}
```

## Complete Example: Multi-Language Pipeline

```crush
fn main() {
    // Fetch data with JavaScript
    @javascript {
        const fetch = require('node-fetch');
        const response = await fetch('https://api.github.com/repos/rust-lang/rust');
        const data = await response.json();
        repoData = data;
    }
    
    // Process with Python
    @python {
        import json
        
        # Extract relevant fields
        processed = {
            'name': repoData['name'],
            'stars': repoData['stargazers_count'],
            'forks': repoData['forks_count']
        }
        
        # Calculate popularity score
        score = processed['stars'] + processed['forks'] * 2
        processed['score'] = score
    }
    
    // Format with Rust
    @rust {
        let formatted = format!(
            "Repository: {}\nStars: {}\nForks: {}\nScore: {}",
            processed["name"],
            processed["stars"],
            processed["forks"],
            processed["score"]
        );
    }
    
    // Output
    io.print(formatted);
    
    // Save with Bash
    @bash {
        echo "$formatted" > repo_stats.txt
        cat repo_stats.txt
    }
}
```

## Best Practices

### 1. Use the Right Language for the Job

```crush
// Good: Python for data processing
@python {
    import pandas as pd
    df = pd.read_csv("data.csv")
    result = df.groupby("category").sum()
}

// Good: Bash for system tasks
@bash {
    systemctl restart nginx
}

// Good: Rust for performance
@rust {
    fn compute_intensive_task() -> i64 {
        // ...
    }
}
```

### 2. Minimize Language Switches

```crush
// Less efficient: Multiple switches
@python { x = 1 }
@python { y = 2 }
@python { z = x + y }

// Better: Single block
@python {
    x = 1
    y = 2
    z = x + y
}
```

### 3. Handle Language-Specific Errors

```crush
@python {
    try:
        data = process_file("input.csv")
    except Exception as e:
        error_msg = str(e)
}

if error_msg != null {
    io.eprint("Python error: " + error_msg);
}
```

## Variable Type Mapping

| Crush Type | Python | JavaScript | Bash | Rust | C | Go |
|------------|--------|------------|------|------|---|-----|
| Int | `int` | `number` | `$VAR` | `i64` | `int64_t` | `int64` |
| Float | `float` | `number` | `$VAR` | `f64` | `double` | `float64` |
| String | `str` | `string` | `$VAR` | `String` | `char*` | `string` |
| Bool | `bool` | `boolean` | `true/false` | `bool` | `bool` | `bool` |
| Array | `list` | `Array` | `array` | `Vec` | `array` | `[]` |
| Map | `dict` | `Object` | `assoc array` | `HashMap` | `struct` | `map` |

## Limitations

### 1. No Direct Function Calls Across Languages

```crush
// Not supported:
@python {
    def helper():
        return 42
}

// Can't call Python function from Crush
// let x = helper();  // Error
```

**Workaround:** Use variables:

```crush
@python {
    def helper():
        return 42
    result = helper()
}

let x = result;  // OK
```

### 2. Language Block Isolation

Each language block runs in its own context:

```crush
@python {
    x = 42
}

@python {
    # x is not available here
    # Must re-import from Crush
    print(x)  # Error unless x was exported from Crush
}
```

## Next Steps

- **[Standard Library](stdlib.md)**: Additional capabilities
- **[CAST Specification](../cast/README.md)**: The walker output format
- **[CASM Overview](../casm/README.md)**: The bytecode walkers compile to
