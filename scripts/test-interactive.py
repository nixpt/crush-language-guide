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
  * a documented refusal shows the refusal verdict; host-only labels name the reason;
  * with JavaScript disabled the page has plain code blocks and no controls;
  * a narrow (mobile) viewport has no horizontal overflow; a dark theme renders.

Needs python3 + playwright and a Chromium (Playwright's, or set CHROMIUM=/path).
"""
import argparse, functools, http.server, json, os, shutil, socketserver, subprocess, sys, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "book"
PAGES = ["crush/types.html", "crush/control_flow.html", "crush/capabilities.html", "crush/polyglot.html"]
failures = []


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


def run_block(page, block):
    block.locator("button.crush-run").click()
    page.wait_for_function("b => b.querySelector('.crush-out .crush-status') && !b.querySelector('button.crush-run').disabled",
                           arg=block.element_handle(), timeout=30000)
    return block.locator(".crush-out .crush-status").inner_text()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--screenshots", help="write light/dark/mobile screenshots here")
    a = ap.parse_args()
    if not (BOOK / "index.html").exists():
        sys.exit("book/ not built: run `mdbook build` first")
    manifest = json.loads(subprocess.check_output([sys.executable, str(ROOT / "scripts" / "mdbook-crush-run.py"), "--manifest"]))
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
                    status = run_block(page, blocks.nth(i))
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
            refusal = page.locator('div.crush-block[data-src="crush/capabilities.md:100"]')
            run_block(page, refusal)
            check("Refused: capability fs.read was not granted" in refusal.locator(".crush-verdict").inner_text(), "fs.read refusal shows the refusal verdict")
            host = page.locator('div.crush-block[data-src="crush/capabilities.md:151"]')
            check("env.get" in host.locator(".crush-why").inner_text() and host.locator("button.crush-run").count() == 0,
                  "host-only block names its capabilities and has no Run")
            page.goto(base + "crush/polyglot.html")
            check("@python" in page.locator('div.crush-block[data-src="crush/polyglot.md:77"] .crush-why').inner_text(), "polyglot block says it uses @python")
            check(not errors, f"no page errors ({errors[:2]})")

            # 5. no JavaScript: plain code blocks
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
                blk = pg.locator('div.crush-block[data-src="crush/capabilities.md:100"]')
                run_block(pg, blk)
                fg = pg.evaluate("getComputedStyle(document.querySelector('.crush-run')).color")
                bg = pg.evaluate("getComputedStyle(document.body).backgroundColor")
                active = pg.evaluate(f"document.documentElement.classList.contains('{theme}')")
                check(active and fg != bg, f"{theme} theme active: Run button colour {fg} on page background {bg}")
                if a.screenshots:
                    blk.scroll_into_view_if_needed()
                    pg.screenshot(path=f"{a.screenshots}/{theme}.png")
            browser.close()
    finally:
        httpd.shutdown()
    print(f"\n{len(failures)} failure(s)" if failures else "\nall checks passed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
