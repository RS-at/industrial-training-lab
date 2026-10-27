# Claude 迁移适配说明

这些技能来自本机 Codex 安装，用于用户在 Claude 的私人迁移。保留原作者、许可证和参考文件。

- 使用当前 Claude 会话实际提供的工具。原文中的 Codex 工具命名并不证明该工具在 Claude 可用。
- Bash/Read/Write/Edit/浏览器和连接器：按真实工具能力映射，先发现 schema；不要编造 `functions.exec`、`mcp__codex_app`、`artifactSession`、`cua_repl` 或其他不可用接口。
- Windows 本地路径只在本机 Claude Code/有文件访问的桌面环境有效；普通云端对话不能读取 C 盘或连接 127.0.0.1 的 MCP。上传技能只提供指引，不会安装软件和 MCP。
- PLC/TIA/机器人/电气项目保留原有验证与控制器操作授权边界。未连接软件时可分析、编写和准备文件，不能声称已经编译、下载或验证真实设备。
- Blender 使用 industrial_blender；旧 blender 配置原本停用，继续保持停用。现成模型优先，本地索引 <local asset library>/industrial-models/index.json；以及自己的云盘素材库（如有）。保留来源和许可；外形不等于核验过端子、动作或运动学。
- Word/Excel/PPT/PDF 优先 Claude 自带或 Anthropic 官方技能。Google 工作区用 Claude 端重新授权的连接器。不能移植 Codex 登录令牌或 ChatGPT 的 OAuth。
- Codex 专用 Sites 发布、ChatGPT Pets、Codex 任务/侧栏管理、内嵌画布及宿主浏览器桥接不能仅靠技能文件迁移；缺失这些能力时明确说明，不伪造成功。
