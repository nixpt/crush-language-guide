#!/usr/bin/env python3
"""Headless-Chromium test for the book's Run / Edit controls.

    mdbook build && scripts/test-interactive.py [--screenshots DIR]

Serves book/ on a local port and drives it with Playwright:

  * on several pages, every block gets the controls its classification says
    (scripts/mdbook-crush-run.py --manifest): Run on run/fail blocks, a label and no
    Run on host/none blocks;
  * every run/fail block on every page is run in the browser: runnable blocks must
    report "matches the guide's output" when the page shows output, expected
    failures "fails as the guide says";
  * Edit → change the code → Run runs the edited code; Reset restores the original;
  * output printed before a run-time error is shown above the error;
  * io.read asks for a line under the block: the guide's input matches its output,
    End input gives "", time spent waiting is not running time, and the instruction
    quota covers the whole run;
  * a granted @javascript block matches its page output, has no page DOM, storage or
    network, is refused when the browser can't reproduce node, and times out;
  * a documented refusal shows the refusal verdict; host-only labels name the reason;
  * with JavaScript disabled the page has plain code blocks and no controls;
  * a narrow (mobile) viewport has no horizontal overflow; a dark theme renders;
  * every page with a ```crush block links its chapter notebook, the link downloads
    that chapter's `.crush-nb`, and notebooks.html lists them all (so run
    scripts/build-notebooks.py --out book/notebooks after `mdbook build`).

Needs python3 + playwright and a Chromium (Playwright's, or set CHROMIUM=/path).
"""
import argparse, functools, http.server, json, os, shutil, socketserver, subprocess, sys, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "book"
PAGES = ["crush/types.html", "crush/control_flow.html", "crush/capabilities.html", "crush/polyglot.html"]
failures = []
MANIFEST = []


def block_src(page, needle):
    """The data-src of the block on `page` (e.g. crush/capabilities.md) whose code contains `needle`."""
    found = [b["src"] for b in MANIFEST if b["src"].split(":")[0] == page and needle in b["code"]]
    assert len(found) == 1, f"{page}: {len(found)} blocks contain {needle!r}"
    return found[0]


def check(cond, what):
    print(("ok    " if cond else "FAIL  ") + what)
    if not cond:
        failures.append(what)


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    handler = functools.partial(Quiet, directory=str(BOOK))
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
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


