# CASM Examples

Every program here is CASM **text assembly** — the form you can write by hand and run
with `crush-run run FILE.casm --cap io.print` — and every one is executed by this
guide's checker against crush-ast `v0.3.9`, with the output shown. The JSON IR is
covered in [Program Structure](structure.md) and
[Serialization](serialization.md). Opcode details are in the
[Instruction Reference](instructions.md).

All programs print with `CAP_CALL "io.print" N`, so run them with `--cap io.print`
(a `.casm` file carries no permissions of its own).

## 1. Hello, world

```casm
.func main
    PUSH_STR "Hello, CASM!"
    CAP_CALL "io.print" 1
    HALT
```

<!-- check: output -->
```text
Hello, CASM!
```

`io.print` takes any number of arguments (here `1`), prints them back to back and
adds a newline.

## 2. Variables and arithmetic

`STORE n` pops into slot `n`; `LOAD n` pushes it back.

```casm
.func main
    PUSH 6
    STORE 0             ; a = 6
    PUSH 7
    STORE 1             ; b = 7
    LOAD 0
    LOAD 1
    MUL
    STORE 2             ; product = a * b
    PUSH_STR "6 * 7 = "
    LOAD 2
    CAP_CALL "io.print" 2
    HALT
```

<!-- check: output -->
```text
6 * 7 = 42
```

## 3. Conditionals

`JZ` jumps when the popped value is falsy, so an `if` compiles to a `JZ` over the
"then" branch plus a `JMP` over the "else" branch.

```casm
.func main
    PUSH 3
    STORE 0             ; n = 3
    LOAD 0
    PUSH 2
    GT                  ; n > 2
    JZ else
    PUSH_STR "big"
    CAP_CALL "io.print" 1
    JMP end
else:
    PUSH_STR "small"
    CAP_CALL "io.print" 1
end:
    HALT
```

<!-- check: output -->
```text
big
```

## 4. Loops

```casm
.func main
    PUSH 1
    STORE 0             ; i = 1
    PUSH 0
    STORE 1             ; sum = 0
loop:
    LOAD 0
    PUSH 5
    GT                  ; i > 5 ?
    JNZ done
    LOAD 1
    LOAD 0
    ADD
    STORE 1             ; sum = sum + i
    LOAD 0
    PUSH 1
    ADD
    STORE 0             ; i = i + 1
    JMP loop
done:
    PUSH_STR "sum 1..5 = "
    LOAD 1
    CAP_CALL "io.print" 2
    HALT
```

<!-- check: output -->
```text
sum 1..5 = 15
```

## 5. Functions

Arguments are pushed **last first**; the callee's first instructions `STORE` its
parameters in order, so the first `STORE` receives the *first* argument. `RET`
returns whatever the callee left on top of the stack.

```casm
.func main
    PUSH 3              ; second argument (b)
    PUSH 10             ; first argument  (a)
    CALL sub
    CAP_CALL "io.print" 1
    HALT
.func sub
    STORE 0             ; a
    STORE 1             ; b
    LOAD 0
    LOAD 1
    SUB                 ; a - b
    RET
```

<!-- check: output -->
```text
7
```

Recursion works the same way (each call gets fresh slots). The default call-depth
quota is 256:

```casm
.func main
    PUSH 10
    CALL fact
    CAP_CALL "io.print" 1
    HALT
.func fact
    STORE 0             ; n
    LOAD 0
    PUSH 1
    LE
    JNZ base
    LOAD 0
    LOAD 0
    PUSH 1
    SUB
    CALL fact           ; fact(n - 1)
    MUL                 ; n * fact(n - 1)
    RET
base:
    PUSH 1
    RET
```

<!-- check: output -->
```text
3628800
```

## 6. Arrays and objects

```casm
.func main
    PUSH 10
    PUSH 20
    PUSH 30
    NEW_ARRAY 3         ; [10, 20, 30]
    STORE 0
    LOAD 0
    PUSH 40
    ARR_PUSH            ; array v -> array
    STORE 0
    PUSH_STR "length: "
    LOAD 0
    ARR_LEN
    CAP_CALL "io.print" 2
    PUSH_STR "second: "
    LOAD 0
    PUSH 1
    ARR_GET
    CAP_CALL "io.print" 2

    NEW_OBJ
    PUSH_STR "Ada"
    SET_FIELD "name"    ; obj v -> obj
    STORE 1
    LOAD 1
    GET_FIELD "name"
    CAP_CALL "io.print" 1
    HALT
```

<!-- check: output -->
```text
length: 4
second: 20
Ada
```

