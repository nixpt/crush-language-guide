#!/usr/bin/env python3
"""mdBook preprocessor: mark every ```crush block with what the browser can do with it.

The book's Run / Edit buttons (interactive/crush-run.js) need to know, per block,
whether it can run in the browser (crush-web: a fresh VM per run, only `print`
granted, no stdlib modules, no stdin), whether it is *meant* to fail, or whether
it needs the host. That is derived here, at build time, from the same directives
and block contents scripts/check-examples.py uses — nothing is hand-labelled, and
the Markdown stays the only source.

Each ```crush block is wrapped in

    <div class="crush-block" data-crush="run|fail|host|none" data-why="..."
         data-expect="..." data-expect-error="..." data-src="crush/types.md:91">

which is invisible without JavaScript (the code block renders exactly as before).

    data-crush=run    runs in the browser; data-expect is the checker-verified output
    data-crush=fail   meant to fail (compile error, documented refusal, not yet
                      implemented); Run demonstrates the failure
    data-crush=host   needs something the browser does not grant (polyglot, fs, net,
                      env, time, process, stdlib modules, stdin); labelled, no Run
    data-crush=none   not a standalone program (fragment, needs special setup)

Usage:
    mdbook build                                   (book.toml runs this as a preprocessor)
    scripts/mdbook-crush-run.py --manifest         every block's classification as JSON
                                                   (scripts/check-browser.mjs verifies it
                                                   against the real crush-web build)
"""
import html, importlib.util, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("check_examples", ROOT / "scripts" / "check-examples.py")
checker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(checker)

# What crush-web (crush-ast 4e9c388, src/play/pkg) handles itself: crush_vm::run's
# built-in capabilities (crates/crush-vm/src/scheduler.rs). `io.read` is there but
# always returns "" (no stdin in a browser), so it is treated as a host need below.
BROWSER_CAPS = {"io.print", "str.concat", "str.contains", "str.join", "str.len",
                "str.replace", "str.split", "conv.chr", "conv.ord"}
# Capability namespaces that need a host grant (`crush-run` flags, or `--stdlib`
# for the standard-library modules). scripts/check-browser.mjs proves each such
# block really fails in crush-web, so a stale list shows up as a failure.
HOST_CAPS = {
    "fs": "the filesystem", "file": "the filesystem", "net": "the network",
    "env": "the environment", "time": "the clock", "process": "processes",
    "db": "a database", "graphics": "graphics", "system": "the host system",
}
STDLIB = ("str", "text", "math", "conv", "collections", "json", "path", "regex",
          "result", "bytes", "binary", "buffer", "crypto")
CALL = re.compile(r"(?<![\w.])([a-z_]+)\.([a-z_][a-z_0-9]*)\s*\(")
POLYGLOT = re.compile(r"@(python|javascript|js|bash|sh|rust|ruby|lua|go)\b")
FLAG_WHY = {"--polyglot": "polyglot blocks", "--fs": "the filesystem", "--net": "the network",
            "--env": "the environment", "--time": "the clock", "--process": "processes"}


def host_needs(d, code):
    """What this block needs from the host that the browser cannot give, as short phrases."""
    needs, flags = [], d.get("flags", "").split()
    langs = sorted(set(POLYGLOT.findall(code)))
    if "--polyglot" in flags and langs:
        needs.append("uses " + ", ".join(f"`@{l}`" for l in langs) + " blocks (polyglot)")
    calls = {}
    for ns, fn in CALL.findall(code):
        if ns == "io" and fn == "read":
            calls.setdefault("stdin", []).append("io.read")
        elif (ns in HOST_CAPS or ns in STDLIB) and f"{ns}.{fn}" not in BROWSER_CAPS:
            calls.setdefault(ns, []).append(f"{ns}.{fn}")
    if "stdin" in d and "stdin" not in calls:
        calls["stdin"] = ["io.read"]
    host_ns = [ns for ns in calls if ns in HOST_CAPS]
    granted = {f for f in flags if f in FLAG_WHY} | {"--fs" for f in flags if f.startswith("fs.")}
    if host_ns:
        uniq = sorted({c for ns in host_ns for c in calls[ns]})
        needs.append("uses " + ", ".join(f"`{c}`" for c in uniq[:4]) + (" …" if len(uniq) > 4 else ""))
    elif granted - {"--polyglot"} or ("--polyglot" in flags and not langs):
        needs.append("needs " + ", ".join(sorted(FLAG_WHY[f] for f in granted)))
    lib = sorted({c for ns in calls if ns in STDLIB for c in calls[ns]})
    if lib:
        needs.append("uses the standard library (" + ", ".join(f"`{c}`" for c in lib[:3]) + (" …" if len(lib) > 3 else "") + ")")
    if "stdin" in calls:
        needs.append("reads standard input (`io.read`)")
    return needs


