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
    @io.print("Hello, " + name + "!");
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
| Compilation | To bytecode | To native code |

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

## When to Use Crush

✅ **Use Crush when:**
- You need to combine multiple languages
- Security and isolation are important
- You want capability-based permissions
- You're building polyglot applications

❌ **Consider alternatives when:**
- You need maximum performance (use Rust/C)
- You have a large existing codebase in another language
- You need mature ecosystem (Python/JavaScript)
- You're building web frontends (use JavaScript/TypeScript)

## Migration Guide

### From Python

1. Add type hints to function signatures
2. Replace `print()` with `@io.print()`
3. Add capability permissions to manifest
4. Keep Python code in `@python {}` blocks during transition

### From JavaScript

1. Change `function` to `fn`
2. Add semicolons
3. Replace `console.log()` with `@io.print()`
4. Keep JavaScript in `@javascript {}` blocks

### From Bash

1. Wrap shell commands in `@bash {}` blocks
2. Use Crush for logic and control flow
3. Add type safety with Crush variables
