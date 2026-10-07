# Syntax and Grammar

This chapter covers the lexical structure and grammar that the Crush parser
(`crush-frontend`) accepts today. Every `crush` example in this guide is run
through the real toolchain by `scripts/check-examples.py`; where something is
described in the design but the parser does not accept it yet, the page says so
and links the crush-ast ticket.

> **Status: alpha.** The language is small and still moving. If a feature isn't
> in this chapter, assume it doesn't exist yet.

## A program

A Crush file is a sequence of statements. There are two styles, and they can be
mixed:

- **Script style** — bare top-level statements run top to bottom.
- **`fn main()`** — an explicit entry function.

When a file has both, the top-level statements run first and then `main`'s body
runs.

```crush
print("top-level runs first")

fn main() {
    print("then main")
}
```

<!-- check: output -->
```text
top-level runs first
then main
```

Functions can be called before they are defined:

```crush
print(seven())

fn seven() {
    return 7
}
```

<!-- check: output -->
```text
7
```

## Comments

Single-line comments start with `//` or `#`. There are no block comments —
`/* ... */` is a parse error.

```crush
// a slash comment
# a hash comment
print("hello") // trailing comments work too
```

<!-- check: output -->
```text
hello
```

## Identifiers

Identifiers start with a letter or underscore and continue with letters, digits
and underscores. Hyphens are not allowed, and a name can't be a keyword.

```crush
let counter1 = 1
let _private = 2
let my_variable = 3
print(counter1 + _private + my_variable)
```

<!-- check: output -->
```text
6
```

## Keywords

```text
let   fn      if       else    while   for     in
return break  continue struct  new     try     catch
throw  match  use      import  export  capability
async  await  spawn    yield   lang    mut
true   false  null
```

`mut` and `capability` are reserved, but `let mut x = ...` is **not** accepted
(see [Variables](variables.md)), and `capability` has no usable statement form
yet. `and`, `or` and `not` are **not** keywords — logic uses `&&`, `||` and `!`.

The lexer also recognises a handful of localised keyword aliases —
`karya`/`manau`/`yadi`/`natra`/`farkau`/`jaba_samma`/`sahi`/`galat` (Nepali) plus a
few Chinese and Japanese forms — which map to `fn`/`let`/`if`/`else`/`return`/
`while`/`true`/`false`:

```crush
karya sign(x) {
    yadi x > 0 { farkau "positive" } natra { farkau "not positive" }
}
manau r = sign(1)
print(r)
```

<!-- check: output -->
```text
positive
```

## Literals

| Kind | Examples | Notes |
|---|---|---|
| Integer | `42`, `-7` | decimal only — `0x2A`, `0b101` and `1_000` are not lexed |
| Float | `3.14`, `0.5` | no exponent form (`1.5e3` is rejected) |
| String | `"hello"` | **double quotes only**; escapes `\n \t \" \\` |
| Boolean | `true`, `false` | |
| Null | `null` | |
| Array | `[1, 2, 3]` | see [Types](types.md) |
| Object | `{"a": 1, b: 2}` | see [Types](types.md) |

Single-quoted and triple-quoted strings are parse errors; a string literal may
contain a raw newline.

```crush
let n = 42
let pi = 3.14
let s = "tab:\there"
print(n)
print(pi)
print(s)
```

<!-- check: output -->
```text
42
3.14
tab:	here
```

## Statements and semicolons

Semicolons are **optional**. A statement ends at a newline, or you may write `;`
(and `a; b` on one line) if you prefer. Both of these are the same program:

```crush
let a = 1; let b = 2;
print(a + b);
```

<!-- check: output -->
```text
3
```

```crush
let a = 1
let b = 2
print(a + b)
```

<!-- check: output -->
```text
3
```

### Return values

A function returns a value only through an explicit `return`. A bare final
expression is **not** an implicit return — it yields `null`:

```crush
fn explicit() { return 5 }
fn implicit() { 5 }
print(explicit())
print(implicit())
```

<!-- check: output -->
```text
5
null
```

## Blocks

Blocks are delimited by `{ }` and are used by functions, `if`, loops and
`try`/`catch`. A bare block as a statement is not supported; use `if true { ... }`
if you need one.

Crush has **function-level scope**, not block scope: a `let` inside an `if` or
loop body that reuses an existing name rebinds the same variable (see
[Variables](variables.md)).

## Variables and functions

```crush
let x = 42
let name: String = "Alice"

fn add(a: Int, b: Int) -> Int {
    return a + b
}

print(add(x, 1))
print(name)
```

<!-- check: output -->
```text
43
Alice
```

Type annotations on variables, parameters and return values are checked at
compile time — see [Types](types.md).

## Operators