## 7. Errors

`ENTER_TRY handler` … `THROW` jumps to the handler with the thrown value on the
stack; `EXIT_TRY` retires the handler when the body finishes normally.

```casm
.func main
    ENTER_TRY handler
    PUSH_STR "disk full"
    THROW
    EXIT_TRY
    JMP end
handler:
    STORE 0
    PUSH_STR "recovered from: "
    LOAD 0
    CAP_CALL "io.print" 2
end:
    HALT
```

<!-- check: output -->
```text
recovered from: disk full
```

A capability that is not registered, or a type error, is **not** catchable this way:
it ends the program with a `[runtime]` error.

## 8. Host capabilities

File access needs the `--fs` flag **and** the capability in the manifest, so run
this one as `crush-run run prog.casm --cap io.print --cap fs.exists --fs`:

<!-- check: flags --cap fs.exists --fs -->
```casm
.func main
    PUSH_STR "no-such-file.txt"
    CAP_CALL "fs.exists" 1
    CAP_CALL "io.print" 1
    HALT
```

<!-- check: output -->
```text
0
```

The manifest is checked first. Leave out `--cap fs.exists` and the VM stops with
`capability not declared in manifest: fs.exists`; pass `--cap fs.exists` but leave out
`--fs` and it stops with `unknown capability: fs.exists` (declared, but the host never
registered it).

<!-- check: runfail capability not declared in manifest: fs.exists -->
```casm
.func main
    PUSH_STR "no-such-file.txt"
    CAP_CALL "fs.exists" 1
    CAP_CALL "io.print" 1
    HALT
```

## 9. What the compiler writes

The text assembly is also what `crushc --emit casm` prints, so you can read how
Crush constructs lower. Labels there are byte offsets (`L42`).

**`if` / `else`:**

```crush
let n = 3
if n > 2 {
    io.print("big")
} else {
    io.print("small")
}
```

<!-- check: output -->
```text
big
```

```casm
.func main
    PUSH 3
    STORE 0
    LOAD 0
    PUSH 2
    GT
    JZ L42
    PUSH_STR "big"
    CAP_CALL "io.print" 1
    JMP L49
L42:
    PUSH_STR "small"
    CAP_CALL "io.print" 1
L49:
    PUSH_NULL
    RET
```

**`try` / `catch`:**

```crush
try {
    throw "bad"
} catch e {
    io.print("caught ", e)
}
```

<!-- check: output -->
```text
caught bad
```

```casm
.func main
    ENTER_TRY L15
    PUSH_STR "bad"
    THROW
    EXIT_TRY
    JMP L28
L15:
    STORE 0
    PUSH_STR "caught "
    LOAD 0
    CAP_CALL "io.print" 2
L28:
    PUSH_NULL
    RET
```

**`for x in array`** expands into an index loop: the array in slot 1, the index in
slot 2, and `ARR_LEN … GT … JZ` as the loop test:

```crush
let t = 0
for x in [1, 2, 3] { t = t + x }
io.print(t)
```

<!-- check: output -->
```text
6
```

```casm
.func main
    PUSH 0
    STORE 0
    NEW_ARRAY 0
    PUSH 1
    ARR_PUSH
    PUSH 2
    ARR_PUSH
    PUSH 3
    ARR_PUSH
    STORE 1
    PUSH 0
    STORE 2
L60:
    LOAD 1
    ARR_LEN
    LOAD 2
    GT
    JZ L114
    LOAD 1
    LOAD 2
    ARR_GET
    STORE 3
    LOAD 0
    LOAD 3
    ADD
    STORE 0
    LOAD 2
    PUSH 1
    ADD
    STORE 2
    JMP L60
L114:
    LOAD 0
    CAP_CALL "io.print" 1
    PUSH_NULL
    RET
```

Notice the array literal: `NEW_ARRAY 0` followed by one `ARR_PUSH` per element —
which is why the [IR's `new_array`](instructions.md#collections-and-objects) never
needs its `size`.

## Tips

1. **Comment freely.** `;` and `#` start a comment in the text assembly (JSON has no comments).
2. **Name your labels.** The assembler resolves them; you never count bytes.
3. **Keep the entry function called `main`** and put it first.
4. **Mind the stack.** Each `CAP_CALL` to a value-returning capability leaves a value;
   a stray one at `HALT` shows up as `stack=1` in the `[steps=…, stack=…]` line that
   `crush-run` prints. Compare it to `0` when debugging.
5. **To see what a Crush construct costs, compile it:** `crushc FILE.crush --emit casm`.
