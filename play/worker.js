// Runs Crush off the main thread for the guide's Run buttons (interactive/crush-run.js).
// Adapted from crush-website's playground/worker.js. The VM stops at its
// instruction quota; the page also has a wall-clock timeout that terminates this
// worker and starts a fresh one. Each message is a fresh run: no state is shared.
import init, { execute } from './pkg/crush_web.js';

const ready = init();

self.onmessage = async ({ data }) => {
    await ready;
    const started = performance.now();
    try {
        const result = execute(data.source);
        self.postMessage({ id: data.id, ok: true, output: result.output, steps: result.steps, ms: performance.now() - started });
    } catch (err) {
        self.postMessage({ id: data.id, ok: false, error: String(err), ms: performance.now() - started });
    }
};

ready.then(() => self.postMessage({ ready: true }));
