---
name: electrical-lab-3d
description: "为日光灯/磁镇流器/启辉器/电工实训板构建 Blender 与 Three.js 的实物级三维网页实训。适用于创建真实元件模型、自由接线端子与导线、通电状态机、故障注入、教学评分和 Codex 自动验收；先检查电气逻辑，再实现可视化。"
---

迁移到 Claude 的副本。先读取 [Claude 适配说明](CLAUDE-ADAPTER.md)，再执行以下工作流。

# 3D Electrical Lab (荧光灯实训)

使用场景：用户要求“搭建/升级/修复日光灯三维接线仿真”、“利用 Blender 建模”“Three.js 模型交互”“启辉器预热与闪烁动画”“教师故障考核”。

## 每次执行都要
1. 读取项目 `AGENTS.md`、`references/电气规则与故障模型.md`、`references/验收标准.md`。
2. 检查当前环境与已有模型，不猜测已有安装。优先复用经过用户许可的资产；不要把动画当作电路计算。
3. 确认 3D 物体建模与布线引擎分离：`terminalId` 是逻辑 ID，不用 mesh index / 颜色来推断端子。
4. 优先使用本包 `src/netlist.mjs` + Node tests 验证连线；Vite / TS 实施时提取可测试模块并新增反例。
5. 每个模型（电感镇流器、启辉器、灯管、灯座、开关、端子、网孔板）建立真实尺寸近似；端子需可拾取并提供吸附点。导线以贝塞尔曲线 / TubeGeometry 或带路径点的 Cable 表示，随元件移动实时更新。
6. 禁止在线 CDN 运行时依赖；模型素材与字体本地封装。若性能低，先检查贴图分辨率与 draw calls。
7. 预热、闪烁应由状态机驱动，包括“启动失败”；若接线错误，显示具体错误节点，不进入点亮状态。
8. 学生端不能需要 Blender；有 Blender 时通过 bpy 生成/优化 GLB；无 Blender 时采用 Three.js 原生程序建模并注明差异。
9. 如果使用第三方 MCP，请先审计权限和遥测条款，备份 `config.toml`，不得无同意自动下载未知模型或运行外部代码。

## 分阶段产出
- P0 真实三维板、移动元件、旋转缩放、端子可选
- P1 自由接线、拆线、重做、六条正确连接、错误拓扑判定
- P2 启辉器/灯丝/镇流器联动的四阶段启动和故障注入
- P3 教师模式、任务清单与评分、离线包、性能与界面优化

参考：项目根目录 `tasks/CODEX_TASK.md`。任何实际验证失败要保留错误报告，不要声称全部完成。


## Local installation

Project resources: `<electrical-lab-3d-starter project>`. Resolve project AGENTS.md, tasks/ and references/ against this root. Blender: `<BLENDER_EXE (Blender 4.5)>`. The Blender MCP server is installed as `blender`; preserve the existing electrical_lab server.

## 用户的模型选材偏好（2026-10-15）

处理3D/CAD模型需求时，优先复用已下载模型与用户云盘“现成3D模型素材库”；缺少合适模型时，先联网检索并下载许可合适的现成模型，确认无合适资源或必须补充特殊结构时再自建。不要重复建已有模型。
本地索引：<local asset library>/industrial-models/index.json。
云盘目录：自己的云盘素材库（如有）。
保留原文件、来源及许可证；STL/STEP外形不等于已核验电气端子或真实设备动作。KUKA碰撞分件不等于完整机器人运动学模型。
