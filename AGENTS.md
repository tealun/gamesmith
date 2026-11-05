# gamesmith 仓库的 Agent 指令

本仓库开发的是技能 gamesmith（休闲小游戏开发流程）。技能源码在 `gamesmith/`（`SKILL.md`、`references/`、`templates/`）；`.claude-plugin/plugin.json` 是插件清单，也是版本的唯一来源。发布体系照搬 tealun/tealun-dev-pdca，决定见 `docs/88_planning/plugin-release-20261105.md`。

## 配套技能：要调用，不要只“照着精神做”

本仓库的工作流程使用 Tealun Dev PDCA（planner、tasker、bugfixer、auditor、evolver）。触发条件满足时，通过技能工具调用对应技能；技能工具里看不到时，读取 tealun/tealun-dev-pdca 仓库里对应目录的 `SKILL.md`（`planner/SKILL.md` 等）并按步骤执行。只按“大意”去做不算调用。每个会话的第一条回复，先说明这五个技能里哪些可用、用的是技能工具还是读取的 `SKILL.md`；缺哪个就直说。

- **planner：任何规划意图，不论大小。** 技能结构调整、新增参考或骨架、发布方式、新平台、文档体系或流程。在改文件之前调用，先把决定写进 `docs/88_planning/`。
- **tasker：任何对文件或状态的改动，包括看起来很小的修补。** 动手前写清完成定义和一个可执行的检查；收尾时给出证据（命令输出、读回结果），不要只给描述。只读的问答不需要。
- **bugfixer：用户说有问题或“还是不对”、某个检查失败、CI 失败、外部平台（插件目录、WorkBuddy）上传或审核被拒时。** 先复现或直接观察，证明原因，只修这个原因，再验证最初的症状已经消失。
- **auditor：推送影响打包脚本、发布流程或平台规则表的改动之前，发布之前，以及任何审计请求。**
- **evolver：用户报告的问题修好并验证之后、同一周期内第二次被纠正之后、以及每个工作周期结束时。** 把经验和对应的防线记到 `docs/98_evolution/evolution-ledger.md`；同时在 `docs/98_evolution/compliance-log.md` 按其中 5 道 Gate 各记一行。

## 本仓库的硬规则

- **发布到外部平台之前，先查清它的全部规则。** 字段、长度、数量、目录结构等要求逐条登记到对照表（Claude 插件目录见 `docs/claude-directory-rules.md`，WorkBuddy 见 `docs/workbuddy-rules.md`），每条要么写进 `scripts/build_plugin.py --check` 或 `scripts/build_suite.py --check`，要么写明不校验的原因；本地通过后再上传。不要用平台的报错来逐条试规则，也不要只挑带数字的规则做校验。平台报出的新项，先登记进对照表再处理。照搬别的仓库的规则表时，回到原始来源逐条核对，并在表头写明核对日期，不能只核对抄来的表本身。
- **改了 `gamesmith/` 里的任何文件，** 运行下面的检查，全部通过才提交：
  - `python3 scripts/build_plugin.py --check`
  - `python3 scripts/build_suite.py --check`
  - `python3 scripts/check_ledger.py`
  - `python3 -m unittest discover -s tests`
  - 在 `gamesmith/templates/` 下：`python3 validate_config.py`、`node --test core.test.mjs`、`node solve.mjs`
- **版本以 `.claude-plugin/plugin.json` 为唯一来源。** `SKILL.md` 不写 `version`（WorkBuddy 包的版本由 `build_suite.py` 从 `plugin.json` 注入）。改了 `gamesmith/` 就升版本，并在 `CHANGELOG.md` 加一节 `## gamesmith <版本>`。升法：删掉阶段、改变技能名或触发范围的大改升 major；新增阶段、参考文件或骨架脚本升 minor；其余（修正文字、补充条目、修骨架的 bug）升 patch。CI 用 `build_plugin.py --check --since <上一个 tag>` 拦截没升版本的改动。
- **发布只靠推送 `v<版本>` tag，** 由 `.github/workflows/release.yml` 构建并创建 Release，附上 `gamesmith-<版本>.plugin`、`.zip`、`gamesmith-workbuddy.zip` 和 flat 包。不手动上传 Release 附件，不把 `.zip`、`.plugin` 提交进仓库（`build_plugin.py --check` 会阻断）。
- **`plugin` 分支只由 CI 写入：** `release.yml` 的 `plugin-branch` 作业在全部发布检查通过、Release 建好之后写入；`plugin-branch.yml` 只用于从已有的 Release tag 手动补写，不发布 main。 插件目录和 tealun 市场都跟踪这个分支。它只包含打包好的插件（技能、`plugin.json`、README、LICENSE、图标），不要手动往里提交，也不要把开发文件（CI、脚本、测试、文档、`CLAUDE.md`）放进去。
- **`.gitattributes` 保持 `* -text`。** 任何会改写内容的属性（`text`、`eol`、`filter`、`export-ignore` 等）都会让插件目录的 Validate 因导出内容和存储内容不一致而失败；`build_plugin.py --check` 会阻断。
- **README 里不写下载后直接执行的命令**（`curl | sh`、`git clone` 后运行脚本、`npx` 等）。安装说明只用插件市场命令、Release 下载和复制文件夹；`build_plugin.py --check` 会阻断。
- **本仓库不放 `marketplace.json`。** 市场清单在 `tealun/tealun-plugins`：新插件在那里加一条（`source` 为 `{"source":"github","repo":"tealun/gamesmith","ref":"plugin"}`），README 插件表加一行。两份同名的 `tealun` 市场会冲突。
- **提交 Claude 插件目录：** 每个插件单独提交一次；第一个版本必须经 Anthropic 审核员批准；提交后在 GitHub 配置 push webhook（secret 只显示一次）。数据问卷的答案要和 `PRIVACY.md` 一致（本插件：No · No · Not retained · No）。这些是门户操作，由 Tealun 完成，结果登记进 `docs/claude-directory-rules.md`。
- **插件里不加 MCP、hooks 或命令。** 它们会让目录审核更严，也只能在 Claude Code 里用；只有技能的插件在 claude.ai 等处都能用。`templates/` 里的骨架脚本是给用户项目复制的，不由插件自动运行，也不联网；新增脚本时保持这两点，并同步 `PRIVACY.md`。
- **新增技能内容或大改工作流之后、发布之前，** 派一个只拿到 `gamesmith/SKILL.md` 路径的全新 agent，在真实项目上按技能执行一次，要求它列出指令不清、矛盾或缺失之处；核验它的产出后按反馈迭代。用作样本的项目一律只读：规划里写明，产出写到会话 scratchpad，不写进样本仓库。
- **本仓库是公开仓库。** 文件、提交信息和 PR 描述里不写内部决策过程、会话编号或会话链接、私有仓库名、商业安排，只写对使用者和贡献者有用的内容；拿不准的先问维护者。提交信息末尾只保留 `Co-Authored-By` 行，不写 `Claude-Session` 行。开 PR 后读回描述：服务端可能在末尾自动追加带会话链接的页脚，出现就删掉。已经推送的提交保持原样，不改写历史。
- **平台事实不臆造。** 技能正文里的平台规则只写官方原文或真机实测过的，附来源；其他 AI、第三方代办、论坛的答复只作线索，没核实的标「待核实」。
