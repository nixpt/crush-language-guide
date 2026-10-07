#!/usr/bin/env python3
"""Turn each chapter of the guide into a crush-notebook (`.crush-nb`).

    scripts/build-notebooks.py [--out book/notebooks] [--validate SCHEMA] [--list]

One notebook per chapter that has ```crush examples (src/**/*.md): prose becomes
markdown cells, each ```crush block a `crush` cell, every other block stays a code
block inside the markdown. Generated from the Markdown on every build (CI runs this
after `mdbook build`), so the notebooks cannot drift from the guide; nothing here is
committed output.

Per crush cell, `meta.extra.guide` carries what the guide knows about the block:

    src            "crush/types.md:91" (page and line of the block)
    browser        run | fail | host | none (scripts/mdbook-crush-run.py)
    why            the reason, for fail / host
    expect_output  the checker-verified stdout the page prints, when it has one
    expect_error   the documented failure text (`check: runfail`), when it has one

and `meta.tags` repeats the class (`runnable`, `expected-failure`, `needs-host`) so
a notebook UI can filter on it. Outputs are left empty: running is the kernel's job.

Cells share variables in the notebook kernel, which runs a cell as the body of
`main`. Examples that declare top-level functions or structs are given an explicit
`fn main()` at generation time (`isolate()`), without touching the guide's text.

--validate checks every notebook against crush-notebook's JSON schema (vendored at
schemas/notebook.schema.json); needs the `jsonschema` module.
"""
import argparse, importlib.util, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
SITE = "https://docs.crushlang.org/"
_spec = importlib.util.spec_from_file_location("crush_run", ROOT / "scripts" / "mdbook-crush-run.py")
crush_run = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(crush_run)

FENCE = re.compile(r"^```(\S*)\s*$")
DIRECTIVE = re.compile(r"^\s*<!--\s*check:.*-->\s*$")
LINK = re.compile(r"\]\((?!https?:|mailto:|#)([^)\s]+?\.md)(#[^)\s]*)?\)")
TAG = {"run": "runnable", "fail": "expected-failure", "host": "needs-host"}


def notebook_path(rel):
    """crush/types.md -> crush/types.crush-nb (README.md -> index.crush-nb, like the book)."""
    p = Path(rel)
    return (p.parent / ("index" if p.stem == "README" else p.stem)).as_posix() + ".crush-nb"


def page_url(rel):
    p = Path(rel)
    return SITE + (p.parent / ("index" if p.stem == "README" else p.stem)).as_posix() + ".html"


def absolutize(text, rel):
    """Relative .md links -> absolute links into the published book."""
    base = Path(rel).parent
    def fix(m):
        target = (base / m.group(1)).as_posix()
        parts = []
        for seg in target.split("/"):
            if seg == "..":
                parts and parts.pop()
            elif seg != ".":
                parts.append(seg)
        return "](" + page_url("/".join(parts)) + (m.group(2) or "") + ")"
    return LINK.sub(fix, text)


ITEM = re.compile(r"^(fn|karya|struct)\s")  # `karya` is the Nepali keyword for fn


def isolate(code, kind):
    """Make a block run in the kernel as it runs on the page (see module doc).

    The kernel runs a cell that has no `fn main` as the *body* of `main`, with the
    session's variables declared first. A guide example that declares top-level
    functions or structs next to loose statements would then nest those
    declarations inside `main`, which does not parse. Such a cell gets an explicit
    `fn main()` around its loose statements instead (what `crush-run` does
    implicitly), so the kernel runs it as a standalone program. Crush functions do
    not see top-level `let`s, so this changes nothing about what the example means.
    Cells with only statements stay session cells and share variables.
    """
    if re.search(r"^(fn|karya)\s+main\s*\(", code, re.M) or not any(ITEM.match(l) for l in code.split("\n")):
        return code
    items, body, depth, in_item = [], [], 0, False
    for line in code.rstrip("\n").split("\n"):
        if depth == 0 and ITEM.match(line):
            in_item = True
        (items if in_item else body).append(line)
        if in_item:
            depth += line.count("{") - line.count("}")
            if depth <= 0:
                in_item, depth = False, 0
    while body and not body[0].strip():
        body.pop(0)
    while body and not body[-1].strip():
        body.pop()
    if not any(l.strip() for l in body):
        return code
    main = ["fn main() {"] + [("    " + l) if l.strip() else "" for l in body] + ["}"]
    return "\n".join(items).rstrip("\n") + "\n\n" + "\n".join(main) + "\n"


