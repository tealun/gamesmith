# templates：可运行的最小骨架

一个玩具横版跑酷（自动跑 + 跳），用来演示 gamesmith 的工程骨架。**数值与规则只是示例**，复制到项目后换成你自己的玩法核心与配置。不需要安装依赖（预览工具除外，它要本机已有 Playwright 和 Chromium），Node ≥ 18、Python ≥ 3.8。迁移到真实项目并改用 TypeScript 后，测试和类型检查通常需要先 `npm ci` 安装 devDependencies。所有文件放在同一层，这样技能包在只允许浅目录的平台上也能原样携带；复制进真实项目时，按下表「项目里的位置」摆放，并改脚本开头的路径常量。

| 文件 | 作用 | 项目里的位置 |
|---|---|---|
| `sim.mjs` | 引擎无关玩法核心：固定步长、输入缓冲、土狼时间、按住高跳、多段跳、方块（站立/撞墙弹回）、尖刺、收集物、事件 | `game/core/` |
| `player.json`、`entities.json`、`levels.json`、`solver.json`、`chunks_<场景>.json` | 手感、实体类型、关卡、求解器验收线、片段库（每个场景一个文件） | `config/`（片段库可放 `config/chunks/`） |
| `validate_config.py` | 配置校验：schema、id 唯一、引用、取值范围、网格、安全区、「危险物须立在从地面升起的方块上」、教学节奏（每关新内容 ≤ 2）、存档点、验收线完整、可选构建模板 AppID | `tools/` |
| `solve.mjs` | 片段求解器：束搜索证明可无伤通过（撞墙也算失误）、操作密度、每个操作的时机窗口；全量/单片段/前缀通配。也导出 `loadConfig()` | `game/tools/` |
| `preview.mjs` | 无引擎预览：无头浏览器画出片段与求解路线并截图（需要本机已装 Playwright 和 Chromium） | `tools/`；真实项目应换成打包后的画面层 |
| `sync_to_engine.py` | 把核心与配置复制进引擎工程（生成头、保留 `.meta`、清理已删除配置），按 Cocos 目录布局 | `tools/`；路径按你的引擎调整 |
| `core.test.mjs` | 规则测试 + 求解器测试 + 「禁止展开 Set/Map」源码扫描 | `game/test/` |

在本目录运行：

```bash
python3 validate_config.py          # 改配置后必跑
node --test core.test.mjs           # 改核心后必跑
node solve.mjs                      # 改片段/手感后必跑；单个：node solve.mjs demo_d2_01
node preview.mjs preview_out        # 看图
python3 sync_to_engine.py <工程目录> # 构建前
```

这些脚本只读写本地文件，不访问网络。

## 迁移到真实项目

1. 核心换成你的玩法（建议 TypeScript，只用可擦除语法，Node 可直接跑测试与工具）。保留 `clone()`、固定步长 `step()`、输入方法与事件，求解器就能复用。
2. 求解器的动作集换成你的操作（翻滚、冲刺、换道……），状态去重键换成你的关键状态。
3. 校验脚本按你的配置表加规则；每次真机问题能静态描述的，加一条规则并先让它对坏数据报错。
4. 预览工具改为：esbuild 打包画面层 + 画布版精灵宿主，按场景/界面/片段截图，收集页面错误。
