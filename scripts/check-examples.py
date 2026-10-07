#!/usr/bin/env python3
"""Validate every ```crush block in src/ through the real crush-ast pipeline.

Usage:
    scripts/check-examples.py [--bin-dir DIR] [--report] [-v] [FILE.md ...]

Pipeline per block: `crushc -C` (parse + semantic check + compile), then, unless
the block says otherwise, `crush-run run` (execute) in a scratch directory with
a step budget and a wall-clock timeout.

Binaries come from --bin-dir, $CRUSH_BIN_DIR, or PATH. Build them from
crush-ast with `cargo build -p crush-lang-sdk` (see scripts/README.md).

A block may carry a directive in an HTML comment on the line(s) directly above
its opening fence (invisible in the rendered book):

    <!-- check: run -->            compile + execute, must exit 0 (the default)
    <!-- check: compile -->        compile only (needs host state / is a fragment)
    <!-- check: error -->          must FAIL to compile (the page shows an error)
    <!-- check: nyi CRUSH-NN -->   not yet implemented in crush-ast; expected to fail
    <!-- check: skip <reason> --> not a standalone program (pseudo-code, diff, ...)
    <!-- check: flags --time --net -->   extra crush-run flags (combine with run)
    <!-- check: stdin <text> -->   feed this text to stdin

Directives combine on separate comment lines. Exit status is non-zero if any
block misbehaves relative to its directive (an `nyi` block that starts working
is also flagged, so the marker gets removed).
"""
import argparse, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
FENCE = re.compile(r"^```(\S*)\s*$")
DIRECTIVE = re.compile(r"^\s*<!--\s*check:\s*(\w+)\s*(.*?)\s*-->\s*$")


def extract(md: Path):
    lines = md.read_text().splitlines()
    i = 0
    pending = {}
    while i < len(lines):
        line = lines[i]
        m = DIRECTIVE.match(line)
        if m:
            pending[m.group(1)] = m.group(2)
            i += 1
            continue
        m = FENCE.match(line)
        if m and m.group(1) == "crush":
            start = i + 1
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            yield {"file": md, "line": start + 1, "code": "\n".join(lines[start:j]) + "\n", "d": pending}
            pending = {}
            i = j + 1
            continue
        if m or line.strip():
            if m:  # some other fenced block: skip it entirely
                j = i + 1
                while j < len(lines) and not lines[j].startswith("```"):
                    j += 1
                i = j
            pending = {}
        i += 1


def run(cmd, cwd, timeout, stdin=""):
    try:
        p = subprocess.run(cmd, cwd=cwd, input=stdin, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr)
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT"


def check(block, bins, tmp):
    d = block["d"]
    if "skip" in d:
        return "skipped", d["skip"]
    work = Path(tmp)
    src = work / "block.crush"
    src.write_text(block["code"])
    rc, out = run([bins["crushc"], "-C", str(src)], work, 30)
    if "error" in d:
        return ("green", "fails to compile as documented") if rc != 0 else ("fail", "expected a compile error, but it compiled")
    if "nyi" in d:
        ok = rc == 0 and "compile" in d or False
        if rc == 0:
            if "compile" in d:
                return "nyi", d["nyi"]
            rc2, out2 = run([bins["crush-run"], "run", *d.get("flags", "").split(), "--max-steps", "5000000", str(src)], work, 20, d.get("stdin", ""))
            return ("fail", f"marked nyi ({d['nyi']}) but it runs now") if rc2 == 0 else ("nyi", d["nyi"])
        return "nyi", d["nyi"]
    if rc != 0:
        return "fail", "compile: " + out.strip().splitlines()[0] if out.strip() else "compile failed"
    if "compile" in d:
        return "green", "compiles (compile-only)"
    flags = ["--stdlib", "--fs-root", str(work)] + d.get("flags", "").split()
    rc, out = run([bins["crush-run"], "run", *flags, "--max-steps", "5000000", str(src)], work, 20, d.get("stdin", ""))
    if rc != 0:
        last = out.strip().splitlines()
        return "fail", "run: " + (last[0] if last else f"exit {rc}")
    return "green", "runs"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bin-dir", default=os.environ.get("CRUSH_BIN_DIR"))
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("files", nargs="*")
    a = ap.parse_args()
    bins = {}
    for n in ("crushc", "crush-run"):
        p = (Path(a.bin_dir) / n) if a.bin_dir else shutil.which(n)
        if not p or not Path(p).exists():
            sys.exit(f"missing binary {n} (set --bin-dir / CRUSH_BIN_DIR, or put crush-ast's build on PATH)")
        bins[n] = str(p)
    files = [Path(f).resolve() for f in a.files] or sorted(SRC.rglob("*.md"))
    counts, bad = {}, []
    for md in files:
        for b in extract(md):
            with tempfile.TemporaryDirectory() as tmp:
                status, msg = check(b, bins, tmp)
            counts[status] = counts.get(status, 0) + 1
            rel = f"{b['file'].relative_to(ROOT)}:{b['line']}"
            if status == "fail":
                bad.append((rel, msg))
            if a.verbose or status == "fail":
                print(f"{status:8} {rel}  {msg}")
    total = sum(counts.values())
    print("\n" + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) + f"  (total {total})")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