Full tables are in [Operators](operators.md). In short: `+ - * / %`,
`== != < > <= >=`, `&& || !`, unary `-`, and the pipeline `|>`. There is no `**`,
`//`, `+=`/`-=`, `and`/`or`/`not`, or ternary `? :`.

### Precedence (high → low)

1. Calls, field access, indexing: `f()`, `obj.field`, `a[i]`
2. Unary: `-`, `!`
3. Multiplicative: `*`, `/`, `%`
4. Additive: `+`, `-`
5. Comparison: `<`, `>`, `<=`, `>=`
6. Equality: `==`, `!=`
7. Logical AND: `&&`
8. Logical OR: `||`
9. Pipeline: `|>`

```crush
print(1 + 2 * 3)
print((1 + 2) * 3)
print(1 < 2 && 2 < 3)
```

<!-- check: output -->
```text
7
9
true
```

## Control flow

```crush
let x = 5
if x > 3 {
    print("big")
} else if x > 1 {
    print("medium")
} else {
    print("small")
}

let i = 0
while i < 3 {
    i = i + 1
}
print(i)

for n in 0..3 {
    print(n)
}
```

<!-- check: output -->
```text
big
3
0
1
2
```

`break` and `continue` work in `while` and `for`. See [Control Flow](control_flow.md).

## Capability calls

A capability call looks like an ordinary dotted call — **no `@` prefix**:

```crush
io.print("Hello, ", "Crush")
```

<!-- check: output -->
```text
Hello, Crush
```

(`io.print` accepts any number of arguments and concatenates them with no
separator; the built-in `print(x)` takes exactly one.) Which capabilities exist,
and which command-line flags grant them, is covered in
[Capability System](capabilities.md).

## Language blocks

Another language's code is embedded with `@language { ... }`. The `@` here is
required; it is what introduces the block. Polyglot execution is **off by
default** and needs `--polyglot`:

<!-- check: flags --polyglot -->
```crush
@python {
print("Hello from Python")
}
```

<!-- check: output -->
```text
Hello from Python
```

See [Polyglot Programming](polyglot.md) for the supported languages, how
variables cross the boundary, and the (important) security caveats.

## Imports and exports

`import a.b` and `use @lang ...` **parse**, but importing does not load anything
yet: `import` is lowered to a `module.load` capability that nothing registers, so
a program containing one fails at run time with `unknown capability:
module.load` (crush-ast **CRUSH-110**). Every program is currently a single
file. There is no `std.*` module tree.

<!-- check: nyi CRUSH-110 -->
```crush
import std.io
print("never reached")
```

`export name` parses and marks an existing variable or function for export. It
is not an expression-level declaration:

```crush
let result = 6 * 7
export result
print(result)
```

<!-- check: output -->
```text
42
```

`export let x = ...` and `export fn f() {...}` are parse errors.

## Annotations

`@name` also introduces compiler/AI annotations such as `@invariant` and
`@decision`, attached to the next declaration. These are metadata for tooling,
not runtime behaviour; see the note at the end of the
[Capability System](capabilities.md) chapter and the [AI-Native CAST](../cast/ai-native.md)
chapter.

## Style

- `snake_case` for functions and variables, `PascalCase` for structs.
- Four-space indentation; keep lines under ~100 characters.
- Omit semicolons unless you are putting two statements on one line.

## Grammar summary

This is the grammar the parser implements, simplified (from
`crates/crush-frontend/src/parser/mod.rs`):

```ebnf
program     = statement* ;

statement   = let_stmt | fn_def | struct_def | if_stmt | while_stmt
            | for_stmt | return_stmt | break | continue
            | try_stmt | throw_stmt | export_stmt | import_stmt
            | lang_block | expr_stmt ;

let_stmt    = "let" IDENT ( ":" type )? "=" expression ";"? ;
fn_def      = "async"? "fn" IDENT "(" params? ")" ( "->" type )? block ;
struct_def  = "struct" IDENT "{" ( IDENT ( ":" type )? ","? )* "}" ;
if_stmt     = "if" expression block ( "else" ( if_stmt | block ) )? ;
while_stmt  = "while" expression block ;
for_stmt    = "for" IDENT "in" expression block ;
try_stmt    = "try" block "catch" IDENT block ;
throw_stmt  = "throw" expression ;
export_stmt = "export" IDENT ;
lang_block  = "@" IDENT ( "[" deps "]" )? "{" raw source "}" ;
block       = "{" statement* "}" ;

expression  = literal | IDENT | expression binop expression
            | unop expression | call | field | index
            | "new" IDENT "(" ")" | "match" expression "{" arms "}" ;
call        = expression "(" args? ")" ;
```

## Next Steps

- **[Data Types](types.md)**: the type system and collections
- **[Variables](variables.md)**: declaration and scope
- **[Control Flow](control_flow.md)**: loops, `match`, errors
- **[Functions](functions.md)**: parameters, returns, recursion
