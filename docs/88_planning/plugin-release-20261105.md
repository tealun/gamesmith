# 规划：gamesmith 发布体系（插件目录 + tealun 市场 + WorkBuddy）

日期：2026-11-05 · 归属：Tealun + AI · 依据：照搬 tealun/tealun-dev-pdca 的发布体系

## 理解卡

- **是什么**：gamesmith 是单个技能（`SKILL.md` + `references/` + `templates/`），目标同时发布到三处：Claude 插件目录、Tealun 自己的 Claude Code 插件市场 `tealun`、WorkBuddy。
- **照搬对象**：dev-pdca 的 `AGENTS.md`（技能调用规则、发布硬规则）、两张平台规则对照表、`build_plugin.py` / `build_suite.py` / `publish_plugin_branch.sh`、三个 workflow、`.gitattributes`，以及演进台账里的四条防线。
- **约束**：发布前把平台规则全部登记并写成本地检查；仓库不放 zip、`.plugin` 或 `marketplace.json`；README 里不写下载后直接执行的命令；版本只认 `plugin.json`；只靠推 tag 发布；`plugin` 分支只由 CI 写入。
- **差异**：dev-pdca 有六个技能，WorkBuddy 要打成套件包。gamesmith 只有一个技能，WorkBuddy 包就是技能本身，再加上平台要求的展示字段。

## 读取的演进台账条目（来自 tealun-dev-pdca）

| 条目 | 教训 | 本仓库的落点 |
|---|---|---|
| EV-20261102-001 | 拿平台报错逐条试规则，连续被拒 4 次 | D9：WorkBuddy 规则全部登记，写进 `build_suite.py` 再上传 |
| EV-20261102-003 | 只挑带数字的规则做校验，漏了「只能有一个 SKILL.md」 | D9：结构类规则（层级、单个 SKILL.md、无 BOM、无其他技能 frontmatter）同样做成检查 |
| EV-20261105-002 | `.gitattributes` 的换行转换让导出内容和存储内容不一致，插件目录 Validate 失败 | D8：`* -text`；`build_plugin.py --check` 检查会改写内容的属性，并逐个比对导出内容 |
| EV-20261105-003 | 插件文件夹等于仓库根目录，CI、脚本、测试被一起扫描，报出 policy hold | D7：插件目录跟踪 `plugin` 分支，分支里只有打包产物 |

本仓库自己的台账此前不存在：本规划新建 `docs/98_evolution/evolution-ledger.md`。

## Decisions

