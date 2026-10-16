// Run / Edit / Reset for the guide's ```crush blocks.
//
// scripts/mdbook-crush-run.py wraps every block in <div class="crush-block"
// data-crush="run|fail|host|none" ...> at build time; this script turns that into
// controls. Runs happen in a module Web Worker (src/play/worker.js) on the
// crush-web build in src/play/pkg, loaded on the first Run. Without JavaScript
// the blocks are plain code blocks.
(function () {
    'use strict';

    const TIMEOUT_MS = 8000;
    const PLAYGROUND = 'https://crushlang.org/playground/#code=';
    const root = typeof path_to_root === 'string' ? path_to_root : '';

    // ── worker: one per page, started on first use, one VM step at a time ──────
    // A run is a series of steps (start, then one per line of input). Steps of
    // different runs are queued, so a run waiting for its reader does not hold
    // up the others.
    let worker = null, workerReady = null, generation = 0, queue = Promise.resolve(), nextId = 1;

    function startWorker() {
        generation++;
        worker = new Worker(new URL(root + 'play/worker.js', document.baseURI), { type: 'module' });
        workerReady = new Promise((resolve, reject) => {
            worker.addEventListener('message', function onReady({ data }) {
                if (data.ready) { worker.removeEventListener('message', onReady); resolve(); }
            });
            worker.addEventListener('error', (e) => reject(new Error(e.message || 'the runtime failed to load')));
        });
    }

    function stopWorker() {
        worker.terminate();
        worker = null;
    }

    // Send one step and wait for the worker's report, stopping the worker if the
    // VM runs longer than `budget` ms. A step of a run whose worker has since been
    // replaced (another run timed out) reports `lost`.
    function step(msg, budget, gen) {
        const job = queue.then(async () => {
            if (!worker) {
                if (gen != null) return { status: 'lost' };
                startWorker();
            }
            await workerReady;
            if (gen != null && gen !== generation) return { status: 'lost' };
            const mine = generation;
            return new Promise((resolve) => {
                const timer = setTimeout(() => {
                    worker.removeEventListener('message', onMessage);
                    stopWorker();
                    resolve({ status: 'timeout' });
                }, Math.max(budget, 0));
                const onMessage = ({ data }) => {
                    if (data.id !== msg.id) return;
                    clearTimeout(timer);
                    worker.removeEventListener('message', onMessage);
                    if (data.fatal) stopWorker();
                    resolve(Object.assign({ gen: mine }, data));
                };
                worker.addEventListener('message', onMessage);
                worker.postMessage(msg);
            });
        });
        queue = job.catch(() => { worker = null; });
        return job;
    }

    // Run `source` to completion. When the program calls io.read, `readLine(output,
    // inputs)` is asked for a line (output is everything printed so far, inputs the
    // lines given so far); it resolves to a
    // string, or null for end of input (io.read then returns ""). The wall-clock
    // limit counts only time the VM spends running, not time waiting for the reader;
    // the instruction quota covers the whole run.
    // Resolves to { ok, output, error?, exit_code?, steps, ms, timeout?, lost?, inputs }.
    async function execute(source, readLine) {
        const id = nextId++;
        const inputs = [];
        let output = '', ms = 0, gen = null;
        let r = await step({ id, op: 'start', source }, TIMEOUT_MS, null);
        for (;;) {
            if (r.status === 'timeout') {
                return { ok: false, timeout: true, output, inputs, ms: TIMEOUT_MS,
                    error: `Stopped after ${TIMEOUT_MS / 1000} s of running time.` };
            }
            if (r.status === 'lost') {
                return { ok: false, lost: true, output, inputs, ms,
                    error: 'The runtime was restarted while this program waited for input (another example ran out of time). Run it again.' };
            }
            gen = r.gen;
            output += r.output;
            ms += r.ms;
            if (r.status !== 'need_input') break;
            const line = await readLine(output, inputs);
            inputs.push(line);
            r = await step(line == null ? { id, op: 'eof' } : { id, op: 'input', line }, TIMEOUT_MS - ms, gen);
        }
        const exited = r.exit_code != null && r.exit_code !== 0;
        return { ok: r.status === 'done' && !exited, output, inputs, steps: r.steps, ms, exit_code: r.exit_code,
            error: r.error || (exited ? `exited with status ${r.exit_code}` : undefined) };
    }

    // ── explaining failures (after crush-website's playground classify()) ───────
    function classify(error) {
        let m = error.match(/@(\w+) requires the 'polyglot\.\w+' capability/);
        if (m) {
            return { kind: 'refused', title: `Refused: the @${m[1]} block was not granted`,
                body: 'Crush never runs a polyglot block unless whoever runs the program grants it ' +
                    '(natively, the --polyglot flag). This page grants nothing, and a browser has no ' +
                    'host process to run Python, JavaScript or Bash in.' };
        }
        m = error.match(/unknown capability: ([\w.]+)/);
        if (m) {
            return { kind: 'refused', title: `Refused: capability ${m[1]} was not granted`,
                body: 'Capabilities are granted by whoever runs the program, not by the program. ' +
                    'The in-browser runtime grants print and a few string builtins, so this call is refused before it does anything.' };
        }
        if (/quota exceeded/.test(error)) {
            return { kind: 'stopped', title: 'Stopped: a VM quota was reached',
                body: 'Every run is capped (one million instructions, bounded call depth), so a runaway program ends cleanly.' };
        }
        if (/^compile error:/.test(error)) {
            return { kind: 'error', title: 'Compile error', body: 'The program was rejected before it ran.' };
        }
        return null;
    }

    // ── helpers ───────────────────────────────────────────────────────────────
    function el(tag, cls, text) {
        const e = document.createElement(tag);
        if (cls) e.className = cls;
        if (text != null) e.textContent = text;
        return e;
    }

    // data-why uses `backticks` for code; render those as <code>.
    function richText(target, text) {
        text.split(/(`[^`]+`)/).forEach((part) => {
            if (part.startsWith('`') && part.endsWith('`') && part.length > 1) target.append(el('code', null, part.slice(1, -1)));
            else if (part) target.append(part);
        });
        return target;
    }

    function base64url(text) {
        let bin = '';
        new TextEncoder().encode(text).forEach((b) => (bin += String.fromCharCode(b)));
        return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    }

    function button(label, cls, title) {
        const b = el('button', 'crush-btn ' + cls, label);
        b.type = 'button';
        if (title) b.title = title;
        return b;
    }

    const LABELS = { fail: 'expected to fail', host: 'needs the host', none: 'not runnable' };

    // ── one block ─────────────────────────────────────────────────────────────
    function setup(block) {
        const kind = block.dataset.crush;
        const pre = block.querySelector('pre');
        const code = pre && pre.querySelector('code');
        if (!code) return;
        const original = code.textContent.replace(/\n$/, '') + '\n';
        const bar = el('div', 'crush-bar');
        block.append(bar);

        if (kind !== 'run') {
            const badge = el('span', 'crush-badge crush-badge-' + kind, LABELS[kind] || kind);
            bar.append(badge);
            if (block.dataset.why) bar.append(richText(el('span', 'crush-why'), block.dataset.why));
        }
        if (kind !== 'run' && kind !== 'fail') return;

        const run = button('Run', 'crush-run', 'Run this example in your browser (Ctrl+Enter while editing)');
        const edit = button('Edit', 'crush-edit', 'Edit this example in place');
        const reset = button('Reset', 'crush-reset', 'Restore the guide\'s original code');
        const play = el('a', 'crush-btn crush-play', 'Playground ↗');
        play.target = '_blank';
        play.rel = 'noopener';
        play.title = 'Open this example on crushlang.org/playground';
        reset.hidden = true;
        bar.prepend(run, edit, reset, play);

        const editor = el('textarea', 'crush-editor');
        editor.spellcheck = false;
        editor.setAttribute('autocapitalize', 'off');
        editor.setAttribute('aria-label', 'Crush code');
        editor.hidden = true;
        editor.value = original;
        pre.after(editor);

        const out = el('div', 'crush-out');
        out.hidden = true;
        block.append(out);

        const source = () => (editor.hidden ? original : editor.value);
        const edited = () => source().trimEnd() !== original.trimEnd();
        const fit = () => { editor.style.height = 'auto'; editor.style.height = editor.scrollHeight + 2 + 'px'; };
        const syncLinks = () => {
            play.href = PLAYGROUND + base64url(source());
            reset.hidden = !edited() && editor.hidden;
        };
        syncLinks();

        edit.addEventListener('click', () => {
            if (!editor.hidden) { editor.focus(); return; }
            editor.style.minHeight = pre.offsetHeight + 'px';
            pre.hidden = true;
            editor.hidden = false;
            edit.hidden = true;
            fit();
            editor.focus();
            syncLinks();
        });
        reset.addEventListener('click', () => {
            editor.value = original;
            editor.hidden = true;
            pre.hidden = false;
            edit.hidden = false;
            out.hidden = true;
            syncLinks();
        });
        editor.addEventListener('input', () => { fit(); syncLinks(); });
        editor.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                run.click();
            } else if (e.key === 'Tab' && !e.shiftKey && !e.altKey) {
                e.preventDefault();
                editor.setRangeText('    ', editor.selectionStart, editor.selectionEnd, 'end');
                syncLinks();
            }
        });

        // While a run waits for input: the transcript so far (typed lines echoed)
        // and an input line. Enter sends a line; End input, Ctrl+D or Reset ends
        // input, and io.read returns "" from then on.
        let term = null, shown = 0, pendingInput = null;
        const guideInput = block.dataset.stdin != null ? block.dataset.stdin.replace(/\n$/, '').split('\n') : null;

        function readLine(output, inputs) {
            term.append(output.slice(shown));
            shown = output.length;
            const form = el('form', 'crush-input');
            const field = el('input', 'crush-input-line');
            field.type = 'text';
            field.autocomplete = 'off';
            field.spellcheck = false;
            field.setAttribute('aria-label', 'Input for io.read');
            const guide = guideInput && !edited() ? guideInput[inputs.length] : undefined;
            field.placeholder = guide != null ? `the guide types: ${guide}` : 'a line for io.read';
            const send = button('Send', 'crush-send', 'Send this line (Enter)');
            send.type = 'submit';
            const eof = button('End input', 'crush-eof', 'End of input: io.read returns "" (Ctrl+D)');
            form.append(el('span', 'crush-prompt', '›'), field, send, eof);
            const foot = el('div', 'crush-status', 'waiting for input · Enter sends a line · End input (Ctrl+D) closes it');
            out.replaceChildren(term, form, foot);
            field.focus({ preventScroll: true });
            return new Promise((resolve) => {
                pendingInput = (line) => {
                    pendingInput = null;
                    term.append(el('span', 'crush-typed', line == null ? '⏎ end of input\n' : line + '\n'));
                    out.replaceChildren(term, el('div', 'crush-status', 'running…'));
                    resolve(line);
                };
                form.addEventListener('submit', (e) => { e.preventDefault(); pendingInput(field.value); });
                eof.addEventListener('click', () => pendingInput(null));
                field.addEventListener('keydown', (e) => {
                    if (e.ctrlKey && (e.key === 'd' || e.key === 'D')) { e.preventDefault(); pendingInput(null); }
                });
            });
        }
        reset.addEventListener('click', () => { if (pendingInput) pendingInput(null); });

        run.addEventListener('click', async () => {
            if (run.disabled) return;
            run.disabled = true;
            run.textContent = 'Running…';
            out.hidden = false;
            out.replaceChildren(el('div', 'crush-status', worker ? 'running…' : 'loading the Crush runtime…'));
            term = el('pre', 'crush-output crush-term');
            shown = 0;
            const wasEdited = edited();
            let r;
            try {
                r = await execute(source(), readLine);
            } catch (err) {
                r = { ok: false, loadError: true, inputs: [], error: 'Could not start the Crush runtime: ' + err.message +
                    '. Running examples needs WebAssembly and module workers (a recent Chrome, Firefox, Safari or Edge).' };
            }
            run.disabled = false;
            run.textContent = 'Run';
            show(r, wasEdited);
        });

        // The output as a <pre>: for a run that read input, the transcript with
        // the typed lines in it.
        function outputPre(r, empty) {
            if (!r.inputs.length) return r.output || empty ? el('pre', 'crush-output', r.output || empty) : null;
            term.append(r.output.slice(shown));
            return term;
        }

        // Whether the reader typed what the guide feeds this example (its
        // `check: stdin`), so the guide's output is the one to compare with.
        function guideInputUsed(inputs) {
            const lines = guideInput || [];
            return inputs.every((x, i) => (i < lines.length ? x === lines[i] : x == null));
        }

        function show(r, wasEdited) {
            const parts = [];
            const ms = r.ms == null ? '' : ` · ${r.ms < 1 ? '<1' : Math.round(r.ms)} ms`;
            let verdict = null, status;
            if (r.ok) {
                parts.push(outputPre(r, '(no output)'));
                status = `ok · ${r.steps.toLocaleString()} steps${ms}`;
                if (wasEdited) {
                    status += ' · edited';
                } else if (kind === 'fail') {
                    verdict = { cls: 'differs', text: 'Ran without an error, but the guide expects this example to fail. The page may be out of date.' };
                } else if (block.dataset.expect != null && !guideInputUsed(r.inputs)) {
                    status += ' · your input differs from the guide\'s';
                } else if (block.dataset.expect != null) {
                    verdict = r.output.trimEnd() === block.dataset.expect.trimEnd()
                        ? { cls: 'matches', text: '✓ matches the guide\'s output' }
                        : { cls: 'differs', text: '✗ differs from the guide\'s output' };
                }
            } else {
                const c = !r.timeout && !r.loadError && !r.lost ? classify(r.error) : null;
                if (c) {
                    const box = el('div', 'crush-verdict crush-verdict-' + c.kind);
                    box.append(el('strong', null, c.title), el('p', null, c.body));
                    parts.push(box);
                }
                const pre = outputPre(r, '');
                if (pre) parts.push(pre);
                parts.push(el('pre', 'crush-output crush-error', r.error));
                status = (r.timeout ? 'timed out' : r.loadError ? 'runtime unavailable' : r.lost ? 'interrupted' : 'failed') + ms;
                if (!wasEdited && kind === 'fail' && !r.loadError && !r.timeout && !r.lost) {
                    const want = block.dataset.expectError;
                    verdict = !want || r.error.includes(want)
                        ? { cls: 'matches', text: '✓ fails as the guide says' }
                        : { cls: 'differs', text: '✗ fails, but not with the error the guide shows' };
                } else if (!wasEdited && kind === 'run' && !r.loadError && !r.lost) {
                    verdict = { cls: 'differs', text: '✗ the guide expects this example to run' };
                }
            }
            const foot = el('div', 'crush-status', status);
            if (verdict) foot.append(' · ', el('span', 'crush-' + verdict.cls, verdict.text));
            out.replaceChildren(...parts, foot);
        }
    }

    function init() {
        document.querySelectorAll('div.crush-block[data-crush]').forEach(setup);
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
})();
