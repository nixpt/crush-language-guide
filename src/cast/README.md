# Crush AST (CAST) Specification v0.3

## Overview
CAST is the intermediate representation used by Crush to enable polyglot programming. Language walkers translate source code into CAST, and the Crush compiler translates CAST into CASM bytecode.

## Design Principles
1. **Language-Agnostic**: CAST nodes should represent common programming constructs, not language-specific syntax
2. **Explicit Control Flow**: Control flow (if/while/for) is represented explicitly, not as jumps
3. **Metadata Preservation**: Each node includes `meta` for source language, line numbers, etc.
4. **Type Hints**: Optional type annotations for static analysis

## Document Structure

### Top-Level CAST Document
```json
{
  "version": "0.3",
  "entry": "main",
  "lang": "python",
  "imports": {
    "native": ["os", "sys"],
    "crush": []
  },
  "functions": {
    "main": {
      "params": [],
      "body": [ /* Statement[] */ ],
      "return_type": null,
      "meta": {}
    }
  },
  "structs": {}
}
```

## Statement Nodes

### VarDecl - Variable Declaration
```json
{
  "type": "VarDecl",
  "name": "x",
  "value": { /* Expr */ },
  "type_hint": "int",  // Optional
  "meta": { "lang": "python", "line": 5 }
}
```

### Export - Export Variable
```json
{
  "type": "Export",
  "name": "result",
  "value": { /* Expr */ },
  "meta": { "lang": "python" }
}
```

### ExprStmt - Expression Statement
```json
{
  "type": "ExprStmt",
  "expr": { /* Expr */ },
  "meta": { "lang": "python" }
}
```

### If - Conditional Statement
```json
{
  "type": "If",
  "condition": { /* Expr */ },
  "then_body": [ /* Statement[] */ ],
  "else_body": [ /* Statement[] */ ],  // Optional, can be null or []
  "meta": { "lang": "python", "line": 10 }
}
```

### While - While Loop
```json
{
  "type": "While",
  "condition": { /* Expr */ },
  "body": [ /* Statement[] */ ],
  "meta": { "lang": "python", "line": 15 }
}
```

### For - For Loop
```json
{
  "type": "For",
  "iterator": "item",
  "iterable": { /* Expr */ },
  "body": [ /* Statement[] */ ],
  "meta": { "lang": "python", "line": 20 }
}
```

### Return - Function Return
```json
{
  "type": "Return",
  "value": { /* Expr */ },  // Optional, null for void return
  "meta": { "lang": "python" }
}
```

### StructDef - Struct/Class Definition
```json
{
  "type": "StructDef",
  "name": "Point",
  "fields": [
    { "name": "x", "type_hint": "int" },
    { "name": "y", "type_hint": "int" }
  ],
  "methods": [
    {
      "name": "distance",
      "params": ["other"],
      "body": [ /* Statement[] */ ],
      "return_type": "float"
    }
  ],
  "meta": { "lang": "python" }
}
```

## Expression Nodes

### Literals

#### IntLiteral
```json
{
  "type": "IntLiteral",
  "value": 42,
  "meta": { "lang": "python" }
}
```

#### StringLiteral
```json
{
  "type": "StringLiteral",
  "value": "Hello, World!",
  "meta": { "lang": "python" }
}
```

#### BoolLiteral
```json
{
  "type": "BoolLiteral",
  "value": true,
  "meta": { "lang": "python" }
}
```

#### NullLiteral
```json
{
  "type": "NullLiteral",
  "meta": { "lang": "python" }
}
```

#### ArrayLiteral
```json
{
  "type": "ArrayLiteral",
  "elements": [ /* Expr[] */ ],
  "meta": { "lang": "python" }
}
```

#### MapLiteral
```json
{
  "type": "MapLiteral",
  "entries": [
    { "key": { /* Expr */ }, "value": { /* Expr */ } }
  ],
  "meta": { "lang": "python" }
}
```

### Var - Variable Reference
```json
{
  "type": "Var",
  "name": "x",
  "meta": { "lang": "python" }
}
```

### BinaryOp - Binary Operation
```json
{
  "type": "BinaryOp",
  "operator": "+",  // +, -, *, /, %, ==, !=, <, >, <=, >=, and, or
  "left": { /* Expr */ },
  "right": { /* Expr */ },
  "meta": { "lang": "python" }
}
```

### UnaryOp - Unary Operation
```json
{
  "type": "UnaryOp",
  "operator": "-",  // -, not, ~
  "operand": { /* Expr */ },
  "meta": { "lang": "python" }
}
```

### Call - Function Call
```json
{
  "type": "Call",
  "function": "add",
  "args": [ /* Expr[] */ ],
  "meta": { "lang": "python" }
}
```

### CapabilityCall - Capability Invocation
```json
{
  "type": "CapabilityCall",
  "name": "io.print",
  "args": [ /* Expr[] */ ],
  "meta": {
    "capability": true,
    "namespace": "io",
    "method": "print",
    "lang": "python"
  }
}
```

### FieldAccess - Struct Field Access
```json
{
  "type": "FieldAccess",
  "object": { /* Expr */ },
  "field": "x",
  "meta": { "lang": "python" }
}
```

### Index - Array/Map Indexing
```json
{
  "type": "Index",
  "object": { /* Expr */ },
  "index": { /* Expr */ },
  "meta": { "lang": "python" }
}
```

## Metadata

All nodes should include a `meta` field with:
- `lang`: Source language (e.g., "python", "rust", "c")
- `line`: Optional line number in source
- `column`: Optional column number in source
- Additional language-specific metadata as needed

## Type Hints

Optional `type_hint` fields can be:
- Primitives: `"int"`, `"float"`, `"str"`, `"bool"`
- Collections: `"array"`, `"map"`
- Custom: `"StructName"`
- Generic: `"Array<int>"`, `"Map<str, int>"`

## Compilation Strategy

### Control Flow → CASM

**If Statement**:
```
compile(condition)
jmp_if_not else_label
compile(then_body)
jmp end_label
else_label:
compile(else_body)
end_label:
```

**While Loop**:
```
loop_start:
compile(condition)
jmp_if_not loop_end
compile(body)
jmp loop_start
loop_end:
```

**For Loop** (requires iterator protocol):
```
compile(iterable)
store __iter
loop_start:
load __iter
cap_call iter.next 1
dup
jmp_if_not loop_end
store iterator
compile(body)
jmp loop_start
loop_end:
pop
```

## Version History

- **v0.3**: Added control flow nodes (If, While, For), data structures (StructDef), and formal specification
- **v0.2**: Added CapabilityCall, Import, Export
- **v0.1**: Initial version with basic expressions and statements
