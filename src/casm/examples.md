# CASM Examples

This chapter provides practical examples of CASM programs, from simple to complex.

## Example 1: Hello World

The simplest CASM program:

```json
{
  "version": "0.1",
  "functions": {
    "main": {
      "params": [],
      "locals": [],
      "body": [
        {"op": "push_str", "value": "Hello, World!"},
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

**Execution trace:**
```text
1. push_str "Hello, World!"  → Stack: ["Hello, World!"]
2. cap_call io.print 1       → Prints "Hello, World!", Stack: []
3. ret                       → Returns from main
```

## Example 2: Variables and Arithmetic

```json
{
  "version": "0.1",
  "functions": {
    "main": {
      "params": [],
      "locals": ["x", "y", "sum"],
      "body": [
        {"op": "push_int", "value": 10},
        {"op": "store", "name": "x"},
        
        {"op": "push_int", "value": 32},
        {"op": "store", "name": "y"},
        
        {"op": "load", "name": "x"},
        {"op": "load", "name": "y"},
        {"op": "add"},
        {"op": "store", "name": "sum"},
        
        {"op": "push_str", "value": "The sum is: "},
        {"op": "load", "name": "sum"},
        {"op": "add"},
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

**Output:** `The sum is: 42`

## Example 3: Conditional (If/Else)

```json
{
  "version": "0.1",
  "functions": {
    "main": {
      "params": [],
      "locals": ["age"],
      "body": [
        {"op": "push_int", "value": 18},
        {"op": "store", "name": "age"},
        
        {"op": "load", "name": "age"},
        {"op": "push_int", "value": 18},
        {"op": "ge"},
        {"op": "jmp_if_not", "target": 9},
        
        {"op": "push_str", "value": "You are an adult"},
        {"op": "cap_call", "name": "io.print", "argc": 1},
        {"op": "jmp", "target": 11},
        
        {"op": "push_str", "value": "You are a minor"},
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

**Control flow:**
```text
if age >= 18:
    print("You are an adult")
else:
    print("You are a minor")
```

## Example 4: While Loop

Count from 1 to 5:

```json
{
  "version": "0.1",
  "functions": {
    "main": {
      "params": [],
      "locals": ["i"],
      "body": [
        {"op": "push_int", "value": 1},
        {"op": "store", "name": "i"},
        
        {"op": "load", "name": "i"},
        {"op": "push_int", "value": 5},
        {"op": "le"},
        {"op": "jmp_if_not", "target": 14},
        
        {"op": "load", "name": "i"},
        {"op": "cap_call", "name": "io.print", "argc": 1},
        
        {"op": "load", "name": "i"},
        {"op": "push_int", "value": 1},
        {"op": "add"},
        {"op": "store", "name": "i"},
        
        {"op": "jmp", "target": 2},
        
        {"op": "ret"}
      ]
    }
  },
  "manifest": {
    "permissions": ["io.print"]
  }
}
```

**Output:**
```text
1
2
3
4
5
```

## Example 5: Function Calls

Factorial function:

```json
{
  "version": "0.1",
  "functions": {
    "main": {
      "params": [],
      "locals": ["result"],
      "body": [
        {"op": "push_int", "value": 5},
        {"op": "call", "function": "factorial"},
        {"op": "store", "name": "result"},
        
        {"op": "push_str", "value": "5! = "},
        {"op": "load", "name": "result"},
        {"op": "add"},
        {"op": "cap_call", "name": "io.print", "argc": 1},
        
        {"op": "ret"}
      ]
    },
    "factorial": {
      "params": ["n"],
      "locals": ["temp"],
      "body": [
        {"op": "load", "name": "n"},
        {"op": "push_int", "value": 1},
        {"op": "le"},
        {"op": "jmp_if_not", "target": 5},
        
        {"op": "push_int", "value": 1},
        {"op": "ret"},
        
        {"op": "load", "name": "n"},
        {"op": "push_int", "value": 1},
        {"op": "sub"},
        {"op": "call", "function": "factorial"},
        {"op": "store", "name": "temp"},
        
        {"op": "load", "name": "n"},
        {"op": "load", "name": "temp"},
        {"op": "mul"},
        {"op": "ret"}
      ]
    }
  },
  "manifest": {
    "permissions": ["io.print"]
  }
}
```

**Output:** `5! = 120`

## Example 6: Arrays

Working with arrays:

```json
{
  "version": "0.1",
  "functions": {
    "main": {
      "params": [],
      "locals": ["arr", "len", "i"],
      "body": [
        {"op": "push_int", "value": 10},
        {"op": "push_int", "value": 20},
        {"op": "push_int", "value": 30},
        {"op": "new_array", "size": 3},
        {"op": "store", "name": "arr"},
        
        {"op": "load", "name": "arr"},
        {"op": "arr_len"},
        {"op": "store", "name": "len"},
        
        {"op": "push_str", "value": "Array length: "},
        {"op": "load", "name": "len"},
        {"op": "add"},
        {"op": "cap_call", "name": "io.print", "argc": 1},
        
        {"op": "load", "name": "arr"},
        {"op": "push_int", "value": 1},
        {"op": "arr_get"},
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

**Output:**
```text
Array length: 3
20
```

## Example 7: Objects and Structs

```json
{
  "version": "0.1",
  "functions": {
    "main": {
      "params": [],
      "locals": ["point"],
      "body": [
        {"op": "new_struct", "name": "Point"},
        {"op": "store", "name": "point"},
        
        {"op": "load", "name": "point"},
        {"op": "push_int", "value": 10},
        {"op": "set_field", "name": "x"},
        {"op": "store", "name": "point"},
        
        {"op": "load", "name": "point"},
        {"op": "push_int", "value": 20},
        {"op": "set_field", "name": "y"},
        {"op": "store", "name": "point"},
        
        {"op": "load", "name": "point"},
        {"op": "get_field", "name": "x"},
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

**Output:** `10`

## Example 8: File I/O

Reading and writing files:

```json
{
  "version": "0.1",
  "functions": {
    "main": {
      "params": [],
      "locals": ["content"],
      "body": [
        {"op": "push_str", "value": "data.txt"},
        {"op": "push_str", "value": "Hello from CASM!"},
        {"op": "cap_call", "name": "fs.write", "argc": 2},
        
        {"op": "push_str", "value": "File written successfully"},
        {"op": "cap_call", "name": "io.print", "argc": 1},
        
        {"op": "push_str", "value": "data.txt"},
        {"op": "cap_call", "name": "fs.read", "argc": 1},
        {"op": "store", "name": "content"},
        
        {"op": "push_str", "value": "File content: "},
        {"op": "load", "name": "content"},
        {"op": "add"},
        {"op": "cap_call", "name": "io.print", "argc": 1},
        
        {"op": "ret"}
      ]
    }
  },
  "manifest": {
    "permissions": ["io.print", "fs.read", "fs.write"]
  }
}
```

## Example 9: Error Handling

Using metadata for error reporting:

```json
{
  "version": "0.1",
  "lang": "python",
  "functions": {
    "main": {
      "params": [],
      "locals": ["x", "y"],
      "body": [
        {
          "op": "push_int",
          "value": 10,
          "lang": "python",
          "meta": {"file": "script.py", "line": 1, "column": 5}
        },
        {
          "op": "store",
          "name": "x",
          "lang": "python",
          "meta": {"file": "script.py", "line": 1}
        },
        {
          "op": "push_int",
          "value": 0,
          "lang": "python",
          "meta": {"file": "script.py", "line": 2, "column": 5}
        },
        {
          "op": "store",
          "name": "y",
          "lang": "python",
          "meta": {"file": "script.py", "line": 2}
        },
        {
          "op": "load",
          "name": "x",
          "lang": "python",
          "meta": {"file": "script.py", "line": 3, "column": 8}
        },
        {
          "op": "load",
          "name": "y",
          "lang": "python",
          "meta": {"file": "script.py", "line": 3, "column": 12}
        },
        {
          "op": "div",
          "lang": "python",
          "meta": {"file": "script.py", "line": 3, "column": 10}
        },
        {
          "op": "ret",
          "lang": "python",
          "meta": {"file": "script.py", "line": 3}
        }
      ]
    }
  }
}
```

**Error output:**
```text
Error at script.py:3:10
  |
3 | result = x / y
  |          ^^^^^
  | Division by zero
```

## Example 10: Complete Program

A complete program with multiple functions and capabilities:

```json
{
  "version": "0.1",
  "lang": "crush",
  "functions": {
    "main": {
      "params": [],
      "locals": ["numbers", "sum", "avg"],
      "body": [
        {"op": "push_int", "value": 10},
        {"op": "push_int", "value": 20},
        {"op": "push_int", "value": 30},
        {"op": "push_int", "value": 40},
        {"op": "push_int", "value": 50},
        {"op": "new_array", "size": 5},
        {"op": "store", "name": "numbers"},
        
        {"op": "load", "name": "numbers"},
        {"op": "call", "function": "sum_array"},
        {"op": "store", "name": "sum"},
        
        {"op": "load", "name": "sum"},
        {"op": "push_int", "value": 5},
        {"op": "div"},
        {"op": "store", "name": "avg"},
        
        {"op": "push_str", "value": "Sum: "},
        {"op": "load", "name": "sum"},
        {"op": "add"},
        {"op": "cap_call", "name": "io.print", "argc": 1},
        
        {"op": "push_str", "value": "Average: "},
        {"op": "load", "name": "avg"},
        {"op": "add"},
        {"op": "cap_call", "name": "io.print", "argc": 1},
        
        {"op": "ret"}
      ]
    },
    "sum_array": {
      "params": ["arr"],
      "locals": ["total", "i", "len"],
      "body": [
        {"op": "push_int", "value": 0},
        {"op": "store", "name": "total"},
        
        {"op": "push_int", "value": 0},
        {"op": "store", "name": "i"},
        
        {"op": "load", "name": "arr"},
        {"op": "arr_len"},
        {"op": "store", "name": "len"},
        
        {"op": "load", "name": "i"},
        {"op": "load", "name": "len"},
        {"op": "lt"},
        {"op": "jmp_if_not", "target": 23},
        
        {"op": "load", "name": "total"},
        {"op": "load", "name": "arr"},
        {"op": "load", "name": "i"},
        {"op": "arr_get"},
        {"op": "add"},
        {"op": "store", "name": "total"},
        
        {"op": "load", "name": "i"},
        {"op": "push_int", "value": 1},
        {"op": "add"},
        {"op": "store", "name": "i"},
        
        {"op": "jmp", "target": 9},
        
        {"op": "load", "name": "total"},
        {"op": "ret"}
      ]
    }
  },
  "manifest": {
    "permissions": ["io.print"]
  }
}
```

**Output:**
```text
Sum: 150
Average: 30
```

## Tips for Writing CASM

### 1. Use Comments in JSON

While CASM itself doesn't support comments, you can add them in your JSON during development:

```json
{
  "body": [
    {"op": "push_int", "value": 42},
    {"_comment": "Print the value"},
    {"op": "cap_call", "name": "io.print", "argc": 1}
  ]
}
```

(The VM will ignore unknown fields like `_comment`)

### 2. Label Jump Targets

Keep track of instruction indices:

```json
{
  "body": [
    /* 0 */ {"op": "load", "name": "x"},
    /* 1 */ {"op": "push_int", "value": 0},
    /* 2 */ {"op": "gt"},
    /* 3 */ {"op": "jmp_if_not", "target": 6},
    /* 4 */ {"op": "push_str", "value": "Positive"},
    /* 5 */ {"op": "jmp", "target": 7},
    /* 6 */ {"op": "push_str", "value": "Non-positive"},
    /* 7 */ {"op": "cap_call", "name": "io.print", "argc": 1}
  ]
}
```

### 3. Always Include Metadata

```json
{
  "op": "add",
  "lang": "crush",
  "meta": {
    "file": "program.crush",
    "line": 10,
    "column": 15
  }
}
```

### 4. Validate Your CASM

```bash
crush validate program.casm
```

## Next Steps

- **[Program Structure](structure.md)**: Understand CASM program anatomy
- **[Instruction Reference](instructions.md)**: Complete instruction documentation
- **[Crush Language](../crush/README.md)**: Learn the high-level Crush language
