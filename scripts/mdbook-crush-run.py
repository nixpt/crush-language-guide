#!/usr/bin/env python3
"""mdBook preprocessor: mark every ```crush block with what the browser can do with it.

The book's Run / Edit buttons (interactive/crush-run.js) need to know, per block,
whether it can run in the browser (crush-web: a fresh VM per run with what
`crush-run` grants without flags; `io.read` asks the reader for a line), whether
it is *meant* to fail, or whether it needs the host. That is derived here, at build time, from the same directives
and block contents scripts/check-examples.py uses — nothing is hand-labelled, and
the Markdown stays the only source.

Each ```crush block is wrapped in

    <div class="crush-block" data-crush="run|fail|host|none" data-why="..."
         data-expect="..." data-expect-error="..." data-stdin="..." data-src="crush/types.md:91">

which is invisible without JavaScript (the code block renders exactly as before).

A page with at least one ```crush block also gets an "Open as a notebook" link
under its title, to the chapter notebook scripts/build-notebooks.py writes to
book/notebooks/ (notebook_path(); the explainer page is notebooks.md).

    data-crush=run    runs in the browser; data-expect is the checker-verified output,
                      data-stdin the input it was verified with (`check: stdin`)
    data-grants       capabilities the page grants the block's runs (polyglot.javascript,
                      time, env), from the block's `check: flags`
    data-crush=fail   meant to fail (compile error, documented refusal, not yet
                      implemented); Run demonstrates the failure
    data-crush=host   needs something the browser does not grant (@python/@bash, fs, net,
                      process); labelled, no Run
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

# What crush-web (crush-ast c1cc21fb, src/play/pkg) handles itself: crush_vm::run's
# built-in capabilities plus the whole standard library (str.*, math.*, conv.*,
# collections.*, json.*, ...: on by default since CRUSH-113), sys.args/sys.exit,
# and io.read (the page asks the reader for each line).
BROWSER_CAPS = {"io.print", "str.concat", "str.contains", "str.join", "str.len",
                "str.replace", "str.split", "conv.chr", "conv.ord"}
# Capability namespaces that need a host grant (`crush-run` flags). The
# file-reading text.* helpers need --fs. scripts/check-browser.mjs proves each
# such block really fails in crush-web, so a stale list shows up as a failure.
HOST_CAPS = {
    "fs": "the filesystem", "file": "the filesystem", "net": "the network",
    "env": "the environment", "time": "the clock", "process": "processes",
    "db": "a database", "graphics": "graphics", "crypto": "cryptography",
    "text": "the filesystem",
}
# Standard-library namespaces the browser build lacks (none since crush-web
# registers the stdlib); kept so a future slimmer build can list them again.
STDLIB = ()
CALL = re.compile(r"(?<![\w.])([a-z_]+)\.([a-z_][a-z_0-9]*)\s*\(")
POLYGLOT = re.compile(r"@(python|javascript|js|bash|sh|rust|ruby|lua|go)\b")
# Polyglot languages the browser runs when the block is granted (`--polyglot` on
# the host): the page grants the matching capability for that run only, and
# crush-web hands the block to src/play/guest-js.js (@javascript) or
# src/play/guest-py.js (@python, in Pyodide) inside the sandboxed worker.
BROWSER_LANGS = {"javascript": "polyglot.javascript", "js": "polyglot.javascript",
                 "python": "polyglot.python"}
# What an @python block can only do on the host, as src/play/guest-py.js
# refuses it (it would otherwise get answers from Pyodide's empty in-memory
# filesystem, or none): files, processes, the network, packages. A block that
# uses any of these stays labelled as needing the host.
PY_HOST = [
    (re.compile(r"\bopen\s*\(|\bos\.(listdir|scandir|walk|l?stat|remove|unlink|rmdir|mkdir|makedirs|rename|replace|chdir|getcwd|open)\b"),
     "the host's files"),
    (re.compile(r"\b(subprocess|multiprocessing)\b|\bos\.(system|popen|fork|spawn\w*|exec\w*|kill)\b"), "processes"),
    (re.compile(r"\b(socket|ssl|select|ftplib|smtplib)\b|\burllib\.request\b|\bhttp\.client\b"), "the network"),
    (re.compile(r"\bpypi:"), "packages"),
]
# What a @javascript block can only do in node, as src/play/guest-js.js refuses
# it: node modules other than `util`, the network, the process's own details.
JS_HOST = [
    (re.compile(r"\brequire\s*\(\s*['\"](?!(?:node:)?util['\"])|\bimport\s*\(|^\s*import\s", re.M), "node modules"),
    (re.compile(r"\b(fetch|XMLHttpRequest|WebSocket|EventSource)\b"), "the network"),
    (re.compile(r"\bprocess\.(?!(?:env|exit|exitCode|stdout|stderr)\b)\w+"), "the process (`process.*`)"),
]
LANG_HEADER = re.compile(r"@(\w+)[^{\n]*\{")


def lang_bodies(code, lang):
    """The text of each `@lang { ... }` block in `code` (braces matched)."""
    bodies = []
    for m in LANG_HEADER.finditer(code):
        if m.group(1) != lang:
            continue
        depth, i = 1, m.end()
        while i < len(code) and depth:
            depth += {"{": 1, "}": -1}.get(code[i], 0)
            i += 1
        bodies.append(code[m.end():i - 1])
    return bodies
# Host flags whose capabilities the browser can grant a run too: the clock (from
# JavaScript's Date), the environment (empty in a browser, as under `env -i`) and
# the filesystem (an empty in-memory directory of the run's own, answering as an
# empty --fs-root does; the guide's --fs examples all start from one).
BROWSER_FLAGS = {"--time": "time", "--env": "env", "--fs": "fs"}
# Namespaces each browser grant covers, as its crush-run flag does.
GRANT_NAMESPACES = {"time": {"time"}, "env": {"env"}, "fs": {"fs", "file", "text"}}
# Calls that report facts about the machine running the program. In a browser they
# describe the browser (wasm32, an empty environment), so a block that prints them
# cannot match the output the guide shows: it stays labelled as needing the host.
MACHINE_FACTS = {"env.os", "env.arch", "env.home_dir", "env.all"}
FLAG_WHY = {"--polyglot": "polyglot blocks", "--fs": "the filesystem", "--net": "the network",
            "--env": "the environment", "--time": "the clock", "--process": "processes"}


def host_needs(d, code):
    """What this block needs from the host that the browser cannot give, as short phrases."""
    needs, flags = [], d.get("flags", "").split()
    langs = sorted(set(POLYGLOT.findall(code)))
    host_langs = [l for l in langs if l not in BROWSER_LANGS]
    if "--polyglot" in flags and host_langs:
        needs.append("uses " + ", ".join(f"`@{l}`" for l in host_langs) + " blocks (polyglot)")
    for lang, rules in (("python", PY_HOST), ("javascript", JS_HOST)):
        if "--polyglot" in flags and lang in langs:
            body = "\n".join(lang_bodies(code, lang))
            uses = [what for pattern, what in rules if pattern.search(body)]
            if uses:
                needs.append(f"has an `@{lang}` block that uses " + ", ".join(uses))
    calls = {}
    for ns, fn in CALL.findall(code):
        if (ns in HOST_CAPS or ns in STDLIB) and f"{ns}.{fn}" not in BROWSER_CAPS:
            calls.setdefault(ns, []).append(f"{ns}.{fn}")
    browser_ns = {ns for f in flags if f in BROWSER_FLAGS for ns in GRANT_NAMESPACES[BROWSER_FLAGS[f]]}
    host_ns = [ns for ns in calls if ns in HOST_CAPS and ns not in browser_ns]
    granted = {f for f in flags if f in FLAG_WHY} | {"--fs" for f in flags if f.startswith("fs.")}
    if host_ns:
        uniq = sorted({c for ns in host_ns for c in calls[ns]})
        needs.append("uses " + ", ".join(f"`{c}`" for c in uniq[:4]) + (" …" if len(uniq) > 4 else ""))
    elif granted - {"--polyglot"} - set(BROWSER_FLAGS) or ("--polyglot" in flags and not langs):
        needs.append("needs " + ", ".join(sorted(FLAG_WHY[f] for f in granted - set(BROWSER_FLAGS))))
    facts = sorted({c for cs in calls.values() for c in cs if c in MACHINE_FACTS})
    if facts and not host_ns:
        needs.append("reports the machine it runs on (" + ", ".join(f"`{c}`" for c in facts) + ")")
    lib = sorted({c for ns in calls if ns in STDLIB for c in calls[ns]})
    if lib:
        needs.append("uses the standard library (" + ", ".join(f"`{c}`" for c in lib[:3]) + (" …" if len(lib) > 3 else "") + ")")
    return needs


def grants(d, code):
    """The capabilities the page grants this block's runs: what its host flags grant
    that the browser can provide (@javascript / @python under --polyglot, --time,
    --env)."""
    flags = d.get("flags", "").split()
    out = {BROWSER_FLAGS[f] for f in flags if f in BROWSER_FLAGS}
    if "--polyglot" in flags:
        out |= {BROWSER_LANGS[l] for l in POLYGLOT.findall(code) if l in BROWSER_LANGS}
    return sorted(out)


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
    if "runfail" in d:
        return "fail", "this example shows a run-time error"
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
               "expect_error": b["d"].get("runfail"), "stdin": b["d"].get("stdin"),
               "grants": grants(b["d"], b["code"]) if kind in ("run", "fail") else [], "directives": b["d"]}


def has_notebook(text, rel):
    """Whether scripts/build-notebooks.py makes a notebook of this page."""
    return rel != "SUMMARY.md" and any(True for _ in blocks_of(text, rel))


def notebook_path(rel):
    """crush/types.md -> crush/types.crush-nb (README.md -> index.crush-nb, like the book)."""
    p = Path(rel)
    return (p.parent / ("index" if p.stem == "README" else p.stem)).as_posix() + ".crush-nb"


def page_title(rel):
    """The page's title in SUMMARY.md (what the sidebar shows)."""
    m = re.search(r"\[([^\]]+)\]\(" + re.escape(rel) + r"\)", (ROOT / "src" / "SUMMARY.md").read_text())
    return m.group(1) if m else rel


