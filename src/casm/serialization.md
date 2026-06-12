# Serialization Formats

CASM programs can be serialized in two formats: **JSON** (human-readable) and **Binary** (compact). This chapter explains both formats and when to use each.

## JSON Format (.casm)

The JSON format is the primary, human-readable serialization format for CASM programs.

### Characteristics

- **Human-readable**: Easy to read, write, and debug
- **Text-based**: Can be version-controlled with git
- **Portable**: Works across all platforms
- **Larger size**: More verbose than binary format
- **Slower parsing**: JSON parsing has overhead

### File Extension

`.casm`

### Example

```json
{
  "version": "0.1",
  "functions": {
    "main": {
      "params": [],
      "locals": [],
      "body": [
        {"op": "push_int", "value": 42},
        {"op": "cap_call", "name": "io.print", "argc": 1},
        {"op": "ret"}
      ]
    }
  },
  "manifest": {
    "permissions": ["io.print"]
  }
}
```

### When to Use

✅ **Use JSON when:**
- Developing and debugging programs
- Hand-writing CASM code
- Generating CASM from tools
- Version controlling bytecode
- Sharing examples and documentation
- Learning CASM

❌ **Avoid JSON when:**
- Deploying to production (use binary)
- Size matters (embedded systems, network transfer)
- Performance is critical

## Binary Format (.casmb)

The binary format uses MessagePack for compact, efficient serialization.

### Characteristics

- **Compact**: 30-50% smaller than JSON
- **Fast**: Faster to parse and serialize
- **Binary**: Not human-readable
- **Portable**: MessagePack is cross-platform

### File Extension

`.casmb`

### Structure

