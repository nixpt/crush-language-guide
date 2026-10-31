# Windows: the `ui.*` API

> Verified against crush-ast `bad81048` (v0.9.0, 2026-10-31) **up to the window**: the
> refusal, the error without a display and the API below were checked against the
> release binaries and crush-ast's source. The guide's checker has no desktop session,
> so it has not opened a window; crush-ast says the same of its own desktop backend
> (its tests drive the page headless, by element id).

Since 0.9.0 a Crush program can draw a window. This is a **separate package**:
`crush-gui` is in the prebuilt release tarball next to `crush`, but it is not part of
`cargo install crush-lang-sdk` (it brings a whole rendering stack, [arniko](https://crates.io/crates/arniko)),
and the browser build has no windows. `crush-run` refuses a `ui.*` program and
points you at `crush gui`.

```sh
crush gui run counter.crush --ui        # the umbrella CLI runs the crush-gui next to it
crush-gui run counter.crush --ui        # the same thing
```

## The grant

`--ui` unlocks every `ui.*` capability and nothing else (the other grants such as
`--fs` or `--net` work as they do for `crush-run`). Without it nothing runs:

```text
$ crush gui run counter.crush
[capabilities] counter.crush needs capabilities this run does not grant; nothing was run:
  --ui: ui.button, ui.next_event, ui.render, ui.title
```

With `--ui` on a machine with no desktop session, the run stops before the program
starts: `crush-gui: cannot open a window: no display (neither DISPLAY nor
WAYLAND_DISPLAY is set); run this where a desktop session exists`.

## The model: render a page, pull events

There are no callbacks. The program draws a page of HTML with `ui.render`, then asks
for the next thing the user did with `ui.next_event()`, which blocks until there is
one. A counter:

```text
fn page(count) {
    let html = "<h1>Counter</h1>"
    html = html + "<p id=\"count\">Count: " + count + "</p>"
    html = html + ui.button("dec", "-1", "outline")
    html = html + ui.button("inc", "+1", "accent")
    return html
}

ui.title("Counter")
let count = 0
ui.render(page(count))

while true {
    let ev = ui.next_event()
    if ev.kind == "close" { break }
    if ev.kind == "click" {
        if ev.id == "inc" { count = count + 1 }
        if ev.id == "dec" { count = count - 1 }
        ui.render(page(count))
    }
}
print("bye, count was " + count)
```

(This block is not run by the guide's checker, which has no window to open; it is
the repository's `examples/gui/counter.crush`, which crush-ast's own tests drive
headless.)

| Call | Returns | Notes |
|---|---|---|
| `ui.render(markup)` | | replace the whole page with `markup` (HTML) |
| `ui.next_event()` | event map | blocks until the next event; after the window closes it returns `close` every time |
| `ui.title(s)` | | the window title, read once when the window opens, so call it before the first `render` |
| `ui.escape(s)` | string | HTML-escape `s`; use it on any text you put into markup |
| `ui.button(id, label[, variant])` | markup | variants: `default` `destructive` `outline` `secondary` `ghost` `accent` |
| `ui.input(id[, value[, placeholder]])` | markup | a text input |
| `ui.card(title, body_html)` | markup | `body_html` is markup, not escaped |
| `ui.alert(message[, variant])` | markup | `info` `success` `warning` `error` |
| `ui.badge(text[, variant])` | markup | `default` `success` `warning` `error` `info` `purple` |

The markup helpers are conveniences: markup is plain HTML, and an element is
addressable if it has an `id` attribute.

### Events

Every event is a map with the same four string fields, `kind`, `id`, `value` and
`key`; a field that does not apply is `""`, so `ev.id` never needs an existence check.

| `kind` | When | `id` | `value` | `key` |
|---|---|---|---|---|
| `click` | a click on, or inside, an element with an `id` | that id | | |
| `input` | the text of an `<input id=…>` changed | the input | its new text | |
| `submit` | Enter in an `<input id=…>` | the input | its text | |
| `key` | a non-printing key (`Escape`, `Tab`, `ArrowUp`, …) | | | the key name |
| `close` | the window was closed | | | |

### Three things to know

- **`ui.render` replaces the page**, so an `<input>` loses focus and its caret every
  time. Do not re-render on every `input` event: remember `ev.value`, and redraw on
  `click` or `submit`.
- On `close` the program should `break`; it is not killed, so it can save its state.
- By crush-ast's design note, a `crush-gui` run has a larger default step quota (500
  million) because a window is long-lived, and the time spent waiting in `ui.next_event()` costs no steps.
