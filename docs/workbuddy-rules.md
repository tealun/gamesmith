# WorkBuddy 上架规则对照表（gamesmith）

`gamesmith-workbuddy.zip`（由 `scripts/build_suite.py` 生成到 `dist/`，发版时附在 Release 上）上传 WorkBuddy 前要满足的全部已知规则，以及每条规则在本地由谁检查。新增规则时，先在这里加一行，再补校验；能校验的必须写进 `scripts/build_suite.py`，不能校验的写明原因。

照搬自 tealun/tealun-dev-pdca 的同名表（2026-11-05 读取）。来源：**实测** = dev-pdca 上传或审核实际报错过；**第三方** = [wb-skill-converter 的 workbuddy-schema.md](https://github.com/starve001/wb-skill-converter/blob/main/references/workbuddy-schema.md)，非官方文档；**推断** = 为规避已知问题而加的约束。

gamesmith 只有一个技能，所以包就是技能文件夹本身，不需要 dev-pdca 那样的套件入口。WorkBuddy 要求的展示字段放在 `workbuddy/frontmatter.json`，打包时与 `gamesmith/SKILL.md` 的 `name` 以及 `plugin.json` 的 `version` 合并成包内的 `SKILL.md`；包内的 `description` 取 `description_zh`（平台约定），Claude 用的中英双语触发描述留在 `gamesmith/SKILL.md`。

第三方来源 2026-11-05 逐条对照过一次（发布前审计发现首版漏登了 6 条，已补在下表）。

| 规则 | 来源 | 本地检查 |
| --- | --- | --- |
| 目录最多三层：根目录 / 二级目录 / 文件 | 实测 | `validate_package()`：包内路径（加上顶层 `gamesmith/`）超过即报错。为此 `templates/` 在源码里就是单层目录 |
| 包内只能有一个 `SKILL.md`（多个会被判为多 skill 包、资产无效） | 实测 + 第三方 | `validate_package()`：只允许根目录一个 |
| 其他 `.md` 不能带技能 frontmatter | 推断（规避被识别为第二个技能） | `validate_package()` |
| 必填 `display_name`、`display_name_en`、`description_zh`、`description_en` | 实测 | `validate()` |
| 必填 `name`、`description`、`version` | 第三方 | `validate()`：都存在，`version` 为 x.y.z（取自 `plugin.json`） |
| `description` 约定与 `description_zh` 同值（市场列表与技能召回都用它） | 第三方 | `validate()`：包内两者必须相同 |
| `workbuddy-` 前缀疑似官方保留 | 第三方 | `validate()`：`name` 不能以它开头 |
| 付费资产的展示名只允许中英文、数字和 `-` `—`，不能含空格（免费时无此限制） | 第三方 | `validate()`：`display_name` 不能含空白，免得以后转付费被退回 |
| 建议填 `agent_created: true`（标记由 agent 创建，之后用 `skill_manage` 修改不受限） | 第三方 | 不采纳：只影响平台内由 agent 修改技能的权限；本技能在仓库里维护、由 CI 打包，不需要。被拒或有需要时再加 |
| `name` 符合 `^[a-z0-9][a-z0-9-]{0,39}$` | 第三方 | `validate()` |
| `display_name_en` ≤ 60 字符 | 第三方 | `validate()` |
| `description_zh` ≤ 500 字符 | 第三方 | `validate()` |
| `description_en` ≤ 1000 字符 | 实测 | `validate()` |
| `description` ≤ 1024 字符 | Agent Skills 规范 | `validate()` |
| `examples_zh`、`examples_en` 各 1–3 条 | 实测 | `validate()` |
| frontmatter 必须是合法 YAML（值里有 `: ` 要加引号） | 第三方 | 生成时每个值都写成 JSON 引号字符串；`validate_package()` 用自带解析器读回比对，装了 PyYAML 时再用它读回比对 |
| 编码 UTF-8 无 BOM | 第三方 | `validate_package()`：逐个文本文件检查 BOM 与 UTF-8 解码 |
| 换行统一 LF | 第三方 | `read_normalized()`：打包时把文本文件的 CRLF 换成 LF；仓库 `.gitattributes` 为 `* -text`，存的本来就是 LF |
| 排除 `__pycache__`、`.git`、`.DS_Store`、`node_modules`、`*.pyc` | 第三方 | `EXCLUDE_PATTERNS`（另排除 `preview_out`）；`.git` 不会进包：只收 `gamesmith/` 目录里的文件和 `LICENSE` |
| 压缩包根目录直接放 `SKILL.md`，不要多套一层目录 | 第三方 | 不校验：dev-pdca 实测内含顶层文件夹的包已解析通过；只有因这一条（目录层级）被拒时才改传 Release 里的 `-flat.zip`；其他原因被拒，先把规则登记进本表、补检查、修复，再重新上传同一个包 |
| `name` 全平台唯一 | 第三方 | 不能本地校验：只有上传时平台才能判断（规划 V2） |
| `category` 建议填写 | 第三方 | 已填 `developer`，不强制校验 |
| 包内可以带脚本文件（`.py`、`.mjs`） | 未知 | 不校验：没有找到规则；dev-pdca 的包带 `.py` 已通过。gamesmith 还带 `.mjs`，上传结果回填本行（规划 V2） |
