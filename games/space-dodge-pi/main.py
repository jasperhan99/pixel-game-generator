# TITLE: SPACE DODGE
# One-line pitch: 驾驶太空飞船左右闪避不断坠落的陨石，活得越久分越高
# Controls: ←/→ or A/D move, SPACE/RETURN start & restart, R restart, ESC quit
import pyxel

W, H = 160, 120

SCENE_TITLE = "title"
SCENE_PLAY = "play"
SCENE_GAMEOVER = "gameover"

# ---- sprites: one hex digit per pixel (palette index), 0 = transparent -----
SPRITES = {
    # name: (u, v, rows)   -- u, v = position in image bank 0
    "ship": (0, 0, [
        "00007000",
        "00077000",
        "007c7700",
        "00777700",
        "07777770",
        "77777777",
        "07000070",
        "0d0000d0",
    ]),
    "rock_s": (8, 0, [
        "004400",
        "04d440",
        "4d4441",
        "444411",
        "044110",
        "001100",
    ]),
    "rock_b": (16, 0, [
        "00044100",
        "004dd440",
        "04dd4441",
        "4d444411",
        "44444411",
        "44444111",
        "04441110",
        "00411100",
    ]),
}

# ---- sounds: slot -> (notes, tones, volumes, effects, speed) ---------------
SOUNDS = {
    0: ("c3e3g3c4", "p", "6", "nnnf", 8),   # start
    1: ("f2c1", "n", "74", "f", 12),        # hit / game over
}


def collide(a, b, pad=0):
    return (a.x + pad < b.x + b.w and b.x < a.x + a.w - pad
            and a.y + pad < b.y + b.h and b.y < a.y + a.h - pad)


class Player:
    def __init__(self):
        self.w, self.h = 8, 8
        self.x = (W - self.w) / 2.0
        self.y = H - 20
        self.speed = 2.0

    def update(self):
        if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A):
            self.x -= self.speed
        if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D):
            self.x += self.speed
        self.x = max(0.0, min(W - self.w, self.x))

    def draw(self):
        u, v, _ = SPRITES["ship"]
        pyxel.blt(self.x, self.y, 0, u, v, self.w, self.h, colkey=0)
        flame = pyxel.frame_count // 4 % 2
        col = pyxel.COLOR_ORANGE if flame else pyxel.COLOR_YELLOW
        pyxel.rect(self.x + 2, self.y + self.h, 4, 2 + flame, col)


class Meteor:
    def __init__(self, ramp):
        big = pyxel.rndi(0, 1) == 1
        self.sprite = "rock_b" if big else "rock_s"
        u, v, rows = SPRITES[self.sprite]
        self.w = len(rows[0])
        self.h = len(rows)
        self.x = float(pyxel.rndi(0, W - self.w))
        self.y = float(-self.h)
        self.speed = pyxel.rndf(1.0, 1.8) + ramp

    def update(self):
        self.y += self.speed

    def escaped(self):
        return self.y > H

    def draw(self):
        u, v, rows = SPRITES[self.sprite]
        pyxel.blt(self.x, self.y, 0, u, v, self.w, self.h, colkey=0)


class App:
    def __init__(self):
        pyxel.init(W, H, title="SPACE DODGE", fps=30)
        for u, v, rows in SPRITES.values():
            pyxel.images[0].set(u, v, rows)
        for slot, args in SOUNDS.items():
            pyxel.sounds[slot].set(*args)
        self.high_score = 0
        self.stars = [(pyxel.rndi(0, W - 1), pyxel.rndi(0, H - 1), pyxel.rndi(0, 1))
                      for _ in range(40)]
        self.reset()
        self.scene = SCENE_TITLE
        pyxel.run(self.update, self.draw)   # must be the last line

    def reset(self):
        self.scene = SCENE_PLAY
        self.score = 0
        self.timer = 0
        self.spawn_t = 30
        self.player = Player()
        self.meteors = []
        self.boom = None

    # ---------------------------------------------------------------- update
    def update(self):
        start = pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN)
        if self.scene == SCENE_TITLE:
            if start:
                self.reset()
                pyxel.play(3, 0)
        elif self.scene == SCENE_PLAY:
            self.update_play()
        elif self.scene == SCENE_GAMEOVER:
            if self.boom:
                self.boom[2] += 1
            if start or pyxel.btnp(pyxel.KEY_R):
                self.reset()

    def update_play(self):
        self.timer += 1
        self.player.update()
        if self.timer % 30 == 0:
            self.score += 1
        self.spawn_t -= 1
        if self.spawn_t <= 0:
            ramp = min(1.5, self.timer / 1200.0)
            self.meteors.append(Meteor(ramp))
            self.spawn_t = max(12, 45 - self.timer // 40)
        hit = False
        keep = []
        for m in self.meteors:
            m.update()
            if m.escaped():
                self.score += 2
            elif collide(self.player, m, pad=2):
                hit = True
            else:
                keep.append(m)
        self.meteors = keep
        if hit:
            self.boom = [self.player.x + self.player.w / 2,
                         self.player.y + self.player.h / 2, 0]
            self.scene = SCENE_GAMEOVER
            self.high_score = max(self.high_score, self.score)
            pyxel.play(3, 1)

    # ---------------------------------------------------------------- draw
    def draw(self):
        pyxel.cls(pyxel.COLOR_BLACK)
        self.draw_stars()
        if self.scene == SCENE_TITLE:
            u, v, rows = SPRITES["ship"]
            pyxel.blt((W - 8) / 2, 44, 0, u, v, 8, 8, colkey=0)
            self.center("SPACE DODGE", 30, pyxel.COLOR_CYAN)
            if pyxel.frame_count // 15 % 2:
                self.center("PRESS SPACE TO START", 70, pyxel.COLOR_YELLOW)
            self.center("ARROWS OR A/D TO MOVE", 84, pyxel.COLOR_GRAY)
            if self.high_score:
                self.center("BEST %d" % self.high_score, 98, pyxel.COLOR_PEACH)
            return
        for m in self.meteors:
            m.draw()
        if self.boom is None:
            self.player.draw()
        else:
            t = self.boom[2]
            r = 2 + t // 2
            col = (pyxel.COLOR_YELLOW, pyxel.COLOR_ORANGE, pyxel.COLOR_RED)[t // 8 % 3]
            pyxel.circb(self.boom[0], self.boom[1], r, col)
        pyxel.text(4, 4, "SCORE %d" % self.score, pyxel.COLOR_WHITE)
        best = "BEST %d" % self.high_score
        pyxel.text(W - 4 - len(best) * pyxel.FONT_WIDTH, 4, best, pyxel.COLOR_GRAY)
        if self.scene == SCENE_GAMEOVER:
            pyxel.rect(24, 44, 112, 36, pyxel.COLOR_NAVY)
            self.center("GAME OVER", 50, pyxel.COLOR_RED)
            self.center("SCORE %d  BEST %d" % (self.score, self.high_score),
                        62, pyxel.COLOR_WHITE)
            self.center("SPACE / R TO RETRY", 72, pyxel.COLOR_GRAY)

    def draw_stars(self):
        for x, y, p in self.stars:
            col = pyxel.COLOR_WHITE if (pyxel.frame_count // 20 + p) % 2 else pyxel.COLOR_DARK_BLUE
            pyxel.pset(x, y, col)

    @staticmethod
    def center(s, y, col):
        pyxel.text((W - len(s) * pyxel.FONT_WIDTH) // 2, y, s, col)


App()
