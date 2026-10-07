# System Info Report

Crush as a *conductor*: gather facts from the host through capability calls, then
assemble them. The program needs three capability groups, so it is run with
`crush run --stdlib --env --time sysinfo.crush`; with any flag missing, the
corresponding call fails with `unknown capability`.

<!-- check: flags --env --time -->
```crush
// Gather host facts through capabilities and render a small report.
let os = env.os()
let arch = env.arch()
let home = env.get("HOME")
let lines = ["System report", "-------------", "os:   " + os, "arch: " + arch]
print(str.join(lines, "\n"))
if home != null {
    print("home is set")
}
print("clock ok: " + (time.now() > 0))
```

<!-- check: output -->
```text
System report
-------------
os:   linux
arch: x86_64
home is set
clock ok: true
```

(The `os` and `arch` lines depend on the machine that runs the example.)

**What this shows:**

- `env.os()` / `env.arch()` (`--stdlib`), `env.get(name)` (`--env`, returns `null`
  when the variable is unset), `time.now()` (`--time`) — each group is
  deny-by-default
- `str.join(array, delimiter)` to assemble text
- `"label" + (expression)` concatenation with a `Bool` result
- Calls that don't exist yet: this page used to show `sys.hostname()`,
  `sys.cpu_usage()`, `sys.memory_info()` and a `capability system readonly`
  declaration. None of those exist in the runtime today; host metrics beyond
  `env.*` and `time.*` have to come from `process.exec` (see
  [Build Pipeline](build-pipeline.md)) or a polyglot block.
