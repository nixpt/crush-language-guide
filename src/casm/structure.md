# Program Structure

A CASM program is a JSON document with a well-defined structure. This chapter explains each component in detail.

## Top-Level Structure

```json
{
  "version": "0.1",
  "functions": { /* ... */ },
  "lang": "python",
  "manifest": { /* ... */ }
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | String | ✓ | CASM format version (currently `"0.1"`) |
| `functions` | Object | ✓ | Map of function name to function definition |
| `lang` | String | ✗ | Source language (e.g., `"python"`, `"crush"`, `"rust"`) |
| `manifest` | Object | ✗ | Capability permissions and metadata |

## Function Structure

Each function in the `functions` object has this structure:

```json
{
  "params": ["arg1", "arg2"],
  "locals": ["temp", "counter"],
  "body": [ /* instructions */ ]
}
```

### Function Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `params` | Array\<String\> | ✗ | Parameter names (default: `[]`) |
| `locals` | Array\<String\> | ✗ | Local variable names (default: `[]`) |
| `body` | Array\<Instruction\> | ✓ | Instruction sequence |

### Parameters vs Locals

- **Parameters**: Function arguments, bound when the function is called
- **Locals**: Additional local variables declared in the function

Example:

```json
{
  "functions": {
    "add": {
      "params": ["a", "b"],
      "locals": ["result"],
      "body": [
        {"op": "load", "name": "a"},
        {"op": "load", "name": "b"},
        {"op": "add"},
        {"op": "store", "name": "result"},
        {"op": "load", "name": "result"},
        {"op": "ret"}
      ]
    }
  }
}
```

## Instruction Structure

Each instruction is a JSON object with these fields:

```json
{
  "op": "push_int",
  "value": 42,
  "lang": "python",
  "meta": {
    "file": "script.py",
    "line": 10,
    "column": 5
  }
}
```

### Instruction Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `op` | String | ✓ | Operation name (e.g., `"push_int"`, `"add"`) |
| `lang` | String | ✗ | Source language for this instruction |
| `meta` | Object | ✗ | Metadata (file, line, column, etc.) |
| *others* | Various | Varies | Operation-specific arguments |

### Operation-Specific Arguments

Different operations require different arguments. These are flattened into the instruction object:

```json
// push_int requires "value"
{"op": "push_int", "value": 42}

// store requires "name"
{"op": "store", "name": "x"}

// cap_call requires "name" and "argc"
{"op": "cap_call", "name": "io.print", "argc": 1}

// jmp requires "target"
{"op": "jmp", "target": 10}
```

See the [Instruction Set Reference](instructions.md) for complete details on each operation's arguments.

## Metadata

The `meta` field can contain arbitrary JSON data, but these fields have special meaning:

| Field | Type | Description |
|-------|------|-------------|
| `file` | String | Source file path |
| `line` | Integer | Line number in source file |
| `column` | Integer | Column number in source file |
| `lang` | String | Source language |

Example with full metadata:

```json
{
  "op": "push_str",
  "value": "Hello",
  "lang": "crush",
  "meta": {
    "file": "examples/hello.crush",
    "line": 4,
    "column": 15,
    "lang": "crush"
  }
}
```

This metadata is used by the VM to provide accurate error messages:

```text
Error at examples/hello.crush:4:15
  |
4 |     let msg = "Hello";
  |               ^^^^^^^
  | Type error: expected Int, got String
