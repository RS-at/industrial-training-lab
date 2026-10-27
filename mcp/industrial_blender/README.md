# Blender V3.2 — 单 MCP · DSH 完整后端接口适配

**一个 MCP：`industrial_blender`。一个 Skill：`industrial-blender-v3`。**

此包将原有工业 Blender V3 基础功能与 **DSH 原版 Blender 后端 HTTP API** 统一封装进 **单个 Codex MCP 服务端**。它不再限制 DSH `/plan` 的操作白名单：全部操作由上游原版 `runtime/engine.mjs` + `runtime/*.py` 执行，适配层只进行协议转换、错误处理和图像回传。保留原作者实现、版本与许可证。

> **重要交付边界：** 这不是把 DSH 的 2MB 级完整源码重写后塞进 ZIP 的离线包。`BOOTSTRAP_DSH.ps1` 会在用户 Windows 电脑上**下载完整上游代码并固定到指定 Git commit**，包括所有 186 个 `/plan` 操作、addon 和测试。运行时**不需要 DSH 主程序**。DSH 的浏览器/桌面宿主视口面板、点选交互 UI 不能在 Codex 里原样显示；其 HTTP 接口保留，Codex 的截图、对象名、视图命令可替代主要建模流程。
>
> 本环境不具备你的 Windows Blender/RTX 3070，因此**只完成接口适配与离线测试，尚不能证明真机完整运行**；准确说是“**全后端 API 接入版，现场验收待完成**”，不能说已经实际完成所有 186 项功能的运行验证。

## 核心能力

- **V3 内置功能**：`.blend` 场景检查、导入网格、三视角渲染、图片交给 Codex 视觉、结构化修改闭环、真实端子核验、端子接线、BLEND/GLB/PNG 导出、本机 Three.js/Playwright 30 FPS 测试。
- **DSH 真实原版后端**：`/act` 执行 bpy、`/frame.png` 和 `/view` 实时图像、`/cmd` addon 命令、`/plan` 全目录、`/loop` 内环优化、`/perf`、`/opt`、`/headless`、`/worker`、`/job`、`/txn`、`/preset`、`/lease`、`/release`、`/who`、`/doctor`、支持部分 `/host/*` 交互 API。
- **源代码固定**：`82c588d464005410e12e0a96c6c4e146a6e6f557`（2026-10-18 commit，项目当时 package.json 版本 2.1.0）。保持原 BSD-3-Clause LICENSE。
- **严格单 MCP**：DSH Node 进程是本机 HTTP 执行引擎，不是第二个 MCP；Codex 只看到 `industrial_blender`。其它非 Blender MCP（GitHub、Google Drive）可继续使用。

## 安装入口

请**从头到尾阅读 [`CODEX_安装整合与验收.md`](./CODEX_安装整合与验收.md)**，里面有完整适用于 Codex 的可复制指令、路径、安装步骤、安全检查、回退策略与验收标准。先确保装了 Git for Windows、Node.js >=20、Python/uv、Blender 4.x/5.x，并能访问 GitHub。

```powershell
cd "D:\你的解压目录\Blender_V3_Full_DSH_Single_MCP_20261019"
.\INSTALL_WINDOWS.ps1 -Workspace "D:\你的工业实训项目"
.\START_DSH_BACKEND.ps1  # 另开终端运行，保持窗口
```

安装时下载 `vendor/dsh-blender-plugin` 全量源码；需要在 Blender GUI 中启用这份来源的 `addon/dsh_blender_bridge.py`，并在侧边栏 Connect，默认本机端口 9876。之后：

```powershell
python .\tools\verify_install.py
```

返回 `doctor.kind=ok`、截图成功和 catalog 成功才算联通。只有真正完成几何、端子、导出和网页性能测试后才能将之前四个待验收项改成 PASS。

## 注意事项

- `/act`、`/headless` 等能运行任意本地 Python。**只在可信项目使用，不要把公网 URL 当作 DSH 后端，执行前备份**。本适配器仅访问 `http://127.0.0.1:9877`。
- 安装器执行前会从 GitHub 下载上游完整源代码。若无法访问 GitHub，则**失败并保留旧 Codex 配置**；不要以“安装完成”掩盖下载失败。
- 不盲目启用旧版 GUI MCP 或旧 addon：它们可能同时占用 Blender 9876 端口。安装之前退出旧 addon 的监听或择一启用；全部可备份回退。
- 几何体积、截图和脚本执行成功都**不代表**真实工业尺寸正确；电气安全由独立接线规则校验。

来源：<https://github.com/sixtysevenlf/dsh-blender-plugin> · 许可证 BSD-3-Clause。
