# System Info Dashboard

> Source: `exosphere-apps/crates/apps/super-surfer/apps/sysinfo.crush`

A complete Super-Surfer app that queries system capabilities and renders an HTML
dashboard. Shows how Crush acts as a conductor over capability-gated host calls.

```crush
capability system readonly

fn main() {
    let hostname = sys.hostname()
    let os       = sys.os_name()
    let cpus     = sys.cpu_count()
    let cpu      = sys.cpu_usage()
    let memory   = sys.memory_info()
    let disk     = sys.disk_usage()
    let uptime   = sys.uptime()
    let processes = sys.process_count()
    let now      = time.now()

    // Round to 2 decimal places
    let mem_used  = math.round(memory.used_gb * 100) / 100
    let mem_total = math.round(memory.total_gb * 100) / 100
    let mem_pct   = math.round(memory.percent)
    let disk_pct  = math.round(disk.percent)
    let cpu_pct   = math.round(cpu)

    // Build an HTML card grid
    let html = "<div style='max-width:800px;margin:0 auto;padding:40px 32px;'>"
    let html = html + "<h1>System Information</h1>"
    let html = html + "<p>Generated at " + now + "</p>"

    let html = html + "<div style='display:grid;grid-template-columns:1fr 1fr;gap:16px;'>"

    // CPU card
    let html = html + "<div><div>CPU</div>"
    let html = html + "<div>" + str(cpu_pct) + "%</div>"
    let html = html + "<div>" + str(cpus) + " cores</div></div>"

    // Memory card
    let html = html + "<div><div>Memory</div>"
    let html = html + "<div>" + str(mem_pct) + "%</div>"
    let html = html + "<div>" + str(mem_used) + " / " + str(mem_total) + " GB</div></div>"

    let html = html + "</div>"
    let html = html + "</div>"

    return html
}
```

**What this shows:**
- `capability system readonly` — manifest-level capability declaration at the top of the file
- Struct field access: `memory.used_gb`, `disk.percent`
- `math.round()` for formatting
- `str()` coercion for concatenation
- Functions that return HTML strings (Super-Surfer renders the return value)
- The conductor pattern: Crush drives many host calls then assembles their results

## Capabilities Used

| Call | Capability |
|------|-----------|
| `sys.hostname()` | `sys.hostname` |
| `sys.cpu_usage()` | `sys.cpu_usage` |
| `sys.memory_info()` | `sys.memory_info` |
| `sys.disk_usage()` | `sys.disk_usage` |
| `time.now()` | `time.now` |
| `math.round()` | `math.round` (stdlib, no cap needed) |
