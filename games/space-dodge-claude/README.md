# Meteor Dodge

Pitch: 做一个太空飞船躲避陨石的游戏 (a spaceship dodging meteors).

Fly a small ship at the bottom of space and dodge falling meteors. Each meteor that
leaves the bottom of the screen is +1 point. Meteors fall faster and spawn more often
over time. One hit and it's game over.

## Controls
- Arrow keys or WASD: move (the ship stays in the lower two-thirds of the screen)
- SPACE / RETURN: start
- SPACE / RETURN / R: restart after game over
- ESC: quit

## Run
```bash
cd games/space-dodge-claude && uv run pyxel run main.py
```

## Playtest
```bash
cd games/space-dodge-claude && uv run python ../../.claude/skills/pixel-game/scripts/playtest.py main.py --scenario playtest.json
```
The headless playtest (seed 1, 300 frames, 13 checks, all passing) checks:
- starts on the title screen, and SPACE starts play
- LEFT, RIGHT, UP, DOWN and A each move the ship the right way
- meteors spawn and the score goes up while dodging
- the difficulty ramps (spawn interval shrinks, fall speed grows)
- a meteor hit (forced at frame 200) ends the game and records the best score
- SPACE on the game-over screen restarts with score 0 and no meteors

Not verified: how the game feels or whether the difficulty is well balanced.
