// Runs Crush off the main thread for the guide's Run buttons (interactive/crush-run.js).
// Adapted from crush-website's playground/worker.js. The VM stops at its
// instruction quota; the page also has a wall-clock timeout that terminates this
// worker and starts a fresh one. Each run is its own VM: no state is shared.
//
// Every run is a crush-web Session, so a program that calls io.read pauses
// until the page sends a line (or EOF). Messages:
//   { id, op: 'start', source, grants }   compile and run until done or input
//   { id, op: 'input', line }             provide one line and continue
//   { id, op: 'eof' }                     end of input (io.read returns "") and continue
// Each answer is the Session report { id, status, output, error?, exit_code?,
// steps } plus `ms`, the time this step spent running (the page's wall-clock
// limit counts only that, not time spent waiting for the reader).
import init, { Session } from './pkg/crush_web.js';

const crush = { Session };
const sessions = new Map();

function step(m) {
    let s = sessions.get(m.id), r;
    try {
        if (m.op === 'start') {
            s = new crush.Session(m.source, { grants: m.grants || [] });
            sessions.set(m.id, s);
            r = s.run();
        } else if (!s) {
            r = { status: 'error', output: '', error: 'this run has already finished', steps: 0 };
        } else if (m.op === 'input') {
            r = s.provide(m.line);
        } else {
            r = s.close();
        }
    } catch (e) {
        // A wasm trap (a panic in crush-web) leaves the instance unusable.
        const fatal = e instanceof WebAssembly.RuntimeError;
        r = { status: 'error', output: '', error: String((e && e.message) || e), steps: 0, fatal };
    }
    if (r.status !== 'need_input' && s) {
        sessions.delete(m.id);
        try { s.free(); } catch (_) { /* already gone after a trap */ }
    }
    return r;
}

const ready = init();

self.onmessage = async ({ data: m }) => {
    await ready;
    const started = performance.now();
    const r = step(m);
    self.postMessage(Object.assign({ id: m.id, ms: performance.now() - started }, r));
};

ready.then(() => self.postMessage({ ready: true }));
