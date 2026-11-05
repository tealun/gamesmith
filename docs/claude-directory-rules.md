# Claude 插件目录规则对照表（gamesmith）

提交 Claude 插件目录前要满足的已知规则，以及每条规则由什么检查。新增规则时，先在这里加一行，再补校验；能写成本地检查的就写进 `scripts/build_plugin.py --check`，写不了的要注明原因。

插件目录跟踪 `plugin` 分支（只由 CI 写入：`release.yml` 的 `plugin-branch` 作业在发布检查通过后写入，`plugin-branch.yml` 只能从已有 Release 的 tag 手动补写），插件路径留空：目录读取的是打包产物，不是 main 上的开发文件。`build_plugin.py --check` 仍对 main 的被跟踪文件做同样的检查，这样分支内容与仓库都不会违规。照搬自 tealun/tealun-dev-pdca 的同名表（2026-11-05 读取），来源一栏沿用该表的核对结果。

**来源**（tealun-dev-pdca 于 2026-11-04 读取，本表 2026-11-05 照搬）：
- **提交**：[Submit a plugin](https://claude.com/docs/plugins/submit)
- **清单**：[Pre-submission checklist](https://claude.com/docs/plugins/pre-submission-checklist.md)
- **构建**：[Build a plugin](https://claude.com/docs/plugins/build.md)
- **参考**：[Plugins reference](https://code.claude.com/docs/en/plugins-reference)
- **CLI**：`claude plugin validate`（2.1.318）的实际输出
- **方案**：维护者整理的发布方案里的说法，以上官方页面里找不到原文

**检查级别**：
- **阻断**：`--check` 报错，CI 失败；
- **提示**：`--check` 打印 warning，不阻断，因为目录对这类问题的处理是转人工审核，不是拒收。

## 提交与托管

| 规则 | 来源 | 本地检查 |
| --- | --- | --- |
| 目录只从 github.com 上的仓库读取插件 | 提交 | 不校验：仓库托管在 GitHub 上是既定事实 |
| 提交和验证期间仓库可以是私有的，上架前必须公开 | 提交 | 不校验：仓库是否公开是 GitHub 设置；提交时由用户在开发者门户确认 |
| 每个插件文件夹单独提交一次；同一组织对同一仓库加文件夹只能有一个提交 | 提交 | 不校验：本仓库只有一个插件（gamesmith），提交一次 |
| 每个组织 24 小时内最多创建 10 个提交，草稿和撤回的提交也计入 | 提交 | 不校验：属于门户操作次数 |
| 首次提交之后，目录跟踪的分支一有新提交就会扫描、检查、发布；本仓库跟踪 `plugin` 分支 | 提交 | 不校验：在门户里设置（提交时 Source 选 `plugin` 分支，插件路径留空） |
| 第一个版本必须由 Anthropic 审核员批准才能上线；在此之前点 Publish 只是登记一个请求。门户的 Auto-publish 开关只对之后通过检查的版本生效 | 门户 | 不校验：门户流程 |
| 同一仓库加文件夹已有提交（含草稿）时，再新建会报 `SUBMISSION_EXISTS`；继续已保存的草稿时，仓库、文件夹和分支都不能改，要换来源只能删掉草稿重建 | 门户 | 不校验：门户操作。首次建草稿时就选 `plugin` 分支 |
| 目录每约 6 小时检查一次跟踪的分支；配置 GitHub push webhook 后，推送几分钟内就会被拾取。webhook 的 secret 只显示一次 | 门户 | 不校验：仓库设置。提交后配置，结果回填本行 |
| 提交时要回答数据处理问卷（个人数据、外发数据、数据保留、是否面向未成年人）并勾选 4 项合规声明，答案要和 `PRIVACY.md` 一致 | 门户 | 部分校验：`tests/test_scripts.py` 的 `test_templates_make_no_network_requests` 扫描骨架脚本，出现网络请求写法即失败，保证 `PRIVACY.md`「不发起网络请求」成立。问卷本身是门户操作，答案：No · No · Not retained · No |
| 每次扫描都会按目录规则重新校验，并做安全扫描（未披露的外发数据、隐藏代码、修改权限设置）；首次提交没通过安全扫描会直接被拒；另有政策审核 | 提交 | 部分校验：`claude plugin validate` 只覆盖目录规则的一部分，不做安全扫描和政策审核 |

## 清单（plugin.json）

| 规则 | 来源 | 本地检查 |
| --- | --- | --- |
| 清单位于 `.claude-plugin/plugin.json`，`name` 必填 | 参考 | 阻断：`check()` 第 1 项 |
| 应设置 `description`、`author`、`version`，缺少会给警告 | 清单 | 阻断：`check()` 要求三项都有 |
| 名称只能用小写字母、数字、连字符，最长 64 字符，首尾必须是字母或数字；不能是保留名（`claude`、`anthropic`、`official`、`plugin`、`mcp`、`test`）；不能以 `claude-`、`anthropic-`、`anthropics-`、`cc-plugin-` 开头 | 清单 | 阻断：`check()` 的命名规则 |
| 设了 `version` 就要在每次发布时升高；Claude Code 会固定使用这个版本，直到它改变 | 提交、参考 | 阻断：`--since <上一个 tag>`，技能有改动但版本没升高 |
| `skills` 是相对插件根目录、以 `./` 开头的目录路径；本仓库的技能在 `gamesmith/`，所以显式列出（打包时改写为 `./skills/gamesmith`） | 参考 | 阻断：`check()` 第 2、3 项（和根目录下含 `SKILL.md` 的文件夹一致，每个技能都有 `SKILL.md` 且名称对得上，`SKILL.md` 和参考文件里引用的 `references/`、`templates/` 路径都存在） |
| 上架页的文字取自 `plugin.json` 和 README；上架后，名称和简短描述跟随线上版本 | 提交 | 不校验：属于文案内容 |
| `icon` 是插件内图片文件的路径；Claude Code 不读它，目录在提交时读取 | 参考 | 阻断：`icon` 指向的文件必须存在 |
| 图标规格：512–2048 px 正方形、小于 2 MB、不接受 SVG/WebP；只在第一次提交或保存时生效 | 方案 | 不校验：官方页面没找到原文。本仓库图标 `assets/gamesmith-icon.png` 为 512×512 PNG、约 75 KB（`scripts/make_icon.mjs` 生成），已满足上述说法 |

## 文件与内容

| 规则 | 来源 | 本地检查 |
| --- | --- | --- |
| 插件文件夹里要有 README，代码块之外至少 40 个单词 | 清单 | 阻断：`check()` 统计 `README.md`（按空白切分；中文按段计数偏少，README 附英文一节） |
| 要有 `LICENSE` 文件，或在 `plugin.json` 设置 `license` | 清单 | 阻断：两者都没有时报错 |
| 单个文件超过 5 MiB，校验会停止 | 清单 | 阻断：逐个检查被跟踪的文件 |
| 不能有符号链接 | 清单 | 阻断：逐个检查被跟踪的文件 |
| 不能有子模块和 LFS 指针 | 清单 | 不校验：仓库里没有 `.gitmodules`，也没有用 LFS |
| 仓库导出（git archive）的内容必须和仓库存储的完全一致：`.gitattributes` 里不能有 `export-ignore`、`filter`（包括 LFS）或会改动换行的 `eol` 规则，也不能有 Git replace refs；文件名不能含冒号或反斜杠、不能以点或空格结尾、不能是 Windows 设备名、不能有只差大小写的同名文件 | 实测（2026-11-05 门户 Validate 报错原文） | 阻断：`content_rewriting_attributes()` 不允许 `.gitattributes` 出现任何会改写内容的属性（第一次只去掉 `eol=crlf`，Validate 仍报错；改为 `* -text` 后再验证）；`export_mismatches()` 导出索引后逐个比对；文件名规则目前没有触发，暂不单独校验 |
| 图片和字体以外的文件超过 256 KiB，转人工审核 | 清单 | 提示：`directory_warnings()` |
| 文件超过 512 个，转人工审核 | 清单 | 提示：`directory_warnings()` |
| 只允许文本、SVG、PNG、JPEG、GIF、WebP 和字体；其他二进制文件（如 `.zip`、`.ico`、`.pdf`）转人工审核 | 清单 | `.zip`、`.plugin`：阻断（`FORBIDDEN_SUFFIXES`，安装包只由 `release.yml` 构建）；其他不在白名单（`TEXT_SUFFIXES` 与 `MEDIA_SUFFIXES`）里的文件：提示（`directory_warnings()`），例如 `.mp3`、`.wasm`、`.ico` |
| 删掉 `.DS_Store`、`Thumbs.db`、`desktop.ini`、`__MACOSX` | 清单 | 提示：`directory_warnings()` |
| 包启动器要固定版本（如 `npx pkg@1.2.3`），`@latest` 和不固定的版本范围会被拦下 | 清单 | 不校验：插件本身不调用启动器。CI 里的 `npx -y @anthropic-ai/claude-code@2.1.318` 已固定版本，且 CI 不进入 `plugin` 分支 |
| 凭据不能写死在代码里 | 清单 | 不校验：插件不需要任何凭据 |
| 顶层有 `bin/` 目录时，claude.ai 和 Cowork 无法安装 | 清单 | 不校验：没有 `bin/`，且打包时只收技能目录、README、LICENSE 和图标 |
| 插件里有 MCP、hooks、命令时审核更严，且只能在 Claude Code 里用 | 用户经验（2026-11-05，来自 dev-pdca 上架） | 阻断：`check()` 发现 `plugin.json` 声明 `mcpServers`、`hooks`、`commands`、`agents`、`lspServers`，或存在 `.mcp.json`、`hooks/hooks.json` 就报错。要加，先改规划、本表与 `AGENTS.md` |
| 安全扫描读不懂的编译或压缩代码，转人工审核 | 清单 | 不校验：技能目录里只有 Markdown、JSON 和 Python、JavaScript 源码，没有打包或压缩过的代码 |

## 安装包

| 规则 | 来源 | 本地检查 |
| --- | --- | --- |
| claude.ai 的安装方式：Customize > Plugins > Add > Upload plugin，上传 zip；zip 根目录（或唯一的顶层目录）里要有 `.claude-plugin/plugin.json` | 构建 | 阻断：单元测试检查包的结构；发布流程用 CLI 校验解包后的 `dist/gamesmith/` |
| `.plugin` 后缀 | 方案 | 不校验：官方页面没有 `.plugin` 格式的说明。Release 同时附上内容完全相同的 `.zip` 和 `.plugin`，README 指导用户上传 `.zip` |

## 扫描范围

目录会把插件文件夹里的所有文件都当成插件来扫描。dev-pdca 曾因插件文件夹等于仓库根目录，被报出 6 个 policy hold（CI 里的凭据、脚本与测试、下载后直接执行的命令、根目录的 `CLAUDE.md`，见其台账 EV-20261105-003）。本仓库从一开始就让目录跟踪 `plugin` 分支：`release.yml` 的 `plugin-branch` 作业在发布检查全部通过后把 `dist/gamesmith/`（技能、`plugin.json`、README、LICENSE、图标）追加提交到这个分支。

## 继承的防线（来自 tealun-dev-pdca 演进台账）

| 条目 | 坑 | 本仓库的防线 |
| --- | --- | --- |
| EV-20261102-001 | 拿 WorkBuddy 的报错逐条试规则，连续被拒 4 次 | `docs/workbuddy-rules.md` 逐条登记，`build_suite.py --check` 在打包前校验；CI 每次推送都跑 |
| EV-20261102-003 | 只把带数字的规则写成校验，漏了「包内只能有一个 SKILL.md」 | `build_suite.py` 的 `validate_package()` 检查结构类规则：单个 `SKILL.md`、层级、BOM、其他 `.md` 无技能 frontmatter |
| EV-20261105-002 | `.gitattributes` 的换行转换让导出内容与存储内容不一致，Validate 失败；只去掉 `eol=crlf` 仍不够 | `.gitattributes` 为 `* -text`；`content_rewriting_attributes()` 与 `export_mismatches()` 阻断 |
| EV-20261105-003 | 插件文件夹等于仓库根目录，开发工具被一起扫描 | 目录跟踪只由 CI 写入的 `plugin` 分支 |

## 待回填（提交门户后）

| 事项 | 结果 |
| --- | --- |
| `plugin` 分支的 Validate（7 项检查） | 待提交 |
| 安全扫描与目录政策报出的项（特别是 `templates/` 里的脚本，规划 V4） | 待提交；报出的每一项先登记到本表，再决定处理方式 |
| 审核员批准首版 | 待提交 |
| push webhook | 待配置 |
