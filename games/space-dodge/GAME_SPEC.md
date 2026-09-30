# SPACE DODGE（太空躲避）

Pitch: 做一个太空飞船躲避陨石的游戏
Genre: dodge（躲避）
Screen: 160x120 @ 30 fps，默认 16 色调色板，黑色太空背景 + 缓慢下落的星星

Controls:
- LEFT/RIGHT 或 A/D：左右移动
- SPACE/RETURN：开始 / 重开
- R：游戏结束后重开
- ESC：退出

Player: 像素飞船 sprite 7x7 px（另加 3 个交替闪动的喷焰像素），speed 2.5 px/frame，
固定在底部 y=96，限制在 x ∈ [0, 153]

Objects: 陨石（圆，半径 r ∈ {3,3,4,4,5,7}），从顶部随机 x 生成，
下落速度 vy = 1.2 + rndf(0, 0.8) + 难度加成，横向漂移 vx ∈ ±0.3（x 限制在屏幕内）；
碰撞为 AABB，双方各缩小 1~2 px（公平判定）

Score: 每颗陨石完整飞出屏幕底部 +1 分，并播放 blip 音效

Difficulty: 生成间隔 = max(14, 40 - score//2) 帧（40 → 14）；
下落速度加成 = min(score * 0.03, 1.4) px/frame

Lose: 任一陨石 AABB 与飞船 AABB 相交 → GAME OVER，播放爆炸音

Sounds: 0 开始 jingle / 2 得分 blip（通道 2）/ 1 爆炸（通道 3）

Test plan:
1. 启动后停在 title 界面（检查 frame 10）
2. frame 20 按 SPACE → 进入 play（检查 frame 25）
3. frame 30~70 按住 LEFT → 玩家移到最左（x≈0，检查 frame 69）
4. frame 70~130 按住 RIGHT → 玩家移到右侧（x≈147，检查 frame 129）
5. frame 130~170 再按住 LEFT → 玩家回到左侧（检查 frame 169）
6. frame 172 检查 score > 0（陨石飞出底部即计分）
7. frame 173 确认存活且场上有陨石；frame 175 用 exec 把 rocks[0] 传送到玩家位置
   → frame 185 应为 gameover（由游戏规则强制触发败局）
8. frame 195 按 SPACE → frame 205 回到 play 且 score == 0（重开并清零分数）
