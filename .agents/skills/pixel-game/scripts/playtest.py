#!/usr/bin/env python3
"""Headless playtest harness for single-file Pyxel games.

Agent-neutral: needs only Python + pyxel (no MCP, no vision model).

    uv run python playtest.py main.py                       # lint + smoke run
    uv run python playtest.py main.py --scenario playtest.json --out playtest_out

What it does
  1. Lint: compiles the script and checks every `pyxel.<name>` it uses exists.
  2. Runs the game headlessly (pyxel.run is intercepted; frames are driven here),
     injecting scheduled key input, executing forced actions, evaluating checks.
  3. Writes PNG screenshots plus a text report with coarse ASCII screen grids
     so text-only models can "see" each captured frame.

Exit code: 0 = all checks passed, 1 = crash / failed check / lint error.

Scenario JSON (all keys optional):
{
  "seed": 1,                 # pyxel.rseed() value, for reproducible runs
  "frames": 600,             # frame budget
  "inputs": [
    {"at": 10, "press": ["KEY_RETURN"]},              # held for 1 frame
    {"from": 30, "to": 90, "hold": ["KEY_LEFT"]},     # held on frames [30, 90)
    {"at": 200, "exec": "app.player.x = 80"}          # run Python before update()
  ],
  "watch": ["app.scene", "app.score"],   # sampled every `watch_every` frames
  "watch_every": 30,
  "checks": [
    {"at": 5, "expr": "app.scene == 'title'", "desc": "title screen shown"},
    {"at": "end", "expr": "app.score > 0"}
  ],
  "screenshots": [5, 60, "end"],
  "stop_when": "app.scene == 'gameover'"  # optional early stop (checks at "end" still run)
}
Expressions are evaluated with `app` (the object owning update()), `pyxel`,
`g` (the game module's globals) and `f` (current frame index) in scope.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import runpy
import struct
import sys
import traceback
import zlib
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pyxel  # noqa: E402

HEX = "0123456789abcdef"
DEFAULT_SCENARIO = {
    "seed": 1,
    "frames": 360,
    "inputs": [
        {"at": 15, "press": ["KEY_RETURN"]},
        {"at": 16, "press": ["KEY_SPACE"]},
        {"from": 40, "to": 80, "hold": ["KEY_LEFT"]},
        {"from": 80, "to": 120, "hold": ["KEY_RIGHT"]},
        {"from": 120, "to": 150, "hold": ["KEY_UP"]},
        {"from": 150, "to": 180, "hold": ["KEY_DOWN"]},
    ],
    "watch": [],
    "checks": [],
    "screenshots": [5, 30, 100, 200, "end"],
}


class _Done(Exception):
    pass


class _Quit(Exception):
    pass


# ---------------------------------------------------------------- lint


def lint(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as e:
        return [f"SyntaxError line {e.lineno}: {e.msg}"], warnings

    seen_init = seen_run = False
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "pyxel"
        ):
            if node.attr == "init":
                seen_init = True
            if node.attr == "run":
                seen_run = True
            if not hasattr(pyxel, node.attr) and not isinstance(node.ctx, ast.Store):
                errors.append(
                    f"line {node.lineno}: pyxel.{node.attr} does not exist in pyxel {pyxel.VERSION}"
                )
        if isinstance(node, ast.Import) and any(a.name == "random" for a in node.names):
            warnings.append(
                f"line {node.lineno}: uses `random`; prefer pyxel.rndi/rndf so seeded playtests are reproducible"
            )
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "load" and isinstance(node.func.value, ast.Name) and node.func.value.id == "pyxel":
                warnings.append(f"line {node.lineno}: pyxel.load() needs a .pyxres file; prefer in-code assets")
    if not seen_init:
        errors.append("pyxel.init(...) is never called")
    if not seen_run:
        errors.append("pyxel.run(update, draw) is never called")
    return errors, warnings


# ---------------------------------------------------------------- screen capture


def screen_indices() -> bytes:
    w, h = pyxel.width, pyxel.height
    return bytes(pyxel.screen.data_ptr()[: w * h])


def write_png(path: Path, idx: bytes, scale: int = 3) -> None:
    w, h = pyxel.width, pyxel.height
    pal = [((c >> 16) & 255, (c >> 8) & 255, c & 255) for c in pyxel.colors]
    pal += [(0, 0, 0)] * (256 - len(pal))
    rows = []
    for y in range(h):
        line = bytearray()
        for x in range(w):
            line.extend(bytes(pal[idx[y * w + x]]) * scale)
        rows.extend([b"\x00" + bytes(line)] * scale)
    raw = b"".join(rows)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w * scale, h * scale, 8, 2, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    )


def ascii_grid(idx: bytes, cols: int = 40) -> list[str]:
    """Downsample to a hex grid: each cell shows the most common non-background color."""
    w, h = pyxel.width, pyxel.height
    cell = max(1, w // cols)
    counts = [0] * 256
    for c in idx:
        counts[c] += 1
    bg = max(range(256), key=counts.__getitem__)
    out = []
    for cy in range(0, h, cell * 2 if cell > 1 else 1):
        row = []
        ch = cell * 2 if cell > 1 else 1
        for cx in range(0, w, cell):
            tally: dict[int, int] = {}
            for y in range(cy, min(cy + ch, h)):
                base = y * w
                for x in range(cx, min(cx + cell, w)):
                    c = idx[base + x]
                    if c != bg:
                        tally[c] = tally.get(c, 0) + 1
            row.append(HEX[max(tally, key=tally.get) & 15] if tally else ".")
        out.append("".join(row))
    return out


def screen_stats(idx: bytes) -> dict:
    counts: dict[int, int] = {}
    for c in idx:
        counts[c] = counts.get(c, 0) + 1
    bg, bg_n = max(counts.items(), key=lambda kv: kv[1])
    return {"colors": len(counts), "background": bg, "non_background_pct": round(100 * (1 - bg_n / len(idx)), 1)}


# ---------------------------------------------------------------- run


def run_game(script: Path, sc: dict, out: Path) -> dict:
    frames = int(sc.get("frames", 600))
    seed = sc.get("seed")
    watch = sc.get("watch", [])
    watch_every = int(sc.get("watch_every", 30))
    stop_when = sc.get("stop_when")
    shots = sc.get("screenshots", [])
    checks = sc.get("checks", [])

    held_at: list[set[str]] = [set() for _ in range(frames + 1)]
    execs: dict[int, list[str]] = {}
    for item in sc.get("inputs", []):
        if "exec" in item:
            execs.setdefault(int(item["at"]), []).append(item["exec"])
        keys = item.get("press") or item.get("hold") or []
        for k in keys:
            if not isinstance(getattr(pyxel, k, None), int):
                raise SystemExit(f"scenario error: unknown key constant {k!r}")
        if "press" in item:
            lo, hi = int(item["at"]), int(item["at"]) + 1
        elif "hold" in item:
            lo, hi = int(item["from"]), int(item["to"])
        else:
            continue
        for f in range(max(0, lo), min(hi, frames)):
            held_at[f].update(keys)

    report: dict = {
        "script": str(script),
        "pyxel": pyxel.VERSION,
        "status": "ok",
        "frames_run": 0,
        "errors": [],
        "checks": [],
        "watch": [],
        "screens": [],
    }
    ctx: dict = {}

    def ev(expr: str, f: int):
        return eval(expr, {"pyxel": pyxel, **ctx, "f": f})

    def capture(f: int, label: str) -> None:
        idx = screen_indices()
        png = out / f"frame_{label}.png"
        write_png(png, idx)
        report["screens"].append({"frame": f, "label": label, "png": str(png), **screen_stats(idx), "grid": ascii_grid(idx)})

    evaluated: set[int] = set()

    def run_checks(f: int, is_end: bool) -> None:
        for i, c in enumerate(checks):
            at = c.get("at", "end")
            if (at == "end" and is_end) or (at != "end" and int(at) == f):
                evaluated.add(i)
                try:
                    ok = bool(ev(c["expr"], f))
                    err = None
                except Exception as e:  # noqa: BLE001
                    ok, err = False, f"{type(e).__name__}: {e}"
                report["checks"].append(
                    {"frame": f, "expr": c["expr"], "desc": c.get("desc", ""), "pass": ok, **({"error": err} if err else {})}
                )

    def sample_watch(f: int) -> None:
        if not watch:
            return
        vals = {}
        for w in watch:
            try:
                vals[w] = repr(ev(w, f))
            except Exception as e:  # noqa: BLE001
                vals[w] = f"<{type(e).__name__}: {e}>"
        report["watch"].append({"frame": f, **vals})

    def drive(update, draw):
        app = getattr(update, "__self__", None)
        fn = getattr(update, "__func__", update)
        ctx.update(app=app, g=getattr(fn, "__globals__", {}))
        prev: set[str] = set()
        last = frames - 1
        f = 0
        for f in range(frames):
            pyxel.frame_count = f
            cur = held_at[f]
            for k in cur - prev:
                pyxel.set_btn(getattr(pyxel, k), True)
            for k in prev - cur:
                pyxel.set_btn(getattr(pyxel, k), False)
            prev = cur
            for code in execs.get(f, []):
                try:
                    exec(code, {"pyxel": pyxel, **ctx, "f": f})
                except Exception as e:  # noqa: BLE001
                    report["checks"].append({"frame": f, "expr": f"exec: {code}", "desc": "scenario exec input",
                                             "pass": False, "error": f"{type(e).__name__}: {e}"})
            update()
            draw()
            report["frames_run"] = f + 1
            stop = bool(stop_when and ev(stop_when, f))
            is_end = f == last or stop
            if f in shots:
                capture(f, str(f))
            if f % watch_every == 0 or is_end:
                sample_watch(f)
            run_checks(f, is_end=False)
            if is_end:
                if "end" in shots:
                    capture(f, "end")
                run_checks(f, is_end=True)
                if stop:
                    report["stopped_by"] = stop_when
                break
            pyxel.flip()
        raise _Done

    real_init = pyxel.init

    def headless_init(*args, **kwargs):
        kwargs["headless"] = True
        kwargs["fps"] = 10000  # flip() won't sleep; logic is frame-based anyway
        real_init(*args, **kwargs)
        if seed is not None:
            pyxel.rseed(int(seed))  # seed before App.__init__ draws any random numbers
        os.chdir(script.parent)

    def fake_quit():
        raise _Quit

    pyxel.init, pyxel.run, pyxel.quit = headless_init, drive, fake_quit
    sys.path.insert(0, str(script.parent))
    try:
        runpy.run_path(str(script), run_name="__main__")
        report["status"] = "error"
        report["errors"].append("script finished without calling pyxel.run()")
    except _Done:
        pass
    except _Quit:
        report["status"] = "quit"
    except SystemExit as e:
        report["status"] = "error"
        report["errors"].append(f"SystemExit({e.code}) raised by game")
    except Exception:  # noqa: BLE001
        report["status"] = "crashed"
        report["errors"].append(traceback.format_exc(limit=8))
        try:
            capture(report["frames_run"], "crash")
        except Exception:  # noqa: BLE001
            pass
    for i, c in enumerate(checks):
        if i not in evaluated:
            report["checks"].append({"frame": c.get("at", "end"), "expr": c["expr"], "desc": c.get("desc", ""),
                                     "pass": False, "error": "not reached (run stopped or crashed first)"})
    return report


# ---------------------------------------------------------------- main


def render_text(rep: dict, lint_err: list[str], lint_warn: list[str]) -> str:
    L = [f"# Playtest report: {rep.get('script')}  (pyxel {pyxel.VERSION})", ""]
    L.append(f"status: {rep.get('status')}   frames_run: {rep.get('frames_run')}")
    if rep.get("stopped_by"):
        L.append(f"stopped early by: {rep['stopped_by']}")
    for e in lint_err:
        L.append(f"LINT ERROR: {e}")
    for w in lint_warn:
        L.append(f"lint warning: {w}")
    for e in rep.get("errors", []):
        L += ["", "ERROR:", e.rstrip()]
    if rep.get("checks"):
        L += ["", "## Checks"]
        for c in rep["checks"]:
            mark = "PASS" if c["pass"] else "FAIL"
            L.append(f"[{mark}] f={str(c['frame']):>4}  {c['expr']}  {('- ' + c['desc']) if c['desc'] else ''}"
                     + (f"  ({c['error']})" if c.get("error") else ""))
    if rep.get("watch"):
        L += ["", "## Watch (rows identical to the previous one are skipped)"]
        prev = None
        rows = rep["watch"]
        for i, w in enumerate(rows):
            vals = {k: v for k, v in w.items() if k != "frame"}
            if vals == prev and i != len(rows) - 1:
                continue
            prev = vals
            L.append(f"f={w['frame']:>4}  " + "  ".join(f"{k}={v}" for k, v in vals.items()))
    if rep.get("screens"):
        L += ["", "## Screens (hex = palette index of dominant non-background color, '.' = background)"]
        for s in rep["screens"]:
            L.append(f"\n### frame {s['label']}  colors={s['colors']} bg={s['background']} "
                     f"non_bg={s['non_background_pct']}%  -> {s['png']}")
            L += s["grid"]
    warns = []
    for s in rep.get("screens", []):
        if s["colors"] <= 1:
            warns.append(f"frame {s['label']} is a single solid color (blank screen?)")
    grids = [tuple(s["grid"]) for s in rep.get("screens", [])]
    if len(grids) >= 3 and len(set(grids)) == 1:
        warns.append("all captured screens are identical (game not animating / input ignored?)")
    if warns:
        L += ["", "## Heuristic warnings"] + [f"- {w}" for w in warns]
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", type=Path)
    ap.add_argument("--scenario", type=Path, help="scenario JSON (default: built-in smoke test)")
    ap.add_argument("--out", type=Path, default=None, help="output dir (default: <script dir>/playtest_out)")
    ap.add_argument("--lint-only", action="store_true")
    a = ap.parse_args()

    script = a.script.resolve()
    if not script.exists():
        print(f"no such file: {script}")
        return 1
    out = (a.out or script.parent / "playtest_out").resolve()
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("frame_*.png"):
        old.unlink()

    lint_err, lint_warn = lint(script)
    if a.lint_only or any(e.startswith("SyntaxError") for e in lint_err):
        print(render_text({"script": str(script), "status": "lint", "frames_run": 0}, lint_err, lint_warn))
        return 1 if lint_err else 0

    sc = json.loads(a.scenario.read_text(encoding="utf-8")) if a.scenario else DEFAULT_SCENARIO
    rep = run_game(script, sc, out)
    text = render_text(rep, lint_err, lint_warn)
    (out / "report.txt").write_text(text, encoding="utf-8")
    (out / "report.json").write_text(json.dumps({**rep, "lint_errors": lint_err, "lint_warnings": lint_warn}, indent=2), encoding="utf-8")
    print(text)
    print(f"(report saved to {out / 'report.txt'})")
    failed = rep["status"] not in ("ok",) or lint_err or any(not c["pass"] for c in rep["checks"])
    print("RESULT:", "FAIL" if failed else "PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
