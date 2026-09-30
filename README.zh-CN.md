# pixel-game-generator

[English](README.md) | **简体中文**

一个 [Agent Skill](https://agentskills.io/specification)：**一句话**生成**可运行的复古像素游戏**，基于 [Pyxel](https://github.com/kitao/pyxel)。它会自动配置 Python 环境、编写游戏代码，并在无窗口模式下反复试玩测试，直到全部通过。

同一份 skill 同时支持 **Claude Code** 和 **[pi](https://www.npmjs.com/package/@earendil-works/pi-coding-agent)**，GLM-5.3-flash 这类小模型也能跑通。它不依赖 MCP，也不要求模型能看图。

![Space Dodge：pi + GLM-5.3-flash 根据"做一个太空飞船躲避陨石的游戏"生成](docs/screenshot.png)

*Space Dodge：由 pi + GLM-5.3-flash 根据"做一个太空飞船躲避陨石的游戏"生成。*

## 工作流程

```
"做一个太空飞船躲避陨石的游戏"
        │
        ▼
1. 设计     GAME_SPEC.md：操作、对象、计分、难度、失败条件、测试计划
2. 环境     scripts/setup_env.sh → uv 项目 + Python 3.12 + pyxel（可重复运行）
3. 代码     按固定骨架写 main.py；精灵图和音效都写在代码里（没有二进制素材）
4. 测试计划 playtest.json：按帧模拟按键、强制触发事件、断言游戏状态
5. 试玩     scripts/playtest.py：静态检查 + 无窗口运行 → 检查结果、PNG 截图、ASCII 画面网格
            └─ 修复并重跑，直到 RESULT: PASS（最多 5 轮）
6. 交付     README.md + 运行命令
```

`scripts/playtest.py` 只依赖 Python 和 pyxel，工作方式如下：
- 拦截 `pyxel.run`，由脚本自己逐帧驱动游戏，并在指定帧注入按键。
- 对运行中的游戏对象求值 Python 表达式，比如 `app.scene == 'gameover'`。
- 保存 PNG 截图，同时把每一帧画面降采样成十六进制文字网格，让纯文本模型也能"看到"画面。
- 运行前先做静态检查：代码里用到任何不存在的 `pyxel.<name>` 都会直接判为失败，专门拦住较弱模型编造的 API 名。

## 目录结构

```
.agents/skills/pixel-game/            # skill 本体（pi 等 Agent Skills 客户端自动发现这个路径）
├── SKILL.md                          # agent 执行的工作流
├── scripts/setup_env.sh              # 环境配置
├── scripts/playtest.py               # 无窗口试玩测试脚本
└── references/
    ├── pyxel-api.md                  # 对照 pyxel 2.9.9 核实过的 API 速查表
    ├── template_main.py              # 必须使用的游戏代码骨架
    └── scenario_template.json        # 测试场景模板
.claude/skills/pixel-game → ../../.agents/skills/pixel-game   # 给 Claude Code 用的软链接
games/                                # 生成示例
├── space-dodge/                      # pi + GLM-5.3-flash（交互模式），9/9 通过
├── space-dodge-pi/                   # pi + GLM-5.3-flash（非交互模式），7/7 通过
└── space-dodge-claude/               # Claude Code，13/13 通过
```

## 从零开始

### 1. 准备工具

| 工具 | 用途 | 安装方式 |
|---|---|---|
| git | 克隆仓库 | macOS 自带，或 `xcode-select --install` |
| [uv](https://docs.astral.sh/uv/) | 为每个游戏管理 Python 和 pyxel | `brew install uv` 或 `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js ≥ 20 | 只有 pi 需要 | `brew install node` |
| Agent | 执行 skill | Claude Code **或** pi（见下文） |

不需要自己装 Python，uv 会在需要时自动下载 Python 3.12。

### 2. 克隆仓库

```bash
git clone https://github.com/jasperhan99/pixel-game-generator.git
cd pixel-game-generator
```

### 3a. 在 Claude Code 中使用

skill 已经通过软链接放在 `.claude/skills/pixel-game`。在仓库目录启动 Claude Code，然后输入：

```
/pixel-game 做一个太空飞船躲避陨石的游戏
```

### 3b. 在 pi 中使用（可以配任意模型）

**安装 pi**

```bash
npm install -g @earendil-works/pi-coding-agent
pi --version
```

**配置模型**，任选一种方式：

- **方式 A：内置 provider，交互登录。** 运行 `pi`，输入 `/login`，选择 provider。智谱 GLM 选 *ZAI Coding Plan (Global)* 或 *ZAI Coding Plan (China)*。密钥会保存在 `~/.pi/agent/auth.json`，这个文件千万不要提交到仓库。
- **方式 B：环境变量。**

  ```bash
  export ZAI_API_KEY=...            # ZAI Coding Plan（国际版）
  export ZAI_CODING_CN_API_KEY=...  # ZAI Coding Plan（国内版）
  ```

  其他 provider 用各自的变量，比如 `ANTHROPIC_API_KEY`、`OPENAI_API_KEY`、`GEMINI_API_KEY`、`DEEPSEEK_API_KEY`、`OPENROUTER_API_KEY` 等。
- **方式 C：自定义 OpenAI 兼容接口。** 写进 `~/.pi/agent/models.json`，再用 `/login` 保存它的密钥：

  ```json
  {
    "providers": {
      "zhipuai-coding-plan": {
        "baseUrl": "https://api.z.ai/api/coding/paas/v4",
        "api": "openai-completions",
        "models": [
          { "id": "glm-5.3-flash", "name": "GLM-5.3 Flash", "reasoning": true, "contextWindow": 200000 }
        ]
      }
    }
  }
  ```

确认模型可用：

```bash
pi --list-models glm
```

```bash
pi auth check --provider zhipuai-coding-plan --model glm-5.3-flash
```

想设为默认模型，在 `~/.pi/agent/settings.json` 里设置 `defaultProvider` 和 `defaultModel`。

**运行 skill。** pi 会自动发现当前项目里的 `.agents/skills/`。`--approve` 表示本次运行信任项目内的文件。

```bash
pi --provider zhipuai-coding-plan --model glm-5.3-flash --approve "/skill:pixel-game 做一个太空飞船躲避陨石的游戏"
```

加上 `-p` 就是非交互模式，只输出结果。

### 4. 试玩

```bash
cd games/<slug>
uv run pyxel run main.py        # 方向键 / A-D 移动，SPACE 开始，R 重来，ESC 退出
```

随时可以重跑测试：

```bash
uv run python ../../.agents/skills/pixel-game/scripts/playtest.py main.py --scenario playtest.json
```

## 全局安装 skill（在任意目录可用）

```bash
# pi 及其他 Agent Skills 客户端
mkdir -p ~/.agents/skills && ln -s "$PWD/.agents/skills/pixel-game" ~/.agents/skills/pixel-game
# Claude Code
mkdir -p ~/.claude/skills && ln -s "$PWD/.agents/skills/pixel-game" ~/.claude/skills/pixel-game
```

也可以不安装，只在单次 pi 运行时加载：

```bash
pi --skill /path/to/pixel-game-generator/.agents/skills/pixel-game "/skill:pixel-game ..."
```

游戏会生成在你运行 agent 的目录下的 `games/<slug>/`。

## 可选功能

- **导出网页版：**

  ```bash
  cd games/<slug> && uv run pyxel package . main.py && uv run pyxel app2html <slug>.pyxapp
  ```

- **官方 Pyxel MCP（仅 Claude Code）：**

  ```bash
  claude mcp add --scope user pyxel -- uvx --from 'pyxel-mcp>=1.3.1' pyxel-mcp
  ```

  加上 [kitao/pyxel-mcp](https://github.com/kitao/pyxel-mcp) 的工具作为额外检查，但 `playtest.py` 通过仍是必须的。

## 限制

- 范围刻意做得很小：一个屏幕、一种核心机制、标题 → 游戏 → 结束 → 重开。
- 自动测试能证明游戏能跑、机制生效，但判断不了手感和难度是否合适，这些需要人来试玩。
- 精灵图是在代码里手写的简单像素画，不涉及图像生成，也没有二进制 `.pyxres` 素材。

## 致谢

- [Pyxel](https://github.com/kitao/pyxel)，作者 Takashi Kitao（MIT）。无窗口运行的方法参考了 [pyxel-mcp](https://github.com/kitao/pyxel-mcp)。
- 许可证：MIT
