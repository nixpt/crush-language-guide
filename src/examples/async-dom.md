# Polyglot Pipeline

The same data, handled by the language best suited to each step, with Crush
variables as the glue. This replaces an earlier "Async LLM Dashboard" page whose
`dom.*`, `seahorse` and `async`/`await` calls do not run in the current
toolchain.

Run it with `crush run --polyglot poly.crush` (needs `python3`, `node` and `bash`
on `PATH`).

<!-- check: flags --polyglot -->
```crush
// Three languages, one program. Values flow through Crush variables.
let numbers = [3, 1, 4, 1, 5, 9, 2, 6]

@python {
import statistics
mean = statistics.mean(numbers)
}

@javascript {
const spread = Math.max(...numbers) - Math.min(...numbers)
}

let m = mean
let s = spread
@bash {
echo "mean=$m spread=$s"
}
print("")
print("done")
```

<!-- check: output -->
```text
mean=3.875 spread=8
done
```

**What this shows:**

- `@python`: reads the Crush variable `numbers`, and its last top-level binding,
  `mean`, becomes a Crush variable
- `@javascript`: the same protocol; `spread` comes back as a number
- `@bash`: receives the `let` variables declared before it as environment
  variables. Results of earlier blocks are not passed automatically, so they are
  copied into `let m = mean` / `let s = spread` first
- Block output is trimmed and has no trailing newline, which is why `print("")`
  is used to finish the line
- All three run as ordinary subprocesses with your user's authority — see
  [Polyglot Programming](../crush/polyglot.md#sandbox-and-authority)
