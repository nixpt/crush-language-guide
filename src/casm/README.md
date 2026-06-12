# CASM Overview

**CASM** (Crush Assembly) is the low-level, target-independent instruction set for the Crush Virtual Machine. It is the final stage of the compilation pipeline before execution.

## What is CASM?

CASM is a **stack-based assembly language** designed for high-performance and secure execution. It serves as the universal "lingua franca" of the Crush ecosystem:

- **Unified Target**: Whether source code is written in Python, Rust, or Crush, it eventually becomes CASM.
- **Explicit Effects**: Every system interaction is visible as a `cap_call` (capability call).
- **Rich Metadata**: CASM preserves source line and file information for precise error reporting.
- **Portability**: Programs are serialized as JSON (for development) or MessagePack (for distribution).

## The Execution Model

### Stack-Based Logic
Like WebAssembly or JVM bytecode, CASM operates on a stack:

```json
{"op": "push_int", "value": 10}
{"op": "push_int", "value": 20}
{"op": "add"} // Pops 20, Pops 10, Pushes 30
```

### Capability-First Security
CASM does not have instructions for raw syscalls. All host interactions must go through the capability system:

```json
{"op": "push_str", "value": "logs.txt"}
{"op": "cap_call", "name": "fs.read", "argc": 1}
```

The VM validates this call against the capsule's manifest at runtime. If the `fs.read` capability was not granted, the execution is immediately terminated.

## Key Features

### 1. Unified Value System
CASM uses a unified `RuntimeValue` system that supports:
- **Primitives**: `Int`, `Float`, `Bool`, `Null`.
- **References**: `String`, `Array`, `Map` (managed in the VM Arena).
- **Functions**: First-class function handles.

### 2. Arena-Based Memory
All complex objects in CASM are created within the VM's **Arena**. This ensures that memory management is deterministic and that capsules remain strictly isolated from each other.

### 3. Source Mapping
Each instruction in a `.casm` file can include a `meta` block:
```json
{
  "op": "add",
  "meta": {
    "file": "main.py",
    "line": 10
  }
}
```
If an error occurs, the VM uses this metadata to provide a human-readable trace back to the original source code.

## File Structure

A `.casm` capsule is a JSON object containing:
- **`manifest`**: Metadata and capability requirements.
- **`functions`**: A collection of named blocks of code.
- **`entry`**: The name of the function to execute first.

## Next Steps

- **[Instruction Reference](instructions.md)**: Explore the complete set of CASM opcodes.
- **[Binary Format](serialization.md)**: Learn how CASM is optimized for distribution.
- **[Crush Language Guide](../crush/README.md)**: See how the high-level language maps to CASM.
