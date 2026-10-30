// Runs a granted @python block for crush-web's set_lang_executor in Pyodide
// (CPython compiled to WebAssembly), the way native `crush-run --polyglot` runs
// it with `python3 -c <code>`: the block's inputs arrive as JSON strings in
// `os.environ`, standard input is empty (native connects it to /dev/null),
// everything it prints to stdout is returned (crush-web strips the
// result-sentinel line), and a non-zero exit fails the block with what python3
// would put on stderr: the same traceback, with the block's source lines.
//
// The browser is not the host, so what Python can only do there is refused
// loudly instead of answered differently: files (`open`, `os` file and
// directory calls), processes (`subprocess`, `os.system`, ...) and the network
// (`socket`, `urllib.request`, `http.client`, ...). Pyodide would otherwise
// answer them from its own empty in-memory filesystem.
//
// Each block runs in a fresh `__main__` namespace with the environment and
// sys.modules restored afterwards, so blocks share no state (native: a fresh
// python3 per block).
//
// Loaded by worker.js (as a classic script, `crushGuestPy`) and by
// scripts/check-browser.mjs, so both run blocks through the same code. Neither
// can run a block until `crushGuestPy.init(pyodide)` has been given a loaded
// Pyodide.
(function (global) {
    'use strict';

    class Unsupported extends Error {}

    const RUNNER = String.raw`
import builtins, io, linecache, os, sys, traceback
import importlib.abc


class CrushUnsupported(Exception):
    pass


def _refuse(what):
    raise CrushUnsupported(
        f"{what} is not supported by the in-browser Python runtime (it cannot "
        "reproduce python3 on the host exactly); run this program with crush-run --polyglot"
    )


_REFUSED_MODULES = {
    "subprocess": "Running processes (subprocess)",
    "multiprocessing": "Running processes (multiprocessing)",
    "socket": "The network (socket)",
    "ssl": "The network (ssl)",
    "select": "The network (select)",
    "urllib.request": "The network (urllib.request)",
    "http.client": "The network (http.client)",
    "ftplib": "The network (ftplib)",
    "smtplib": "The network (smtplib)",
}
_REFUSED_OS = {
    name: f"os.{name}()"
    for name in (
        "listdir", "scandir", "walk", "stat", "lstat", "remove", "unlink", "rmdir",
        "mkdir", "makedirs", "rename", "replace", "chdir", "getcwd", "open",
        "system", "popen", "fork", "spawnl", "spawnv", "execv", "execvp", "kill",
    )
    if hasattr(os, name)
}


def _refusing(what):
    def f(*_a, **_k):
        _refuse(what)
    return f


# Pyodide's own bridges to JavaScript: python3 has no such modules, so a block
# that imports one fails as it does natively.
_ABSENT_MODULES = ("js", "pyodide_js", "pyodide")


def _absent(name):
    return name.split(".")[0] in _ABSENT_MODULES


class _RefuseImports(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name in _REFUSED_MODULES:
            _refuse(_REFUSED_MODULES[name])
        if _absent(name):
            raise ModuleNotFoundError(f"No module named '{name.split('.')[0]}'", name=name.split(".")[0])
        return None


_RUNNER_FILE = "<crush-guest-py>"


def _format_exception(e, tb):
    # python3 -c shows the block's frames and nothing of the runner's (its own
    # importlib frames are hidden the same way), in chained exceptions too.
    te = traceback.TracebackException(type(e), e, tb)
    todo, seen = [te], set()
    while todo:
        t = todo.pop()
        if t is None or id(t) in seen:
            continue
        seen.add(id(t))
        t.stack = traceback.StackSummary.from_list([f for f in t.stack if f.filename != _RUNNER_FILE])
        todo += [t.__cause__, t.__context__] + list(t.exceptions or [])
    return "".join(te.format())


class _NoStdin(io.StringIO):
    # native: stdin is /dev/null, so input() raises EOFError and read() gives ""
    def isatty(self):
        return False


def __crush_run_block__(code, env):
    out, err = io.StringIO(), io.StringIO()
    saved_streams = (sys.stdout, sys.stderr, sys.stdin)
    saved_env = dict(os.environ)
    saved_modules = set(sys.modules)
    saved_argv = sys.argv
    saved_open = (builtins.open, io.open)
    saved_os = {name: getattr(os, name) for name in _REFUSED_OS}
    hidden = {name: sys.modules.pop(name) for name in list(sys.modules)
              if name in _REFUSED_MODULES or _absent(name)}
    finder = _RefuseImports()
    status = 0
    unsupported = None
    linecache.cache["<string>"] = (len(code), None, code.splitlines(True), "<string>")
    try:
        os.environ.update(env)
        sys.argv = ["-c"]
        sys.stdout, sys.stderr, sys.stdin = out, err, _NoStdin("")
        builtins.open = io.open = _refusing("Files (open)")
        for name, what in _REFUSED_OS.items():
            setattr(os, name, _refusing(what))
        sys.meta_path.insert(0, finder)
        try:
            compiled = compile(code, "<string>", "exec")
        except SyntaxError as e:
            err.write("".join(traceback.format_exception_only(type(e), e)))
            status = 1
        else:
            namespace = {"__name__": "__main__", "__builtins__": builtins, "__doc__": None,
                         "__package__": None, "__spec__": None, "__loader__": None}
            try:
                exec(compiled, namespace)
            except CrushUnsupported as e:
                unsupported = str(e)
            except SystemExit as e:
                # what python3 does with the exit code
                if e.code is None:
                    status = 0
                elif isinstance(e.code, int):
                    status = e.code
                else:
                    err.write(f"{e.code}\n")
                    status = 1
            except BaseException as e:
                # drop the exec() frame: python3 -c starts at the block's own code
                err.write(_format_exception(e, e.__traceback__.tb_next))
                status = 1
        try:
            sys.stdout.flush()
        except Exception:
            pass
    finally:
        sys.meta_path.remove(finder)
        builtins.open, io.open = saved_open
        for name, value in saved_os.items():
            setattr(os, name, value)
        sys.stdout, sys.stderr, sys.stdin = saved_streams
        sys.argv = saved_argv
        os.environ.clear()
        os.environ.update(saved_env)
        for name in list(sys.modules):
            if name not in saved_modules:
                del sys.modules[name]
        sys.modules.update(hidden)
        linecache.cache.pop("<string>", None)
    if unsupported is not None:
        return ["unsupported", unsupported, ""]
    return [str(status), out.getvalue(), err.getvalue()]
`;

    let runBlock = null;

    // Give the runner a loaded Pyodide (from loadPyodide). Idempotent.
    function init(pyodide) {
        if (runBlock) return;
        pyodide.runPython(RUNNER, { filename: '<crush-guest-py>' });
        runBlock = pyodide.globals.get('__crush_run_block__');
        global.crushGuestPy.pyodide = pyodide;
    }

    function run(code, env) {
        if (!runBlock) throw new Error('@python blocks need Python, which has not been loaded on this page');
        const pyodide = global.crushGuestPy.pyodide;
        const pyEnv = pyodide.toPy(Object.assign({}, env));
        let result;
        try {
            const r = runBlock(code, pyEnv);
            result = r.toJs();
            r.destroy();
        } finally {
            pyEnv.destroy();
        }
        const [status, stdout, stderr] = result;
        if (status === 'unsupported') throw new Unsupported(stdout);
        if (status !== '0') throw new Error(stderr.trim() || `exit status ${status}`);
        return stdout;
    }

    global.crushGuestPy = { init, run, Unsupported, pyodide: null };
})(typeof self !== 'undefined' ? self : globalThis);
