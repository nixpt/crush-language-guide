#!/usr/bin/env node
// Prove the book's per-block Run/label decisions against the real browser runtime.
//
//   node scripts/check-browser.mjs [-v]
//
// Takes every ```crush block's classification from `scripts/mdbook-crush-run.py
// --manifest` and runs each block through src/play/pkg (the same crush-web build
// the book's Run button uses), in Node:
//
//   run   must succeed, and print exactly the checker-verified output when the page shows one
//   fail  must fail, with the documented text when the block has `check: runfail <text>`
//   host  must fail here too (else the label hides a block the browser could run)
//   none  not run
//
// Needs only node and python3, so it runs in CI next to `mdbook build`.
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const pkg = path.join(root, 'src', 'play', 'pkg');
const verbose = process.argv.includes('-v');
const { initSync, Session, set_lang_executor } = await import(path.join(pkg, 'crush_web.js'));
initSync({ module: fs.readFileSync(path.join(pkg, 'crush_web_bg.wasm')) });
// Granted @javascript blocks run through the page's own executor (worker.js does the same).
await import(path.join(root, 'src', 'play', 'guest-js.js'));
set_lang_executor((lang, code, env) => {
    if (lang === 'javascript' || lang === 'js') return globalThis.crushGuestJs.run(code, env);
    throw new Error(`@${lang} blocks cannot run in the browser`);
});

// What the page's Run does (interactive/crush-run.js): a Session with the block's
// grants (data-grants: polyglot.javascript under --polyglot); each io.read gets
// the next line of the block's `check: stdin` text (what a reader following the
// guide types), then end of input. A non-zero sys.exit status is a failure.
function run(code, stdin, grants) {
    const s = new Session(code, { grants });
    const lines = stdin == null ? [] : stdin.replace(/\n$/, '').split('\n');
    let r = s.run(), out = r.output;
    while (r.status === 'need_input') { r = lines.length ? s.provide(lines.shift()) : s.close(); out += r.output; }
    s.free();
    const exited = r.exit_code != null && r.exit_code !== 0;
    if (r.status === 'done' && !exited) return { ok: true, out };
    return { ok: false, out, err: r.error || `exited with status ${r.exit_code}` };
}

const blocks = JSON.parse(execFileSync('python3', [path.join(root, 'scripts', 'mdbook-crush-run.py'), '--manifest'], { maxBuffer: 1 << 26 }));
const counts = {}, bad = [];
for (const b of blocks) {
    counts[b.kind] = (counts[b.kind] || 0) + 1;
    if (b.kind === 'none') continue;
    const r = run(b.code, b.stdin, b.grants);
    let problem = null;
    if (b.kind === 'run') {
        if (!r.ok) problem = 'labelled runnable, but fails in the browser: ' + r.err.split('\n')[0];
        else if (b.expect != null && r.out.trimEnd() !== b.expect.trimEnd()) problem = `output differs from the page: got ${JSON.stringify(r.out.trimEnd())}`;
    } else if (b.kind === 'fail') {
        if (r.ok) problem = 'labelled as failing, but runs in the browser';
        else if (b.expect_error && !r.err.includes(b.expect_error)) problem = `fails, but without ${JSON.stringify(b.expect_error)}: ${r.err.split('\n')[0]}`;
    } else if (b.kind === 'host' && r.ok) {
        problem = 'labelled host-only, but runs in the browser (make it runnable)';
    }
    if (problem) bad.push(`${b.src}: ${problem}`);
    if (verbose || problem) console.log(`${problem ? 'FAIL' : 'ok  '} ${b.kind.padEnd(4)} ${b.src}${problem ? '  ' + problem : ''}`);
}
console.log(Object.entries(counts).map(([k, v]) => `${k}=${v}`).join(', ') + `  (total ${blocks.length})`);
if (bad.length) { console.log(`${bad.length} block(s) misclassified`); process.exit(1); }
