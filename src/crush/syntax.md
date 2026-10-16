# Syntax and Grammar

> Verified against crush-ast `aa07413` (2026-10-16): every runnable block on this
> page was compiled and run with that build.

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
and    or     not      true    false   null
```

`and`, `or` and `not` are keyword spellings of `&&`, `||` and `!`. `mut` and
`capability` are reserved, but `let mut x = ...` is **not** accepted (see
[Variables](variables.md)), and `capability` has no usable statement form yet.

`impl` and `trait` are **contextual** keywords: they start a declaration only at
the top level of a file (see [Structs, Methods and Kinds](structs.md)), so a
variable may still be called `impl`.

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
| Integer | `42`, `-7`, `0x2A`, `0b101` | hex and binary prefixes lex; `0o17` and `1_000` do not |
| Float | `3.14`, `0.5` | no exponent form (`1.5e3` is rejected) |
| String | `"hello"`, `'hello'` | single or double quotes; escapes `\n \t \" \\` |
| Boolean | `true`, `false` | |
| Null | `null` | |
| Array | `[1, 2, 3]` | see [Types](types.md) |
| Object | `{"a": 1, b: 2}` | see [Types](types.md) |

Triple-quoted strings are parse errors, and bytes literals (`b"..."`) are refused
with `bytes literals (b"...") are not supported yet`. A string literal may
contain a raw newline.

```crush
let n = 42
let pi = 3.14
let s = "tab:\there"
print(n)
print(pi)
print(s)
print(0x2A + 0b101)
print('single "quotes" work too')
```

<!-- check: output -->
```text
42
3.14
tab:	here
47
single "quotes" work too
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

An expression cannot continue onto the next line, **even inside `()`, `[]` or
`{}`**: the newline ends it, so a multi-line array, map or argument list is a parse
error (`unexpected token in expression: newline`). Keep such expressions on one
line, or build them with several statements. Blocks (`fn`/`if`/`while` bodies,
lambda bodies, `match` arms) do span lines.

<!-- check: error -->
```crush
let a = [1,
  2]
print(a)
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

Names resolve at **function level**, not per block: after a `let` inside an `if`
or loop body, the name refers to that binding for the rest of the function (see
[Variables](variables.md)). Each execution of a `let` does create a fresh
binding, which is what a [closure](closures.md) captures.

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
`== != < > <= >=`, `&& || !` (also spelled `and`, `or`, `not`), unary `-`, and the
pipeline `|>`. There is no `**`, `//`, `+=`/`-=`, or ternary `? :`.

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
for n in 1..=2 {
    print(n * 10)
}
```

<!-- check: output -->
```text
big
3
0
1
2
10
20
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

A block that sends values back to Crush names them after `->`:
`@python -> total { ... }`.

<!-- check: output -->
```text
Hello from Python
```

See [Polyglot Programming](polyglot.md) for the supported languages, how
variables cross the boundary, and the (important) security caveats.

## Imports and exports

`import a.b` **parses**, but importing does not load anything yet: `import` is
lowered to a `module.load` capability that nothing registers, so a program
containing one is refused before it runs (`not available in this host:
module.load`, crush-ast **CRUSH-110**). Every program is currently a single file.
There is no `std.*` module tree.

`use @lang python "math"` is different and does work: it writes `import math` into
every later `@python` block (see [Polyglot](polyglot.md#imports-for-blocks-use-lang)).

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

`@name` also introduces annotations:

- `@capabilities [fs.read, time.now_ms]` declares what the program may use, and
  the compiler enforces it ([Capability System](capabilities.md#declaring-what-a-program-uses-capabilities)).
- `@kind(...)` before a `struct` chooses its object semantics
  ([Structs, Methods and Kinds](structs.md#kind-choosing-object-semantics)).
- `@module`, `@decision`, `@invariant`, `@wip`, `@temporary`, `@errors` are
  metadata for tools and agents, attached to the next declaration; they don't
  change what the program does ([Annotations](annotations.md)).

## Style

- `snake_case` for functions and variables, `PascalCase` for structs.
- Four-space indentation; keep lines under ~100 characters.
- Omit semicolons unless you are putting two statements on one line.

## Grammar summary

This is the grammar the parser implements, simplified (from
`crates/crush-frontend/src/parser/mod.rs`):

```ebnf
program     = ( statement | impl_block | trait_def | annotation )* ;

statement   = let_stmt | fn_def | struct_def | if_stmt | while_stmt
            | for_stmt | return_stmt | break | continue
            | try_stmt | throw_stmt | export_stmt | import_stmt | use_stmt
            | lang_block | match_expr | expr_stmt ;

let_stmt    = "let" IDENT ( ":" type )? "=" expression ";"? ;
fn_def      = "async"? "fn" IDENT "(" params? ")" ( "->" type )? block ;
struct_def  = kind_annot? "struct" IDENT "{" ( IDENT ( ":" type )? ","? )* "}" ;  (* one line *)
kind_annot  = "@kind" "(" IDENT ":" value ( "," IDENT ":" value )* ")" ;
impl_block  = "impl" ( IDENT "for" )? IDENT "{" fn_def* "}" ;
trait_def   = "trait" IDENT "{" ( "fn" IDENT "(" params ")" ( ";" | block ) )* "}" ;
if_stmt     = "if" expression block ( "else" ( if_stmt | block ) )? ;
while_stmt  = "while" expression block ;
for_stmt    = "for" IDENT "in" expression block ;           (* a..b, a..=b, arrays, strings, maps *)
try_stmt    = "try" block "catch" IDENT block ;
throw_stmt  = "throw" expression ;
export_stmt = "export" IDENT ;
use_stmt    = "use" "@lang" IDENT STRING ( "as" IDENT )? ;
lang_block  = "@" IDENT ( "[" deps "]" )? ( "->" ( IDENT | "(" IDENT ( "," IDENT )* ")" ) )?
              "{" raw source "}" ;
block       = "{" statement* "}" ;

expression  = literal | IDENT | expression binop expression
            | unop expression | call | field | index | slice
            | lambda | struct_lit | "new" IDENT "(" ")" | IDENT "::" IDENT
            | match_expr | "spawn" call | "await" expression ;
lambda      = "|" params? "|" ( expression | block ) ;
struct_lit  = IDENT "{" ( IDENT ":" expression ","? )* "}" ;
match_expr  = "match" expression "{" ( pattern ( "=>" | "->" ) ( expression | block ) ","? )* "}" ;
pattern     = literal | IDENT | "_" | IDENT "{" ( IDENT ":" pattern ","? )* "}" ;
call        = IDENT "(" args? ")" | expression "." IDENT "(" args? ")" ;
```

A call's callee must be a name (or `value.method`): `fs[0](1)` and `f()(x)` are
parse errors today (crush-ast CRUSH-zorro-24).

## Next Steps

- **[Data Types](types.md)**: the type system and collections
- **[Closures](closures.md)** and **[Structs, Methods and Kinds](structs.md)**
- **[Variables](variables.md)**: declaration and scope
- **[Control Flow](control_flow.md)**: loops, `match`, errors
- **[Functions](functions.md)**: parameters, returns, recursion
