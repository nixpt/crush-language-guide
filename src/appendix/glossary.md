# Glossary

### AOT (ahead-of-time) backends
`crush-aot` and `crush-aotc` translate CASM to Rust or C source for native
compilation. They live in the crush-ast repository and are not published to
crates.io. They reject programs that use CASM instructions they do not support.

### Capability
A named host function that a Crush program may call, written as a dotted call
(`fs.read(path)`, `io.print(x)`). A capability exists only if the host registered it
(on the CLI, with a flag such as `--fs`) *and* the program's manifest lists it. There
is no ambient authority. See [Capabilities](../crush/capabilities.md).

### CAST (Crush AST)
The JSON abstract syntax tree between front ends and the compiler: produced by the
Crush parser and the language walkers, or written directly by an agent. See
[CAST](../cast/README.md).

### CASM (Crush Assembly)
The stack-machine instruction set programs compile to. The name covers the **IR**
(JSON, `casm::Program`), the **text assembly** (`.func`/`PUSH`/`CAP_CALL`, the
`.casm` files `crush-run` reads) and, one step down, the **CVM1** binary. See
[CASM](../casm/README.md).

### CVM1
The binary bytecode format the VM executes (`.cvm1`): magic `CVM1`, a version byte, a
JSON manifest, a constant pool and flat code. Also the name of the default
interpreter. See [Program Structure](../casm/structure.md#the-cvm1-binary).

### Embedder / host
The program that runs Crush code and decides which capabilities and quotas it gets —
the `crush-run` CLI, or your own Rust program using `crush-lang-sdk`.

### FastVM
A second interpreter in `crush-vm`, lowered from the IR with pre-resolved symbols,
aimed at loops with many iterations. Slower than CVM1 on tiny programs.

### Gate
A check that refuses an operation unless it was enabled. Examples: the `--polyglot`
flag for `@lang` blocks; the manifest check on `CAP_CALL`; the `ai_native.*`
capability names that guard the AI opcodes.

### Lowering
Turning one representation into the next: CAST → CASM IR (the compiler), and
CASM IR → CVM1 (`casm_to_vm`). Lowering can lose information; the
[instruction reference](../casm/instructions.md#what-lowers-to-cvm1) lists what.

### Manifest
The list of capability names a program may call (`{"permissions": [...]}`), carried
in the CASM IR and in the CVM1 header. Checked on every `CAP_CALL`.

### Polyglot block
A `@python { }`, `@javascript { }` or `@bash { }` block inside a Crush program. It
runs in a host subprocess, with free variables marshalled in and assigned variables
marshalled out. Needs `--polyglot`. See [Polyglot](../crush/polyglot.md).

### Quota
A resource limit the VM enforces: instruction count, stack slots, output bytes, call
depth, and wall-clock time per polyglot subprocess.

### Sandboxed polyglot
An optional, off-by-default, Linux-only build feature (`crush-vm`'s
`sandboxed-polyglot`) that runs polyglot blocks under bubblewrap, provisioning
interpreters and dependencies with `buckets`. Without it, polyglot blocks have the
host process's full authority.

### SDK (`crush-lang-sdk`)
The Rust crate to embed Crush: `Runtime`, `HostCapsBuilder`, `ProgramBuilder`, and the
`compile` module. It also provides the `crush`, `crushc`, `crush-run`, `crush-compile`,
`crush-repl` and `crush-diff` binaries.

### Slot
A numbered local variable in a CVM1 call frame (`LOAD 3`, `STORE 3`). The IR names
variables; lowering assigns slots.

### Stub
An implemented interface with placeholder behaviour. The `ai_*`, `dom_*` and
`spawn`/`yield`/`await` instructions are stubs today. See
[AI-Native CAST](../cast/ai-native.md#what-actually-runs).

### Walker
A front end that translates source in some language into CAST (Python, JavaScript,
Bash and others, in `crush-lang-*` crates). Coverage varies by language; walkers are
not the same thing as `@lang` execution — only Python, JavaScript and Bash blocks can
actually run.
