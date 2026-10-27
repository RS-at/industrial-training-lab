# 关于 DSH 源代码的明确说明

- ZIP 不包含完整上游 GitHub 文件，这是有意设计的：`BOOTSTRAP_DSH.ps1` 会在**用户安装时**获取固定版本的完整源代码和 Blender addon。
- 完整 DSH 后端不依赖其 DSH 主程序运行，使用原有 Node HTTP 执行引擎。
- 适配器提供一个 MCP 入口，动态覆盖 `/plan` 目录操作和 HTTP 路由，不是重写原版所有算法。
- DSH 原生的宿主面板 UI 没有移植；不应说成整个 DSH 产品被迁移。
- 需要 GitHub 访问与本机 Blender GUI、Node 20+。未通过真机连接和 GPU 负载验收前状态为待验证。
