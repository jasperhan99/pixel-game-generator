# SPACE DODGE（太空躲避）

Pitch: 做一个太空飞船躲避陨石的游戏

## 玩法

驾驶太空飞船在屏幕底部左右移动，躲开从天而降的陨石。每躲过一颗（陨石飞出屏幕底部）+1 分。
陨石越生越多、越落越快，被撞到即 GAME OVER。

## 运行

```bash
cd games/space-dodge && uv run pyxel run main.py
```

（会打开一个 160x120 窗口，ESC 退出）

## 操作

| 按键 | 作用 |
|---|---|
| ←/→ 或 A/D | 左右移动 |
| SPACE / RETURN | 开始 / 重开 |
| R | 游戏结束后重开 |
| ESC | 退出 |

## 规则 / 数值

- 飞船：7x7 px 像素飞船，速度 2.5 px/frame，固定在底部一排
- 陨石：半径 3~7 px，从顶部随机 x 生成，下落 1.2~2.0 px/frame + 难度加成，带 ±0.3 横向漂移
- 难度：生成间隔 `max(14, 40 - score//2)` 帧；下落加速 `min(score*0.03, 1.4)`
- 碰撞：AABB，双方各缩小 1~2 px
- 音效：开始 jingle / 得分 blip / 爆炸（全部代码内合成，无外部资源）

## 文件

- `main.py` — 单文件游戏（仅标准库 + pyxel）
- `GAME_SPEC.md` — 设计规格
- `playtest.json` — 无头试玩测试场景
- `playtest_out/report.txt` — 最近一次测试报告

## Playtest 验证内容

`uv run python <skill>/scripts/playtest.py main.py --scenario playtest.json`（seed=3），
2 轮通过，9/9 检查项 PASS：

1. 启动停在 title 界面
2. SPACE 进入 play
3. LEFT / RIGHT / LEFT 三段按住分别把玩家移到最左、最右、再回左侧
4. 陨石飞出底部后 score 增加
5. 用 exec 把陨石传送到飞船上强制触发 → 进入 gameover（败局由游戏规则产生）
6. gameover 后按 SPACE 重开，回到 play 且分数清零

未覆盖：实际手感、难度曲线的平衡性（需真人试玩调整）。
