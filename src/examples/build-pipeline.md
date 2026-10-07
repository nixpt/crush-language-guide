# Build Pipeline

Crush's intended role is a small, auditable *conductor* for other tools: it
decides what runs and in what order, while capability calls do the work. Here each
step is a real process started through `process.exec`, and the pipeline stops at
the first failure.

Run it with `crush run --stdlib --process build.crush`.

<!-- check: flags --process -->
```crush
// A tiny build pipeline: run each step as a process, stop at the first failure.
fn run_tool(cmd: String, arg: String) -> Int {
    let raw = process.exec(cmd, arg)
    let res = json.parse(raw)
    return res.exit_code
}

fn step(name: String, cmd: String, arg: String) -> Int {
    print("[start] " + name)
    let code = run_tool(cmd, arg)
    if code != 0 {
        print("[failed] " + name + " (exit " + code + ")")
        return code
    }
    print("[ok] " + name)
    return 0
}

fn main() {
    let steps = [["configure", "echo", "config"], ["compile", "echo", "cc"], ["test", "false", "x"], ["package", "echo", "tar"]]
    for s in steps {
        let code = step(s[0], s[1], s[2])
        if code != 0 {
            print("pipeline stopped")
            break
        }
    }
}
```

<!-- check: output -->
```text
[start] configure
[ok] configure
[start] compile
[ok] compile
[start] test
[failed] test (exit 1)
pipeline stopped
```

**What this shows:**

- **Capability-gated side effects.** `process.exec` only exists because of the
  `--process` flag; without it the program fails with `unknown capability:
  process.exec`.
- **Structured results.** `process.exec(cmd, arg)` returns a JSON string with
  `exit_code`, `stdout` and `stderr`; `json.parse` turns it into an object.
- **Fail-fast.** `step` returns the exit code, `main` breaks out of the loop on
  the first non-zero one.
- **Data-driven steps.** The pipeline is an array of `[name, command, argument]`
  triples, indexed with `s[0]`, `s[1]`, `s[2]`.

`process.exec` takes exactly two arguments — the command and a single argument
string — so multi-argument commands need to be wrapped (`process.exec("sh", "make
-j8")` or similar). It runs with the full authority of the user, so enable
`--process` only for programs you trust.
