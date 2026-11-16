# Modules, Packages and Visibility

> Verified against crush-ast `7f3fef31` (main, 2026-11-16). Every behaviour on this
> page was run with that build. The programs live in the verified corpus,
> [`examples/verified/modules/`](https://github.com/nixpt/crush-language-guide/tree/main/examples/verified/modules),
> each with the modules it imports in a `NAME.files/` directory beside it, and
> `scripts/verify-examples` re-runs them.

A Crush program can be split over several files. `import` loads another `.crush`
file **at compile time** (crush-ast CRUSH-110): the compiler parses it and merges
its definitions into the program before checking it, so imported functions are
checked like your own, and the capability check sees imported code exactly as if
it were local. Nothing is loaded at run time, and no capability is involved.

Because an import needs a file to search from, it works when you compile or run a
file (`crush run`, `crush-run run`, `crushc`, `crush-debug`, the REPL from its
working directory). It does not work in the browser: the Run buttons in this book
compile a string, and an `import` there is refused with "`import x` was not
resolved: … this compile has no file path to search from". The examples on this
page are therefore shown, not runnable; their output is the corpus's.

## The three forms

Given `geom.crush` and `util/strings.crush` next to the program:

<!-- check: compile -->
```crush
// geom.crush
fn area(w, h) { return w * h }
fn scaled(x) { return __unit() * x }
fn __unit() { return 10 }
```

<!-- check: compile -->
```crush
// util/strings.crush
fn shout(s) { return str.to_upper(s) + "!" }
fn twice(s) { return s + s }
```

<!-- check: skip multi-file program: examples/verified/modules/import-forms -->
```crush
import geom
import util.strings as s
import util.strings { twice }
print(geom.area(3, 4))
print(geom.scaled(2))
print(s.shout("hi"))
print(twice("ab"))
let f = geom.area
print(f(2, 5))
```

```text
12
20
HI!
abab
10
```

| Form | Binds | Call |
|---|---|---|
| `import geom` | the qualifier `geom` (the last segment of the path) | `geom.area(3, 4)` |
| `import util.strings` | the qualifier `strings`; loads `util/strings.crush` | `strings.shout("hi")` |
| `import util.strings as s` | the qualifier `s` instead | `s.shout("hi")` |
| `import util.strings { twice }` | the bare name `twice` (and the qualifier only when `as x` is also given) | `twice("ab")` |

`geom.area` without a call is a function value, as for a local function. Inside a
module, a bare call finds the module's own functions first (`scaled` calls
`__unit` above), then the module's own imports, then the built-ins and
capabilities.

## What a module may contain

A module is **definitions only**: `fn`, `struct`, `impl`, `trait` (with `@kind`),
and `import`s of other modules. Its `main`, if it has one, is ignored. Any other
top-level statement is a compile error naming the file and line, so a module has
no init code and there is no hidden init order. Write a function for a constant
(`fn limit() { return 10 }`):

```text
[compile] state.crush:2:1: a top-level `let` in imported module `state`: a module may only define functions, structs, impls and traits, and import other Crush modules — it has no init code (move the statement into a function)
```

