# Standard Library

Crush's "standard library" is a set of **capabilities** — dotted functions such
as `str.split` and `math.sqrt` — that the host registers. It is *not* a module
system: there is no `import std.io`, and `import` does not load anything yet
(crush-ast **CRUSH-110**). You call these functions by their full dotted name.

## Turning it on

Almost all of the library lives behind a Cargo feature **and** a CLI flag:

1. Build the toolchain with the `stdlib` feature of `crush-lang-sdk`
   (`cargo build -p crush-lang-sdk --features stdlib`). It is **off by default**
   (crush-ast **CRUSH-113**); on a build without it, `--stdlib` only prints
   `warning: --stdlib requires the 'stdlib' feature`.
2. Run with `--stdlib`: `crush run --stdlib prog.crush`.

The examples in this chapter are all executed with `--stdlib`. These are
pure-computation capabilities — they do no I/O. For files, network, time and
processes see [Capability System](capabilities.md).

Arguments are positional and the arity is checked (`[runtime] str.replace takes 3
arg(s), got 2`). Note that some predicates return `1`/`0` rather than
`true`/`false` (for example `str.starts_with`, `regex.test`,
`collections.includes`), so compare with `== 1` rather than assuming a `Bool`.

## Strings — `str.*`

| Function | Result |
|---|---|
| `str.split(s, delim)` | array of parts |
| `str.join(array, delim)` | string |
| `str.trim(s)`, `str.trim_start(s)`, `str.trim_end(s)` | string |
| `str.replace(s, old, new)` | string |
| `str.contains(s, sub)`, `str.starts_with(s, p)`, `str.ends_with(s, p)` | truthy |
| `str.to_upper(s)`, `str.to_lower(s)` | string |
| `str.pad_left(s, width, fill)`, `str.pad_right(s, width, fill)` | string |
| `str.repeat(s, n)` | string |
| `str.substring(s, start, end)` | string (`end` exclusive) |
| `str.char_at(s, i)`, `str.index_of(s, sub)` | one-char string / index |
| `str.format(template, args)` | `{}` placeholders filled from `args` |

`str.concat(...)` and `str.len(s)` are always available, even without `--stdlib`.

```crush
print(str.split("a,b,c", ","))
print(str.join(["a", "b"], "-"))
print("[" + str.trim("  x  ") + "]")
print(str.replace("hello world", "world", "crush"))
print(str.to_upper("abc"))
print(str.pad_left("7", 3, "0"))
print(str.repeat("ab", 3))
print(str.substring("hello", 1, 3))
print(str.index_of("hello", "l"))
```

<!-- check: output -->
```text
[a, b, c]
a-b
[x]
hello crush
ABC
007
ababab
el
2
```

(Arrays print as `[a, b, c]` — strings inside an array are shown unquoted.)

## Math — `math.*`

`math.sqrt`, `math.abs`, `math.floor`, `math.ceil`, `math.round`, `math.sin`,
`math.cos`, `math.tan`, `math.pow(base, exp)`, `math.min(a, b)`, `math.max(a, b)`,
`math.pi()`. Results are `Float`. `math.random()`, `math.random_int(lo, hi)`
(requires `lo < hi`) and `math.seed(n)` use a deterministic built-in generator
(crush-ast CRUSH-116), so seeded runs are reproducible.

```crush
print(math.sqrt(16))
print(math.pow(2, 10))
print(math.floor(-1.5))
print(math.round(3.6))
print(math.max(2.5, 1))
```

<!-- check: output -->
```text
4.0
1024.0
-2.0
4.0
2.5
```

## Conversion — `conv.*`

`conv.to_int`, `conv.to_float`, `conv.to_str`, `conv.to_bool`,
`conv.parse_int(text, radix)`, `conv.parse_float`, `conv.type_of`, plus the
always-on `conv.chr` / `conv.ord`.

```crush
print(conv.to_int("42") + 1)
print(conv.to_int(3.9))
print(conv.parse_int("ff", 16))
print(conv.parse_int("101", 2))
print(conv.to_float("2"))
print(conv.type_of(3.5))
```

<!-- check: output -->
```text
43
3
255
5
2.0
float
```