def cells_for(text, rel):
    """Split one page into notebook cells."""
    lines = text.split("\n")
    blocks = {b["fence"]: b for b in crush_run.blocks_of(text, rel)}
    drop = set()  # the ```text expected-output blocks: carried in cell metadata instead
    for b in blocks.values():
        if b["expect"] is None:
            continue
        j = b["end"] + 1
        while j < len(lines) and (not lines[j].strip() or DIRECTIVE.match(lines[j])):
            j += 1
        if j < len(lines) and FENCE.match(lines[j]) and lines[j].startswith("```text"):
            k = j + 1
            while k < len(lines) and not lines[k].startswith("```"):
                k += 1
            drop.update(range(j, k + 1))
    cells, prose, n = [], [], 0
    slug = re.sub(r"[^a-z0-9]+", "-", Path(rel).with_suffix("").as_posix().lower()).strip("-")

    def flush():
        md = "\n".join(prose).strip("\n")
        md = re.sub(r"\n{3,}", "\n\n", md)
        if md.strip():
            cells.append(cell(f"{slug}-md-{len(cells) + 1}", "markdown", absolutize(md, rel) + "\n", {}))
        prose.clear()

    i = 0
    while i < len(lines):
        line = lines[i]
        if i in drop or DIRECTIVE.match(line):
            i += 1
            continue
        b = blocks.get(i)
        if b and b["kind"] != "none":
            flush()
            n += 1
            guide = {"src": b["src"], "browser": b["kind"]}
            if b["why"]:
                guide["why"] = b["why"]
            if b["expect"] is not None:
                guide["expect_output"] = b["expect"]
            if b["expect_error"]:
                guide["expect_error"] = b["expect_error"]
            meta = {"tags": ["guide", TAG[b["kind"]]], "extra": {"guide": guide}}
            cells.append(cell(f"{slug}-{n}", "crush", isolate(b["code"], b["kind"]), meta))
            i = b["end"] + 1
            continue
        m = FENCE.match(line)
        if m:  # any other fenced block stays verbatim inside the markdown
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            prose.extend(lines[i : j + 1])
            i = j + 1
            continue
        prose.append(line)
        i += 1
    flush()
    return cells


def cell(cid, kind, source, meta):
    return {"id": cid, "kind": {"type": kind}, "source": source,
            "state": {"status": "done" if kind == "markdown" else "pending"}, "meta": meta, "outputs": []}


def build(rel, text):
    title = next((l[2:].strip() for l in text.splitlines() if l.startswith("# ")), rel)
    return {
        "meta": {
            "title": title + " — The Crush Language Guide",
            "description": f"Generated from {rel} of The Crush Language Guide ({page_url(rel)}). "
                           "Edit the guide, not this file: it is regenerated on every build.",
            "frontends": ["crush"],
            "author": "The Crush Language Guide",
            "tags": {"source": rel, "guide_url": page_url(rel), "generator": "scripts/build-notebooks.py"},
        },
        "cells": cells_for(text, rel),
    }


def chapters():
    """(rel, text) of every page with at least one ```crush example."""
    for md in sorted(SRC.rglob("*.md")):
        rel = md.relative_to(SRC).as_posix()
        if rel == "SUMMARY.md":
            continue
        text = md.read_text()
        if any(True for _ in crush_run.blocks_of(text, rel)):
            yield rel, text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "book" / "notebooks"))
    ap.add_argument("--validate", metavar="SCHEMA", help="validate every notebook against this JSON schema")
    ap.add_argument("--list", action="store_true", help="print the page -> notebook mapping and exit")
    a = ap.parse_args()
    if a.list:
        for rel, _ in chapters():
            print(rel, notebook_path(rel))
        return
    validator = None
    if a.validate:
        import jsonschema
        schema = json.loads(Path(a.validate).read_text())
        validator = jsonschema.Draft202012Validator(schema)
    out, bad, total = Path(a.out), 0, 0
    for rel, text in chapters():
        nb = build(rel, text)
        dest = out / notebook_path(rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
        total += 1
        kinds = {}
        for c in nb["cells"]:
            k = c["kind"]["type"] if c["kind"]["type"] == "markdown" else c["meta"]["tags"][1]
            kinds[k] = kinds.get(k, 0) + 1
        errors = list(validator.iter_errors(nb)) if validator else []
        bad += bool(errors)
        status = ("INVALID " + "; ".join(e.message[:80] for e in errors[:3])) if errors else ("valid" if validator else "")
        print(f"{notebook_path(rel):34} {len(nb['cells']):3} cells ({', '.join(f'{k} {v}' for k, v in sorted(kinds.items()))}) {status}")
    print(f"{total} notebooks -> {out}" + (f", {bad} invalid" if bad else (", all schema-valid" if validator else "")))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