def classify(block):
    """(kind, why) for one extracted ```crush block."""
    d, code = block["d"], block["code"]
    if "skip" in d:
        return "none", "not a standalone program: " + d["skip"]
    if "compile" in d:
        return "none", "a fragment: it compiles, but needs setup from the surrounding text to run"
    if "error" in d:
        return "fail", "this example shows a compile error"
    if "runfail" in d and not d.get("flags"):
        # Nothing granted on the host either: the failure is the point, and the
        # browser reproduces it (an ungranted capability is refused the same way).
        if POLYGLOT.search(code) or "capability" in d["runfail"]:
            return "fail", "this example shows a refusal"
        return "fail", "this example shows a run-time error"
    needs = host_needs(d, code)
    if needs:
        return "host", "; ".join(needs) + ", which the in-browser runtime does not provide"
    if "nyi" in d:
        return "fail", f"not implemented yet ({d['nyi']}); Run shows what happens today"
    return "run", ""


def blocks_of(text, rel):
    """Classified ```crush blocks of one page, with 1-based fence line numbers."""
    # list(): extract() fills in a block's expected output after yielding it
    for b in list(checker.extract(Path(rel), text)):
        if b["kind"] != "crush":
            continue
        kind, why = classify(b)
        yield {"src": f"{rel}:{b['line'] - 1}", "fence": b["line"] - 2, "end": b["line"] - 1 + b["code"].count("\n"),
               "kind": kind, "why": why, "code": b["code"], "expect": b["expect"],
               "expect_error": b["d"].get("runfail"), "directives": b["d"]}


def attr(s):
    return html.escape(s, quote=True).replace("\n", "&#10;")


def annotate(text, rel):
    lines = text.split("\n")
    for b in sorted(blocks_of(text, rel), key=lambda b: -b["fence"]):
        a = [f'class="crush-block"', f'data-crush="{b["kind"]}"', f'data-src="{attr(b["src"])}"']
        if b["why"]:
            a.append(f'data-why="{attr(b["why"])}"')
        if b["expect"] is not None and b["kind"] == "run":
            a.append(f'data-expect="{attr(b["expect"])}"')
        if b["expect_error"] and b["kind"] == "fail":
            a.append(f'data-expect-error="{attr(b["expect_error"])}"')
        lines[b["end"] + 1 : b["end"] + 1] = ["", "</div>", ""]
        lines[b["fence"] : b["fence"]] = ["<div " + " ".join(a) + ">", ""]
    return "\n".join(lines)


def walk(node):
    if isinstance(node, dict):
        ch = node.get("Chapter")
        if isinstance(ch, dict) and ch.get("content") and ch.get("path"):
            ch["content"] = annotate(ch["content"], ch["path"])
        for v in node.values():
            walk(v)
    elif isinstance(node, list):
        for v in node:
            walk(v)


def manifest():
    out = []
    for md in sorted((ROOT / "src").rglob("*.md")):
        rel = md.relative_to(ROOT / "src").as_posix()
        out.extend(blocks_of(md.read_text(), rel))
    return out


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "supports":
        sys.exit(0 if sys.argv[2:3] == ["html"] else 1)
    if len(sys.argv) > 1 and sys.argv[1] == "--manifest":
        json.dump(manifest(), sys.stdout, indent=1)
        return
    _context, book = json.load(sys.stdin)
    walk(book)
    json.dump(book, sys.stdout)


if __name__ == "__main__":
    main()
