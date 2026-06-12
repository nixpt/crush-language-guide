# Async LLM Dashboard

> Source: `examples/crush-pipefish-dashboard/dashboard.crush`

A Super-Surfer web application that integrates with pipefish (the local LLM server)
via the `seahorse` module. Demonstrates `async`/`await`, DOM manipulation, event
listeners, and try/catch around async calls.

```crush
import seahorse

let current_model = "llama3.2";
let is_generating = false;

fn init() {
    dom.set_text_content(dom.get_element_by_id("status"), "Ready");
    dom.set_text_content(dom.get_element_by_id("model-name"), current_model);
    update_model_list();
    setup_event_handlers();
    print("Dashboard initialized");
}

fn setup_event_handlers() {
    dom.add_event_listener(
        dom.get_element_by_id("generate-btn"),
        "click",
        "on_generate_click"
    );
    dom.add_event_listener(
        dom.get_element_by_id("model-select"),
        "change",
        "on_model_change"
    );
}

fn on_generate_click() {
    if is_generating {
        return;
    }

    let prompt_input = dom.get_element_by_id("prompt-input");
    let prompt = dom.get_attribute(prompt_input, "value");

    if prompt == "" {
        show_error("Please enter a prompt");
        return;
    }

    is_generating = true;
    update_ui_for_generation(true);

    let temperature = get_temperature();
    let max_tokens = get_max_tokens();

    // Fire and forget — UI stays responsive while generation runs
    generate_async(current_model, prompt, temperature, max_tokens);
}

// async fn runs in the background; the caller is not blocked
async fn generate_async(model: String, prompt: String, temp: Float, max_tokens: Int) {
    try {
        let result = await seahorse.generate(model, prompt, {
            "temperature": temp,
            "max_tokens": max_tokens
        });
        display_result(result);
    } catch error {
        show_error("Generation failed: " + error);
    }

    is_generating = false;
    update_ui_for_generation(false);
}
```

**What this shows:**

- `import module` — loads the `seahorse` LLM client module
- `dom.get_element_by_id()` / `dom.set_text_content()` / `dom.get_attribute()` — DOM capability calls
- `dom.add_event_listener(element, event, handler_name)` — string-named event handler wiring
- `async fn` — declares a function that runs asynchronously
- `await expr` — suspends until the async value resolves
- Fire-and-forget: `generate_async(...)` is called without `await` so the caller returns immediately
- `try { await ... } catch error { ... }` — exception handling around async operations
- Module-level mutable state: `is_generating` guards against double-submission

## Async/Await Basics

```crush
// Simple sequential await
io.print("Test: Sequential awaits")
await async.sleep(50)
io.print("First sleep done")
await async.sleep(50)
io.print("Second sleep done")
```

> Source: `tests/language/async_test.crush`
