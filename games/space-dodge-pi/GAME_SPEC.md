# SPACE DODGE
Pitch: 做一个太空飞船躲避陨石的游戏
Genre: dodge（躲避）
Screen: 160x120 @ 30 fps，默认 16 色调色板
Controls: ←/→ 或 A/D 左右移动；SPACE/RETURN 开始、重开；R 重开；ESC 退出
Player: 太空飞船（带尾焰动画），8x8 px，左右 2 px/帧，固定在屏幕底部 y=100
Objects: 陨石两种（小 6x6、大 8x8），从屏幕顶部随机 x 生成，速度 1.0–1.8 px/帧 + 难度加成；飞出屏幕底部即算"躲过"
Score: 每存活 30 帧 +1 分；每躲过一颗陨石 +2 分
Difficulty: 生成间隔从 45 帧线性降到 12 帧（约 44 秒到顶）；陨石速度加成在前 1200 帧内从 0 线性升到 +1.5 px/帧
Lose: 任一陨石碰撞盒（双方各内缩 2 px）与飞船相交 → 爆炸动画 → GAME OVER
Sounds: 开始 jingle（sound 0）；撞击爆炸（sound 1）
Test plan: 开局在标题页；SPACE 进入 play；按住 LEFT 后 player.x 变小、按住 RIGHT 后变大；350 帧时 score > 0；440 帧用 exec 把一颗陨石移到飞船上强制触发失败；SPACE 重开后 scene=play 且 score=0
