# Blender V3.2 单 MCP 全接口适配 — 离线测试

- 日期：2026-10-19
- 项目：从 V3.1 工程延伸的唯一 `industrial_blender` MCP，原版 DSH 后端固定版本通过安装器安装。
- 执行指令：`PYTHONPATH=<解压工程根目录> python -m pytest -q tests`
- 结果：**25 passed**（纯离线 Python 测试）。
- 额外检测：`python -m compileall` Python 语法通过；Web JavaScript 用 `node --check` 检查。
- 检测覆盖：已有端子/文件完整性校验、MCP 单入口注册、导入限制、非破坏性修改测试、DSH HTTP 读写路由映射、安全 loopback 校验、上游业务错误传递、NDJSON 流末尾解析、PNG 字节识别。
- 无法检测：DSH 全部 186 项 op 的逐项实机运行、Blender GUI Bridge 连接、Node HTTP 运行时在 Windows 是否兼容、真实图像质量、RTX 3070 的 Three.js FPS。原因：当前执行环境无用户 Windows Blender/RTX 显卡且无 GitHub 直连。
- 现场验收工具：`tools/verify_install.py` 运行后保存 `reports/dsh_integration_probe.json`。`/doctor.kind=ok` 是真正连通判据。
- **结论：** 全后端 API **代码适配完成，离线测试通过；生产级真机验证未完成**。不要将“API 动态转发覆盖”和“186 项业务逐一验证”混为一谈。
