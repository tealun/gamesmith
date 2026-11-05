# Gamesmith

中文 | [English](#english)

一人 + AI 做休闲小游戏的阶段化开发技能。适用于微信、抖音等小游戏平台，任意玩法；覆盖从立项合规到上线后运营的完整流程。经验来自一款已走完开发、备案流程的微信小游戏（横版跑酷，Cocos Creator 3.8 + 引擎无关 TypeScript 核心），技能正文保持通用，案例只在「示例」中引用。

## 它帮你做什么

技能入口 `SKILL.md` 把开发分成九个阶段，每个阶段写清做什么、产出物、完成判据和常见坑：

| 阶段 | 要点 |
| --- | --- |
| 立项与合规 | 先查名称和商标，定备案与网络类型，列出健康游戏忠告、适龄提示、隐私、字体授权等上线必备项 |
| 原型与手感 | 网页灰盒原型在手机上调手感：输入缓冲、土狼时间、受击反馈 |
| 架构与配置驱动 | 玩法核心写成引擎无关代码并单测，数值和内容进配置表并配校验脚本，引擎只做壳 |
| 内容管线 | 关卡由片段组成；求解器验收能否无伤通过、操作密度、时机窗口；生成器从骨架片段派生新场景 |
| 美术管线 | 代码绘制烘焙图集，单页不超过 2048×2048，按「公共 + 每场景」拆分 |
| 平台接入与构建 | 分包与首帧加载页、构建模板、编译目标的坑、真机屏幕报错、埋点整数编码 |
| 真机试玩迭代 | 反馈 → 复现 → 最小修复 → 回归测试 → 证据，配演进台账 |
| 上线清单 | 资质、合规、构建、开关、质量、数据、提审材料逐项勾选 |
| 上线后 | 指标阈值、片段死亡率排行、分批或限时开放内容、赛季规划 |

技能目录里的 `references/` 是各主题的检查表，`templates/` 是可运行的最小骨架（玩具跑酷）：配置表与校验脚本、片段求解器、无引擎预览、同步脚本、规则测试。平台事实（审核规则、包体上限、接口能力）只写已核实或实测过的，并注明以官方文档为准；没核实的标为「待核实」。

## 安装

同一个工具里只用一种方式，否则技能会出现两份。

### Claude Code：tealun 插件市场

在 Claude Code 会话里输入：

```text
/plugin marketplace add tealun/tealun-plugins
/plugin install gamesmith@tealun
```

装好后新建会话。说「做一个微信小游戏」「帮我写关卡求解器」「小游戏上线清单」等，技能会自动加载；手动调用写 `/gamesmith:gamesmith`。更新：`/plugin marketplace update tealun`。

### claude.ai

1. 打开 [最新 Release](https://github.com/tealun/gamesmith/releases/latest)，下载 `gamesmith-<版本>.zip`（同一个包也以 `.plugin` 后缀附上，内容相同）。
2. 在 claude.ai 打开 Customize > Plugins > Add > Upload plugin，上传这个 zip。

### 其他 Agent 工具

1. 从最新 Release 下载 `gamesmith-<版本>.zip` 并解压。
2. 把里面的 `skills/gamesmith` 文件夹复制到工具的技能目录，例如 `~/.claude/skills`、`~/.codex/skills` 或共享的 `~/.agents/skills`。
3. 重新打开工具或新建会话。

### WorkBuddy 等只接受单个技能压缩包的平台

从最新 Release 下载 `gamesmith-workbuddy.zip`，在平台的技能上传入口选择它。只有平台因目录层级（要求 `SKILL.md` 直接位于压缩包根目录）拒收时，才改用同一 Release 里的 `gamesmith-workbuddy-<版本>-flat.zip`。

## 隐私

技能只是一组说明和骨架代码，不收集、不发送任何数据，见 [隐私政策](https://github.com/tealun/gamesmith/blob/main/PRIVACY.md)。插件本身不会执行任何代码；骨架脚本要复制进你自己的项目、装好依赖（预览工具需要 Playwright 和 Chromium）后，由你或 Claude 在项目里运行，只读写本地文件。

## 许可

[MIT](LICENSE)

---

## English

Gamesmith is a skill for building casual mini games with AI, for WeChat, Douyin and similar platforms and any genre. It splits the work into nine stages, from kickoff and compliance to post-launch iteration, and for each stage states what to do, the deliverables, the done criteria and the common pitfalls. Inside the skill folder, `references/` holds topic checklists and `templates/` holds runnable skeletons: config tables with a validator, a chunk solver that proves each level chunk clears unhurt with a fair action density and timing window, an engine-free preview, a sync script and rule tests. Platform facts are limited to ones verified against official documentation or on a real device; everything else is marked to verify.

Install in Claude Code from the tealun marketplace:

```text
/plugin marketplace add tealun/tealun-plugins
/plugin install gamesmith@tealun
```

On claude.ai, download `gamesmith-<version>.zip` from the latest Release and upload it under Customize > Plugins > Add > Upload plugin. For other agent tools, copy `skills/gamesmith` from that zip into the tool's skills folder. For WorkBuddy, upload `gamesmith-workbuddy.zip`. The skill collects and sends no data ([privacy policy](https://github.com/tealun/gamesmith/blob/main/PRIVACY.md)). License: [MIT](LICENSE).
