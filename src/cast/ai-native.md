# AI-Native CAST

## The doctrine

CAST is JSON. An agent that knows the [schema](README.md) can emit a complete
program as one JSON document — no lexer, no parser, no walker — validate it, and
hand it to the compiler:

```
agent output (JSON) ──▶ validate_json ──▶ compile_cast ──▶ CASM ──▶ crush-vm
          ▲
          └─ no front-end: the agent *is* the front-end
```

```rust,no_run
fn main() -> anyhow::Result<()> {
    let cast_json = r#"{
        "cast_version": "0.1.0", "entry": "main", "lang": null,
        "functions": { "main": { "params": [], "meta": {}, "body": [
            { "type": "ExprStmt", "expr": { "type": "CapabilityCall",
              "name": "io.print", "meta": {},
              "args": [ { "type": "StringLiteral", "value": "from an agent" } ] } }
        ] } }
    }"#;

    // 1. Schema check: errors carry a JSON path and, for common mistakes, a hint.
    if let Err(errors) = crush_cast::validate_json(cast_json) {
        for e in errors {
            eprintln!("{e}");
        }
        anyhow::bail!("invalid CAST");
    }

    // 2. CAST -> CASM IR -> CVM1, then run it.
    let program: crush_cast::Program = serde_json::from_str(cast_json)?;
    let casm = crush_frontend::compile_cast_owned(program)?;
    let vm = crush_lang_sdk::compile::casm_to_vm(&casm)?;
    let result = crush_lang_sdk::Runtime::new().run(&vm)?;
    assert_eq!(result.output, "from an agent\n");
    Ok(())
}
```

