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
const { initSync, execute } = await import(path.join(pkg, 'crush_web.js'));
initSync({ module: fs.readFileSync(path.join(pkg, 'crush_web_bg.wasm')) });

const blocks = JSON.parse(execFileSync('python3', [path.join(root, 'scripts', 'mdbook-crush-run.py'), '--manifest'], { maxBuffer: 1 << 26 }));
const counts = {}, bad = [];
for (const b of blocks) {
    counts[b.kind] = (counts[b.kind] || 0) + 1;
    if (b.kind === 'none') continue;
    let r;
    try { r = { ok: true, out: execute(b.code).output }; } catch (e) { r = { ok: false, err: String(e) }; }
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
