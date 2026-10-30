// Runs Crush for the guide's Run buttons (interactive/crush-run.js).
//
// This is a classic worker started from a blob inside a sandboxed iframe that
// has an opaque origin and the CSP `default-src 'none'`. It has no page DOM,
// no cookies, no storage and no network, so a granted @javascript or @python
// block (which runs right here, synchronously, inside the VM's call) has none
// of them either. The page fetches this file with play/guest-js.js and
// play/guest-py.js prepended, the crush-web glue and the .wasm, and sends them
// in the first message along with the MessagePort it talks to us on. Before
// the first run granted @python it sends Pyodide's files too:
//   { id: 'python', op: 'python', files }  load Python; answered { ready } or { loadError }
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

// A granted block, handed out by a deferLang Session (`need_lang`): @javascript
// runs asynchronously, as node runs a script (its promises and timers), and
// @python in Pyodide. Resolves to what it printed; rejects with what it would
// print on stderr.
async function runBlock(lang, code, env) {
    if (lang === 'javascript' || lang === 'js') return self.crushGuestJs.run(code, env);
    if (lang === 'python') return self.crushGuestPy.run(code, env);
    throw new Error(`@${lang} blocks cannot run in the browser`);
}

// Load Pyodide from the files the page fetched and checked (play/pyodide.json):
// this worker has no network, so its loader's requests for the wasm and the
// standard library are answered from those bytes, under a made-up indexURL,
// and its main module is imported from a blob instead of from indexURL.
const PYODIDE_URL = 'https://pyodide.invalid/';

async function loadPython(files) {
    if (self.crushGuestPy.pyodide) return;
    const blobModule = (name) => import(URL.createObjectURL(new Blob([files[name]], { type: 'text/javascript' })));
    const realFetch = self.fetch;
    self.fetch = (url, init) => {
        const u = String(url instanceof Request ? url.url : url);
        if (!u.startsWith(PYODIDE_URL)) return realFetch.call(self, url, init);
        const name = u.slice(PYODIDE_URL.length);
        if (!files[name]) return Promise.reject(new Error(`Pyodide asked for ${name}, which the page did not provide`));
        const type = name.endsWith('.wasm') ? 'application/wasm' : 'application/octet-stream';
        return Promise.resolve(new Response(files[name], { headers: { 'Content-Type': type } }));
    };
    const [loader, asm] = await Promise.all([blobModule('pyodide.mjs'), blobModule('pyodide.asm.mjs')]);
    const pyodide = await loader.loadPyodide({
        indexURL: PYODIDE_URL,
        createPyodideModule: asm.default,
        lockFileContents: new TextDecoder().decode(files['pyodide-lock.json']),
    });
    self.crushGuestPy.init(pyodide);
}

async function step(m) {
    let s = sessions.get(m.id), r;
    try {
        if (m.op === 'start') {
            s = new crush.Session(m.source, { grants: m.grants || [], deferLang: true });
            sessions.set(m.id, s);
            r = s.run();
        } else if (!s) {
            r = { status: 'error', output: '', error: 'this run has already finished', steps: 0 };
        } else if (m.op === 'input') {
            r = s.provide(m.line);
        } else {
            r = s.close();
        }
        // Each granted block the run reaches: run it, then continue the run.
        let output = r.output;
        while (r.status === 'need_lang') {
            const { lang, code, env } = r.lang;
            let next;
            try {
                next = s.provide_lang(await runBlock(lang, code, env));
            } catch (e) {
                next = s.fail_lang(String((e && e.message) || e));
            }
            output += next.output;
            r = next;
        }
        r.output = output;
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
        // Sessions run with deferLang: each granted block comes back to step()
        // as `need_lang` (runBlock), so no synchronous executor is installed.
    } catch (e) {
        port.postMessage({ loadError: String((e && e.message) || e) });
        return;
    }
    port.onmessage = ({ data: m }) => {
        if (m.op === 'python') {
            loadPython(m.files).then(() => port.postMessage({ id: m.id, ready: true }),
                (e) => port.postMessage({ id: m.id, loadError: String((e && e.message) || e) }));
            return;
        }
        const started = performance.now();
        step(m).then((r) => port.postMessage(Object.assign({ id: m.id, ms: performance.now() - started }, r)));
    };
    port.postMessage({ ready: true });
};
