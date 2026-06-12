# Crush Overview

**Crush** is a capability-based, polyglot virtual operating system (vOS) and language. It is designed to provide a secure, high-performance environment where multiple languages can coexist and interact seamlessly.

## What is Crush?

Crush is both a programming language and a runtime environment. It features:

- **Everything is a Capsule**: High-level isolation for all code units.
- **Capability-Based Security**: Fine-grained, explicit permissions for all system interactions.
- **Polyglot Execution**: First-class support for Python, Rust, Bash, C, and Go.
- **Exo-Core Architecture**: A minimal virtualization layer that manages hardware interactions via a Hardware Abstraction Layer (HAL).

## The Crush Language

The Crush language provides a clean, expression-oriented syntax that acts as the glue for the vOS.

```crush
fn main() {
    @io.print("Hello, Crush!");
}
```

### The `@` Operator
In Crush, the `@` prefix is used to denote a **Capability Call**. This visual marker identifies code that crosses the VM boundary to interact with the host or other capsules.

```crush
@fs.read("config.json");  // Crossing the boundary to the filesystem
let x = 1 + 2;             // Internal VM computation (no @)
```

## Core Philosophy

### 1. Security by Capability
Unlike traditional operating systems where permissions are tied to the user, Crush ties permissions to the **Capsule**. A capsule can only perform actions (like reading a file or opening a socket) if it has been explicitly granted that capability in its `Capsule.toml`.

### 2. Radical Polyglotism
Crush doesn't force you to choose one language. You can use the best tool for the job:
- **Rust** for performance-critical logic.
- **Python** for data processing and AI.
- **Bash** for system orchestration.
- **Crush** for high-level logic and capability management.

### 3. Identity and Isolation
Each capsule runs in its own isolated environment. The `exo-core` ensures that capsules cannot interfere with each other's memory or resources unless explicitly allowed via shared handles.

## Execution Model

1.  **Source**: Write code in any supported language.
2.  **Walker**: A language-specific walker generates a [Crush AST (CAST)](../cast/README.md).
3.  **Compiler**: The Crush compiler transforms CAST into [Crush Assembly (CASM)](../casm/README.md).
4.  **VM**: The Crush VM executes CASM, enforcing security and resource limits.

## Next Steps

- **[Syntax & Fundamentals](syntax.md)**: Deep dive into the Crush language.
- **[The Capability System](capabilities.md)**: Understand how security works.
- **[Polyglot Programming](polyglot.md)**: Master cross-language execution.
