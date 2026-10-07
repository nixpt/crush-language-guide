#!/usr/bin/env python3
"""Validate every ```crush block in src/ through the real crush-ast pipeline.

Usage:
    scripts/check-examples.py [--bin-dir DIR] [-v] [FILE.md ...]

Pipeline per block: `crushc -C` (parse + semantic check + compile), then, unless
the block says otherwise, `crush-run run` (execute) in a scratch directory with
a step budget and a wall-clock timeout.

Binaries come from --bin-dir, $CRUSH_BIN_DIR, or PATH. Build them from
crush-ast with the command in scripts/README.md.

A block may carry directives in HTML comments on the lines directly above its
opening fence (invisible in the rendered book):

    <!-- check: run -->            compile + execute, must exit 0 (the default)
    <!-- check: compile -->        compile only (needs host state / is a fragment)
    <!-- check: error -->          must FAIL to compile (the page shows an error)
    <!-- check: runfail <text> -->  compiles, but must fail at run time with
                                   <text> in its error output
    <!-- check: nyi CRUSH-NN -->   not yet implemented in crush-ast; must fail,
                                   and is flagged the day it starts working
    <!-- check: skip <reason> -->  not a standalone program (pseudo-code, ...)
    <!-- check: flags --time --net -->   extra crush-run flags
    <!-- check: stdin <text> -->   feed this text to stdin

With --crush-ast DIR (a crush-ast checkout, with `buckets` beside it), the
```rust,no_run blocks are also compiled and run against that checkout's
`crush-lang-sdk` (they are the embedding examples; each must exit 0).

Other checked fences (all optional-directive blocks run the same way):

    ```casm                          CVM1 text assembly: `crush-run run --cap io.print`
    <!-- check: casm-json -->        a ```json block: JSON CASM, loaded through
                                     casm::Program::deserialize, lowered and run
    <!-- check: cast-json -->        a ```json block: JSON CAST, validated, compiled, run
    <!-- check: cast-validate -->    a ```json block: JSON CAST that must validate, compile and lower (not run)
    <!-- check: cast-load-fails TEXT -->  JSON CAST that the version-gated loader rejects
    <!-- check: casmb-fails TEXT -->  JSON CASM whose .casmb (MessagePack) round trip fails
    <!-- check: asm-ai -->           a ```casm block run with the ai_native.* stub gates on
    (the json forms need --crush-ast, like the rust blocks: they use a helper
    built from scripts/casm-check/main.rs against that checkout)

A ```text block introduced by `<!-- check: output -->` is the expected stdout
of the crush block above it (compared after trimming trailing whitespace).

Exit status is non-zero if any block misbehaves relative to its directive.
"""
import argparse, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
FENCE = re.compile(r"^```(\S*)\s*$")
DIRECTIVE = re.compile(r"^\s*<!--\s*check:\s*([\w-]+)\s*(.*?)\s*-->\s*$")


def fence_end(lines, i):
    j = i + 1
    while j < len(lines) and not lines[j].startswith("```"):
        j += 1
    return j


def extract(md: Path):
    lines = md.read_text().splitlines()
    i, pending, last = 0, {}, None
    while i < len(lines):
        line = lines[i]
        m = DIRECTIVE.match(line)
        if m:
            pending[m.group(1)] = m.group(2)
            i += 1
            continue
        m = FENCE.match(line)
        if m:
            j = fence_end(lines, i)
            body = "\n".join(lines[i + 1 : j]) + "\n"
            lang = m.group(1)
            kind = lang if lang in ("crush", "casm") else None
            if lang == "json":
                kind = next((k for k in ("casmb-fails", "cast-load-fails", "casm-json", "cast-json", "cast-validate") if k in pending), None)
            if kind:
                last = {"file": md, "line": i + 2, "code": body, "d": pending, "expect": None, "kind": kind}
                yield last
            elif m.group(1) == "text" and "output" in pending and last is not None:
                last["expect"] = body
            pending = {}
            i = j + 1
            continue
        if line.strip():
            pending, last = {}, None
        i += 1


def extract_rust(md: Path):
    lines = md.read_text().splitlines()
    i = 0
    while i < len(lines):
        m = FENCE.match(lines[i])
        if m:
            j = fence_end(lines, i)
            if m.group(1) == "rust,no_run":
                yield {"file": md, "line": i + 2, "code": "\n".join(lines[i + 1 : j]) + "\n"}
            i = j + 1
            continue
        i += 1


