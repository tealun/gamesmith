# gamesmith

通用休闲小游戏开发技能（Claude Code / Agent Skills 格式）。覆盖从立项合规到上线运营的完整流程，适用于微信、抖音等小游戏平台与任意休闲玩法；经验来自一款已走完开发、备案流程的微信小游戏（横版跑酷，Cocos Creator 3.8 + 引擎无关 TypeScript 核心），技能正文保持通用，案例只在「示例」中引用。

## 包含什么

```
SKILL.md                         技能入口：触发条件 + 九个阶段（做什么 / 产出物 / 完成判据 / 常见坑）
references/
  compliance.md                  备案与网络类型、资质、健康忠告、适龄、隐私、字体素材授权、名称简称、待核实清单
  architecture.md                引擎无关核心 + 引擎壳、配置表与校验、同步脚本、无引擎预览、测试、命令表
  level-pipeline.md              片段与关卡、求解器验收线、骨架派生生成器、教学节奏、场景配置化
  art-pipeline.md                代码绘制烘焙图集、图集尺寸与拆分、视觉语言、评审流程、字体子集
  platform-wechat-cocos.md       分包与首帧加载页、构建模板、ES5 编译坑、真机报错、缓存、meta、安全区、埋点编码、分享
  feel-and-ux.md                 输入缓冲/土狼时间/排队起跳、打击感、首次拾取提示、自动暂停、存档点、攒命、解锁与限时开放
  launch-checklist.md            上线前逐项清单
  playtest-loop.md               真机反馈闭环、文档唯一事实来源、演进台账、任务与数据驱动
templates/                       可运行的最小骨架（玩具跑酷）：核心、配置、校验、求解器、预览、同步、测试
```

平台事实（审核规则、包体上限、接口能力）只写已核实或实测过的，并注明「以官方文档为准」；未核实的标为「待核实」。

## 安装

**个人技能（所有项目可用）**

```bash
git clone https://github.com/tealun/gamesmith.git ~/.claude/skills/gamesmith
```

**项目技能（随仓库共享）**

```bash
git clone https://github.com/tealun/gamesmith.git .claude/skills/gamesmith
```

**作为插件**：放进你的插件仓库的 `skills/gamesmith/` 目录，再按 Claude Code 插件市场的方式安装（插件清单格式以 Claude Code 官方文档为准）。

安装后，在对话里提到「做小游戏」「微信小游戏上线」「关卡求解器」「mini game」等，Claude 会自动加载；也可以直接说「用 gamesmith 技能」。

## 试运行骨架

```bash
cd templates
python3 tools/validate_config.py
node --test test/*.test.mjs
node tools/solve.mjs
node tools/preview.mjs preview_out   # 需要 Playwright + Chromium
```

