# TITLE: <Game Title>
# One-line pitch: <the user's sentence>
# Controls: arrows/WASD move, SPACE/RETURN start, R restart, ESC quit
#
# Skeleton for the pixel-game skill. Keep this structure (App class, scene
# strings, score, player, run() last) so playtest.py scenarios can inspect it.
import pyxel

W, H = 160, 120

SCENE_TITLE = "title"
SCENE_PLAY = "play"
SCENE_GAMEOVER = "gameover"

# ---- sprites: one hex digit per pixel (palette index), 0 = transparent -----
SPRITES = {
    # name: (u, v, rows)   -- u, v = position in image bank 0
    "player": (0, 0, [
        "00077000",
        "00777700",
        "07777770",
        "77777777",
        "00700700",
    ]),
}

# ---- sounds: slot -> (notes, tones, volumes, effects, speed) ---------------
SOUNDS = {
    0: ("c3e3g3c4", "p", "6", "nnnf", 8),   # start / pickup
    1: ("f2c1", "n", "74", "f", 12),        # hit / game over
}


class Player:
    def __init__(self):
        self.w, self.h = 8, 5
        self.x = float((W - self.w) / 2)
        self.y = float(H - 20)
        self.speed = 2

    def update(self):
        if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A):
            self.x -= self.speed
        if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D):
            self.x += self.speed
        self.x = max(0, min(W - self.w, self.x))

    def draw(self):
        u, v, _ = SPRITES["player"]
        pyxel.blt(self.x, self.y, 0, u, v, self.w, self.h, colkey=0)


class App:
    def __init__(self):
        pyxel.init(W, H, title="<Game Title>", fps=30)
        for u, v, rows in SPRITES.values():
            pyxel.images[0].set(u, v, rows)
        for slot, args in SOUNDS.items():
            pyxel.sounds[slot].set(*args)
        self.high_score = 0
        self.reset()
        self.scene = SCENE_TITLE
        pyxel.run(self.update, self.draw)   # must be the last line

    def reset(self):
        self.scene = SCENE_PLAY
        self.score = 0
        self.timer = 0
        self.player = Player()

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
            if start or pyxel.btnp(pyxel.KEY_R):
                self.reset()

    def update_play(self):
        self.timer += 1
        self.player.update()
        # TODO: core mechanic, scoring, and the lose condition:
        # if <lost>:
        #     self.scene = SCENE_GAMEOVER
        #     self.high_score = max(self.high_score, self.score)
        #     pyxel.play(3, 1)

    # ---------------------------------------------------------------- draw
    def draw(self):
        pyxel.cls(pyxel.COLOR_BLACK)
        if self.scene == SCENE_TITLE:
            self.center("<GAME TITLE>", 40, pyxel.COLOR_YELLOW)
            self.center("PRESS SPACE TO START", 70, (7, 13)[pyxel.frame_count // 15 % 2])  # blink between two VISIBLE colors
            return
        self.player.draw()
        pyxel.text(4, 4, f"SCORE {self.score}", pyxel.COLOR_WHITE)
        if self.scene == SCENE_GAMEOVER:
            self.center("GAME OVER", 50, pyxel.COLOR_RED)
            self.center(f"SCORE {self.score}  BEST {self.high_score}", 62, pyxel.COLOR_WHITE)
            self.center("SPACE / R TO RETRY", 74, pyxel.COLOR_GRAY)

    @staticmethod
    def center(s, y, col):
        pyxel.text((W - len(s) * pyxel.FONT_WIDTH) // 2, y, s, col)


App()
