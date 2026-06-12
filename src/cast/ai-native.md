# AI-Native CAST

## The Doctrine

CAST is JSON. Any agent can emit it directly — no walker, no compiler front-end,
no source-to-AST pipeline required. An agent that understands the CAST schema can
produce a complete, runnable program as a single JSON document and hand it to
`crush_lang::compile_cast()` to get CASM bytecode.

This is the **AI-native doctrine** (s107 / EXO-175): the primary authoring surface
for AI agents in Exosphere is CAST, not Crush source code.

```
Agent output (JSON)  →  compile_cast()  →  CASM  →  NanoVM
                ↑
    No lexer, no parser, no walker.
    The agent IS the front-end.
```

Validation before compilation:

```rust
crush_cast::validate_json(&cast_json)?;  // schema check
let casm = crush_lang::compile_cast(&cast_json)?;
```

---

## Program Skeleton

Every CAST document has this top-level shape:

```json
{
  "cast_version": "0.1.0",
  "entry": "main",
  "lang": null,
  "functions": {
    "main": {
      "params": [],
      "body": [ /* Statement[] */ ],
      "meta": {}
    }
  },
  "ai_meta": null
}
```

Set `"lang": "agent"` (or any string) to identify the emitting agent in source maps.
Set `"ai_meta"` to attach program-level metadata (see below).

---

## AI Expression Nodes

Five `"type": "AI"` expression variants. They compile to the `ai_*` CASM instruction family.

### Query

Natural-language query execution. The runtime resolves `query` against the available
LLM/tool context and returns a typed value.

```json
{
  "type": "VarDecl",
  "name": "answer",
  "value": {
    "type": "AI",
    "ai_type": "Query",
    "query": "Answer this question concisely",
    "result_type": "string",
    "context": {
      "question": "What is the capital of France?"
    }
  },
  "type_hint": "String",
  "meta": {}
}
```

### ToolChain

Orchestrate a sequence (or parallel set) of tool calls. `result_binding` names where
each tool's output is stored for downstream tools.

```json
{
  "type": "AI",
  "ai_type": "ToolChain",
  "tools": [
    {
      "tool_name": "search",
      "parameters": { "query": "Python best practices" },
      "result_binding": "search_results"
    },
    {
      "tool_name": "analyze",
      "parameters": { "text": "search_results" },
      "result_binding": "analysis"
    },
    {
      "tool_name": "summarize",
      "parameters": { "input": "analysis" },
      "result_binding": "summary"
    }
  ],
  "strategy": { "type": "Sequential" },
  "error_handling": {
    "type": "Retry",
    "max_retries": 2,
    "retry_condition": "status != ok"
  }
}
```

**`strategy` options:** `Sequential` · `Parallel` · `Conditional` · `Retry`

**`error_handling` options:** `FailFast` · `ContinueOnError` · `Retry { max_retries }` · `Fallback`

### AgentDelegation

Delegate a task to one or more agents. The `delegation_strategy` controls how agents
are selected and results are combined.

```json
{
  "type": "AI",
  "ai_type": "AgentDelegation",
  "task": "Review the diff on branch agent/castbook/EXO-175 for unsoundness",
  "agents": ["agent://reviewers/*"],
  "delegation_strategy": { "Consensus": { "threshold": 0.66 } },
  "expected_format": "markdown"
}
```

**`delegation_strategy` options:**
`FirstAvailable` · `CapabilityMatch` · `ParallelSplit` · `Hierarchical` ·
`{ "Consensus": { "threshold": 0.0–1.0 } }` · `Broadcast` · `Best` · `RoundRobin`

### LearningLoop

Record patterns from execution and adapt future behavior.

```json
{
  "type": "AI",
  "ai_type": "LearningLoop",
  "learning_target": "ExecutionPatterns",
  "strategy": "PatternRecognition",
  "adaptations": ["OptimizeToolChain", "LearnNewPatterns"]
}
```

### ContextAware

Wrap an expression with explicit context requirements and provisions. The runtime
ensures the required context is present before evaluating `expression`.

```json
{
  "type": "AI",
  "ai_type": "ContextAware",
  "expression": {
    "type": "AI",
    "ai_type": "Query",
    "query": "Summarize the review consensus in two sentences",
    "result_type": "string",
    "context": {}
  },
  "requires_context": ["session.goal", "review.findings"],
  "provides_context": ["review.summary"]
}
```

---

## AI Statement Nodes

Five coordination statements at the top level of a function body. They do not
produce values — they signal intent to the agent runtime.

### GoalDeclaration

```json
{
  "type": "AI",
  "ai_type": "GoalDeclaration",
  "goal": "Ship EXO-175 with 80% schema coverage",
  "success_criteria": ["all examples validate", "no FP on real fleet"],
  "deadline": "2026-06-30T00:00:00Z",
  "meta": {}
}
```

### ProgressUpdate

```json
{
  "type": "AI",
  "ai_type": "ProgressUpdate",
  "goal_id": "EXO-175",
  "progress": 0.65,
  "status": "in-progress",
  "notes": "core examples done; AI-native chapter in flight",
  "meta": {}
}
```

### KnowledgeSharing

Share a learned insight with other agents in the fleet.

```json
{
  "type": "AI",
  "ai_type": "KnowledgeSharing",
  "knowledge_type": "Insight",
  "content": { "finding": "review consensus reached", "confidence": 0.9 },
  "recipients": ["agent://reviewers/*", "foreman"],
  "retention_policy": "Session",
  "meta": {}
}
```

