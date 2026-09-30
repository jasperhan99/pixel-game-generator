# Pyxel 2.9 API cheat sheet (verified against pyxel 2.9.9)

Only use names listed here unless you have checked them. `playtest.py` lint fails on any
`pyxel.<name>` that does not exist.

## App lifecycle
```python
pyxel.init(width, height, title="Pyxel", fps=30, quit_key=pyxel.KEY_ESCAPE)
pyxel.run(update, draw)      # never returns; call it LAST in App.__init__
pyxel.quit()
pyxel.frame_count            # int, frames since start
pyxel.width, pyxel.height
```

## Input
```python
pyxel.btn(key)               # held
pyxel.btnp(key)              # pressed this frame; btnp(key, hold, repeat) for auto-repeat
pyxel.btnr(key)              # released this frame
pyxel.mouse_x, pyxel.mouse_y; pyxel.mouse(True)   # show cursor
```
Keys: `KEY_LEFT KEY_RIGHT KEY_UP KEY_DOWN KEY_SPACE KEY_RETURN KEY_ESCAPE KEY_Z KEY_X KEY_R KEY_Q KEY_A..KEY_Z KEY_0..KEY_9`
Mouse: `MOUSE_BUTTON_LEFT MOUSE_BUTTON_RIGHT`
Gamepad: `GAMEPAD1_BUTTON_A GAMEPAD1_BUTTON_B GAMEPAD1_BUTTON_START GAMEPAD1_BUTTON_DPAD_LEFT/RIGHT/UP/DOWN`

Idiom: `if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT):`

## Drawing (all coords are floats, colors are ints 0-15)
```python
pyxel.cls(col)
pyxel.pset(x, y, col)
pyxel.line(x1, y1, x2, y2, col)
pyxel.rect(x, y, w, h, col);  pyxel.rectb(x, y, w, h, col)      # filled / border
pyxel.circ(x, y, r, col);     pyxel.circb(x, y, r, col)
pyxel.elli(x, y, w, h, col);  pyxel.ellib(x, y, w, h, col)
pyxel.tri(x1, y1, x2, y2, x3, y3, col); pyxel.trib(...)
pyxel.text(x, y, "TEXT", col)          # built-in font: 4x6 px per char (FONT_WIDTH/FONT_HEIGHT)
pyxel.blt(x, y, img, u, v, w, h, colkey=None, rotate=0, scale=1)  # img = bank 0-2; negative w/h flips
pyxel.bltm(x, y, tm, u, v, w, h, colkey=None)                      # draw tilemap tm (0-7)
pyxel.camera(x, y); pyxel.camera()     # offset / reset
pyxel.clip(x, y, w, h); pyxel.clip()
pyxel.pal(col1, col2); pyxel.pal()     # swap colors / reset
pyxel.dither(alpha)                    # 0.0-1.0
```
Centered text: `x = (pyxel.width - len(s) * pyxel.FONT_WIDTH) // 2`

## Palette (default 16 colors)
| idx | const | look | idx | const | look |
|---|---|---|---|---|---|
| 0 | COLOR_BLACK | black | 8 | COLOR_RED | crimson |
| 1 | COLOR_NAVY | dark navy | 9 | COLOR_ORANGE | orange |
| 2 | COLOR_PURPLE | purple | 10 | COLOR_YELLOW | yellow |
| 3 | COLOR_GREEN | teal green | 11 | COLOR_LIME | mint |
| 4 | COLOR_BROWN | dusky rose-brown | 12 | COLOR_CYAN | sky blue |
| 5 | COLOR_DARK_BLUE | steel blue | 13 | COLOR_GRAY | gray |
| 6 | COLOR_LIGHT_BLUE | pale blue | 14 | COLOR_PINK | pink |
| 7 | COLOR_WHITE | white | 15 | COLOR_PEACH | peach |

## In-code sprites (no .pyxres files needed)
```python
pyxel.images[0].set(0, 0, [      # bank 0, top-left (0,0); one hex digit per pixel = color index
    "00077000",
    "00777700",
    "07c77c70",
    "77777777",
    "08800880",
])
# later: pyxel.blt(x, y, 0, 0, 0, 8, 5, colkey=0)   # colkey=0 -> color 0 is transparent
```
Image banks are 256x256. Lay sprites out on an 8 or 16 px grid (u = 0, 8, 16, ...).

## Sound (64 slots, 4 channels)
```python
pyxel.sounds[0].set(notes, tones, volumes, effects, speed)
#   notes:   "c3e3g3c4"  (note C-B, optional # or -, octave 0-4; "r" = rest)
#   tones:   "t" triangle, "s" square, "p" pulse, "n" noise   (shorter strings repeat)
#   volumes: "0"-"7"
#   effects: "n" none, "s" slide, "v" vibrato, "f" fade-out
#   speed:   1 = fastest; 120 -> 1 second per note
pyxel.sounds[0].set("c3e3g3c4", "p", "6", "nnnf", 8)     # pickup jingle
pyxel.sounds[1].set("f2c1", "n", "74", "f", 12)          # explosion
pyxel.play(ch, snd, loop=False)   # ch 0-3, snd = slot number or list of slots
pyxel.stop(ch)                    # or pyxel.stop() for all
pyxel.musics[0].set([2, 3], [4], [], [])   # one list of sound slots per channel
pyxel.playm(0, loop=True)
```
Reserve channel 3 for SFX when music uses 0-2.

## Math / random (use these, not `random`, so seeded playtests are reproducible)
```python
pyxel.rndi(a, b)      # int in [a, b]
pyxel.rndf(a, b)      # float in [a, b]
pyxel.rseed(seed)
pyxel.sin(deg); pyxel.cos(deg); pyxel.atan2(y, x)   # DEGREES
pyxel.noise(x, y=0, z=0)
```

## Things that do NOT exist (common hallucinations)
`pyxel.draw_text`, `pyxel.sprite`, `pyxel.key_pressed`, `pyxel.KEY_ENTER` (use `KEY_RETURN`),
`pyxel.random`, `pyxel.fill_rect`, `pyxel.update()`, `pyxel.draw()`, `pyxel.delta_time`,
`pyxel.COLOR_BLUE` (use `COLOR_DARK_BLUE` / `COLOR_CYAN`).