def notebook_link(text, rel):
    """Insert the "Open as a notebook" line after the page's title (`# ` or `</h1>`)."""
    if not has_notebook(text, rel):
        return text
    root = "../" * rel.count("/")
    link = (f'<p class="crush-notebook-link"><a href="{root}notebooks/{notebook_path(rel)}" download>'
            f'Open as a notebook</a> <span>(<code>.crush-nb</code>, '
            f'<a href="{root}notebooks.html">how to run it</a>)</span></p>')
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("# ") or line.strip() == "</h1>":
            lines[i + 1 : i + 1] = ["", link, ""]
            break
    return "\n".join(lines)


LIST_MARK = "<!-- notebooks: list -->"


def notebook_list(rel):
    """Markdown list of every chapter notebook, for the LIST_MARK in notebooks.md."""
    root = "../" * rel.count("/")
    out = []
    for md in sorted((ROOT / "src").rglob("*.md")):
        r = md.relative_to(ROOT / "src").as_posix()
        text = md.read_text()
        if has_notebook(text, r):
            nb = notebook_path(r)
            out.append(f'- <a href="{root}notebooks/{nb}" download><code>{nb}</code></a>, '
                       f'from [{html.escape(page_title(r))}]({root}{notebook_path(r)[:-len(".crush-nb")]}.md)')
    return "\n".join(out)


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
        if b["grants"]:
            a.append(f'data-grants="{attr(" ".join(b["grants"]))}"')
        if b["stdin"] is not None and b["kind"] in ("run", "fail"):
            a.append(f'data-stdin="{attr(b["stdin"])}"')
        if b["expect_error"] and b["kind"] == "fail":
            a.append(f'data-expect-error="{attr(b["expect_error"])}"')
        lines[b["end"] + 1 : b["end"] + 1] = ["", "</div>", ""]
        lines[b["fence"] : b["fence"]] = ["<div " + " ".join(a) + ">", ""]
    return "\n".join(lines)


def walk(node):
    if isinstance(node, dict):
        ch = node.get("Chapter")
        if isinstance(ch, dict) and ch.get("content") and ch.get("path"):
            ch["content"] = notebook_link(annotate(ch["content"], ch["path"]), ch["path"])
            if LIST_MARK in ch["content"]:
                ch["content"] = ch["content"].replace(LIST_MARK, notebook_list(ch["path"]))
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
