# Language Comparisons

How Crush compares to other popular languages.

## Crush vs Python

### Similarities
- Simple, readable syntax
- Dynamic typing
- High-level abstractions

### Differences

| Feature | Crush | Python |
|---------|-------|--------|
| Polyglot | ✓ Embed multiple languages | ✗ Single language |
| Security | ✓ Capability-based | ✗ Full system access |
| Compilation | ✓ Compiles to bytecode | ✗ Interpreted |
| Type Hints | ✓ Optional | ✓ Optional (PEP 484) |

### Example Comparison

**Python:**
```python
def greet(name):
    print(f"Hello, {name}!")

greet("Alice")
```

**Crush:**
```crush
fn greet(name: String) {
    io.print("Hello, " + name + "!");
}

greet("Alice");
```

## Crush vs JavaScript

### Similarities
- Dynamic typing
- First-class functions
- Async support (future)

### Differences

| Feature | Crush | JavaScript |
|---------|-------|------------|
| Polyglot | ✓ | ✗ |
| Security | ✓ Capabilities | ✗ Node.js has full access |
| Syntax | Rust-like | C-like |

## Crush vs Rust

### Similarities
- Similar syntax
- Type hints
- Performance focus

### Differences

| Feature | Crush | Rust |
|---------|-------|------|
| Type System | Dynamic | Static, strict |
| Memory Safety | VM-managed | Borrow checker |
| Polyglot | ✓ | ✗ |
| Compilation | To bytecode + AOT native | To native code |
| AOT Performance | Near-native via `crush-aotc` | Native |

## Crush vs Bash

### Similarities
- Scripting focus
- System administration
- Command execution

### Differences

| Feature | Crush | Bash |
|---------|-------|------|
| Type System | ✓ Types | ✗ Everything is string |
| Polyglot | ✓ | ✗ |
| Syntax | Modern | Unix shell |
| Error Handling | Better | Limited |

## Performance

Crush has five execution tiers spanning interpreter to native code:

| Tier | Speed vs CVM1 (simple) | Speed vs CVM1 (compute) |
|------|------------------------|------------------------|
| CVM1 (interpreter) | 1.0× | 1.0× |
| FastVM | 0.09× | 0.5× |
| AOT Rust (rustc) | 42× | 130× |
| AOT C (gcc -O3) | 54× | 317× |
| AOT C (clang -O3) | 55× | 378× |

AOT-compiled Crush achieves **near-C performance** — LLVM and GCC constant-fold
the stack machine operations into direct native code. For compute-bound Crush programs,
`crush-aotc` produces `.so` files that run within 2-5× of hand-written C.

See the [crush-ast benchmarks](https://github.com/nixpt/crush-ast/tree/main/docs/benchmarks)
for detailed cross-language comparisons.

## When to Use Crush

✅ **Use Crush when:**
- You need to combine multiple languages
- Security and isolation are important
- You want capability-based permissions
- You're building polyglot applications
- You need native performance with scripting ergonomics (`crush-aotc`)

❌ **Consider alternatives when:**
- You have a large existing codebase in another language
- You need mature ecosystem (Python/JavaScript)
- You're building web frontends (use JavaScript/TypeScript)

## Migration Guide

### From Python

1. Add type hints to function signatures
2. Replace `print()` with `io.print()`
3. Add capability permissions to manifest
4. Keep Python code in `@python {}` blocks during transition

### From JavaScript

1. Change `function` to `fn`
2. Add semicolons
3. Replace `console.log()` with `io.print()`
4. Keep JavaScript in `@javascript {}` blocks

### From Bash

1. Wrap shell commands in `@bash {}` blocks
2. Use Crush for logic and control flow
3. Add type safety with Crush variables
