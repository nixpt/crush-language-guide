// Runs Crush for the guide's Run buttons (interactive/crush-run.js).
//
// This is a classic worker started from a blob inside a sandboxed iframe that
// has an opaque origin and the CSP `default-src 'none'`. It has no page DOM,
// no cookies, no storage and no network, so a granted @javascript block (which
// runs right here, synchronously, inside the VM's call) has none of them
// either. The page fetches this file with play/guest-js.js prepended, the
// crush-web glue and the .wasm, and sends them in the first message along
// with the MessagePort it talks to us on.
//
// Every run is a crush-web Session, so a program that calls io.read pauses
// until the page sends a line (or EOF). Messages on the port:
//   { id, op: 'start', source, grants }   compile and run until done or input
//   { id, op: 'input', line }             provide one line and continue
//   { id, op: 'eof' }                     end of input (io.read returns "") and continue
// Each answer is the Session report { id, status, output, error?, exit_code?,
// steps } plus `ms`, the time this step spent running (the page's wall-clock
// limit counts only that, not time spent waiting for the reader).
'use strict';

let crush = null;
const sessions = new Map();

function executor(lang, code, env) {
    if (lang === 'javascript' || lang === 'js') return self.crushGuestJs.run(code, env);
    throw new Error(`@${lang} blocks cannot run in the browser`);
}

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

self.onmessage = async ({ data }) => {
    self.onmessage = null;
    const { glue, wasm, port } = data;
    try {
        crush = await import(URL.createObjectURL(new Blob([glue], { type: 'text/javascript' })));
        crush.initSync({ module: wasm });
        crush.set_lang_executor(executor);
    } catch (e) {
        port.postMessage({ loadError: String((e && e.message) || e) });
        return;
    }
    port.onmessage = ({ data: m }) => {
        const started = performance.now();
        const r = step(m);
        port.postMessage(Object.assign({ id: m.id, ms: performance.now() - started }, r));
    };
    port.postMessage({ ready: true });
};
