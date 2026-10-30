// Runs a granted @javascript block for crush-web's set_lang_executor, the way
// native `crush-run --polyglot` runs it with `node -e <code>`: the block's
// inputs arrive as JSON strings in `process.env`, everything it prints to
// stdout is returned (crush-web strips the result-sentinel line), and a throw
// fails the block with what node would put on stderr.
//
// The browser is not node, so this only accepts what it can reproduce exactly
// and refuses the rest loudly, never approximating:
//   - console.log/info/debug and process.stdout.write go to stdout,
//     console.error/warn and process.stderr.write to stderr. Values are
//     formatted like node's util.format/util.inspect for primitives, plain
//     objects and arrays of up to six items; anything else (class instances,
//     Map/Set, functions, longer arrays, which node lays out in columns, ...)
//     is refused.
//   - process.env and process.exit exist; any other process.* property,
//     require(), and anything asynchronous (timers, promises, async/await,
//     fetch) is refused: node would run it before exiting, a synchronous host
//     call cannot.
// Each block runs in a fresh function scope; globals it creates are removed
// afterwards, so blocks share no state (native: a fresh node per block).
//
// Loaded by worker.js (as a classic script, `crushGuestJs`) and by
// scripts/check-browser.mjs, so both run blocks through the same code.
(function (global) {
    'use strict';

    class Unsupported extends Error {}
    class Exit {
        constructor(code) { this.code = code; }
    }

    const BREAK_LENGTH = 80, COMPACT = 3, DEPTH = 2, MAX_ARRAY = 6;

    function unsupported(what) {
        throw new Unsupported(`${what} is not supported by the in-browser JavaScript runtime ` +
            '(it cannot reproduce node exactly); run this program with crush-run --polyglot');
    }

    // ── node's util.inspect, for plain data ────────────────────────────────
    const META = { 8: '\\b', 9: '\\t', 10: '\\n', 12: '\\f', 13: '\\r' };

    function quote(str) {
        let q = "'";
        if (str.includes("'")) {
            if (!str.includes('"')) q = '"';
            else if (!str.includes('`') && !str.includes('${')) q = '`';
        }
        let out = '';
        for (const ch of str) {
            const c = ch.codePointAt(0);
            if (c >= 0xd800 && c <= 0xdfff) unsupported('A string with a lone surrogate');
            if (c < 0x20) out += META[c] || '\\x' + c.toString(16).toUpperCase().padStart(2, '0');
            else if (c >= 0x7f && c <= 0x9f) out += '\\x' + c.toString(16).toUpperCase();
            else if (ch === '\\') out += '\\\\';
            else if (ch === q && q === "'") out += "\\'";
            else out += ch;
        }
        return q + out + q;
    }

    function primitive(v) {
        switch (typeof v) {
            case 'number': return Object.is(v, -0) ? '-0' : String(v);
            case 'bigint': return `${v}n`;
            case 'boolean': return String(v);
            case 'undefined': return 'undefined';
            case 'symbol': return null;
            default: return v === null ? 'null' : null;
        }
    }

    function plainKind(v) {
        if (Array.isArray(v)) {
            if (Object.getPrototypeOf(v) !== Array.prototype) return null;
            const keys = Object.keys(v);
            if (keys.length !== v.length || Object.getOwnPropertySymbols(v).length) return null;
            return 'array';
        }
        if (Object.getPrototypeOf(v) !== Object.prototype || Object.getOwnPropertySymbols(v).length) return null;
        return 'object';
    }

    function inspect(value) {
        return formatValue({ indentationLvl: 0, currentDepth: 0, seen: [] }, value, 0);
    }

    function formatValue(ctx, v, recurseTimes) {
        const p = primitive(v);
        if (p !== null) return p;
        if (typeof v === 'string') {
            if (v.length > 16 && v.includes('\n') && v.length > BREAK_LENGTH - ctx.indentationLvl - 4) {
                unsupported('Logging a long multi-line string inside an object or array');
            }
            return quote(v);
        }
        if (typeof v !== 'object') unsupported(`Logging a ${typeof v}`);
        const kind = plainKind(v);
        if (!kind) unsupported('Logging this kind of object (only plain objects and arrays are)');
        if (ctx.seen.includes(v)) unsupported('Logging a circular structure');
        const keys = Object.keys(v);
        if (keys.length === 0) return kind === 'array' ? '[]' : '{}';
        if (recurseTimes > DEPTH) return kind === 'array' ? '[Array]' : '[Object]';
        if (kind === 'array' && keys.length > MAX_ARRAY) unsupported(`Logging an array of more than ${MAX_ARRAY} items`);
        for (const k of keys) {
            const d = Object.getOwnPropertyDescriptor(v, k);
            if (!('value' in d)) unsupported('Logging an object with a getter or setter');
        }
        ctx.seen.push(v);
        ctx.currentDepth = recurseTimes;
        const output = keys.map((k) => {
            ctx.indentationLvl += 2;
            const str = formatValue(ctx, v[k], recurseTimes + 1);
            ctx.indentationLvl -= 2;
            if (kind === 'array') return str;
            const name = /^[a-zA-Z_][a-zA-Z_0-9]*$/.test(k) ? k : quote(k);
            return `${name}: ${str}`;
        });
        ctx.seen.pop();
        const braces = kind === 'array' ? ['[', ']'] : ['{', '}'];
        // reduceToSingleString (compact: 3)
        if (ctx.currentDepth - recurseTimes < COMPACT) {
            const start = output.length + ctx.indentationLvl + braces[0].length + 10;
            let total = output.length + start, fits = total + output.length <= BREAK_LENGTH;
            for (let i = 0; fits && i < output.length; i++) {
                total += output[i].length;
                if (total > BREAK_LENGTH) fits = false;
            }
            if (fits) {
                const joined = output.join(', ');
                if (!joined.includes('\n')) return `${braces[0]} ${joined} ${braces[1]}`;
            }
        }
        const ind = '\n' + ' '.repeat(ctx.indentationLvl);
        return `${braces[0]}${ind}  ${output.join(`,${ind}  `)}${ind}${braces[1]}`;
    }

    // node's util.format
    function format(args) {
        if (args.length === 0) return '';
        const first = args[0];
        let out = '', a = 0;
        if (typeof first === 'string') {
            if (args.length === 1) return first;
            a = 1;
            for (let i = 0; i < first.length; i++) {
                if (first[i] !== '%' || i + 1 === first.length) { out += first[i]; continue; }
                const c = first[i + 1];
                if (c === '%') { out += '%'; i++; continue; }
                if (!'sdifjoOc'.includes(c)) { out += '%'; continue; }
                if (a >= args.length) { out += '%' + c; i++; continue; }
                const arg = args[a++];
                i++;
                const num = (x) => (typeof x === 'bigint' ? `${x}n` : Object.is(x, -0) ? '-0' : String(x));
                switch (c) {
                    case 's':
                        if (typeof arg === 'string') out += arg;
                        else if (typeof arg === 'object' && arg !== null || typeof arg === 'function' || typeof arg === 'symbol') unsupported('%s with an object');
                        else out += primitive(arg);
                        break;
                    case 'd':
                        if (typeof arg === 'object' && arg !== null || typeof arg === 'symbol') unsupported('%d with an object');
                        out += typeof arg === 'bigint' ? `${arg}n` : num(Number(arg));
                        break;
                    case 'i':
                        if (typeof arg === 'object' && arg !== null || typeof arg === 'symbol') unsupported('%i with an object');
                        out += typeof arg === 'bigint' ? `${arg}n` : num(parseInt(arg));
                        break;
                    case 'f':
                        if (typeof arg === 'symbol') unsupported('%f with a symbol');
                        out += num(parseFloat(arg));
                        break;
                    case 'j':
                        try { out += JSON.stringify(arg); } catch (e) { unsupported('%j with an unserializable value'); }
                        break;
                    case 'c':
                        break;
                    default:
                        unsupported(`%${c}`);
                }
            }
        }
        for (; a < args.length; a++) {
            if (out.length || a > 0) out += ' ';
            out += typeof args[a] === 'string' ? args[a] : inspect(args[a]);
        }
        return out;
    }

    // ── one block ──────────────────────────────────────────────────────────
    const ASYNC = [
        [/\b(async|await)\b/, 'async/await'], [/\.then\s*\(|\bPromise\b/, 'Promises'],
        [/\b(setTimeout|setInterval|setImmediate|queueMicrotask)\b/, 'timers'],
        [/\b(fetch|XMLHttpRequest|WebSocket|EventSource)\b/, 'the network'],
        [/\brequire\s*\(|\bimport\s*\(|^\s*import\b/m, 'require()/import of node modules'],
    ];

    function run(code, env) {
        for (const [re, what] of ASYNC) if (re.test(code)) unsupported(`A block that uses ${what}`);
        let stdout = '', stderr = '';
        const write = (stream) => (chunk) => {
            if (typeof chunk !== 'string') unsupported('Writing a non-string to process.' + stream);
            if (stream === 'stdout') stdout += chunk; else stderr += chunk;
            return true;
        };
        const log = (...args) => { stdout += format(args) + '\n'; };
        const err = (...args) => { stderr += format(args) + '\n'; };
        const console = Object.freeze({ log, info: log, debug: log, error: err, warn: err });
        const envCopy = Object.assign(Object.create(null), env);
        const known = {
            env: envCopy,
            exit: (code) => { throw new Exit(code === undefined ? 0 : Number(code)); },
            stdout: Object.freeze({ write: write('stdout') }),
            stderr: Object.freeze({ write: write('stderr') }),
        };
        const process = new Proxy(known, {
            get(t, k) {
                if (typeof k === 'string' && Object.prototype.hasOwnProperty.call(t, k)) return t[k];
                if (k === Symbol.toPrimitive || k === 'then') return undefined;
                unsupported(`process.${String(k)}`);
            },
        });
        const require = () => unsupported('require()');
        const before = new Set(Object.getOwnPropertyNames(global));
        let fn;
        try {
            fn = new Function('process', 'console', 'require', code);
        } catch (e) {
            throw new Error(`[eval]: ${e.name}: ${e.message}`);
        }
        try {
            fn.call(global, process, console, require);
        } catch (e) {
            if (e instanceof Exit) {
                if (e.code === 0) return stdout;
                throw new Error(stderr.trim() || `process.exit(${e.code})`);
            }
            if (e instanceof Unsupported) throw e;
            const what = e instanceof Error ? `${e.name}: ${e.message}` : `Uncaught ${inspectThrown(e)}`;
            throw new Error((stderr + what).trim());
        } finally {
            for (const name of Object.getOwnPropertyNames(global)) {
                if (!before.has(name)) delete global[name];
            }
        }
        return stdout;
    }

    function inspectThrown(v) {
        try { return typeof v === 'string' ? quote(v) : inspect(v); } catch (_) { return String(v); }
    }

    global.crushGuestJs = { run, format, Unsupported };
})(typeof self !== 'undefined' ? self : globalThis);