CARGO_TOML = """[package]
name = "guide-embed-check"
version = "0.0.0"
edition = "2024"

[dependencies]
crush-lang-sdk = {{ path = "{sdk}", features = ["stdlib"] }}
casm = {{ path = "{casm}" }}
crush-cast = {{ path = "{cast}" }}
crush-frontend = {{ path = "{frontend}" }}
serde_json = "1"
anyhow = "1"

[workspace]
"""


def check_rust(block, crush_ast, tmp):
    work = Path(tmp)
    (work / "src").mkdir()
    (work / "Cargo.toml").write_text(CARGO_TOML.format(sdk=Path(crush_ast).resolve() / "crates" / "crush-lang-sdk", casm=Path(crush_ast).resolve() / "crates" / "casm", cast=Path(crush_ast).resolve() / "crates" / "crush-cast", frontend=Path(crush_ast).resolve() / "crates" / "crush-frontend"))
    (work / "src" / "main.rs").write_text(block["code"])
    rc, out, err = run(["cargo", "run", "--quiet"], work, 1800)
    if rc != 0:
        tail = [l for l in (out + err).splitlines() if l.strip()][-3:]
        return "fail", "cargo run: " + " | ".join(tail)
    return "green", "compiles and runs"


HELPER_TOML = """[package]
name = "casm-check"
version = "0.0.0"
edition = "2024"

[[bin]]
name = "casm-check"
path = "main.rs"

[dependencies]
crush-lang-sdk = {{ path = "{crates}/crush-lang-sdk" }}
casm = {{ path = "{crates}/casm" }}
crush-cast = {{ path = "{crates}/crush-cast" }}
crush-frontend = {{ path = "{crates}/crush-frontend" }}
anyhow = "1"
serde_json = "1"

[workspace]
"""


def build_helper(crush_ast, tmp):
    work = Path(tmp)
    (work / "Cargo.toml").write_text(HELPER_TOML.format(crates=Path(crush_ast).resolve() / "crates"))
    shutil.copy(ROOT / "scripts" / "casm-check" / "main.rs", work / "main.rs")
    rc, out, err = run(["cargo", "build", "--quiet"], work, 3600)
    if rc != 0:
        sys.exit("could not build scripts/casm-check against " + str(crush_ast) + ":\n" + err[-2000:])
    target = Path(os.environ.get("CARGO_TARGET_DIR") or work / "target")
    return str(target / "debug" / "casm-check")


def check_assembly(block, bins, work):
    """```casm and the json CASM/CAST forms: compare output, honour check: skip."""
    d, kind = block["d"], block["kind"]
    if "skip" in d:
        return "skipped", d["skip"]
    src = work / ("block.casm" if kind == "casm" else "block.json")
    src.write_text(block["code"])
    if kind == "casm" and "asm-ai" not in d:
        flags = ["--cap", "io.print"] + d.get("flags", "").split()
        rc, out, err = run([bins["crush-run"], "run", *flags, str(src)], work, 20, d.get("stdin", ""))
    else:
        if "casm-check" not in bins:
            return "skipped", "needs --crush-ast (json CASM/CAST helper)"
        mode = "asm-ai" if kind == "casm" else {"casm-json": "casm", "cast-json": "cast", "cast-validate": "castvalidate", "cast-load-fails": "castload", "casmb-fails": "casmb"}[kind]
        rc, out, err = run([bins["casm-check"], mode, str(src)], work, 60)
    if kind in ("cast-load-fails", "casmb-fails"):
        want = d[kind]
        if rc == 0:
            return "fail", "expected the loader to reject this, but it loaded (remove the marker)"
        return ("green", f"loader rejects it ({want})") if want in out + err else ("fail", f"rejection lacks {want!r}: {first_line(out + err)}")
    if "runfail" in d:
        if rc == 0:
            return "fail", "expected a run-time failure, but it ran fine"
        return ("green", "fails as documented") if d["runfail"] in out + err else ("fail", f"failure lacks {d['runfail']!r}: {first_line(out + err)}")
    if rc != 0:
        return "fail", "run: " + (first_line(out + err) or f"exit {rc}")
    if block["expect"] is not None and out.rstrip() != block["expect"].rstrip():
        return "fail", f"output mismatch: got {out.rstrip()!r}, page says {block['expect'].rstrip()!r}"
    return "green", "runs" + (" + output matches" if block["expect"] is not None else "")


