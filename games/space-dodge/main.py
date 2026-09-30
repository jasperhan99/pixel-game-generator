# TITLE: SPACE DODGE
# One-line pitch: 驾驶太空飞船左右闪避坠落的陨石，活得越久分越高
# Controls: LEFT/RIGHT or A/D move, SPACE/RETURN start, R restart, ESC quit
import pyxel

W, H = 160, 120

SCENE_TITLE = "title"
SCENE_PLAY = "play"
SCENE_GAMEOVER = "gameover"

# ---- sprites: one hex digit per pixel (palette index), 0 = transparent -----
SPRITES = {
    "ship": (0, 0, [
        "0007000",
        "0077700",
        "0777770",
        "07c7c70",
        "0777770",
        "5577755",
        "5700075",
    ]),
}

# ---- sounds: slot -> (notes, tones, volumes, effects, speed) ---------------
SOUNDS = {
    0: ("c3e3g3c4", "p", "6", "nnnf", 8),   # start jingle
    1: ("f2c1", "n", "74", "f", 12),        # explosion
    2: ("c4e4g4", "t", "3", "n", 6),        # dodge blip
}

ROCK_RADII = (3, 3, 4, 4, 5, 7)


class Player:
    def __init__(self):
        self.w, self.h = 7, 7
        self.x = float((W - self.w) / 2)
        self.y = float(H - 24)
        self.speed = 2.5

    def update(self):
        if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A):
            self.x -= self.speed
        if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D):
            self.x += self.speed
        self.x = max(0.0, min(float(W - self.w), self.x))

    def draw(self):
        u, v, _ = SPRITES["ship"]
        pyxel.blt(self.x, self.y, 0, u, v, self.w, self.h, colkey=0)
        col = 10 if pyxel.frame_count % 6 < 3 else 9
        pyxel.pset(self.x + 1, self.y + self.h, col)
        pyxel.pset(self.x + 3, self.y + self.h, col)
        pyxel.pset(self.x + 5, self.y + self.h, col)


class Rock:
    def __init__(self):
        self.r = ROCK_RADII[pyxel.rndi(0, len(ROCK_RADII) - 1)]
        self.w = self.h = self.r * 2
        self.x = float(pyxel.rndi(0, W - self.w))
        self.y = float(-self.h)
        self.vy = 1.2 + pyxel.rndf(0, 0.8)
        self.vx = pyxel.rndf(-0.3, 0.3)

    def update(self, speed_bonus):
        self.y += self.vy + speed_bonus
        self.x = max(0.0, min(float(W - self.w), self.x + self.vx))

    def draw(self):
        cx = self.x + self.r
        cy = self.y + self.r
        pyxel.circ(cx, cy, self.r, 13)
        pyxel.circ(cx - self.r * 0.3, cy - self.r * 0.3, max(1, self.r * 0.35), 4)
        if self.r >= 5:
            pyxel.pset(cx + self.r - 2, cy - 1, 7)


class App:
    def __init__(self):
        pyxel.init(W, H, title="SPACE DODGE", fps=30)
        for u, v, rows in SPRITES.values():
            pyxel.images[0].set(u, v, rows)
        for slot, args in SOUNDS.items():
            pyxel.sounds[slot].set(*args)
        self.stars = []
        for i in range(40):
            self.stars.append([
                float(pyxel.rndi(0, W - 1)),
                float(pyxel.rndi(0, H - 1)),
                pyxel.rndf(0.15, 0.5),
                6 if i % 8 == 0 else 5,
            ])
        self.high_score = 0
        self.reset()
        self.scene = SCENE_TITLE
        pyxel.run(self.update, self.draw)   # must be the last line

    def reset(self):
        self.scene = SCENE_PLAY
        self.score = 0
        self.timer = 0
        self.player = Player()
        self.rocks = []

    # ---------------------------------------------------------------- update
    def update(self):
        for st in self.stars:
            st[1] += st[2]
            if st[1] >= H:
                st[0] = float(pyxel.rndi(0, W - 1))
                st[1] = 0.0
        start = pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN)
        if self.scene == SCENE_TITLE:
            if start:
                self.reset()
                pyxel.play(3, 0)
        elif self.scene == SCENE_PLAY:
            self.update_play()
        elif self.scene == SCENE_GAMEOVER:
            if start or pyxel.btnp(pyxel.KEY_R):
                self.reset()

    def spawn_interval(self):
        return max(14, 40 - self.score // 2)

    def update_play(self):
        self.timer += 1
        self.player.update()
        bonus = min(self.score * 0.03, 1.4)
        if self.timer == 1 or self.timer % self.spawn_interval() == 0:
            self.rocks.append(Rock())
        for r in self.rocks:
            r.update(bonus)
            if self.overlap(self.player.x + 1, self.player.y + 1,
                            self.player.w - 2, self.player.h - 2,
                            r.x + 2, r.y + 2, r.w - 4, r.h - 4):
                self.scene = SCENE_GAMEOVER
                self.high_score = max(self.high_score, self.score)
                pyxel.play(3, 1)
                return
        alive = []
        for r in self.rocks:
            if r.y > H:
                self.score += 1
                pyxel.play(2, 2)
            else:
                alive.append(r)
        self.rocks = alive

    @staticmethod
    def overlap(ax, ay, aw, ah, bx, by, bw, bh):
        return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah

    # ---------------------------------------------------------------- draw
    def draw(self):
        pyxel.cls(pyxel.COLOR_BLACK)
        for st in self.stars:
            pyxel.pset(st[0], st[1], st[3])
        if self.scene == SCENE_TITLE:
            self.center("SPACE DODGE", 36, pyxel.COLOR_CYAN)
            self.center("DODGE THE FALLING ROCKS", 50, pyxel.COLOR_GRAY)
            self.center("PRESS SPACE", 72, (7, 13)[pyxel.frame_count // 15 % 2])
            self.center("ARROWS OR A/D TO MOVE", 96, pyxel.COLOR_LIGHT_BLUE)
            return
        for r in self.rocks:
            r.draw()
        self.player.draw()
        pyxel.text(4, 4, f"SCORE {self.score}", pyxel.COLOR_WHITE)
        best = f"BEST {self.high_score}"
        pyxel.text(W - 4 - len(best) * pyxel.FONT_WIDTH, 4, best, pyxel.COLOR_GRAY)
        if self.scene == SCENE_GAMEOVER:
            self.center("GAME OVER", 48, pyxel.COLOR_RED)
            self.center(f"SCORE {self.score}  BEST {self.high_score}", 62, pyxel.COLOR_WHITE)
            self.center("SPACE / R TO RETRY", 76, pyxel.COLOR_GRAY)

    @staticmethod
    def center(s, y, col):
        pyxel.text((W - len(s) * pyxel.FONT_WIDTH) // 2, y, s, col)


App()