| # | 决定 | 理由 |
|---|---|---|
| D1 | 技能移到 `gamesmith/` 文件夹（`gamesmith/SKILL.md`、`references/`、`templates/`），`plugin.json` 用 `"skills": ["./gamesmith"]` | 与 dev-pdca 相同：技能文件夹名等于 frontmatter 的 `name`，校验和打包规则可以直接复用 |
| D2 | `templates/` 改为单层目录（所有文件直接放在 `templates/` 下，片段库改名为 `chunks_<场景>.json`） | WorkBuddy 限制目录最多三层（根目录 / 二级目录 / 文件），`gamesmith/templates/config/chunks/demo.json` 超限。改成单层后，插件包和 WorkBuddy 包用同一份源码，不需要打包时改写 import 路径 |
| D3 | 版本只写在 `.claude-plugin/plugin.json`；`SKILL.md` 不写 `version`，`build_suite.py` 打 WorkBuddy 包时从 `plugin.json` 注入 | 用户要求「版本以 plugin.json 为唯一来源」 |
| D4 | WorkBuddy 的展示字段（`display_name`、`display_name_en`、`description_zh`、`description_en`、`examples_zh`、`examples_en`、`author`、`category`）放在 `workbuddy/frontmatter.json`，打包时合并进包内 `SKILL.md`；写出时每个值都是 JSON 引号字符串，保证是合法 YAML | Claude 用的 `SKILL.md` 保持干净，不带别的平台的字段 |
| D5 | 包名：插件包 `gamesmith-<版本>.plugin` / `.zip`；WorkBuddy 包 `gamesmith-workbuddy.zip`（另有 `-flat.zip` 备用），都只在 `dist/` 生成，由 `release.yml` 附到 Release | 规则 4：仓库不提交安装包 |
| D6 | 许可证 MIT | 与 dev-pdca 一致；插件目录要求有 LICENSE。**用户可改**，改了要同步 `plugin.json` 的 `license` |
| D7 | 插件目录、tealun 市场都跟踪 `plugin` 分支，由 `release.yml` 的 `plugin-branch` 作业在发布检查全部通过后写入（2026-11-05 审计 F1：原先的独立 workflow 与 release 并行，不受 release 检查约束）；`plugin-branch.yml` 只用于从已有 Release 的 tag 手动补写 | EV-20261105-003 |
| D8 | `.gitattributes` 为 `* -text` | EV-20261105-002 |
| D9 | `docs/claude-directory-rules.md`、`docs/workbuddy-rules.md` 逐条登记规则；每条对应 `build_plugin.py --check` / `build_suite.py --check` 的一项检查，或写明不校验的原因 | EV-20261102-001、-003 |
| D10 | 图标用代码绘制，`scripts/make_icon.mjs` 生成 512×512 PNG 到 `assets/`（只在需要换图标时运行） | 目录读取 `icon` 作为上架图标；本技能本身就推荐代码绘制美术 |
| D11 | README 的安装方式：tealun 市场两条命令、claude.ai 上传 Release 里的 zip、把 Release 里的技能文件夹复制到其他工具的技能目录。不写 `git clone`、`curl`、`npx` | 规则 5；`build_plugin.py --check` 的 `DOWNLOAD_AND_RUN` 检查拦截 |
| D12 | 保留 `templates/` 里的可运行骨架（Python、Node 脚本）。它们只在用户自己的项目里由用户或 Claude 运行，不联网（预览工具启动本机 Chromium，只读本地文件）。`PRIVACY.md` 和目录问卷照此填写：No · No · Not retained · No | 骨架是技能的主要价值之一。代价见 V4 |
| D13 | CI（`suite-package.yml`）每次推送除了跑打包校验，还跑骨架自身的检查：配置校验、`node --test`、求解器 | 骨架是技能的一部分，坏了要在推送时就发现 |
| D14 | 不在本仓库放 `marketplace.json`；市场条目加在 `tealun/tealun-plugins`，`source` 为 `{"source":"github","repo":"tealun/gamesmith","ref":"plugin"}`，README 插件表加一行 | 规则 10 |
| D15 | 发布顺序：本地全部检查通过 → 全新 agent 试跑并迭代 → auditor 审计 → 推 main → 推 `v1.0.0` tag → 确认 CI 建好 Release 和 `plugin` 分支 → 在 tealun-plugins 加条目 | `plugin` 分支要先存在，市场条目才能安装 |

## Assumptions

- A1：Claude Code 插件里的技能允许携带脚本文件（dev-pdca 的 `evolver/scripts/` 已通过目录扫描）。
- A2：WorkBuddy 按 dev-pdca 已验证的方式解析：包内一个顶层文件夹，`SKILL.md` 在其中。

## To Verify

| # | 待核实 | 证据格式 | 负责 |
|---|---|---|---|
| V1 | 插件目录对 `plugin` 分支的 Validate 与扫描结果 | 门户截图或报出项原文，登记进 `docs/claude-directory-rules.md` | Tealun（门户操作） |
| V2 | WorkBuddy 能否解析并通过审核；`name` 是否与平台已有技能重名 | 上传结果截图 | Tealun |
| V3 | claude.ai 上传 Release 里的 zip 能否安装 | 截图 | Tealun |
| V4 | `templates/` 里的脚本是否让目录转人工审核或报出 hold | 门户报出项原文 | Tealun；被报出后先登记规则再处理 |
| V5 | 首次推 tag 后 `release.yml` 的两个作业是否全绿 | Actions 运行结果 | AI |

## 阶段门槛

- **M0（本地）**：两张对照表登记完；`build_plugin.py --check`、`build_suite.py --check`、`check_ledger.py`、`unittest`、骨架检查全部通过；`claude plugin validate` 对打包产物无报错。失败即不推送。
- **M1（试跑）**：全新 agent 只拿到 `gamesmith/SKILL.md` 路径，在一个真实的小游戏项目上执行一次（样本项目只读，产出写到会话的临时目录），列出指令不清、矛盾、缺失之处；核实后修改技能。
- **M2（发布）**：auditor 审计通过 → 推 tag → Release 附件齐全、`plugin` 分支只含打包产物 → tealun 市场条目上线，`check_marketplace.py` 与 `claude plugin validate .` 通过。
- **M3（平台）**：插件目录提交（Tealun 在门户操作，首版要审核员批准，配置 push webhook）；WorkBuddy 上传。结果回填 V1–V4。

## 结论

Ready for implementation（M0 起）。