(For a standalone checkout, `crush_cast::validate_json` and
`crush_frontend::compile_cast` are the entry points; the version-gated
`crush_cast::Program::deserialize` currently rejects the front end's own `1.0.0`
stamp, so parse with `serde_json` as above or write `"cast_version": "0.1.0"`. See
[CAST serialization](README.md#serialization).)

Writing CAST rather than source buys an agent three things: no syntax errors (the
schema is the grammar), a validator that answers with a path and a hint, and
`meta` fields it can use to tag nodes with their own provenance.

## Program skeleton

```json
{
  "cast_version": "0.1.0",
  "entry": "main",
  "lang": "agent",
  "functions": { "main": { "params": [], "body": [ /* statements */ ], "meta": {} } },
  "ai_meta": null
}
```

`lang` may be any string — set it to identify the emitting agent in source maps.
`ai_meta` carries program-level AI metadata (below).

## AI nodes

An AI node is an object with `"type": "AI"` and an `ai_type` discriminator. There are
**seven expressions** (they yield a value and may appear wherever an expression can)
and **six statements** (coordination steps in a statement list).

### Expressions

| `ai_type` | Fields |
|---|---|
| `Query` | `query`, `result_type` (string or null), `context` (object) |
| `ToolChain` | `tools` (array of `{tool_name, parameters, result_binding?, condition?, required_capability?}`), `strategy`, `error_handling` |
| `AgentDelegation` | `task`, `agents` (ids or patterns), `delegation_strategy`, `expected_format?` |
| `LearningLoop` | `learning_target`, `strategy`, `adaptations` |
| `ContextAware` | `expression` (any expression), `requires_context`, `provides_context` |
| `SemanticMatch` | `target` (expression), `concept`, `confidence_threshold` |
| `Synthesize` | `output_type` (a [`CastType`](README.md#types)), `constraints`, `context_refs`, `examples?` |

### Statements

| `ai_type` | Fields |
|---|---|
| `GoalDeclaration` | `goal_id`, `description`, `success_criteria`, `priority`, `deadline?` |
| `ProgressUpdate` | `goal_id`, `progress` (0.0–1.0), `status_message`, `metrics` (name → number) |
| `KnowledgeSharing` | `knowledge_type`, `content` (any JSON), `recipients`, `retention_policy` |
| `CapabilityDiscovery` | `domain`, `requirements`, `discovery_strategy` |
| `AdaptationRequest` | `adaptation_type`, `reason`, `parameters` |
| `SemanticSwitch` | `target` (expression), `cases`: `[[label, statements], …]`, `fallback?` |

### The enumerations

| Field | Values |
|---|---|
| `strategy` (ToolChain) | **objects**: `{"type": "Sequential"}`, `{"type": "Parallel"}`, `{"type": "Conditional", "conditions": [..]}`, `{"type": "Retry", "max_attempts": 3, "backoff_strategy": {"type": "Fixed", "delay_ms": 100}}` (also `Exponential`, `Linear`) |
| `error_handling` | **objects**: `{"type": "FailFast"}`, `{"type": "ContinueOnError"}`, `{"type": "Retry", "max_retries": 2, "retry_condition": null}`, `{"type": "Fallback", "fallback_tools": [..]}` |
| `delegation_strategy` | strings `"FirstAvailable"` `"CapabilityMatch"` `"ParallelSplit"` `"Hierarchical"` `"Broadcast"` `"Best"` `"RoundRobin"`, or `{"Consensus": {"threshold": 0.66}}` |
| `learning_target` | `"UserBehavior"` `"ExecutionPatterns"` `"ErrorPatterns"` `"PerformanceMetrics"` `"ToolUsage"` |
| LearningLoop `strategy` | `"PatternRecognition"` `"StatisticalAnalysis"` `"MachineLearning"` `"RuleBased"` |
| `adaptations` items | `"OptimizeToolChain"` `"ImproveErrorHandling"` `"UpdateAgentSelection"` `"ModifyExecutionStrategy"` `"LearnNewPatterns"` |
| `priority` | `"Low"` `"Medium"` `"High"` `"Critical"` |
| `knowledge_type` | `"Pattern"` `"Solution"` `"BestPractice"` `"Warning"` `"Insight"` |
| `retention_policy` | `"Ephemeral"` `"Session"` `"Persistent"` or `{"Conditional": {"condition": ".."}}` |
| `discovery_strategy` | `"Broadcast"` `"Targeted"` `"Hierarchical"` `"LearningBased"` |
| `adaptation_type` | `"Performance"` `"Reliability"` `"Usability"` `"Compatibility"` `"Learning"` |

Note the asymmetry: `ToolChain.strategy` and `error_handling` are *internally
tagged objects* (`{"type": …}`), while `delegation_strategy` and the others are
plain strings. Mixing them up is the commonest validation failure; the validator's
hint for the delegation case says so.

Here is every node in one program. It is the schema's complete AI surface, checked
by `validate_json`, the compiler and the lowering:

<!-- check: cast-validate -->
```json
{
  "cast_version": "0.1.0",
  "entry": "main",
  "lang": null,
  "functions": {
    "main": {
      "params": [],
      "meta": {},
      "body": [
        { "type": "AI", "ai_type": "GoalDeclaration", "goal_id": "ship-it",
          "description": "Ship the release", "success_criteria": ["tests pass"],
          "priority": "High", "deadline": null },
        { "type": "AI", "ai_type": "ProgressUpdate", "goal_id": "ship-it",
          "progress": 0.5, "status_message": "halfway", "metrics": { "coverage": 0.8 } },
        { "type": "AI", "ai_type": "KnowledgeSharing", "knowledge_type": "Insight",
          "content": { "finding": "x" }, "recipients": ["agent://reviewers/*"],
          "retention_policy": "Session" },
        { "type": "AI", "ai_type": "CapabilityDiscovery", "domain": "code-review",
          "requirements": ["rust"], "discovery_strategy": "Broadcast" },
        { "type": "AI", "ai_type": "AdaptationRequest", "adaptation_type": "Performance",
          "reason": "review latency above target", "parameters": { "workers": 4 } },
        { "type": "VarDecl", "name": "answer", "type_hint": "String",
          "value": { "type": "AI", "ai_type": "Query", "query": "Capital of France?",
                     "result_type": "string", "context": {} } },
        { "type": "VarDecl", "name": "hits", "type_hint": "Any",
          "value": { "type": "AI", "ai_type": "ToolChain",
            "tools": [ { "tool_name": "search", "parameters": { "q": "x" }, "result_binding": "hits" } ],
            "strategy": { "type": "Sequential" }, "error_handling": { "type": "FailFast" } } },
        { "type": "VarDecl", "name": "verdict", "type_hint": "Any",
          "value": { "type": "AI", "ai_type": "AgentDelegation", "task": "Review the diff",
            "agents": ["agent://reviewers/*"],
            "delegation_strategy": { "Consensus": { "threshold": 0.66 } },
            "expected_format": "markdown" } },
        { "type": "VarDecl", "name": "insight", "type_hint": "Any",
          "value": { "type": "AI", "ai_type": "LearningLoop", "learning_target": "ToolUsage",
            "strategy": "RuleBased", "adaptations": ["OptimizeToolChain"] } },
        { "type": "VarDecl", "name": "scoped", "type_hint": "Any",
          "value": { "type": "AI", "ai_type": "ContextAware",
            "expression": { "type": "IntLiteral", "value": 1 },
            "requires_context": ["session.goal"], "provides_context": ["review.summary"] } },
        { "type": "VarDecl", "name": "match", "type_hint": "Any",
          "value": { "type": "AI", "ai_type": "SemanticMatch",
            "target": { "type": "StringLiteral", "value": "hi" },
            "concept": "greeting", "confidence_threshold": 0.8 } },
        { "type": "VarDecl", "name": "draft", "type_hint": "Any",
          "value": { "type": "AI", "ai_type": "Synthesize", "output_type": "String",
            "constraints": ["two sentences"], "context_refs": [], "examples": null } }
      ]
    }
  }
}
```

## Program-level metadata

`ai_meta` describes the program as a whole. It does not change compilation:

```json
{
  "ai_meta": {
    "description": "Review orchestration",
    "ai_tags": ["orchestration", "delegation"],
    "required_capabilities": ["ai.query", "ai.agent_delegation"],
    "execution_context": { "environment": [], "resources": [], "permissions": [], "dependencies": [] },
    "learning_objectives": ["optimize delegation latency"],
    "collaboration_patterns": [
      { "pattern_type": "consensus", "participants": ["reviewers"],
        "communication_style": "async", "decision_making": "vote" }
    ],
    "inputs": [], "outputs": [], "complexity": 3
  }
}
```

## What actually runs

**The AI nodes compile, but nothing executes them yet.** This is the single most
important thing to know before building on this chapter. The CAST compiler turns each
AI node into the matching `ai_*` CASM instruction, but the step that lowers CASM to
runnable CVM1 (`casm_to_vm`) turns every `ai_*` instruction into a `NOP`. Concretely
(crush-ast `v0.3.9`, tickets CRUSH-1 / CRUSH-32 / CRUSH-34):

- **AI statements are no-ops.** A program made of them runs and does nothing:

<!-- check: cast-json -->
```json
{
  "cast_version": "0.1.0", "entry": "main", "lang": null,
  "functions": { "main": { "params": [], "meta": {}, "body": [
    { "type": "AI", "ai_type": "GoalDeclaration", "goal_id": "g", "description": "d",
      "success_criteria": [], "priority": "Low", "deadline": null },
    { "type": "ExprStmt", "expr": { "type": "CapabilityCall", "name": "io.print", "meta": {},
      "args": [ { "type": "StringLiteral", "value": "after the goal" } ] } }
  ] } }
}
```

<!-- check: output -->
```text
after the goal
```

- **AI expressions produce no value.** Because the `NOP` pushes nothing, any program
  that *uses* the result (`VarDecl`, an argument, a `Return`) pops an empty stack and
  fails:

<!-- check: cast-json -->
<!-- check: runfail stack underflow -->
```json
{
  "cast_version": "0.1.0", "entry": "main", "lang": null,
  "functions": { "main": { "params": [], "meta": {}, "body": [
    { "type": "VarDecl", "name": "answer", "type_hint": "String",
      "value": { "type": "AI", "ai_type": "Query", "query": "Capital of France?",
                 "result_type": "string", "context": {} } }
  ] } }
}
```

  This is why the shipped `examples/cast/ai-query.cast.json` and
  `ai-orchestration.cast.json` validate but fail with `stack underflow` when run.

- **Three IR nodes have no bytecode at all.** `ai_capability_discovery`,
  `ai_adaptation_request` and `ai_semantic_switch` exist in the IR but not in CVM1.
  CVM1 has ten AI opcodes (`AI_QUERY`, `AI_SYNTHESIZE`, `AI_AGENT_DELEGATION`,
  `AI_SEMANTIC_MATCH`, `AI_LEARNING_LOOP`, `AI_CONTEXT_AWARE`, `AI_TOOLCHAIN`,
  `AI_GOAL_DECLARATION`, `AI_PROGRESS_UPDATE`, `AI_KNOWLEDGE_SHARING`).
- **The opcodes exist and are gated by capabilities, as stubs.** A hand-written CVM1
  `AI_QUERY` calls the host capability `ai_native.query` — and an embedder can
  register the ten `ai_native.*` stubs with
  `HostCapsBuilder::new().ai_native(true)`. Each stub returns the same thing, a map
  `{ok: true, kind: "<name>", echo: [...]}`, and does nothing else (no model call, no
  delegation, no learning). The CLI has no flag for it. This is the wiring a real
  backend will replace, so the gate names are the stable part:

<!-- check: asm-ai -->
<!-- check: output -->
```casm
.func main
    AI_QUERY "{\"q\": \"capital of France\"}"
    CAP_CALL "io.print" 1
    HALT
```

```text
{ok: true, kind: query, echo: []}
```

  The gates are `ai_native.query`, `.synthesize`, `.agent_delegation`,
  `.semantic_match`, `.learning_loop`, `.context_aware`, `.toolchain`,
  `.goal_declaration`, `.progress_update` and `.knowledge_sharing`. The same pattern
  holds for the DOM opcodes (`dom_native.*`) and `SPAWN`/`YIELD`/`AWAIT`
  (`concurrency_native.*`).

So today the AI-native surface is best understood as a **typed, validated schema for
agent intent** — a program an agent can emit, a tool can lint and an index can read —
not an executing orchestration runtime. Plan for the schema to be stable and the
execution to arrive later.

## Instruction mapping

| CAST node | CASM IR instruction | CVM1 opcode |
|---|---|---|
| `Query` | `ai_query` | `AI_QUERY` |
| `ToolChain` | `ai_tool_chain` | `AI_TOOLCHAIN` |
| `AgentDelegation` | `ai_agent_delegation` | `AI_AGENT_DELEGATION` |
| `LearningLoop` | `ai_learning_loop` | `AI_LEARNING_LOOP` |
| `ContextAware` | `ai_context_aware` | `AI_CONTEXT_AWARE` |
| `SemanticMatch` | `ai_semantic_match` | `AI_SEMANTIC_MATCH` |
| `Synthesize` | `ai_synthesize` | `AI_SYNTHESIZE` |
| `GoalDeclaration` | `ai_goal_decl` | `AI_GOAL_DECLARATION` |
| `ProgressUpdate` | `ai_progress_update` | `AI_PROGRESS_UPDATE` |
| `KnowledgeSharing` | `ai_knowledge_share` | `AI_KNOWLEDGE_SHARING` |
| `CapabilityDiscovery` | `ai_capability_discovery` | — |
| `AdaptationRequest` | `ai_adaptation_request` | — |
| `SemanticSwitch` | `ai_semantic_switch` | — |

("CVM1 opcode" is what the text assembler and the VM have; as explained above the
IR→CVM1 lowering does not currently emit any of them. The IR column is what
`crush_frontend::compile_cast` emits for each node.)

## See also

- [`examples/cast/`](https://github.com/nixpt/crush-ast/tree/main/examples/cast) in crush-ast — the example corpus (validates; most need host capabilities or hit the AI limits above to run)
- [CAST schema](README.md) — the non-AI nodes
- [CASM Instruction Reference](../casm/instructions.md#polyglot-concurrency-ai-and-dom)