def run(cmd, cwd, timeout, stdin=""):
    try:
        p = subprocess.run(cmd, cwd=cwd, input=stdin, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "TIMEOUT"


def first_line(s):
    s = s.strip().splitlines()
    return s[0] if s else ""


def runs_ok(block, bins, work, src):
    d = block["d"]
    flags = ["--stdlib", "--fs-root", str(work)] + d.get("flags", "").split()
    return run([bins["crush-run"], "run", *flags, "--max-steps", "5000000", str(src)], work, 20, d.get("stdin", ""))


def check(block, bins, tmp):
    d = block["d"]
    if block["kind"] != "crush":
        return check_assembly(block, bins, Path(tmp))
    if "skip" in d:
        return "skipped", d["skip"]
    work = Path(tmp)
    src = work / "block.crush"
    src.write_text(block["code"])
    rc, out, err = run([bins["crushc"], "-C", str(src)], work, 30)
    if "error" in d:
        return ("green", "fails to compile, as documented") if rc != 0 else ("fail", "expected a compile error, but it compiled")
    if "nyi" in d:
        if rc == 0 and "compile" not in d:
            rc, out, err = runs_ok(block, bins, work, src)
        return ("fail", f"marked nyi ({d['nyi']}) but it works now; remove the marker") if rc == 0 else ("nyi", d["nyi"])
    if rc != 0:
        return "fail", "compile: " + first_line(out + err)
    if "compile" in d:
        return "green", "compiles (compile-only)"
    rc, out, err = runs_ok(block, bins, work, src)
    if "runfail" in d:
        if rc == 0:
            return "fail", "expected a run-time failure, but it ran fine"
        want = d["runfail"]
        return ("green", f"fails at run time ({want})") if want in out + err else ("fail", f"run-time failure lacks {want!r}: {first_line(out + err)}")
    if rc != 0:
        return "fail", "run: " + (first_line(out + err) or f"exit {rc}")
    if block["expect"] is not None and out.rstrip() != block["expect"].rstrip():
        return "fail", f"output mismatch: got {out.rstrip()!r}, page says {block['expect'].rstrip()!r}"
    return "green", "runs" + (" + output matches" if block["expect"] is not None else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bin-dir", default=os.environ.get("CRUSH_BIN_DIR"))
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--crush-ast", default=os.environ.get("CRUSH_AST_DIR"), help="crush-ast checkout, to build the rust embedding examples")
    ap.add_argument("files", nargs="*")
    a = ap.parse_args()
    bins = {}
    for n in ("crushc", "crush-run"):
        p = (Path(a.bin_dir) / n) if a.bin_dir else shutil.which(n)
        if not p or not Path(p).exists():
            sys.exit(f"missing binary {n} (set --bin-dir / CRUSH_BIN_DIR, or put crush-ast's build on PATH)")
        bins[n] = str(p)
    files = [Path(f).resolve() for f in a.files] or sorted(SRC.rglob("*.md"))
    if a.crush_ast:
        helper_dir = tempfile.mkdtemp(prefix="casm-check-")
        bins["casm-check"] = build_helper(a.crush_ast, helper_dir)
    counts, bad = {}, []
    for md in files:
        for b in list(extract(md)):
            with tempfile.TemporaryDirectory() as tmp:
                status, msg = check(b, bins, tmp)
            counts[status] = counts.get(status, 0) + 1
            rel = f"{b['file'].relative_to(ROOT)}:{b['line']}"
            if status == "fail":
                bad.append((rel, msg))
            if a.verbose or status == "fail":
                print(f"{status:8} {rel}  {msg}")
    for md in files:
        for b in list(extract_rust(md)):
            rel = f"{md.relative_to(ROOT)}:{b['line']}"
            if not a.crush_ast:
                status, msg = "skipped", "rust block: no --crush-ast checkout given"
            else:
                with tempfile.TemporaryDirectory() as tmp:
                    status, msg = check_rust(b, a.crush_ast, tmp)
            counts[status] = counts.get(status, 0) + 1
            if status == "fail":
                bad.append((rel, msg))
            if a.verbose or status == "fail":
                print(f"{status:8} {rel}  {msg}")
    total = sum(counts.values())
    print("\n" + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) + f"  (total {total})")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
