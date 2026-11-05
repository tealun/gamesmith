# gamesmith 演进台账

踩过的坑、根因和对应的防线。格式与 tealun/tealun-dev-pdca 相同（`scripts/check_ledger.py` 校验编号唯一、每行 8 列）；那边与发布体系有关的四条（EV-20261102-001、EV-20261102-003、EV-20261105-002、EV-20261105-003）以防线的形式继承，见 `docs/claude-directory-rules.md`「继承的防线」。

| ID | Trigger/Evidence | Root Cause | Local Fix | Systemic Action | Guard Verification | Closure Level | Next Planning Input |
|---|---|---|---|---|---|---|---|
| EV-20261105-001 | 2026-11-05 用户转来另一个 AI 对 7 个待核实问题的答复。按官方原文复查：「激励视频不限次数」与官方原文相反；埋点配额说的是 `wx.reportAnalytics`，不是我们用的 `wx.reportEvent`；还发现技能与 carrot-run 03_01 都把「`wx.reportEvent` 上报值仅支持整型」标为已核实，但 API 页上找不到这句。 | 「已核实」只要求写了来源链接，没有要求原文能在该页找到；外部答复与官方原文之间没有区分规则。 | 朋友圈分享按原文改为已核实（Beta、暂只 Android）；激励视频补原文；「仅整型」降为待核实（gamesmith 18d9f74，carrot-run 96d4071）。 | `references/compliance.md` 第 7 节与 `AGENTS.md`：只有官方原文（附链接与「最后一次编辑」日期）或实测才能标为已核实，其他 AI、第三方的答复只作线索；carrot-run 03_01 的待核实清单写入同一规则。 | 已读回两仓库的改动与推送后的远端提交。规则本身是文字约束，没有自动检查。 | Guarded | 写平台事实时引用原文句子；下次复查时抽查已核实条目能否在来源页找到原文，找不到的降级。 |
