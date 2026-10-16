# Showcase: awesome-crush

[nixpt/awesome-crush](https://github.com/nixpt/awesome-crush) collects real Crush
programs, each written by a different LLM that was given little more than "can you
learn crush?" and a pointer to crush-ast. Its README tells the story of each one:
which constraints the authors hit, and the compiler bugs they found along the way.

> Every program below was run on crush-ast `3ae0b4a` (2026-10-16) with
> `crush-run run --max-steps 500000000 FILE < /dev/null`. All of them ran to their
> documented conclusion. The outputs quoted are what that run printed.

## The programs

| Program | Author (from the awesome-crush README) | What it is | Ends with | VM steps |
|---|---|---|---|---|
| `games/pong.crush` | Ornith-1.5-35B-A3B | self-playing Pong, scalar state threaded through recursion | `draw 0-0` | 2,303,450 |
| `games/tictactoe.crush` | foreman-v2 (Qwen3.8-27B fine-tune) | board packed as one base-3 integer | `game over: draw` | 117,606 |
| `games/lights_out.crush` | qwen38-base (Qwen3.8-27B) | 25-bit bitfield board, solves itself | `board solved in 8 moves` | 189,907 |
| `games/game_of_life.crush` | Claude (hand-written) | Conway's Life with `@module`/`@decision`/`@invariant` | a blinker oscillating | 286,738 |
| `games/blackjack.crush` | OpenCode | six self-played rounds with a bankroll | `final bankroll: 120` | 5,631 |
| `games/pong-deepseek.crush` | cece / bro (DeepSeek-v4) | a second, independent Pong | `time's up — final score: left 0 : 0 right` | 1,245,978 |
| `games/fifteen_puzzle.crush` | bro (DeepSeek-v4) | IDA* solver, tiles packed as nibbles in one integer | `solved in 6 moves.` | 77,324 |
| `games/breakout.crush` | cece (DeepSeek-v4) | brick-breaker, 30 bricks as bits | `out of ticks — final score: 140` | 5,593,804 |
| `games/rps_tournament.crush` | bro (Muse) | rock-paper-scissors bot round-robin | `champion: Cycler!` and an ASCII trophy | 3,289 |
| `forth/forth.crush` | Buffy (DeepSeek-v4) | a Forth interpreter | five Forth programs run | 63,281 |
| `brainfuck/brainfuck.crush` | Buffy (DeepSeek-v4) | a Brainfuck interpreter | `Hello World!`, A–Z, 0–9 | 94,146 |
| `caison/caison-parsor.crush` | bro (the commit author; the README names no model) | a CAISON parser written in Crush | the parsed document as JSON | 72,957 |
| `agents/log-triage/log_triage.crush` | Claude (Opus 5.5) | an agent-written tool that declares `@capabilities` | see below | — |

The step counts matter: the VM's default budget is 1,000,000 instructions, so the
larger games need `--max-steps`. Without it, `crush-run run games/pong.crush` stops
with `[runtime] instruction quota exceeded (1000000)`.

`games/blackjack_interactive.crush` (also in crush-ast's `examples/crush/`) reads
its moves with `io.read()`. Feed it input, or redirect from `/dev/null` so it sees
end-of-file and leaves the table instead of waiting:

```console
$ printf '10\nh\ns\n0\n' | crush-run run games/blackjack_interactive.crush
...
Bankroll: $110
Bet (1-110) — 0 or q to leave:

You leave the table with $110.
```

## A taste of the output

Game of Life's blinker, from `crush run games/game_of_life.crush`:

```text
Conway's Game of Life -- 5x5, blinker seed, dead border (no wrap)
gen 0:
.....
.....
.###.
.....
.....

gen 1:
.....
..#..
..#..
..#..
.....
```

The Forth interpreter running Forth programs on the Crush VM:

```text
Forth-in-Crush: a Forth interpreter running on the Crush VM

--- stack arithmetic: (3+4)^2 ---
source: 3 4 + dup * .s .

stack(1): 49 
49
(final stack depth: 0)
```

and the Brainfuck interpreter's Hello World:

```text
--- hello world ---
source: ++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++.

Hello World!
```

## What the collection shows about the language

- **Older programs avoid features that now exist.** The games thread all state
  through recursive calls and pack boards into integers, because when they were
  written arrays couldn't be mutated in place and there was no random-number
  capability. Both work now (`a[i] = v`, `math.seed` / `math.random_int`), as do
  closures and struct methods, and the programs still run unchanged.
- **Capabilities are visible.** The `log-triage` agent tool starts with
  `@capabilities [fs.list, fs.cat, time.now_iso]`. `crush-run caps` reports what it
  needs before anything runs, a run without those grants is refused, and a variant
  that adds `net.http_post` without declaring it is refused at compile time:

```console
$ crush-run caps log_triage.crush
log_triage.crush
  declares: fs.list, fs.cat, time.now_iso
  needs these grants to run:
    --fs: fs.cat, fs.list
    --time: time.now_iso
  also uses (ambient): arr_set, io.print, push, str.concat, str.contains, str.ends_with, str.pad_left, str.pad_right, str.split, str.trim
$ crush-run run --fs --fs-root sample-logs --time tampered/undeclared.crush
[compile] the program uses a capability not declared in @capabilities: net.http_post
  add it to @capabilities, or stop using it
```

(`crushc` doesn't apply that check yet: crush-ast
[#258](https://github.com/nixpt/crush-ast/issues/258).)

## Run them yourself

```sh
git clone https://github.com/nixpt/awesome-crush
cd awesome-crush
crush run --max-steps 50000000 games/breakout.crush
crush run games/fifteen_puzzle.crush
crush run forth/forth.crush
```
