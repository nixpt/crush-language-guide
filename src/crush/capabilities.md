# Capability System

The capability system is Crush's security model. All interactions with the outside world (I/O, filesystem, network) require explicit capability permissions.

## What are Capabilities?

Capabilities are **permissions** that grant access to external resources:

- `io.print` - Print to stdout
- `io.read` - Read from stdin
- `fs.read` - Read files
- `fs.write` - Write files
- `net.http` - Make HTTP requests
- `sys.exec` - Execute commands

## Capability Calls

Use the `@` prefix to call capabilities:

```crush
@io.print("Hello, World!");
```

### With Arguments

```crush
@fs.write("file.txt", "content");
let content = @fs.read("file.txt");
```

### Storing Results

```crush
let user_input = @io.read();
let file_data = @fs.read("config.json");
```

## Declaring Permissions

Capabilities must be declared in the program manifest:

```json
{
  "manifest": {
    "permissions": {
      "io.print": true,
      "io.read": true,
      "fs.read": ["./data", "./config"],
      "fs.write": ["./output"],
      "net.connect": ["https://api.example.com"]
    }
  }
}
```

**Permission Scoping:**
- `true` - Full access to that capability
- `[paths]` - Restricted to specific paths or URLs
- Omitted - Denied (default deny-by-default)

**Without the permission, the capability call will fail at runtime.**

## Standard Capabilities

### I/O Capabilities

| Capability | Description | Arguments | Returns | Scope |
|------------|-------------|-----------|---------|-------|
| `io.print` | Print to stdout | `message: String` | `null` | N/A |
| `io.read` | Read from stdin | none | `String` | N/A |
| `io.eprint` | Print to stderr | `message: String` | `null` | N/A |

**Example:**

```crush
@io.print("Enter your name:");
let name = @io.read();
@io.print("Hello, " + name);
```

### Filesystem Capabilities

| Capability | Description | Arguments | Returns | Scope |
|------------|-------------|-----------|---------|-------|
| `fs.read` | Read file | `path: String` | `String` | Path list |
| `fs.write` | Write file | `path: String, content: String` | `null` | Path list |
| `fs.exists` | Check if exists | `path: String` | `Bool` | Path list |
| `fs.delete` | Delete file | `path: String` | `null` | Path list |
| `fs.list` | List directory | `path: String` | `Array<String>` | Path list |

**Example:**

```crush
if @fs.exists("config.json") {
    let config = @fs.read("config.json");
    @io.print(config);
} else {
    @fs.write("config.json", "{}");
}
```

### System Capabilities

| Capability | Description | Arguments | Returns |
|------------|-------------|-----------|---------|
| `sys.exec` | Execute command | `cmd: String` | `String` |
| `sys.env` | Get env variable | `name: String` | `String` |
| `sys.args` | Get CLI args | none | `Array<String>` |
| `sys.exit` | Exit program | `code: Int` | never |

**Example:**

```crush
let args = @sys.args();
if args.length < 2 {
    @io.eprint("Usage: program <file>");
    @sys.exit(1);
}
```

### Network Capabilities

| Capability | Description | Arguments | Returns |
|------------|-------------|-----------|---------|
| `net.http` | HTTP request | `url: String` | `String` |
| `net.get` | HTTP GET | `url: String` | `String` |
| `net.post` | HTTP POST | `url: String, body: String` | `String` |

**Example:**

```crush
let response = @net.get("https://api.example.com/data");
@io.print(response);
```

## Security Model

### Principle of Least Privilege

Only request capabilities you actually use:

```crush
// Good: Minimal permissions
{
  "permissions": ["io.print"]
}

// Bad: Excessive permissions
{
  "permissions": ["io.print", "fs.read", "fs.write", "net.http", "sys.exec"]
}
```

### No Ambient Authority

Unlike traditional OS permissions, capabilities are:
- **Explicit**: Must be declared in manifest
- **Granular**: `fs.read` vs `fs.write` vs `fs.delete`
- **Auditable**: Easy to see what a program can do

### Capability Denial

If a program calls a capability it doesn't have:

```crush
// Manifest: {"permissions": ["io.print"]}

fn main() {
    @io.print("Hello");  // ✓ Allowed
    @fs.read("file.txt");  // ✗ Runtime error: Permission denied
}
```

## Best Practices

### 1. Declare Only What You Need

```crush
// Good
{
  "permissions": ["io.print", "fs.read"]
}

// Avoid
{
  "permissions": ["io.*", "fs.*", "net.*"]
}
```

### 2. Check Before Using

```crush
if @fs.exists("config.json") {
    let config = @fs.read("config.json");
} else {
    @io.print("Config not found");
}
```

### 3. Handle Errors

```crush
// Future: try-catch
try {
    let data = @fs.read("file.txt");
} catch (error) {
    @io.eprint("Failed to read file: " + error);
}
```

## Capability Composition

Capabilities can be composed:

```crush
fn read_and_print(filename: String) {
    let content = @fs.read(filename);
    @io.print(content);
}

// Requires both fs.read and io.print
```

## Next Steps

- **[Polyglot Programming](polyglot.md)**: Embed multiple languages
- **[Standard Library](stdlib.md)**: Additional capabilities
