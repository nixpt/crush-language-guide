#!/usr/bin/env python3
"""Run the generated chapter notebooks through the real crush-notebook kernel.

    scripts/run-notebooks.py --kernel PATH/crush-notebook-kernel [--dir book/notebooks] [-v] [--markdown]

For each `.crush-nb` (a scratch copy: the kernel saves into the file it opened), it
starts `crush-notebook-kernel`, speaks MCP over stdio (`initialize`, then
`notebook_open`, `notebook_eval_all`, `notebook_get_state`), and judges every
crush cell against what the guide says about it (`meta.extra.guide`, see
scripts/build-notebooks.py):

    runnable           must finish, and print the guide's output when the page shows one
    expected-failure   must end in an error; when the page quotes the error, a
                       different message is reported as a note (the kernel's
                       wording can differ from crush-run's, e.g. no CLI flag hint)
    needs-host         skipped: the kernel grants only what `crush run` grants with
                       no flags, so these must be refused; one that runs anyway is
                       judged failed (its label is wrong)
    markdown           skipped

The cell outputs come from the kernel's saved copy (get_state only has counts).
Exit status is non-zero if any cell is judged failed. --markdown prints the
per-notebook table as Markdown (for a PR body).

Install the kernel (https://github.com/nixpt/crush-notebook):
    cargo install --locked crush-notebook-kernel@0.1.1
"""
import argparse, json, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class Kernel:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        self.n = 0
        self.call("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "guide-run-notebooks", "version": "0"}})

    def call(self, method, params):
        self.n += 1
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params}) + "\n")
        self.p.stdin.flush()
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError(f"kernel exited during {method}")
            msg = json.loads(line)
            if msg.get("id") == self.n:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg["result"]

    def tool(self, name, args=None):
        r = self.call("tools/call", {"name": name, "arguments": args or {}})
        return r["content"][0]["text"], r.get("isError", False)

    def close(self):
        self.p.stdin.close()
        try:
            self.p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.p.kill()


def cell_output(c):
    text = []
    for o in c.get("outputs", []):
        k = o.get("kind", {})
        if k.get("mime") == "text" and not o.get("data", {}).get("skipped"):
            text.append(k.get("text", ""))
    return "".join(text)


def judge(c, status):
    """(verdict, category, note) for one crush cell; verdict in ok / failed / skipped."""
    g = c["meta"]["extra"]["guide"]
    tag = c["meta"]["tags"][1]
    err = status.get("message", "")
    if tag == "needs-host":
        if status["status"] == "error":
            return "skipped", "host", "refused: " + err[:90]
        return "failed", "host", "labelled needs-host, but ran in the kernel"
    if tag == "expected-failure":
        if status["status"] != "error":
            return "failed", "fail", "expected a failure, but it ran"
        want = g.get("expect_error")
        if want and want not in err:
            return "ok", "fail", f"failed, but not with the page's text {want!r}: {err[:90]}"
        return "ok", "fail", "failed as expected: " + err[:90]
    if status["status"] != "done":
        return "failed", "run", err[:160]
    want = g.get("expect_output")
    if want is not None and cell_output(c).rstrip() != want.rstrip():
        return "failed", "run", f"output differs: got {cell_output(c).rstrip()[:80]!r}"
    return "ok", "run", "output matches" if want is not None else "ran (the page shows no output)"


COLS = ("run", "match", "fail", "host", "failed")


def run_one(exe, nb_path):
    """Per-notebook counts and one (verdict, src, note) per crush cell."""
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / nb_path.name
        shutil.copy(nb_path, copy)
        k = Kernel(exe)
        try:
            k.tool("notebook_open", {"path": str(copy)})
            k.tool("notebook_eval_all")
            state = json.loads(k.tool("notebook_get_state")[0])
        finally:
            k.close()
        saved = json.loads(copy.read_text())
    states = {c["id"]: c["state"] for c in state["cells"]}
    counts, notes = dict.fromkeys(COLS + ("run_total", "fail_total", "host_total"), 0), []
    for c in saved["cells"]:
        if c["kind"]["type"] != "crush":
            continue
        verdict, cat, note = judge(c, states[c["id"]])
        counts[cat + "_total"] += 1
        if verdict == "failed":
            counts["failed"] += 1
        elif cat == "host":
            counts["host"] += 1
        else:
            counts[cat] += 1
            counts["match"] += note == "output matches"
        notes.append((verdict, c["meta"]["extra"]["guide"]["src"], note))
    return counts, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kernel", required=True, help="path to crush-notebook-kernel")
    ap.add_argument("--dir", default=str(ROOT / "book" / "notebooks"))
    ap.add_argument("-v", "--verbose", action="store_true", help="a line per crush cell, not just the failures")
    ap.add_argument("--markdown", action="store_true", help="print the table as Markdown")
    a = ap.parse_args()
    nbs = sorted(Path(a.dir).rglob("*.crush-nb"))
    if not nbs:
        sys.exit(f"no notebooks under {a.dir}: run scripts/build-notebooks.py first")
    head = ("notebook", "runnable ok", "output = page", "expected failures", "host-only refused", "failed")
    rows, total, failed_nbs, details = [], None, 0, []
    for nb in nbs:
        counts, notes = run_one(a.kernel, nb)
        total = counts if total is None else {k: total[k] + counts[k] for k in total}
        failed_nbs += counts["failed"] > 0
        rows.append((nb.relative_to(a.dir).as_posix(), counts))
        for verdict, src, note in notes:
            if verdict == "failed" or a.verbose or note.startswith("failed, but not"):
                details.append(f"{verdict:7} {src}: {note}")

    def cells(c):
        return (f"{c['run']}/{c['run_total']}", f"{c['match']}", f"{c['fail']}/{c['fail_total']}",
                f"{c['host']}/{c['host_total']}", f"{c['failed']}")
    if a.markdown:
        print("| " + " | ".join(head) + " |")
        print("|" + "---|" + "---:|" * (len(head) - 1))
        for name, c in rows + [(f"**{len(nbs)} notebooks**", total)]:
            print("| " + " | ".join((name,) + cells(c)) + " |")
    else:
        print(f"{head[0]:38} {'run ok':>7} {'= page':>7} {'fail ok':>8} {'host':>7} {'failed':>7}")
        for name, c in rows + [("total", total)]:
            r = cells(c)
            print(f"{name:38} {r[0]:>7} {r[1]:>7} {r[2]:>8} {r[3]:>7} {r[4]:>7}")
    if details:
        print()
        print("\n".join(details))
    print(f"\n{len(nbs)} notebooks: {len(nbs) - failed_nbs} clean, {failed_nbs} with failures")
    sys.exit(1 if failed_nbs else 0)


if __name__ == "__main__":
    main()
