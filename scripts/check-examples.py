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

A ```text block introduced by `<!-- check: output -->` is the expected stdout
of the crush block above it (compared after trimming trailing whitespace).

Exit status is non-zero if any block misbehaves relative to its directive.
"""
import argparse, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
FENCE = re.compile(r"^```(\S*)\s*$")
DIRECTIVE = re.compile(r"^\s*<!--\s*check:\s*(\w+)\s*(.*?)\s*-->\s*$")


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
            if m.group(1) == "crush":
                last = {"file": md, "line": i + 2, "code": body, "d": pending, "expect": None}
                yield last
            elif m.group(1) == "text" and "output" in pending and last is not None:
                last["expect"] = body
            pending = {}
            i = j + 1
            continue
        if line.strip():
            pending, last = {}, None
        i += 1


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
        for b in list(extract(md)):
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
