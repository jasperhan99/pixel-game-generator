# SPACE DODGE

驾驶太空飞船左右闪避不断坠落的陨石，活得越久分越高。

## 运行

```bash
cd games/space-dodge-pi && uv run pyxel run main.py
```

（会打开一个 160x120 窗口；ESC 退出）

## 操作

| 按键 | 作用 |
|---|---|
| ← / → 或 A / D | 左右移动飞船 |
| SPACE / RETURN | 开始游戏 / 失败后重开 |
| R | 重开 |
| ESC | 退出 |

## 规则

- 陨石从屏幕顶部随机位置坠落，躲开它们。
- 每存活 30 秒帧 +1 分，每躲过一颗陨石（飞出屏幕底部）+2 分。
- 难度递增：陨石生成间隔 45 → 12 帧，下落速度加成最高 +1.5 px/帧。
- 被陨石撞到即爆炸，游戏结束；显示本局得分与最高分。

## Playtest 验证（`playtest.py`，RESULT: PASS，第 2 轮）

- 开局为标题页，SPACE 进入游戏
- LEFT / RIGHT 均能正确移动飞船（检查 `app.player.x`）
- 游戏中得分会增长（存活计时得分）
- 通过 exec 强制把陨石移到飞船上，验证碰撞 → GAME OVER
- GAME OVER 后按 SPACE 重开：`scene == 'play'` 且 `score == 0`

**未验证项**：手感与难度曲线是否好玩（需要真人试玩）；音效听感。
