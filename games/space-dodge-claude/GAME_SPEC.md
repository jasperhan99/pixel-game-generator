# Meteor Dodge
Pitch: 做一个太空飞船躲避陨石的游戏 (a spaceship dodging meteors)
Genre: dodge
Screen: 160x120 @ 30 fps, default 16-color palette
Controls: LEFT/RIGHT/UP/DOWN or A/D/W/S move, SPACE/RETURN start, SPACE/RETURN/R restart, ESC quit
Player: white/cyan spaceship sprite, 8x8 px, speed 2 px/frame in 4 directions, clamped to the screen
  (vertical range limited to the lower 2/3 of the screen: y in [40, 112]). Starts at (76, 100).
Objects: meteors fall from above the top edge (y = -size), random x in [0, 160 - size].
  Two sizes: small 8x8 (70%) and big 12x12 (30%). Fall speed = base + rndf(0, 0.8) px/frame.
  Spawn one meteor every `spawn_every` frames. A meteor that leaves the bottom edge is removed.
  Background: 30 scrolling stars (decoration only).
Score: +1 per meteor that leaves the bottom edge (dodged). HUD shows SCORE and TIME (seconds).
Difficulty: base speed = 1.0 + timer / 600 (i.e. +1 px/frame every 20 s), capped at 3.0.
  spawn_every = max(8, 24 - timer // 150) (one frame faster every 5 s, from 24 down to 8).
Lose: player hitbox (ship shrunk by 1 px each side) overlaps a meteor hitbox (shrunk by 1 px) -> game over.
Sounds: slot 0 start jingle, slot 1 soft blip on each dodge (every 5 points), slot 2 explosion on game over.
Test plan: seed 1. SPACE at f=20 -> play. Hold LEFT f30-60, RIGHT f60-100, UP f100-120, DOWN f120-135,
  check x/y after each. Check score > 0 at f=300. Force a hit at f=320 by moving meteors[0] onto the player,
  check gameover, press SPACE at f=340, check scene == 'play' and score == 0 at f=342.