## Collections — `collections.*`

`collections.len`, `reverse`, `includes`, `flatten`, `chunk(array, n)`, `zip`,
`unique`, `all`, `any`, `find`, `sort_by(array, key)`, `pluck(array, key)`,
and for objects: `keys`, `values`, `entries`, `merge`.

```crush
let scores = {"ada": 3, "grace": 5}
print(collections.keys(scores))
print(collections.values(scores))
print(collections.keys(collections.merge(scores, {"linus": 1})))
print(collections.reverse([1, 2, 3]))
print(collections.chunk([1, 2, 3, 4], 2))
print(collections.unique([1, 1, 2, 2, 3]))
```

<!-- check: output -->
```text
[ada, grace]
[3, 5]
[ada, grace, linus]
[3, 2, 1]
[[1, 2], [3, 4]]
[1, 2, 3]
```

`collections.keys(obj)` returns the keys **sorted**, and is how you iterate an
object deterministically — `for k in obj` isn't supported, and printing an object
directly lists its keys in an unspecified (per-run) order:

```crush
let m = {"a": 1, "b": 2}
for k in collections.keys(m) {
    print(k)
}
```

<!-- check: output -->
```text
a
b
```

## JSON — `json.*`

`json.parse(text)` → object/array/scalar; `json.stringify(value)`;
`json.stringify_pretty(value)`.

```crush
let o = json.parse("{\"name\": \"Ada\", \"n\": 3}")
print(o.name)
print(o.n + 1)
print(json.stringify({"x": 1}))
```

<!-- check: output -->
```text
Ada
4
{"x":1}
```

## Paths — `path.*`

`path.join(a, b)`, `dirname`, `basename`, `extension`, `stem`, `is_absolute`,
`normalize` — pure string manipulation, no filesystem access.

```crush
print(path.join("a", "b.txt"))
print(path.dirname("/x/y/z.txt"))
print(path.basename("/x/y/z.txt"))
print(path.stem("z.tar.gz"))
print(path.normalize("a/./b/../c"))
```

<!-- check: output -->
```text
a/b.txt
/x/y
z.txt
z.tar
a/c
```

## Regular expressions — `regex.*`

**The pattern comes first**, then the text: `regex.test(pattern, text)`,
`regex.find_all(pattern, text)`, `regex.replace(pattern, text, replacement)`,
`regex.split(pattern, text)`.

```crush
print(regex.find_all("[0-9]+", "a1b22"))
print(regex.replace("[0-9]", "a1b2", "#"))
print(regex.split("[,;] *", "a, b;c"))
```

<!-- check: output -->
```text
[1, 22]
a#b#
[a, b, c]
```

> **Known bug.** `regex.match` is registered but can't be called from source:
> `match` is a keyword, so `regex.match(...)` is a parse error (`Expected field
> name but found match`).

<!-- check: nyi GAP-KEYWORD-FIELD-NAMES -->
```crush
print(regex.match("([a-z]+)([0-9]+)", "abc123"))
```

## Other families

Also registered under `--stdlib`: `bytes.*` (`from_string`, `to_string`, `len`,
`slice`), `buffer.*` (`alloc`, `read`, `write`, `freeze`), `binary.read_*` /
`binary.write_*` (u16/u32/u64, big/little endian), `result.*` (`ok`, `err`,
`is_ok`, `unwrap` — results are plain `{ok, value}` objects), `text.sort`,
`text.uniq`, `time.format`, `time.parse`, `env.os`, `env.arch`, and the `system.*`
helpers implemented in Crush itself (`crates/crush-lang-sdk/sbl/`).

```crush
print(result.unwrap(result.ok(5)))
print(env.os())
```

<!-- check: output -->
```text
5
linux
```

(The second line depends on the machine running the example.)

## Not in the library

There is no `std.*` module tree, `io.eprint`, `sys.*`, `array.length` or
`map.*`. For output use `print`/`io.print`; for the process environment use
`env.get` (`--env`); for arguments, there is currently no accessor.

## Next Steps

- **[Capability System](capabilities.md)**
- **[Polyglot Programming](polyglot.md)**