def run_block(page, block, stdin=None):
    """Run a block; when it asks for input, type the lines of `stdin` (its `check: stdin`), then End input."""
    lines = [] if stdin is None else stdin.rstrip("\n").split("\n")
    block.locator("button.crush-run").click()
    done = "b => b.querySelector('.crush-out .crush-status') && !b.querySelector('button.crush-run').disabled"
    asking = "b => !!b.querySelector('input.crush-input-line')"
    while True:
        page.wait_for_function(f"b => ({done})(b) || ({asking})(b)", arg=block.element_handle(), timeout=30000)
        if page.evaluate(f"({done})", block.element_handle()):
            return block.locator(".crush-out .crush-status").inner_text()
        if lines:
            block.locator("input.crush-input-line").fill(lines.pop(0))
            block.locator("input.crush-input-line").press("Enter")
        else:
            block.locator("button.crush-eof").click()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--screenshots", help="write light/dark/mobile screenshots here")
    a = ap.parse_args()
    if not (BOOK / "index.html").exists():
        sys.exit("book/ not built: run `mdbook build` first")
    if not (BOOK / "notebooks").is_dir():
        sys.exit("no book/notebooks: run `scripts/build-notebooks.py --out book/notebooks` after `mdbook build`")
    MANIFEST[:] = manifest = json.loads(subprocess.check_output([sys.executable, str(ROOT / "scripts" / "mdbook-crush-run.py"), "--manifest"]))
    by_page = {}
    for b in manifest:
        by_page.setdefault(b["src"].split(":")[0].replace(".md", ".html").replace("README.html", "index.html"), []).append(b)
    httpd, base = serve()
    try:
        with sync_playwright() as p:
            browser = launch(p)
            page = browser.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))

            # 1. controls match the classification on the sample pages
            for rel in PAGES:
                page.goto(base + rel)
                want = by_page[rel]
                blocks = page.locator("div.crush-block")
                check(blocks.count() == len(want), f"{rel}: {len(want)} classified blocks on the page (found {blocks.count()})")
                for i, b in enumerate(want):
                    blk = blocks.nth(i)
                    has_run = blk.locator("button.crush-run").count() == 1
                    check(has_run == (b["kind"] in ("run", "fail")), f"{b['src']} [{b['kind']}]: Run button {'present' if has_run else 'absent'}")
                    if b["kind"] != "run":
                        check(blk.locator(".crush-badge").count() == 1 and blk.locator(".crush-why").inner_text().strip() != "",
                              f"{b['src']} [{b['kind']}]: labelled ({blk.locator('.crush-why').inner_text()[:70]!r})")

            # 2. every run/fail block in the book, run in Chromium
            ran = {"matches": 0, "plain": 0}
            for rel, want in sorted(by_page.items()):
                if not any(b["kind"] in ("run", "fail") for b in want):
                    continue
                page.goto(base + rel)
                blocks = page.locator("div.crush-block")
                for i, b in enumerate(want):
                    if b["kind"] not in ("run", "fail"):
                        continue
                    status = run_block(page, blocks.nth(i), b["stdin"])
                    if b["kind"] == "fail":
                        check("fails as the guide says" in status, f"{b['src']} [fail]: {status}")
                        ran["matches"] += 1
                    elif b["expect"] is not None:
                        check("matches the guide's output" in status, f"{b['src']} [run]: {status}")
                        ran["matches"] += 1
                    else:
                        check(status.startswith("ok"), f"{b['src']} [run, no expected output shown]: {status}")
                        ran["plain"] += 1
            print(f"ran {ran['matches'] + ran['plain']} blocks in Chromium ({ran['matches']} compared with the page, {ran['plain']} without page output)")

            # 3. edit / run / reset
            page.goto(base + "examples/fibonacci.html")
            blk = page.locator("div.crush-block[data-crush=run]").first
            original = blk.locator("pre code").inner_text()
            blk.locator("button.crush-edit").click()
            ed = blk.locator("textarea.crush-editor")
            check(ed.is_visible() and ed.input_value().strip() == original.strip(), "Edit opens an editor holding the original code")
            ed.fill('print("edited " + (6 * 7))\n')
            status = run_block(page, blk)
            out = blk.locator(".crush-out pre.crush-output").inner_text()
            check(out.strip() == "edited 42" and "edited" in status and "matches" not in status, f"Run runs the edited code (output {out.strip()!r}, status {status!r})")
            ed.fill('print("before")\nlet xs = [1]\nprint(xs[5])\n')
            status = run_block(page, blk)
            outs = [o.inner_text().strip() for o in blk.locator(".crush-out pre.crush-output").all()]
            check("failed" in status and outs[:1] == ["before"] and "out of range" in outs[-1],
                  f"output printed before a run-time error is shown with the error ({outs!r})")
            ed.fill("print(\n")
            status = run_block(page, blk)
            check("failed" in status and blk.locator(".crush-verdict-error").count() == 1, f"an edited compile error is explained ({status!r})")
            blk.locator("button.crush-reset").click()
            check(blk.locator("pre code").is_visible() and not ed.is_visible() and blk.locator("button.crush-reset").is_hidden(),
                  "Reset restores the original block")
            status = run_block(page, blk)
            check("matches the guide's output" in status, f"after Reset, Run matches the guide again ({status!r})")

            # 4. a refusal is shown as one, host labels name the reason
            page.goto(base + "crush/capabilities.html")
            refusal_src = block_src("crush/capabilities.md", 'fs.read("data.txt")')
            refusal = page.locator(f'div.crush-block[data-src="{refusal_src}"]')
            run_block(page, refusal)
            check("Refused: capability fs.read was not granted" in refusal.locator(".crush-verdict").inner_text(), "fs.read refusal shows the refusal verdict")
            host = page.locator(f'div.crush-block[data-src="{block_src("crush/capabilities.md", "CRUSH_GUIDE_DEMO_UNSET")}"]')
            check("env.get" in host.locator(".crush-why").inner_text() and host.locator("button.crush-run").count() == 0,
                  "host-only block names its capabilities and has no Run")
            page.goto(base + "crush/polyglot.html")
            check("@python" in page.locator(f'div.crush-block[data-src="{block_src("crush/polyglot.md", "print(\"two\")")}"] .crush-why').inner_text(),
                  "polyglot block says it uses @python")
            check(not errors, f"no page errors ({errors[:2]})")

            # 5. standard input: io.read asks for a line under the block
            page.goto(base + "crush/capabilities.html")
            blk = page.locator(f'div.crush-block[data-src="{block_src("crush/capabilities.md", "io.read()")}"]')
            field = blk.locator("input.crush-input-line")
            blk.locator("button.crush-run").click()
            field.wait_for(timeout=30000)
            check(field.get_attribute("placeholder") == "the guide types: Ada", f"io.read shows an input line with the guide's input as a hint ({field.get_attribute('placeholder')!r})")
            field.fill("Ada")
            field.press("Enter")
            page.wait_for_function("b => !b.querySelector('button.crush-run').disabled", arg=blk.element_handle(), timeout=30000)
            status = blk.locator(".crush-out .crush-status").inner_text()
            term = blk.locator(".crush-out pre.crush-output").inner_text()
            check("matches the guide's output" in status and term.strip() == "Ada\nHello, Ada", f"typing the guide's input matches its output ({status!r}, transcript {term!r})")

            def interactive(code, lines, wait_ms=0):
                blk.locator("button.crush-reset").click() if blk.locator("button.crush-reset").is_visible() else None
                blk.locator("button.crush-edit").click()
                blk.locator("textarea.crush-editor").fill(code)
                blk.locator("button.crush-run").click()
                for line in lines:
                    field.wait_for(timeout=30000)
                    page.wait_for_timeout(wait_ms)
                    if line is None:
                        blk.locator("button.crush-eof").click()
                    else:
                        field.fill(line)
                        field.press("Enter")
                page.wait_for_function("b => !b.querySelector('button.crush-run').disabled", arg=blk.element_handle(), timeout=60000)
                outs = [o.inner_text() for o in blk.locator(".crush-out pre.crush-output").all()]
                return blk.locator(".crush-out .crush-status").inner_text(), outs

            status, outs = interactive('let a = io.read()\nlet b = io.read()\nprint(a + "|" + b + "|" + str.len(b))\n', ["x", None])
            check(status.startswith("ok") and outs[0].strip().endswith("x||0"), f"End input: io.read returns \"\" ({status!r}, {outs!r})")
            status, outs = interactive('let a = io.read()\nprint("got " + a)\n', ["late"], wait_ms=9000)
            check(status.startswith("ok") and "got late" in outs[0], f"waiting 9 s for input does not count against the 8 s limit ({status!r})")
            status, outs = interactive('let a = io.read()\nlet i = 0\nwhile i < 70000 { i = i + 1 }\nprint("half")\n'
                                       'let b = io.read()\nwhile i < 140000 { i = i + 1 }\nprint(i)\n', ["x", "y"])
            check("failed" in status and "instruction quota exceeded" in outs[-1] and "half" in outs[0],
                  f"the instruction quota covers the whole interactive run ({status!r}, {outs[-1]!r})")
            blk.locator("button.crush-reset").click()

            # 6. granted @javascript runs isolated: no page, storage or network
            page.goto(base + "crush/polyglot.html")
            js = page.locator(f'div.crush-block[data-src="{block_src("crush/polyglot.md", "tags.join")}"]')
            check("grants @javascript" in js.locator(".crush-badge-grant").inner_text(), "a granted block shows its grant")
            check("matches the guide's output" in run_block(page, js), "the @javascript example matches the guide's output")

            def edited_run(blk, code, timeout=30000):
                if blk.locator("button.crush-reset").is_visible():
                    blk.locator("button.crush-reset").click()
                blk.locator("button.crush-edit").click()
                blk.locator("textarea.crush-editor").fill(code)
                status = run_block(page, blk)
                return status, [o.inner_text().strip() for o in blk.locator(".crush-out pre.crush-output").all()]

            probe = (
                '@javascript -> r {\n'
                'var idb = (() => { try { indexedDB.open("x"); return "opened" } catch (e) { return e.name } })()\n'
                'var xhr = (() => { try { var x = new self["XMLHttp" + "Request"](); x.open("GET", "' + base + 'index.html", false); x.send(); return "sent " + x.status } catch (e) { return e.name } })()\n'
                'var r = [typeof document, typeof window, typeof parent, typeof localStorage, self.origin, idb, xhr]\n'
                '}\nprint(r)\n')
            status, outs = edited_run(js, probe)
            check(status.startswith("ok") and outs[0] == "[undefined, undefined, undefined, undefined, null, SecurityError, NetworkError]",
                  f"a @javascript block sees no page, storage or network ({outs!r})")
            status, outs = edited_run(js, '@javascript {\nconsole.log(new Map())\n}\n')
            check("failed" in status and "not supported by the in-browser JavaScript runtime" in outs[-1],
                  f"what the browser cannot reproduce exactly is refused ({outs[-1][:90]!r})")
            status, outs = edited_run(js, 'print("start")\n@javascript {\nwhile (true) {}\n}\n')
            # The worker is stopped mid-step, so output from that step ("start") is lost; the page says so.
            check(status.startswith("timed out") and outs == ["Stopped after 8 s of running time. Output printed before the stop is lost with the stopped runtime."],
                  f"a runaway @javascript block is stopped at the time limit ({status!r}, {outs!r})")
            status, outs = edited_run(js, '@javascript -> v {\nconst v = 6 * 7\n}\nprint(v)\n')
            check(status.startswith("ok") and outs[0] == "42", f"the runtime restarts after a timeout ({status!r}, {outs!r})")
            js.locator("button.crush-reset").click()
            check(not errors, f"no page errors ({errors[:2]})")

            # 7. no JavaScript: plain code blocks
            ctx = browser.new_context(java_script_enabled=False)
            nojs = ctx.new_page()
            nojs.goto(base + "crush/types.html")
            check(nojs.locator(".crush-bar").count() == 0 and nojs.locator("div.crush-block pre code").first.is_visible(),
                  "without JavaScript: code blocks render, no controls")
            ctx.close()

            # 6. mobile width + dark theme
            mob = browser.new_page(viewport={"width": 375, "height": 800})
            mob.goto(base + "crush/control_flow.html")
            run_block(mob, mob.locator("div.crush-block[data-crush=run]").first)
            overflow = mob.evaluate("document.querySelector('.content main').scrollWidth - document.querySelector('.content main').clientWidth")
            check(overflow <= 1, f"375px viewport: no horizontal overflow in the content ({overflow}px)")
            if a.screenshots:
                Path(a.screenshots).mkdir(parents=True, exist_ok=True)
                mob.screenshot(path=f"{a.screenshots}/mobile.png")
            for theme in ("light", "coal"):
                pg = browser.new_page(viewport={"width": 1200, "height": 900})
                pg.add_init_script(f"localStorage.setItem('mdbook-theme', '{theme}')")
                pg.goto(base + "crush/capabilities.html")
                blk = pg.locator(f'div.crush-block[data-src="{refusal_src}"]')
                run_block(pg, blk)
                fg = pg.evaluate("getComputedStyle(document.querySelector('.crush-run')).color")
                bg = pg.evaluate("getComputedStyle(document.body).backgroundColor")
                active = pg.evaluate(f"document.documentElement.classList.contains('{theme}')")
                check(active and fg != bg, f"{theme} theme active: Run button colour {fg} on page background {bg}")
                if a.screenshots:
                    blk.scroll_into_view_if_needed()
                    pg.screenshot(path=f"{a.screenshots}/{theme}.png")

            # 6. chapter notebooks: a link on every page with examples, to that chapter's file
            for rel in sorted(by_page):
                page.goto(base + rel)
                link = page.locator(".crush-notebook-link a[download]")
                if not link.count() == 1:
                    check(False, f"{rel}: one 'Open as a notebook' link (found {link.count()})")
                    continue
                url = page.evaluate("a => a.href", link.element_handle())
                r = page.request.get(url)
                src = by_page[rel][0]["src"].split(":")[0]
                ok = r.status == 200 and r.json().get("meta", {}).get("tags", {}).get("source") == src
                check(ok, f"{rel}: notebook link {url[len(base):]} downloads the notebook of {src} (HTTP {r.status})")
            page.goto(base + "notebooks.html")
            listed = page.locator("main li a[download]").count()
            check(listed == len(by_page), f"notebooks.html lists {listed} notebooks ({len(by_page)} chapters with examples)")
            browser.close()
    finally:
        httpd.shutdown()
    print(f"\n{len(failures)} failure(s)" if failures else "\nall checks passed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
