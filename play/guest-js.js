// Runs a granted @javascript block the way native `crush-run --polyglot` runs
// it with `node -e <code>`, for a crush-web Session started with `deferLang`
// (the run pauses at the block, this runs it, the run continues with what it
// printed):
//
//   - the block's inputs arrive as JSON strings in `process.env`; everything it
//     prints to stdout is returned (crush-web strips the result-sentinel line),
//     and a failure fails the block with what node would put on stderr;
//   - it runs as node runs a script: top-level `await`, promises, `async`
//     functions, `queueMicrotask` and timers (`setTimeout`, `setInterval`,
//     `setImmediate`), until nothing is left to run. An uncaught exception
//     (also in a timer), an unhandled rejection, `process.exit(n)` with n != 0
//     or a non-zero `process.exitCode` fail it, as they make node exit
//     non-zero;
//   - `console.log` and friends format values with node's own util.inspect /
//     util.format (src/play/node-inspect.js), so output matches node's;
//     `require('util')` is that module.
//
// The browser is not node, so what it cannot reproduce exactly is refused
// loudly instead of approximated: node modules other than `util`, `process.*`
// beyond env/exit/exitCode/stdout/stderr, `process.nextTick`, the network
// (`fetch`, `XMLHttpRequest`, `WebSocket`), printing a Promise or a timer
// object (node shows internals a browser cannot read), and `Proxy.revocable`.
// Each block runs in a fresh function scope; globals it creates are removed
// afterwards, so blocks share no state (native: a fresh node per block).
//
// Loaded by worker.js (as a classic script, `crushGuestJs`) and by
// scripts/check-browser.mjs, after src/play/node-inspect.js, so both run
// blocks through the same code.
(function (global) {
    'use strict';

    const util = global.crushNodeInspect;
    const AsyncFunction = (async function () {}).constructor;
    const realSetTimeout = global.setTimeout.bind(global);
    const realClearTimeout = global.clearTimeout.bind(global);

    class Unsupported extends Error {}
    class Exit {
        constructor(code) { this.code = code; }
    }

    function unsupported(what) {
        throw new Unsupported(`${what} is not supported by the in-browser JavaScript runtime ` +
            '(it cannot reproduce node exactly); run this program with crush-run --polyglot');
    }

    // ── values node prints from internals a browser cannot read ────────────
    class Timeout {
        constructor(id) { this.id = id; }
        [Symbol.toPrimitive]() { return this.id; }
    }

    // inspect's default depth is 2: it looks at most this deep.
    function checkPrintable(values) {
        const seen = new Set();
        const visit = (v, depth) => {
            if (v === null || (typeof v !== 'object' && typeof v !== 'function') || seen.has(v) || depth > 3) return;
            seen.add(v);
            if (v instanceof Promise) unsupported('Printing a Promise (node shows its state)');
            if (v instanceof Timeout) unsupported('Printing a timer object');
            if (typeof v === 'function') return;
            if (v instanceof Map) { for (const [k, x] of v) { visit(k, depth + 1); visit(x, depth + 1); } return; }
            if (v instanceof Set) { for (const x of v) visit(x, depth + 1); return; }
            let keys;
            try { keys = Object.keys(v); } catch (_) { return; }
            for (const k of keys) {
                let x;
                try { x = v[k]; } catch (_) { continue; }
                visit(x, depth + 1);
            }
        };
        for (const v of values) visit(v, 0);
    }

    // ── what node prints for an uncaught error ──────────────────────────────
    function describe(e) {
        if (e instanceof Error) return `${e.name}: ${e.message}`;
        if (typeof e === 'string') return e;
        try { return 'Uncaught ' + util.inspect(e); } catch (_) { return 'Uncaught ' + String(e); }
    }

    function rejectionReason(r) {
        if (r instanceof Error) return `${r.name}: ${r.message}`;
        const text = r !== null && typeof r === 'object' ? `#<${(r.constructor && r.constructor.name) || 'Object'}>` : String(r);
        return 'UnhandledPromiseRejection: This error originated either by throwing inside of an async function ' +
            'without a catch block, or by rejecting a promise which was not handled with .catch(). ' +
            `The promise rejected with the reason "${text}".`;
    }

    // Unhandled rejections, in a worker (the page) and in node (scripts/check-browser.mjs).
    function onUnhandledRejection(handler) {
        if (typeof global.addEventListener === 'function') {
            const h = (event) => { event.preventDefault(); handler(event.reason); };
            global.addEventListener('unhandledrejection', h);
            return () => global.removeEventListener('unhandledrejection', h);
        }
        if (global.process && typeof global.process.on === 'function') {
            const h = (reason) => handler(reason);
            global.process.on('unhandledRejection', h);
            return () => global.process.off('unhandledRejection', h);
        }
        return () => {};
    }

    const tick = () => new Promise((resolve) => realSetTimeout(resolve, 0));
    const STATIC = [[/\bimport\s*\(/, 'import()'], [/^\s*import\s[\s\S]*?\bfrom\b|^\s*import\s*['"]/m, 'import of node modules']];

    // ── one block ──────────────────────────────────────────────────────────
    async function run(code, env) {
        for (const [re, what] of STATIC) if (re.test(code)) unsupported(`A block that uses ${what}`);
        let stdout = '', stderr = '', indent = '', failure = null, exitCode;
        const fail = (e) => { if (!failure) failure = { error: e }; };

        // the event loop's timers, run on the browser's own
        const timers = new Map();
        let nextId = 1;
        function addTimer(fn, ms, args, repeat) {
            if (typeof fn !== 'function') unsupported('A timer whose callback is not a function');
            let delay = Number(ms);
            if (!(delay >= 1 && delay <= 2147483647)) delay = 1;
            const id = nextId++;
            const fire = () => {
                if (failure || !timers.has(id)) return;
                if (repeat) timers.set(id, realSetTimeout(fire, delay)); else timers.delete(id);
                try { fn(...args); } catch (e) { fail(e); }
            };
            timers.set(id, realSetTimeout(fire, delay));
            return new Timeout(id);
        }
        function clearTimer(t) {
            const id = t instanceof Timeout ? t.id : Number(t);
            if (timers.has(id)) { realClearTimeout(timers.get(id)); timers.delete(id); }
        }

        // console, formatting with node's util
        const write = (stream, text) => { if (stream === 'out') stdout += text; else stderr += text; };
        const print = (stream, args) => {
            checkPrintable(args);
            const text = util.format(...args);
            write(stream, (indent ? text.split('\n').map((l) => indent + l).join('\n') : text) + '\n');
        };
        const counts = new Map();
        const consoleMethods = {
            log: (...a) => print('out', a), info: (...a) => print('out', a), debug: (...a) => print('out', a),
            error: (...a) => print('err', a), warn: (...a) => print('err', a),
            dir: (v, options) => {
                checkPrintable([v]);
                write('out', indent + util.inspect(v, Object.assign({ customInspect: false }, options)) + '\n');
            },
            assert: (cond, ...a) => {
                if (cond) return;
                if (typeof a[0] === 'string') a[0] = `Assertion failed: ${a[0]}`; else a.unshift('Assertion failed');
                print('err', a);
            },
            group: (...a) => { if (a.length) print('out', a); indent += '  '; },
            groupCollapsed: (...a) => { if (a.length) print('out', a); indent += '  '; },
            groupEnd: () => { indent = indent.slice(2); },
            count: (label = 'default') => {
                const n = (counts.get(`${label}`) || 0) + 1;
                counts.set(`${label}`, n);
                print('out', [`${label}: ${n}`]);
            },
            countReset: (label = 'default') => { counts.set(`${label}`, 0); },
        };
        const known = (target, what) => new Proxy(target, {
            get(t, k) {
                if (typeof k === 'string' && Object.prototype.hasOwnProperty.call(t, k)) return t[k];
                if (k === Symbol.toPrimitive || k === 'then' || k === Symbol.toStringTag) return undefined;
                unsupported(`${what}.${String(k)}`);
            },
        });
        const console = known(consoleMethods, 'console');

        const streamWrite = (stream) => Object.freeze({
            write: (chunk) => {
                if (typeof chunk !== 'string') unsupported(`Writing a non-string to process.${stream === 'out' ? 'stdout' : 'stderr'}`);
                write(stream, chunk);
                return true;
            },
        });
        const processFields = {
            env: Object.assign(Object.create(null), env),
            exit: (c) => { throw new Exit(c === undefined ? Number(exitCode || 0) : Number(c)); },
            stdout: streamWrite('out'),
            stderr: streamWrite('err'),
        };
        const process = new Proxy(processFields, {
            get(t, k) {
                if (k === 'exitCode') return exitCode;
                if (typeof k === 'string' && Object.prototype.hasOwnProperty.call(t, k)) return t[k];
                if (k === Symbol.toPrimitive || k === 'then' || k === Symbol.toStringTag) return undefined;
                unsupported(`process.${String(k)}`);
            },
            set(t, k, v) {
                if (k !== 'exitCode') unsupported(`Setting process.${String(k)}`);
                exitCode = v;
                return true;
            },
        });

        const utilModule = known({
            format: util.format, formatWithOptions: util.formatWithOptions, inspect: util.inspect,
            stripVTControlCharacters: util.stripVTControlCharacters,
        }, 'util');
        const require = (name) => (name === 'util' || name === 'node:util' ? utilModule : unsupported(`require('${name}')`));
        const network = (what) => function () { unsupported(`The network (${what})`); };
        // node's util can show a Proxy only if it made it: hand the block that Proxy
        function Proxy(target, handler) {
            if (!new.target) throw new TypeError("Constructor Proxy requires 'new'");
            return new util.Proxy(target, handler);
        }
        Proxy.revocable = () => unsupported('Proxy.revocable');

        let fn;
        try {
            fn = new AsyncFunction('process', 'console', 'require', 'setTimeout', 'clearTimeout', 'setInterval',
                'clearInterval', 'setImmediate', 'clearImmediate', 'fetch', 'XMLHttpRequest', 'WebSocket', 'EventSource',
                'Proxy', code);
        } catch (e) {
            throw new Error(`[eval]: ${e.name}: ${e.message}`);
        }
        const before = new Set(Object.getOwnPropertyNames(global));
        // process.exit() or a refusal inside a promise callback arrives as a rejection
        const stopListening = onUnhandledRejection((reason) =>
            fail(reason instanceof Exit || reason instanceof Unsupported ? reason : { rejection: reason }));
        try {
            try {
                await fn.call(global, process, console, require,
                    (f, ms, ...a) => addTimer(f, ms, a, false), clearTimer,
                    (f, ms, ...a) => addTimer(f, ms, a, true), clearTimer,
                    (f, ...a) => addTimer(f, 0, a, false), clearTimer,
                    network('fetch'), network('XMLHttpRequest'), network('WebSocket'), network('EventSource'),
                    Proxy);
            } catch (e) {
                fail(e);
            }
            // node's event loop: until no timer is left (or the block fails or exits);
            // the extra turn lets a last unhandled rejection be reported
            while (!failure) {
                await tick();
                if (timers.size === 0) {
                    await tick();
                    if (timers.size === 0) break;
                }
            }
        } finally {
            for (const handle of timers.values()) realClearTimeout(handle);
            timers.clear();
            stopListening();
            for (const name of Object.getOwnPropertyNames(global)) {
                if (!before.has(name)) delete global[name];
            }
        }
        if (failure) {
            const e = failure.error;
            if (e instanceof Exit) {
                if (e.code === 0) return stdout;
                throw new Error(stderr.trim() || `process.exit(${e.code})`);
            }
            if (e instanceof Unsupported) throw e;
            if (e && Object.prototype.hasOwnProperty.call(e, 'rejection')) throw new Error((stderr + rejectionReason(e.rejection)).trim());
            throw new Error((stderr + describe(e)).trim());
        }
        if (exitCode !== undefined && Number(exitCode) !== 0) throw new Error(stderr.trim() || `process.exitCode = ${exitCode}`);
        return stdout;
    }

    global.crushGuestJs = { run, Unsupported };
})(typeof self !== 'undefined' ? self : globalThis);
