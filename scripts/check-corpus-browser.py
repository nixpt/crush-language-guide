#!/usr/bin/env python3
"""Run the verified corpus (examples/verified/) in headless Chromium and compare.

    mdbook build && scripts/check-corpus-browser.py [--markdown] [PATH ...]

What scripts/verify-examples does for `crush-run`, for the book's Run button:
every `.crush` program runs through the built book's own runtime
(interactive/crush-run.js, `window.crushRun`), with the grants the page would
give it for its `.flags` (`--polyglot` with only `@javascript` blocks →
polyglot.javascript, `--time` → time, `--env` → env; nothing else is
grantable), its `.stdin` fed line by line, and the result compared with its
`.out` / `.err`:

    match     the browser printed exactly the `.out` (trailing whitespace ignored)
              and/or failed with every line of the `.err` (crush-web says
              `compile error:` / `runtime error:` where crush-run prints
              `[compile]` / `[runtime]`; the messages are the same)
    refused   the browser refused loudly (a capability it cannot grant, e.g. --fs
              or @python) where crush-run, given the flags, ran it
    known     fails loudly but differently, for a reason listed in KNOWN
    MISMATCH  anything else: the browser ran it and got a different result

Exits non-zero on any MISMATCH. `.casm` / `.cvm1` programs are skipped (the page
runs Crush source). Needs what scripts/test-interactive.py needs.
"""
import argparse, functools, http.server, os, re, shutil, socketserver, sys, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "book"
CORPUS = ROOT / "examples" / "verified"
POLYGLOT = re.compile(r"@(python|javascript|js|bash|sh|rust|ruby|lua|go)\b")
REFUSALS = ("nothing was run", "can't be granted in a browser", "capability (run with --polyglot")
# Programs where the browser fails loudly, but differently from crush-run, and why.
KNOWN = {
    "polyglot/implicit-output-warning": "the deprecated implicit `@python` output needs the Python analyzer, "
                                        "which crush-web lacks: a compile error instead of the --polyglot refusal",
}


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    httpd = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(BOOK)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}/"


def launch(p):
    exe = os.environ.get("CHROMIUM")
    try:
        return p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
    except Exception:
        for c in ("chromium", "chromium-browser", "google-chrome"):
            if shutil.which(c):
                return p.chromium.launch(executable_path=shutil.which(c))
        raise


def sidecar(prog, ext):
    p = prog.with_suffix(ext)
    return p.read_text() if p.exists() else None


def grants(flags, code):
    """What the page would grant a block run with these crush-run flags."""
    out = set()
    if "--time" in flags:
        out.add("time")
    if "--env" in flags:
        out.add("env")
    langs = set(POLYGLOT.findall(code))
    if "--polyglot" in flags and langs and langs <= {"javascript", "js"}:
        out.add("polyglot.javascript")
    return sorted(out)


def cli_error(err):
    """crush-web's error as crush-run prints it: `compile error: X` is `[compile] X`,
    `runtime error: X` is `[runtime] X` (the messages themselves are the same)."""
    return re.sub(r"^(compile|runtime) error: ", r"[\1] ", err)


def verdict(r, want_out, want_err):
    out = r["output"].rstrip()
    err = cli_error(r.get("error") or "")
    refused = not r["ok"] and any(x in err for x in REFUSALS)
    if r["ok"]:
        if want_err is not None:
            return "MISMATCH", "ran, but crush-run fails"
        if out == want_out.rstrip():
            return "match", ""
        return "MISMATCH", f"output {out[:80]!r}"
    if want_err is not None:
        missing = [l.strip() for l in want_err.splitlines() if l.strip() and l.strip() not in out + "\n" + err]
        if not missing and (want_out is None or out == want_out.rstrip()):
            return "match", ""
        if refused:
            return "refused", err.splitlines()[-1].strip()
        if missing:
            return "MISMATCH", f"fails without {missing[0]!r}: {err.splitlines()[0][:80]!r}"
        return "MISMATCH", f"output before the error {out[:80]!r}"
    if refused:
        return "refused", err.splitlines()[-1].strip()
    return "MISMATCH", f"fails: {err.splitlines()[0][:100] if err else r}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--markdown", action="store_true", help="print a Markdown table")
    a = ap.parse_args()
    if not (BOOK / "index.html").exists():
        sys.exit("book/ not built: run `mdbook build` first")
    roots = [Path(p).resolve() for p in a.paths] or [CORPUS]
    progs = sorted(p for r in roots for p in ([r] if r.is_file() else r.rglob("*.crush")))
    rows, counts = [], {"match": 0, "refused": 0, "known": 0, "MISMATCH": 0}
    httpd, base = serve()
    try:
        with sync_playwright() as p:
            browser = launch(p)
            page = browser.new_page()
            page.goto(base + "running-examples.html")
            page.wait_for_function("window.crushRun")
            for prog in progs:
                code = prog.read_text()
                flags = (sidecar(prog, ".flags") or "").split()
                g = grants(flags, code)
                r = page.evaluate("([s, g, i]) => window.crushRun.run(s, { grants: g, stdin: i })",
                                  [code, g, sidecar(prog, ".stdin") or ""])
                kind, why = verdict(r, sidecar(prog, ".out"), sidecar(prog, ".err"))
                rel = prog.relative_to(CORPUS).with_suffix("").as_posix()
                if kind == "MISMATCH" and rel in KNOWN and not r["ok"]:
                    kind, why = "known", KNOWN[rel] + f" ({cli_error(r['error']).splitlines()[0]})"
                counts[kind] += 1
                rows.append((rel, " ".join(flags) or "—", ", ".join(g) or "—", kind, why))
                if not a.markdown:
                    print(f"{kind:8} {rel:45} {why}")
            browser.close()
    finally:
        httpd.shutdown()
    if a.markdown:
        print("| program | crush-run flags | page grants | browser | note |\n|---|---|---|---|---|")
        for rel, flags, g, kind, why in rows:
            print(f"| `{rel}` | `{flags}` | {g} | {kind} | {why.replace('|', '¦')} |")
    print("\n" + ", ".join(f"{k}={v}" for k, v in counts.items()) + f"  (total {len(rows)})")
    sys.exit(1 if counts["MISMATCH"] else 0)


if __name__ == "__main__":
    main()
