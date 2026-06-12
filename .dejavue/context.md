---
name: crush-language-guide
purpose: Standalone documentation book for the Crush language (Language + CAST + CASM sections), extracted from the exosphere monorepo book where it was buried.
dcp: DCP/1.0
---

# Context

<!-- The DCP instruction layer: what an agent should *do* in this repo.
     Source of truth — adapters (CLAUDE.md / AGENTS.md / …) are generated
     from this file via `dejavue export --target <tool>`. -->

## Operating Rules

- This is a **documentation-only repo** — no Rust code, no build artifacts. The source of truth for all technical claims is the exosphere codebase at `~/WORKSPACE/projects/exosphere/`.
- All docs must be accurate vs. the actual implementation. Before adding or changing any language feature, verify it in `crates/core/crush-lang/src/parser/lexer.rs` (keywords), `compiler.rs` (CASM ops), or `crates/core/crush-cast/src/lib.rs` (AST types).
- Never mark a feature "Future Feature" without checking the lexer and AST first — the crushed-book had a dozen false negatives (try/catch, structs, match, lambdas all implemented but mismarked).
- The exosphere skill at `projects/exosphere/.jagent/skills/crush-lang/SKILL.md` is the ground-truth agent reference. Keep this guide consistent with it.

## Build / Test

```bash
# Install mdBook once (if not present)
cargo install mdbook

# Preview locally (hot-reload)
mdbook serve  # opens http://localhost:3000

# Build static site
mdbook build  # output → book/
```

`book/` is gitignored — build output only, never commit.

## Architecture Map

```
src/
  README.md               # Intro + pipeline diagram
  SUMMARY.md              # mdBook table of contents
  crush/                  # Language chapter (syntax, types, operators, control flow, …)
  cast/                   # CAST AST chapter (spec + AI-native doctrine)
  casm/                   # CASM bytecode chapter (instructions, structure, serialization)
  examples/               # Real scripts extracted from exosphere repos
  appendix/               # Glossary, quick reference, language comparisons
.dejavue/                 # Repo-local agent memory (this file)
book.toml                 # mdBook config
```

Source material locations in exosphere:
- Crushed-book (origin): `docs/crushed-book/src/`
- Real scripts: `tests/language/`, `examples/`, `exosphere-apps/`, `walkers/tree-sitter-crush/`
- AI CAST examples: `examples/cast/`

## Memory

Decisions, blockers, and constraints are captured in `.dejavue/` — run
`dejavue context` for the boot packet and `dejavue recall <query>` to search.