The binary format uses [MessagePack](https://msgpack.org/) to serialize the same structure as JSON:

```text
┌─────────────────────────────────┐
│ MessagePack Binary Data         │
│                                 │
│ Same structure as JSON:         │
│ - version (string)              │
│ - functions (map)               │
│ - lang (optional string)        │
│ - manifest (optional map)       │
└─────────────────────────────────┘
```

### When to Use

✅ **Use Binary when:**
- Deploying to production
- Distributing compiled programs
- Minimizing file size
- Optimizing load time
- Embedding in other formats

❌ **Avoid Binary when:**
- Debugging or development
- Need to inspect bytecode
- Version controlling (use JSON)

## Format Detection

The Crush VM automatically detects the format based on file extension:

| Extension | Format | Auto-detected |
|-----------|--------|---------------|
| `.casm` | JSON | ✓ |
| `.casmb` | Binary (MessagePack) | ✓ |
| Other | JSON (default) | ✓ |

### Example

```bash
# JSON format (auto-detected)
exo run program.casm

# Binary format (auto-detected)
exo run program.casmb

# Explicit format specification
exo run --format=json program.txt
exo run --format=binary program.bin
```

## Converting Between Formats

### JSON to Binary

```bash
# Using crush-cli
exo compile program.casm --output program.casmb

# Or programmatically in Rust
use casm::{Program, Format};

let program = Program::load("program.casm")?;
program.save("program.casmb")?;  // Auto-detects binary format
```

### Binary to JSON

```bash
# Using crush-cli
crush decompile program.casmb --output program.casm

# Or programmatically
let program = Program::load("program.casmb")?;
program.save("program.casm")?;  // Auto-detects JSON format
```

## Size Comparison

Example program sizes:

| Program | JSON (.casm) | Binary (.casmb) | Savings |
|---------|--------------|-----------------|---------|
| Hello World | 450 bytes | 180 bytes | 60% |
| Fibonacci | 1.2 KB | 650 bytes | 46% |
| Complex App | 50 KB | 28 KB | 44% |

Binary format typically saves **40-60%** of file size.

## Performance Comparison

Parsing performance (approximate):

| Format | Parse Time | Serialize Time |
|--------|------------|----------------|
| JSON | 100% (baseline) | 100% (baseline) |
| Binary | 40% (2.5x faster) | 30% (3.3x faster) |

Binary format is **2-3x faster** to parse and serialize.

## Rust API

### Loading Programs

```rust
use casm::{Program, Format};
use std::path::Path;

// Auto-detect format from extension
let program = Program::load(Path::new("program.casm"))?;

// Explicit format
let data = std::fs::read("program.casm")?;
let program = Program::deserialize(&data, Format::Json)?;
```

### Saving Programs

```rust
// Auto-detect format from extension
program.save(Path::new("output.casmb"))?;

// Explicit format
let data = program.serialize(Format::Binary)?;
std::fs::write("output.casmb", data)?;
```

### Format Enum

```rust
pub enum Format {
    Json,   // Human-readable (.casm)
    Binary, // Compact binary (.casmb)
}

impl Format {
    pub fn from_path(path: &Path) -> Self {
        match path.extension().and_then(|e| e.to_str()) {
            Some("casmb") => Format::Binary,
            _ => Format::Json,
        }
    }
}
```

## Best Practices

### Development Workflow

1. **Write in JSON** during development
2. **Version control JSON** files
3. **Compile to binary** for production
4. **Distribute binary** to end users

### Example Workflow

```bash
# 1. Develop in JSON
vim program.casm

# 2. Test with JSON
exo run program.casm

# 3. Commit JSON to git
git add program.casm
git commit -m "Add new feature"

# 4. Build binary for release
exo compile program.casm --output program.casmb

# 5. Distribute binary
cp program.casmb /usr/local/bin/myapp.casmb
```

### CI/CD Pipeline

```yaml
# .github/workflows/build.yml
- name: Compile CASM
  run: |
    exo compile src/*.casm --output-dir dist/
    
- name: Upload artifacts
  uses: actions/upload-artifact@v2
  with:
    name: bytecode
    path: dist/*.casmb
```

## Metadata Preservation

Both formats preserve all metadata:

```json
// JSON format
{
  "op": "push_int",
  "value": 42,
  "lang": "python",
  "meta": {
    "file": "script.py",
    "line": 10
  }
}
```

```text
// Binary format (MessagePack)
// Same data, just binary-encoded
```

Metadata is **fully preserved** in both formats, so debugging information is available even in production binaries.

## Compression

For even smaller sizes, compress the binary format:

```bash
# gzip compression
gzip program.casmb
# Result: program.casmb.gz (typically 60-70% of .casmb size)

# brotli compression (better)
brotli program.casmb
# Result: program.casmb.br (typically 50-60% of .casmb size)
```

Combined savings:

| Format | Size | vs JSON |
|--------|------|---------|
| JSON | 100% | - |
| Binary | 45% | 55% smaller |
| Binary + gzip | 30% | 70% smaller |
| Binary + brotli | 25% | 75% smaller |

## Validation

Both formats are validated on load:

```rust
match Program::load("program.casm") {
    Ok(program) => println!("Valid CASM program"),
    Err(e) => eprintln!("Invalid CASM: {}", e),
}
```

Common validation errors:
- Missing required fields (`version`, `functions`)
- Invalid instruction opcodes
- Malformed JSON/MessagePack
- Type mismatches

## Future Formats

Potential future serialization formats:

- **WebAssembly**: For browser execution
- **Protobuf**: For RPC and network protocols
- **CBOR**: Alternative binary format
- **Custom binary**: Optimized Crush-specific format

## Summary

| Aspect | JSON | Binary |
|--------|------|--------|
| **Extension** | `.casm` | `.casmb` |
| **Encoding** | JSON | MessagePack |
| **Readable** | ✓ | ✗ |
| **Size** | Larger | Smaller (40-60% savings) |
| **Speed** | Slower | Faster (2-3x) |
| **Use Case** | Development, debugging | Production, distribution |
| **Version Control** | ✓ Recommended | ✗ Not recommended |
| **Metadata** | ✓ Preserved | ✓ Preserved |

**Recommendation**: Use JSON for development, binary for production.
