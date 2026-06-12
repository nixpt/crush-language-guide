# Instruction Set Reference

This is the complete reference for all CASM instructions. Each instruction is documented with its syntax, stack effects, parameters, description, and examples.

## Reading Stack Effects

Stack effects show how instructions modify the stack:

```text
before → after
```

For example:
- `a, b → result` means: pop `b`, pop `a`, push `result`
- `value →` means: pop `value` (nothing pushed)
- `→ value` means: push `value` (nothing popped)

## Instruction Categories

- [Stack Operations](#stack-operations)
- [Memory Operations](#memory-operations)
- [Arithmetic Operations](#arithmetic-operations)
- [Comparison Operations](#comparison-operations)
- [Logical Operations](#logical-operations)
- [Bitwise Operations](#bitwise-operations)
- [Stack Manipulation](#stack-manipulation)
- [Control Flow](#control-flow)
- [Array Operations](#array-operations)
- [Object Operations](#object-operations)
- [Type Operations](#type-operations)
- [Capability Calls](#capability-calls)
- [Concurrency](#concurrency)

---

## Stack Operations

### `push_int`

Push an integer onto the stack.

**Syntax:**
```json
{"op": "push_int", "value": 42}
```

**Stack Effect:** `→ int`

**Parameters:**
- `value` (Integer): The integer value to push

**Example:**
```json
{"op": "push_int", "value": 100}
// Stack: [100]
```

---

### `push_float`

Push a floating-point number onto the stack.

**Syntax:**
```json
{"op": "push_float", "value": 3.14}
```

**Stack Effect:** `→ float`

**Parameters:**
- `value` (Float): The float value to push

**Example:**
```json
{"op": "push_float", "value": 2.718}
// Stack: [2.718]
```

---

### `push_str`

Push a string onto the stack.

**Syntax:**
```json
{"op": "push_str", "value": "Hello"}
```

**Stack Effect:** `→ string`

**Parameters:**
- `value` (String): The string value to push

**Example:**
```json
{"op": "push_str", "value": "Hello, World!"}
// Stack: ["Hello, World!"]
```

---

### `push_bool`

Push a boolean onto the stack.

**Syntax:**
```json
{"op": "push_bool", "value": true}
```

**Stack Effect:** `→ bool`

**Parameters:**
- `value` (Boolean): `true` or `false`

**Example:**
```json
{"op": "push_bool", "value": false}
// Stack: [false]
```

---

### `push_null`

Push a null value onto the stack.

**Syntax:**
```json
{"op": "push_null"}
```

**Stack Effect:** `→ null`

**Parameters:** None

**Example:**
```json
{"op": "push_null"}
// Stack: [null]
```

---

### `pop`

Remove the top value from the stack.

**Syntax:**
```json
{"op": "pop"}
```

**Stack Effect:** `value →`

**Parameters:** None

**Example:**
```json
{"op": "push_int", "value": 42}
{"op": "pop"}
// Stack: []
```

---

### `dup`

Duplicate the top stack value.

**Syntax:**
```json
{"op": "dup"}
```

**Stack Effect:** `value → value, value`

**Parameters:** None

**Example:**
```json
{"op": "push_int", "value": 5}
{"op": "dup"}
// Stack: [5, 5]
```

---

## Memory Operations

### `store`

Store the top stack value in a variable.

**Syntax:**
```json
{"op": "store", "name": "variable_name"}
```

**Stack Effect:** `value →`

**Parameters:**
- `name` (String): Variable name

**Example:**
```json
{"op": "push_int", "value": 42}
{"op": "store", "name": "x"}
// Variable x = 42
// Stack: []
```

---

### `load`

Load a variable's value onto the stack.

**Syntax:**
```json
{"op": "load", "name": "variable_name"}
```

**Stack Effect:** `→ value`

**Parameters:**
- `name` (String): Variable name

**Example:**
```json
{"op": "load", "name": "x"}
// Stack: [42] (assuming x = 42)
```

---

### `export_var`

Export a variable to the capsule's export table.

**Syntax:**
```json
{"op": "export_var", "name": "variable_name"}
```

**Stack Effect:** `value →`

**Parameters:**
- `name` (String): Variable name to export

**Example:**
```json
{"op": "push_int", "value": 100}
{"op": "export_var", "name": "result"}
// Exports result = 100 for other capsules
```

---

### `import_var`

Import a variable from another capsule.

**Syntax:**
```json
{"op": "import_var", "name": "variable_name"}
```

**Stack Effect:** `→ value`

**Parameters:**
- `name` (String): Variable name to import

**Example:**
```json
{"op": "import_var", "name": "config"}
// Stack: [<imported value>]
```

---

## Arithmetic Operations

### `add`

Add two values.

**Syntax:**
```json
{"op": "add"}
```

**Stack Effect:** `a, b → result`

**Parameters:** None

**Behavior:**
- Numbers: arithmetic addition
- Strings: concatenation

**Example:**
```json
{"op": "push_int", "value": 5}
{"op": "push_int", "value": 3}
{"op": "add"}
// Stack: [8]
```

---

### `sub`

Subtract two numbers.

**Syntax:**
```json
{"op": "sub"}
```

**Stack Effect:** `a, b → result`

**Parameters:** None

**Example:**
```json
{"op": "push_int", "value": 10}
{"op": "push_int", "value": 3}
{"op": "sub"}
// Stack: [7]  (10 - 3)
```

---

### `mul`

Multiply two numbers.

**Syntax:**
```json
{"op": "mul"}
```

**Stack Effect:** `a, b → result`

**Parameters:** None

**Example:**
```json
{"op": "push_int", "value": 6}
{"op": "push_int", "value": 7}
{"op": "mul"}
// Stack: [42]
```

---

### `div`

Divide two numbers.

**Syntax:**
```json
{"op": "div"}
```

**Stack Effect:** `a, b → result`

**Parameters:** None

**Example:**
```json
{"op": "push_int", "value": 20}
{"op": "push_int", "value": 4}
{"op": "div"}
// Stack: [5]  (20 / 4)
```

---

### `mod`

Compute modulo (remainder).

**Syntax:**
```json
{"op": "mod"}
```

**Stack Effect:** `a, b → result`

**Parameters:** None

**Example:**
```json
{"op": "push_int", "value": 17}
{"op": "push_int", "value": 5}
{"op": "mod"}
// Stack: [2]  (17 % 5)
```

---

### `neg`

Negate a number.

**Syntax:**
```json
{"op": "neg"}
```

**Stack Effect:** `value → -value`

**Parameters:** None

**Example:**
```json
{"op": "push_int", "value": 42}
{"op": "neg"}
// Stack: [-42]
```

---

## Comparison Operations

### `eq`

Test equality.

**Syntax:**
```json
{"op": "eq"}
```

**Stack Effect:** `a, b → bool`

**Parameters:** None

**Example:**
```json
{"op": "push_int", "value": 5}
{"op": "push_int", "value": 5}
{"op": "eq"}
// Stack: [true]
```

---

### `ne`

Test inequality.

**Syntax:**
```json
{"op": "ne"}
```

**Stack Effect:** `a, b → bool`

**Parameters:** None

**Example:**
```json
{"op": "push_int", "value": 5}
{"op": "push_int", "value": 3}
{"op": "ne"}
// Stack: [true]
```

---

### `lt`

Test less than.

**Syntax:**
```json
{"op": "lt"}
```

**Stack Effect:** `a, b → bool`

**Parameters:** None

**Example:**
```json
{"op": "push_int", "value": 3}
{"op": "push_int", "value": 5}
{"op": "lt"}
// Stack: [true]  (3 < 5)
```

---

### `gt`

Test greater than.

**Syntax:**
```json
{"op": "gt"}
```

**Stack Effect:** `a, b → bool`

**Parameters:** None

**Example:**
```json
{"op": "push_int", "value": 7}
{"op": "push_int", "value": 3}
{"op": "gt"}
// Stack: [true]  (7 > 3)
```

---

### `le`

Test less than or equal.

**Syntax:**
```json
{"op": "le"}
```

**Stack Effect:** `a, b → bool`

**Parameters:** None

**Example:**
```json
{"op": "push_int", "value": 5}
{"op": "push_int", "value": 5}
{"op": "le"}
// Stack: [true]  (5 <= 5)
```

---

### `ge`

Test greater than or equal.

**Syntax:**
```json
{"op": "ge"}
```

**Stack Effect:** `a, b → bool`

**Parameters:** None

**Example:**
```json
{"op": "push_int", "value": 8}
{"op": "push_int", "value": 3}
{"op": "ge"}
// Stack: [true]  (8 >= 3)
```

---

## Logical Operations

### `and`

Logical AND.

**Syntax:**
```json
{"op": "and"}
```

**Stack Effect:** `a, b → bool`

**Parameters:** None

**Example:**
```json
{"op": "push_bool", "value": true}
{"op": "push_bool", "value": false}
{"op": "and"}
// Stack: [false]
```

---

### `or`

Logical OR.

**Syntax:**
```json
{"op": "or"}
```

**Stack Effect:** `a, b → bool`

**Parameters:** None

**Example:**
```json
{"op": "push_bool", "value": true}
{"op": "push_bool", "value": false}
{"op": "or"}
// Stack: [true]
```

---

### `not`

Logical NOT.

**Syntax:**
```json
{"op": "not"}
```

**Stack Effect:** `value → bool`

**Parameters:** None

**Example:**
```json
{"op": "push_bool", "value": true}
{"op": "not"}
// Stack: [false]
```

---

## Bitwise Operations

### `bit_and`

Bitwise AND.

**Syntax:**
```json
{"op": "bit_and"}
```

**Stack Effect:** `a, b → result`

**Parameters:** None

**Example:**
```json
{"op": "push_int", "value": 12}  // 1100
{"op": "push_int", "value": 10}  // 1010
{"op": "bit_and"}
// Stack: [8]  // 1000
```

---

### `bit_or`

Bitwise OR.

**Syntax:**
```json
{"op": "bit_or"}
```

**Stack Effect:** `a, b → result`

**Parameters:** None

---

### `bit_xor`

Bitwise XOR.

**Syntax:**
```json
{"op": "bit_xor"}
```

**Stack Effect:** `a, b → result`

**Parameters:** None

---

### `bit_not`

Bitwise NOT.

**Syntax:**
```json
{"op": "bit_not"}
```

**Stack Effect:** `value → result`

**Parameters:** None

---

### `shl`

Shift left.

**Syntax:**
```json
{"op": "shl"}
```

**Stack Effect:** `value, shift → result`

**Parameters:** None

**Example:**
```json
{"op": "push_int", "value": 5}   // 101
{"op": "push_int", "value": 2}
{"op": "shl"}
// Stack: [20]  // 10100
```

---

### `shr`

Shift right.

**Syntax:**
```json
{"op": "shr"}
```

**Stack Effect:** `value, shift → result`

**Parameters:** None

---

## Stack Manipulation

### `swap`

Swap the top two stack values.

**Syntax:**
```json
{"op": "swap"}
```

**Stack Effect:** `a, b → b, a`

**Parameters:** None

**Example:**
```json
{"op": "push_int", "value": 1}
{"op": "push_int", "value": 2}
{"op": "swap"}
// Stack: [1, 2] → [2, 1]
```

---

### `rot`

Rotate top three values.

**Syntax:**
```json
{"op": "rot"}
```

**Stack Effect:** `a, b, c → b, c, a`

**Parameters:** None

---

### `pick`

Copy nth item from stack top.

**Syntax:**
```json
{"op": "pick", "n": 2}
```

**Stack Effect:** `..., a, b, c → ..., a, b, c, a`

**Parameters:**
- `n` (Integer): Depth to pick from (0 = top)

---

### `roll`

Move nth item to stack top.

**Syntax:**
```json
{"op": "roll", "n": 2}
```

**Stack Effect:** `..., a, b, c → ..., b, c, a`

**Parameters:**
- `n` (Integer): Depth to roll from

---

## Control Flow

### `jmp`

Unconditional jump.

**Syntax:**
```json
{"op": "jmp", "target": 10}
```

**Stack Effect:** (none)

**Parameters:**
- `target` (Integer): Instruction index to jump to

**Example:**
```json
{"op": "jmp", "target": 5}
// Jump to instruction 5
```

---

### `jmp_if`

Jump if true.

**Syntax:**
```json
{"op": "jmp_if", "target": 10}
```

**Stack Effect:** `condition →`

**Parameters:**
- `target` (Integer): Instruction index to jump to if true

**Example:**
```json
{"op": "push_bool", "value": true}
{"op": "jmp_if", "target": 5}
// Jumps to instruction 5
```

---

### `jmp_if_not`

Jump if false.

**Syntax:**
```json
{"op": "jmp_if_not", "target": 10}
```

**Stack Effect:** `condition →`

**Parameters:**
- `target` (Integer): Instruction index to jump to if false

---

### `call`

Call a function.

**Syntax:**
```json
{"op": "call", "function": "function_name"}
```

**Stack Effect:** `arg1, arg2, ... → return_value`

**Parameters:**
- `function` (String): Name of function to call

**Example:**
```json
{"op": "push_int", "value": 5}
{"op": "push_int", "value": 3}
{"op": "call", "function": "add"}
// Calls add(5, 3), pushes result
```

---

### `ret`

Return from function.

**Syntax:**
```json
{"op": "ret"}
```

**Stack Effect:** `return_value →` (to caller's stack)

**Parameters:** None

**Example:**
```json
{"op": "push_int", "value": 42}
{"op": "ret"}
// Returns 42 to caller
```

---

### `break`

Exit innermost loop.

**Syntax:**
```json
{"op": "break"}
```

**Stack Effect:** (none)

**Parameters:** None

---

### `continue`

Jump to loop start.

**Syntax:**
```json
{"op": "continue"}
```

**Stack Effect:** (none)

**Parameters:** None

---

## Array Operations

### `new_array`

Create array from stack values.

**Syntax:**
```json
{"op": "new_array", "size": 3}
```

**Stack Effect:** `v1, v2, v3 → array`

**Parameters:**
- `size` (Integer): Number of elements to pop

**Example:**
```json
{"op": "push_int", "value": 1}
{"op": "push_int", "value": 2}
{"op": "push_int", "value": 3}
{"op": "new_array", "size": 3}
// Stack: [[1, 2, 3]]
```

---

### `arr_get`

Get array element.

**Syntax:**
```json
{"op": "arr_get"}
```

**Stack Effect:** `array, index → value`

**Parameters:** None

**Example:**
```json
// Assuming array = [10, 20, 30]
{"op": "load", "name": "arr"}
{"op": "push_int", "value": 1}
{"op": "arr_get"}
// Stack: [20]
```

---

### `arr_set`

Set array element.

**Syntax:**
```json
{"op": "arr_set"}
```

**Stack Effect:** `array, index, value → array`

**Parameters:** None

---

### `arr_len`

Get array length.

**Syntax:**
```json
{"op": "arr_len"}
```

**Stack Effect:** `array → length`

**Parameters:** None

---

### `arr_push`

Append to array.

**Syntax:**
```json
{"op": "arr_push"}
```

**Stack Effect:** `array, value → array`

**Parameters:** None

---

### `arr_pop`

Remove last element.

**Syntax:**
```json
{"op": "arr_pop"}
```

**Stack Effect:** `array → array, value`

**Parameters:** None

---

## Object Operations

### `new_obj`

Create empty object.

**Syntax:**
```json
{"op": "new_obj"}
```

**Stack Effect:** `→ object`

**Parameters:** None

---

### `new_struct`

Create named struct.

**Syntax:**
```json
{"op": "new_struct", "name": "Point"}
```

**Stack Effect:** `→ struct`

**Parameters:**
- `name` (String): Struct type name

---

### `get_field`

Get object field.

**Syntax:**
```json
{"op": "get_field", "name": "field_name"}
```

**Stack Effect:** `object → value`

**Parameters:**
- `name` (String): Field name

**Example:**
```json
{"op": "load", "name": "point"}
{"op": "get_field", "name": "x"}
// Stack: [<x value>]
```

---

### `set_field`

Set object field.

**Syntax:**
```json
{"op": "set_field", "name": "field_name"}
```

**Stack Effect:** `object, value → object`

**Parameters:**
- `name` (String): Field name

---

## Type Operations

### `type_of`

Get type of value.

**Syntax:**
```json
{"op": "type_of"}
```

**Stack Effect:** `value → type_string`

**Parameters:** None

**Example:**
```json
{"op": "push_int", "value": 42}
{"op": "type_of"}
// Stack: ["int"]
```

---

### `cast`

Cast value to type.

**Syntax:**
```json
{"op": "cast", "type": "int"}
```

**Stack Effect:** `value → casted_value`

**Parameters:**
- `type` (String): Target type

---

## Capability Calls

### `cap_call`

Invoke a capability.

**Syntax:**
```json
{"op": "cap_call", "name": "io.print", "argc": 1}
```

**Stack Effect:** `arg1, arg2, ... → return_value`

**Parameters:**
- `name` (String): Capability name (format: `namespace.method`)
- `argc` (Integer): Number of arguments

**Example:**
```json
{"op": "push_str", "value": "Hello!"}
{"op": "cap_call", "name": "io.print", "argc": 1}
// Prints "Hello!" to stdout
```

**Common Capabilities:**
- `io.print` - Print to stdout
- `io.read` - Read from stdin
- `fs.read` - Read file
- `fs.write` - Write file
- `net.http` - HTTP request
- `sys.exec` - Execute command

---

## Concurrency

### `spawn`

Create new task.

**Syntax:**
```json
{"op": "spawn"}
```

**Stack Effect:** `function_name, args... → task_id`

**Parameters:** None

---

### `yield`

Yield execution.

**Syntax:**
```json
{"op": "yield"}
```

**Stack Effect:** (none)

**Parameters:** None

---

## Quick Reference Table

| Category | Instructions |
|----------|-------------|
| Stack | `push_int`, `push_float`, `push_str`, `push_bool`, `push_null`, `pop`, `dup` |
| Memory | `store`, `load`, `export_var`, `import_var` |
| Arithmetic | `add`, `sub`, `mul`, `div`, `mod`, `neg` |
| Comparison | `eq`, `ne`, `lt`, `gt`, `le`, `ge` |
| Logical | `and`, `or`, `not` |
| Bitwise | `bit_and`, `bit_or`, `bit_xor`, `bit_not`, `shl`, `shr` |
| Stack Manip | `swap`, `rot`, `pick`, `roll` |
| Control Flow | `jmp`, `jmp_if`, `jmp_if_not`, `call`, `ret`, `break`, `continue` |
| Arrays | `new_array`, `arr_get`, `arr_set`, `arr_len`, `arr_push`, `arr_pop` |
| Objects | `new_obj`, `new_struct`, `get_field`, `set_field` |
| Types | `type_of`, `cast` |
| Capabilities | `cap_call` |
| Concurrency | `spawn`, `yield` |