### CapabilityDiscovery

Broadcast a request to find agents that can handle a domain.

```json
{
  "type": "AI",
  "ai_type": "CapabilityDiscovery",
  "domain": "code-review",
  "requirements": ["rust", "security-analysis"],
  "discovery_strategy": "Broadcast",
  "meta": {}
}
```

### AdaptationRequest

Request a runtime or coordination change.

```json
{
  "type": "AI",
  "ai_type": "AdaptationRequest",
  "adaptation_type": "Performance",
  "reason": "review latency above target",
  "parameters": { "max_parallel_reviews": 4 },
  "meta": {}
}
```

---

## Program-Level AI Metadata

The top-level `ai_meta` field lets an agent describe the whole program:

```json
{
  "ai_meta": {
    "description": "Demonstrates the AI-native orchestration primitives end to end.",
    "ai_tags": ["orchestration", "delegation", "learning"],
    "required_capabilities": ["ai.query", "ai.agent_delegation"],
    "execution_context": {
      "environment": ["exosphere"],
      "resources": [],
      "permissions": ["ai.query"],
      "dependencies": []
    },
    "learning_objectives": ["optimize delegation latency"],
    "collaboration_patterns": ["consensus", "broadcast"]
  }
}
```

These fields are metadata only — they do not affect CASM compilation — but the
Exosphere runtime uses them for scheduling, capability pre-checks, and audit logs.

---

## Complete Example: Agent Orchestration

The following is a real CAST document from `examples/cast/ai-orchestration.cast.json`.
It is the canonical reference for all five AI expression and statement types together.

```json
{
  "cast_version": "0.1.0",
  "entry": "main",
  "lang": null,
  "functions": {
    "main": {
      "params": [],
      "body": [
        {
          "type": "AI",
          "ai_type": "CapabilityDiscovery",
          "domain": "code-review",
          "requirements": ["rust", "security-analysis"],
          "discovery_strategy": "Broadcast",
          "meta": {}
        },
        {
          "type": "VarDecl",
          "name": "review",
          "value": {
            "type": "AI",
            "ai_type": "AgentDelegation",
            "task": "Review the diff on branch agent/castbook/EXO-175 for unsoundness",
            "agents": ["agent://reviewers/*"],
            "delegation_strategy": { "Consensus": { "threshold": 0.66 } },
            "expected_format": "markdown"
          },
          "type_hint": "Any",
          "meta": {}
        },
        {
          "type": "AI",
          "ai_type": "KnowledgeSharing",
          "knowledge_type": "Insight",
          "content": { "finding": "review consensus reached", "confidence": 0.9 },
          "recipients": ["agent://reviewers/*", "foreman"],
          "retention_policy": "Session",
          "meta": {}
        },
        {
          "type": "VarDecl",
          "name": "insight",
          "value": {
            "type": "AI",
            "ai_type": "LearningLoop",
            "learning_target": "ExecutionPatterns",
            "strategy": "PatternRecognition",
            "adaptations": ["OptimizeToolChain", "LearnNewPatterns"]
          },
          "type_hint": "Any",
          "meta": {}
        },
        {
          "type": "AI",
          "ai_type": "AdaptationRequest",
          "adaptation_type": "Performance",
          "reason": "review latency above target",
          "parameters": { "max_parallel_reviews": 4 },
          "meta": {}
        },
        {
          "type": "VarDecl",
          "name": "summary",
          "value": {
            "type": "AI",
            "ai_type": "ContextAware",
            "expression": {
              "type": "AI",
              "ai_type": "Query",
              "query": "Summarize the review consensus in two sentences",
              "result_type": "string",
              "context": {}
            },
            "requires_context": ["session.goal", "review.findings"],
            "provides_context": ["review.summary"]
          },
          "type_hint": "Any",
          "meta": {}
        },
        {
          "type": "Export",
          "name": "summary",
          "value": { "type": "Var", "name": "summary" },
          "meta": {}
        }
      ],
      "meta": {}
    }
  },
  "ai_meta": {
    "description": "Demonstrates the AI-native orchestration primitives end to end.",
    "ai_tags": ["orchestration", "delegation", "learning"],
    "required_capabilities": ["ai.query", "ai.agent_delegation"]
  }
}
```

---

## CASM Instructions Emitted

| CAST node | CASM instruction |
|-----------|-----------------|
| `AI / Query` | `ai_query` |
| `AI / ToolChain` | `ai_tool_chain` |
| `AI / AgentDelegation` | `ai_agent_delegation` |
| `AI / LearningLoop` | `ai_learning_loop` |
| `AI / ContextAware` | `ai_context_aware` |
| `AI / GoalDeclaration` | `ai_goal_decl` |
| `AI / ProgressUpdate` | `ai_progress_update` |
| `AI / KnowledgeSharing` | `ai_knowledge_share` |
| `AI / CapabilityDiscovery` | `ai_capability_discovery` |
| `AI / AdaptationRequest` | (maps to `ai_context_aware` + runtime signal) |

---

## See Also

- [`examples/cast/`](https://github.com/nixpt/exosphere/tree/main/examples/cast) — canonical example corpus in the exosphere repo
- [CAST Base Spec](README.md) — statement and expression node reference (v0.3 base)
- [CASM Instruction Reference](../casm/instructions.md) — the `ai_*` instruction category