```

## Manifest

The manifest declares capability permissions:

```json
{
  "manifest": {
    "permissions": [
      "io.print",
      "io.read",
      "fs.read",
      "fs.write",
      "net.http"
    ]
  }
}
```

### Manifest Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `permissions` | Array\<String\> | ✓ | List of required capabilities |

### Permission Strings

Permissions follow the format `namespace.method`:

- `io.print` - Print to stdout
- `io.read` - Read from stdin
- `fs.read` - Read files
- `fs.write` - Write files
- `fs.delete` - Delete files
- `net.http` - Make HTTP requests
- `sys.exec` - Execute system commands
- `sys.env` - Access environment variables

The VM will reject any `cap_call` that isn't listed in the manifest.

## Complete Example

Here's a complete CASM program with all components:

```json
{
  "version": "0.1",
  "lang": "crush",
  "functions": {
    "main": {
      "params": [],
      "locals": ["name", "greeting"],
      "body": [
        {
          "op": "push_str",
          "value": "What's your name?",
          "lang": "crush",
          "meta": {"file": "greet.crush", "line": 2}
        },
        {
          "op": "cap_call",
          "name": "io.print",
          "argc": 1,
          "lang": "crush",
          "meta": {"file": "greet.crush", "line": 2}
        },
        {
          "op": "cap_call",
          "name": "io.read",
          "argc": 0,
          "lang": "crush",
          "meta": {"file": "greet.crush", "line": 3}
        },
        {
          "op": "store",
          "name": "name",
          "lang": "crush",
          "meta": {"file": "greet.crush", "line": 3}
        },
        {
          "op": "push_str",
          "value": "Hello, ",
          "lang": "crush",
          "meta": {"file": "greet.crush", "line": 5}
        },
        {
          "op": "load",
          "name": "name",
          "lang": "crush",
          "meta": {"file": "greet.crush", "line": 5}
        },
        {
          "op": "add",
          "lang": "crush",
          "meta": {"file": "greet.crush", "line": 5}
        },
        {
          "op": "push_str",
          "value": "!",
          "lang": "crush",
          "meta": {"file": "greet.crush", "line": 5}
        },
        {
          "op": "add",
          "lang": "crush",
          "meta": {"file": "greet.crush", "line": 5}
        },
        {
          "op": "store",
          "name": "greeting",
          "lang": "crush",
          "meta": {"file": "greet.crush", "line": 5}
        },
        {
          "op": "load",
          "name": "greeting",
          "lang": "crush",
          "meta": {"file": "greet.crush", "line": 6}
        },
        {
          "op": "cap_call",
          "name": "io.print",
          "argc": 1,
          "lang": "crush",
          "meta": {"file": "greet.crush", "line": 6}
        },
        {
          "op": "ret",
          "lang": "crush",
          "meta": {"file": "greet.crush", "line": 7}
        }
      ]
    }
  },
  "manifest": {
    "permissions": [
      "io.print",
      "io.read"
    ]
  }
}
```

This corresponds to the Crush source:

```crush
fn main() {
    io.print("What's your name?");
    let name = io.read();
    
    let greeting = "Hello, " + name + "!";
    io.print(greeting);
}
```

## Entry Point

The VM looks for a function named `"main"` as the entry point. If no `main` function exists, the program cannot be executed.

## Best Practices

### 1. Always Include Metadata

Include `lang`, `file`, `line`, and `column` metadata for better error messages:

```json
{
  "op": "add",
  "lang": "python",
  "meta": {
    "file": "script.py",
    "line": 42,
    "column": 10
  }
}
```

### 2. Declare All Locals

List all local variables in the `locals` array for clarity:

```json
{
  "params": ["x", "y"],
  "locals": ["temp", "result", "i"],
  "body": [ /* ... */ ]
}
```

### 3. Minimal Permissions

Only request capabilities you actually use:

```json
{
  "manifest": {
    "permissions": ["io.print"]  // Only what's needed
  }
}
```

### 4. Use Descriptive Function Names

```json
{
  "functions": {
    "calculate_fibonacci": { /* ... */ },
    "format_output": { /* ... */ }
  }
}
```

## Next Steps

- **[Instruction Set Reference](instructions.md)**: Learn about all available operations
- **[Examples](examples.md)**: See complete CASM programs
- **[Serialization](serialization.md)**: Learn about JSON and binary formats
