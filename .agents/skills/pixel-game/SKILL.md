---
name: pixel-game
description: Turn a one-sentence game idea into a runnable retro pixel game built with Pyxel (Python). Sets up a uv environment, writes a single-file game with in-code sprites and sounds, and verifies it with a headless scripted playtest. Use when the user asks to make, generate, or prototype a pixel / retro / 8-bit game from a short description.
license: MIT
compatibility: Needs bash and either uv or Homebrew (macOS/Linux). Works with any agent that can run shell commands; no MCP required.
metadata:
  engine: pyxel>=2.9
  version: "0.1.0"
---

# pixel-game: one sentence -> playable Pyxel game

`<skill_dir>` below means the directory containing this SKILL.md. Use its absolute path in commands.
Bundled files:
- `scripts/setup_env.sh` - creates the uv project and installs pyxel
- `scripts/playtest.py` - lint + headless scripted playtest; prints a text report with ASCII screen grids
- `references/pyxel-api.md` - verified API cheat sheet. **Read it before writing code.**
- `references/template_main.py` - required code skeleton
- `references/scenario_template.json` - playtest scenario skeleton

Do the steps in order. Do not ask the user clarifying questions; pick sensible defaults and state them.

## Step 1 - Spec (write `GAME_SPEC.md`)

Expand the sentence into a small, finishable design. Scope is ONE screen, ONE core mechanic,
title -> play -> game over -> restart. No levels, menus, save files or online features.

```markdown
# <Title>
Pitch: <user's sentence>
Genre: <dodge / shooter / platformer / puzzle / ...>
Screen: 160x120 @ 30 fps, default 16-color palette
Controls: <e.g. LEFT/RIGHT or A/D move, SPACE start/fire, R restart, ESC quit>
Player: <what it is, size in px, speed px/frame>
Objects: <enemies / pickups: size, spawn rule, speed>
Score: <how points are earned>
Difficulty: <how it ramps over time, with numbers>
Lose: <exact condition>
Sounds: <start, score/pickup, hit/game over>
Test plan: <inputs that exercise each control; how to force the lose condition>
```

Project folder: `games/<slug>/` under the current working directory (slug = short kebab-case English, e.g. `space-dodge`).

## Step 2 - Environment

```bash
bash <skill_dir>/scripts/setup_env.sh games/<slug>
```
It must print `ENV READY`. If it exits with code 2, uv is missing: show the user the install
commands it printed, ask them to install uv (or ask permission to run one), then re-run.
Never `pip install` into the system Python.

## Step 3 - Write `games/<slug>/main.py`

Copy `references/template_main.py` and fill it in. Hard rules (the playtest relies on them):

1. Single file, standard library + `pyxel` only. No `.pyxres`, no image/sound files, no `pyxel.load`.
2. `class App`; `__init__` calls `pyxel.init(160, 120, title=..., fps=30)`, sets up assets, and calls
   `pyxel.run(self.update, self.draw)` as its **last** line. The file ends with `App()`.
3. `self.scene` is one of the strings `"title"`, `"play"`, `"gameover"`. `self.score` is an int.
   The player is `self.player` with float attributes `x`, `y` (top-left) and `w`, `h`.
   Collections of objects are lists on `self` (e.g. `self.rocks`), each item with `x, y, w, h`.
4. SPACE or RETURN starts from title (use `btnp`). On game over, SPACE/RETURN/R restarts via `self.reset()`.
5. Randomness only via `pyxel.rndi` / `pyxel.rndf` (seeded playtests must be reproducible).
6. Sprites via `pyxel.images[0].set(u, v, [hex rows])` + `pyxel.blt(..., colkey=0)`; or plain
   shape primitives. Sounds via `pyxel.sounds[n].set(...)`, played with `pyxel.play(3, n)`.
7. Everything must be visible: a HUD with score, a title screen with the game name and
   "PRESS SPACE", and a game-over screen with score. Keep objects inside the 160x120 screen.
   Draw the HUD last so objects never cover it. Blinking text must alternate two visible colors
   (e.g. 7 and 13), never the background color.
8. Use only API names from `references/pyxel-api.md`. Angles are degrees.
9. Movement per frame, constant speeds (no delta time). Axis-aligned box collision:
   `a.x < b.x + b.w and b.x < a.x + a.w and a.y < b.y + b.h and b.y < a.y + a.h`
   (shrinking hitboxes by 1-2 px feels fairer).

## Step 4 - Write `games/<slug>/playtest.json`

Start from `references/scenario_template.json`. Adapt it so it proves the spec works:
- title at start; SPACE starts play
- every control moves the player in the right direction (check `app.player.x`/`y` after holding)
- score increases during play (check `app.score > 0` at a later frame)
- the lose condition is reachable **and caused by the game rule**. Force it with an `exec` input
  that moves a hazard onto the player, and put a check on the frame just before it proving the
  player is still alive. Schedule it early (an idle player in a dodge game may die by chance):
  ```json
  {"at": 99,  "expr": "app.scene == 'play' and len(app.rocks) > 0", "desc": "alive before forced hit"}
  {"at": 100, "exec": "r = app.rocks[0]; r.x, r.y = app.player.x, app.player.y"}
  {"at": 110, "expr": "app.scene == 'gameover'", "desc": "hit ends the game"}
  ```
  (the first and third go in `checks`, the second in `inputs`)
- restart works: press SPACE after game over, then check `app.scene == 'play'` and `app.score == 0`
Use `stop_when` only if nothing needs checking after it. Checks never reached count as failures,
and an `exec` that raises is reported as a failed check.

Frame timing: on frame `f` the harness applies inputs and `exec`s, then runs `update()` and
`draw()`, then evaluates checks/screenshots for `f`. A `hold` with `"to": 60` covers frames
30..59, so check its effect at frame 59 (or later). `press` holds the key for exactly one frame,
which `btnp` sees on that frame. With the same `seed` and inputs, runs are identical.

## Step 5 - Playtest loop (max 5 rounds)

```bash
cd games/<slug> && uv run python <skill_dir>/scripts/playtest.py main.py --scenario playtest.json
```
Read the whole report. It ends with `RESULT: PASS` or `RESULT: FAIL`.
- `LINT ERROR` -> fix the name using `references/pyxel-api.md`.
- `ERROR` traceback -> fix the crash at the reported line.
- `[FAIL]` check -> decide if the **game** or the **test** is wrong. Fix the game unless the test
  contradicts the spec. Never delete a check just to pass.
- Screens: the ASCII grid shows palette indices (`.` = background). Confirm the player, hazards,
  HUD and text appear where expected. If you can view images, also open the PNGs in `playtest_out/`.
- Heuristic warnings (blank screen, identical screens) are bugs unless explained.

Repeat until `RESULT: PASS` and the screens look right. If still failing after 5 rounds, stop and
report exactly what fails.

Optional: if your agent has the `pyxel` MCP server (`uvx pyxel-mcp`), you may also use its `validate`
and `run` tools, but `playtest.py` passing is the required gate.

## Step 6 - Deliver

Write `games/<slug>/README.md` with: title, pitch, controls, how to run, what the playtest verified.
Then reply to the user with:
- files created
- run command: `cd games/<slug> && uv run pyxel run main.py` (opens a window; ESC quits)
- controls and the one-line rules
- playtest result (checks passed, rounds needed) and anything not verified (feel, difficulty balance)

Optional web build (only if the user asks):
```bash
cd games/<slug> && uv run pyxel package . main.py && uv run pyxel app2html <slug>.pyxapp
```
