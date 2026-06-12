# Build Pipeline

> Source: `crates/core/crush-lang/examples/build_pipeline.crush`
> Donated from `nixpt/nakshatra` — used in production via `crush-run`.

This is Crush in its intended design role: a **capability-gated, event-sourced conductor**
for external toolchains. Crush doesn't compile anything itself — it orchestrates native tools
through capability calls, making the pipeline auditable and policy-checkable instead of an
opaque shell script.

```crush
// Stub capability-bound host calls (in production these bind to
// process.spawn / event.emit capabilities and compile to cap_call).
fn run_tool(cmd: String) -> Int { return 0 }
fn emit(topic: String, name: String) -> Int { return 0 }

// Run one build step: emit start event, run the tool,
// emit success or failure, propagate the exit code.
fn step(name: String, cmd: String) -> Int {
    emit("build.step.start", name)
    let code = run_tool(cmd)
    if code != 0 {
        emit("build.step.failed", name)
        return code
    }
    emit("build.step.ok", name)
    return 0
}

fn main() -> Int {
    emit("build.start", "kernel")

    // 1. Configure
    let c1 = step("config", "cp config/kernel.config kernel/.config")
    if c1 != 0 { return c1 }

    let c2 = step("olddefconfig", "make -C kernel olddefconfig")
    if c2 != 0 { return c2 }

    // 2. Compile (Crush conducts; gcc/Kbuild does the actual work)
    let c3 = step("kernel", "make -C kernel -j8 bzImage")
    if c3 != 0 { return c3 }

    // 3. Build initramfs
    let c4 = step("initramfs", "mkinitramfs --out build/init.cpio.gz")
    if c4 != 0 { return c4 }

    // 4. Smoke-boot in QEMU
    let c5 = step("boot", "qemu-run --kernel kernel/arch/x86/boot/bzImage --initrd build/init.cpio.gz")
    if c5 != 0 { return c5 }

    emit("build.done", "kernel")
    return 0
}

main()
```

**Patterns demonstrated:**

- **Multi-function decomposition** — `step()` encapsulates the emit-run-check pattern
- **Fail-fast via exit code propagation** — `if code != 0 { return code }` short-circuits
- **Event sourcing** — every step emits start/ok/failed events; the stream is replayable
- **Capability-bound host calls** — `run_tool` and `emit` are stubs here; in production
  they compile to `cap_call` against `process.spawn` and `event.emit` capabilities
- **Self-contained example** — stubs replace real caps so the file runs without host wiring

**Grammar note from the source file:**
> `spawn` is a RESERVED keyword (actor concurrency) — name process-spawning helpers
> differently (e.g. `run_tool`). Statements are newline-terminated: no multi-line calls,
> no list literals across lines.
