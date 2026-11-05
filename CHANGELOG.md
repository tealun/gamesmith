# Changelog

版本以 `.claude-plugin/plugin.json` 为唯一来源；发版时 `release.yml` 取本文件里 `## gamesmith <版本>` 一节作为 Release 说明。

## gamesmith 1.0.0

首个发布版本。

- 技能 `gamesmith`：休闲小游戏开发的九个阶段（立项与合规、原型与手感、架构与配置驱动、内容管线、美术管线、平台接入与构建、真机试玩迭代、上线清单、上线后），每阶段写清做什么、产出物、完成判据、常见坑。
- 8 份参考检查表：合规、架构、关卡管线、美术管线、微信 + Cocos 平台、手感与体验、上线清单、真机试玩闭环。平台事实只收已核实或实测项；2026-11-05 按官方原文复查：朋友圈分享为 Beta、暂只支持 Android；激励视频每用户每日次数有限；`wx.reportEvent`「仅整型」降为待核实。
- 可运行骨架（`gamesmith/templates/`，单层目录）：引擎无关核心、配置表与校验脚本、片段求解器、无引擎预览、同步脚本、规则测试。
- 发布体系照搬 tealun/tealun-dev-pdca：插件目录与 tealun 市场跟踪只由 CI 写入的 `plugin` 分支；推 `v<版本>` tag 发布，Release 附插件包和 WorkBuddy 包；两张平台规则对照表逐条对应本地检查。
