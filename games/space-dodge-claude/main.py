# TITLE: Meteor Dodge
# One-line pitch: 做一个太空飞船躲避陨石的游戏 (a spaceship dodging meteors)
# Controls: arrows/WASD move, SPACE/RETURN start, R restart, ESC quit
import pyxel

W, H = 160, 120

SCENE_TITLE = "title"
SCENE_PLAY = "play"
SCENE_GAMEOVER = "gameover"

PLAYER_MIN_Y = 40

# ---- sprites: one hex digit per pixel (palette index), 0 = transparent -----
SPRITES = {
    "player": (0, 0, [
        "00077000",
        "0007c000",
        "0077c700",
        "07777770",
        "77d77d77",
        "77777777",
        "70a00a07",
        "00900900",
    ]),
    "meteor_s": (8, 0, [
        "00444400",
        "04f44940",
        "44444444",
        "49444d44",
        "444d4444",
        "44444494",
        "04494440",
        "00444400",
    ]),
    "meteor_b": (16, 0, [
        "000044440000",
        "0004f4444400",
        "004f44449440",
        "0444444d4444",
        "44944444444d",
        "444444d44444",
        "4444d4444944",
        "4d4444444444",
        "0444449444d0",
        "00444444d440",
        "000444444400",
        "000004444000",
    ]),
}

# ---- sounds: slot -> (notes, tones, volumes, effects, speed) ---------------
SOUNDS = {
    0: ("c3e3g3c4", "p", "6", "nnnf", 8),   # start
    1: ("g3c4", "p", "4", "nf", 5),         # dodge blip
    2: ("f2c1", "n", "74", "f", 12),        # explosion / game over
}


def overlap(a, b, shrink=1):
    return (a.x + shrink < b.x + b.w - shrink and b.x + shrink < a.x + a.w - shrink
            and a.y + shrink < b.y + b.h - shrink and b.y + shrink < a.y + a.h - shrink)


class Player:
    def __init__(self):
        self.w, self.h = 8, 8
        self.x = float((W - self.w) // 2)
        self.y = float(H - 20)
        self.speed = 2

    def update(self):
        if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A):
            self.x -= self.speed
        if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D):
            self.x += self.speed
        if pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.KEY_W):
            self.y -= self.speed
        if pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.KEY_S):
            self.y += self.speed
        self.x = max(0, min(W - self.w, self.x))
        self.y = max(PLAYER_MIN_Y, min(H - self.h, self.y))

    def draw(self):
        u, v, _ = SPRITES["player"]
        pyxel.blt(self.x, self.y, 0, u, v, self.w, self.h, colkey=0)
        # engine flame flicker
        if pyxel.frame_count % 4 < 2:
            pyxel.pset(self.x + 2, self.y + 8, pyxel.COLOR_ORANGE)
            pyxel.pset(self.x + 5, self.y + 8, pyxel.COLOR_ORANGE)


class Meteor:
    def __init__(self, speed):
        big = pyxel.rndi(0, 9) < 3
        self.sprite = "meteor_b" if big else "meteor_s"
        self.w = self.h = 12 if big else 8
        self.x = float(pyxel.rndi(0, W - self.w))
        self.y = float(-self.h)
        self.vy = speed + pyxel.rndf(0, 0.8)

    def update(self):
        self.y += self.vy

    def draw(self):
        u, v, _ = SPRITES[self.sprite]
        pyxel.blt(self.x, self.y, 0, u, v, self.w, self.h, colkey=0)


class App:
    def __init__(self):
        pyxel.init(W, H, title="Meteor Dodge", fps=30)
        for u, v, rows in SPRITES.values():
            pyxel.images[0].set(u, v, rows)
        for slot, args in SOUNDS.items():
            pyxel.sounds[slot].set(*args)
        self.stars = [[pyxel.rndi(0, W - 1), pyxel.rndi(0, H - 1), pyxel.rndi(1, 2)] for _ in range(30)]
        self.high_score = 0
        self.reset()
        self.scene = SCENE_TITLE
        pyxel.run(self.update, self.draw)   # must be the last line

    def reset(self):
        self.scene = SCENE_PLAY
        self.score = 0
        self.timer = 0
        self.player = Player()
        self.meteors = []

    # ---------------------------------------------------------------- update
    def update(self):
        self.update_stars()
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
                pyxel.play(3, 0)

    def update_stars(self):
        for s in self.stars:
            s[1] += s[2] * 0.5
            if s[1] >= H:
                s[1] -= H   # wrap without touching the RNG (keeps gameplay reproducible)

    def base_speed(self):
        return min(3.0, 1.0 + self.timer / 600)

    def spawn_every(self):
        return max(8, 24 - self.timer // 150)

    def update_play(self):
        self.timer += 1
        self.player.update()
        if self.timer % self.spawn_every() == 0:
            self.meteors.append(Meteor(self.base_speed()))
        for m in self.meteors:
            m.update()
        kept = []
        for m in self.meteors:
            if m.y >= H:
                self.score += 1
                if self.score % 5 == 0:
                    pyxel.play(3, 1)
            else:
                kept.append(m)
        self.meteors = kept
        if any(overlap(self.player, m) for m in self.meteors):
            self.scene = SCENE_GAMEOVER
            self.high_score = max(self.high_score, self.score)
            pyxel.play(3, 2)

    # ---------------------------------------------------------------- draw
    def draw(self):
        pyxel.cls(pyxel.COLOR_BLACK)
        for x, y, spd in self.stars:
            pyxel.pset(x, y, pyxel.COLOR_WHITE if spd == 2 else pyxel.COLOR_DARK_BLUE)
        if self.scene == SCENE_TITLE:
            self.center("METEOR DODGE", 36, pyxel.COLOR_YELLOW)
            self.center("DODGE THE FALLING ROCKS", 52, pyxel.COLOR_GRAY)
            u, v, _ = SPRITES["player"]
            pyxel.blt(76, 62, 0, u, v, 8, 8, colkey=0)
            self.center("PRESS SPACE TO START", 82, pyxel.COLOR_WHITE if pyxel.frame_count // 15 % 2 == 0 else pyxel.COLOR_GRAY)
            self.center("ARROWS / WASD TO MOVE", 94, pyxel.COLOR_DARK_BLUE)
            return
        for m in self.meteors:
            m.draw()
        self.player.draw()
        pyxel.text(4, 4, f"SCORE {self.score}", pyxel.COLOR_WHITE)
        t = f"TIME {self.timer // 30}"
        pyxel.text(W - 4 - len(t) * pyxel.FONT_WIDTH, 4, t, pyxel.COLOR_CYAN)
        if self.scene == SCENE_GAMEOVER:
            pyxel.rect(20, 44, 120, 40, pyxel.COLOR_NAVY)
            pyxel.rectb(20, 44, 120, 40, pyxel.COLOR_RED)
            self.center("GAME OVER", 50, pyxel.COLOR_RED)
            self.center(f"SCORE {self.score}  BEST {self.high_score}", 62, pyxel.COLOR_WHITE)
            self.center("SPACE / R TO RETRY", 74, pyxel.COLOR_GRAY)

    @staticmethod
    def center(s, y, col):
        pyxel.text((W - len(s) * pyxel.FONT_WIDTH) // 2, y, s, col)


App()