`export` is such a statement too: a module that contains `export f` is refused
(`a top-level statement in imported module`). Exporting is not how modules work
in Crush; see [Visibility](#visibility-and-pub) for what decides what another file
can call.

Imports go at the **top level** of a file. One inside a function is refused
(`` `import` inside `fn f`: imports go at the top level of a file ``).

> **Pitfall.** An `import` inside `fn main() { … }` is accepted and works at this
> commit, although crush-ast's import design says imports inside a function are
> refused. Don't rely on it; put imports at the top of the file. The corpus program
> `modules/import-in-main-pitfall` records the current behaviour.

## Where modules are found

`import a.b` looks for `a/b.crush`, in this order; the first hit wins:

1. the directory of the file that contains the `import`;
2. each `-L DIR` (`--lib-path`) given to `crush-run`, `crushc`, `crush-debug` or
   `crush-repl` (`crush run` and friends pass it on), in order;
3. each directory in `CRUSH_PATH` (colon-separated).

There is no `a/b/mod.crush` form. A module that is not found is a compile error
that lists every directory searched:

```text
[compile] main.crush:1:1: `import consts`: module not found — no consts.crush in any of:
  . (/home/me/proj)
  libdir (/home/me/proj/libdir)
```

```bash
crush-run run -L lib main.crush             # lib/text/greet.crush for `import text.greet`
CRUSH_PATH=shared crush-run run main.crush   # shared/consts.crush for `import consts`
```

(Corpus: `modules/lib-path`, `modules/crush-path`, `modules/import-not-found`.)

Each file is loaded once per compile, so two modules that import a third share one
copy. Two modules that import each other are a compile error that shows the cycle
(`import cycle: ca.crush → cb.crush → ca.crush`).

## Errors that name the problem

A name the module does not define lists what it does define (names starting with
`__` are left out of the list):

```text
[compile] main.crush:5:7: `geom.perimeter`: module `geom` (geom.crush) defines no function `perimeter` (it defines: area, scaled)
```

A selectively imported name that collides with a function of the importing file
is refused, naming both:

```text
[compile] main.crush:3:1: `import geom { area }` collides with `fn area` (line 4) of the same name in this file
```

## Structs across files

A module's `struct`s and their methods work in the importer. Build values through
a function of the module: a struct **literal** is recognised only in the file that
declares the struct, so `Rect { w: 1, h: 2 }` in the importer is
`[compile] Undefined variable: Rect`.

<!-- check: compile -->
```crush
// shapes.crush
struct Rect { w: Int, h: Int }
impl Rect {
    fn area(self) { return self.w * self.h }
}
fn rect(w, h) { return Rect { w: w, h: h } }
```

<!-- check: skip multi-file program: examples/verified/modules/struct-from-module -->
```crush
import shapes
let r = shapes.rect(2, 3)
print(r)
print(r.area())
r.w = 10
print(r.area())
```

```text
{w: 2, h: 3}
6
30
```

Fields are public: the importer can read and write them (`r.w = 10` above).

### One namespace for struct and trait names

Function names are qualified by their module, but `struct` and `trait` names are
**one global namespace** across all the files of a program. The same name declared
in two files, whether two modules or a module and the file that imports it, is a
compile error that names both files (crush-ast #527):

<!-- check: compile -->
```crush
// plane.crush
struct Point { x: Int, y: Int }
fn origin() { return Point { x: 0, y: 0 } }
```

<!-- check: compile -->
```crush
// map.crush
struct Point { lat: Float, lon: Float }
fn here() { return Point { lat: 27.7, lon: 85.3 } }
```

<!-- check: skip multi-file program: examples/verified/modules/kind-clash -->
```crush
import plane
import map
print(plane.origin())
```

```text
[compile] map.crush:1:1: struct `Point` is also declared in plane.crush:1:1: struct and trait names are one global namespace across imports, so two files cannot both declare `Point` (rename one; per-module Kinds are planned, #523)
```

Before #527 this compiled, the later `Point` silently replaced the earlier one,
and `plane.origin()` failed at run time. Rename one of the two. A redeclaration
inside a single file is not covered by this rule. Per-module kind names are
planned (crush-ast #523).

## Packages

`crush-pkg` (crush-ast's package manager) builds a package from a `capsule.toml`.
`crush-pkg new NAME` scaffolds an application, `crush-pkg new NAME --lib` a library
whose entry is `src/lib.crush`. A package lists its dependencies as
`[[dependencies]]` rows with a `path` (a local directory) or a `git` source:

```toml
[capsule]
name = "app"
version = "0.1.0"
entry = "src/main.crush"
language = "crush"

[[dependencies]]
name = "mathlib"
path = "../mathlib"
```

When the entry file has an `import`, every dependency, and the package itself,
can be imported **by name** (crush-ast CRUSH-367): `import mathlib` loads the
dependency's entry file, and `import mathlib.extra` loads `extra.crush` in the
directory of that entry. The entry's own directory (`src/`) is searched for the
package's other files, as for any file. A package name wins over a file of the same
name on the search path.

<!-- check: skip a crush-pkg package: needs its capsule.toml and the mathlib dependency -->
```crush
// app/src/main.crush
import mathlib { greet }      // ../mathlib/src/lib.crush
import mathlib.extra          // ../mathlib/src/extra.crush
import util                   // src/util.crush

fn main() {
    print(greet("app"))
    print(extra.twice(21))
    print(util.shout("ok"))
}
```

```text
$ crush-pkg run
building app v0.1.0
  resolved dep mathlib -> …/mathlib/src/lib.crush
  …
running app v0.1.0
hello, app
42
ok!
```

This was run by hand at the pinned commit (the corpus runs `crush-run` only), with
`mathlib/src/lib.crush` as `crush-pkg new mathlib --lib` writes it
(`fn greet(who) { return "hello, " + who }`), `mathlib/src/extra.crush` defining
`twice`, and `app/src/util.crush` defining `shout`. Package names resolve only
through `crush-pkg`: `crush-run run src/main.crush` in the same directory says
`` `import mathlib`: module not found ``. An entry file with no `import` at all is
built the older way, with the dependencies' entry files pasted into one source.

## Visibility and `pub`

**Today every function of a module can be imported**, by qualified call or by a
selective import. Nothing is private.

- A leading `__` is a naming convention for "internal". It hides the name from
  the "it defines: …" lists in error messages, and that is all it does:
  `geom.__unit()` and `import geom { __unit }` both work
  (corpus `modules/private-convention`).
- **`pub fn`** (and `pub async fn`) is accepted and **not enforced**: the parser
  drops `pub`, so a function with `pub` and one without behave the same, in the
  file that declares them and from another file (crush-ast #518):

```crush
pub fn add(a, b) { return a + b }
fn sub(a, b) { return a - b }
print(add(2, 3))
print(sub(2, 3))
```

<!-- check: output -->
```text
5
-1
```

<!-- check: skip multi-file program: examples/verified/modules/pub-fn -->
```crush
// shapes.crush has `pub fn square(n)` and plain `fn cube(n)`
import shapes
print(shapes.square(3))
print(shapes.cube(2))
```

```text
9
8
```

- **`pub struct`** and **`pub trait`** do not parse yet. `pub` is not a keyword,
  so the compiler reads a variable named `pub` and refuses the program:

<!-- check: error -->
```crush
pub struct P { x: Int }
print(P { x: 1 })
```

```text
[compile] Undefined variable: pub
```

  `pub trait Shape { … }` gives the same error. A field cannot be marked `pub`
  either: in `struct P { pub x: Int }` the parser takes `pub` as the field's name.

### What is planned

This is **planned work, not present behaviour**. crush-ast's visibility design
(`docs/design/visibility-and-packages.md`) makes visibility per **package**:

- without `pub`, a function is visible to every file of its own package; `pub`
  exports it to other packages;
- the first step (crush-ast #519) records `pub`, accepts `pub struct` and
  `pub trait`, and makes a use of a non-`pub` function from another package a
  **warning**, `W-VIS01`; a module with no `pub` anywhere stays all-public then;
- the warning becomes an **error** before the 1.0 feature freeze of 2026-12-31
  (crush-ast #524).

So: mark the functions other packages should call with `pub` now. It costs
nothing today, and it is what the warning will check.

## Remote imports and other forms

`import @http "…"`, `import @git "…"`, `import @file "…"` and `use @mcp "…"` are
compile errors: they are not supported yet. `use @lang python "math"` is a
different thing that works: it writes `import math` into every later `@python`
block (see [Polyglot](polyglot.md)). See [Import Styles](../examples/imports.md)
for each form with its current result.
