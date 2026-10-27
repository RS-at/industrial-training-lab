---
name: industrial-assets
description: 工业实训素材及非标设备建模规范；从照片、尺寸、CAD、接线图和动作视频创建SVG/2.5D/3D资源的可追溯规格，核验真实端子、版权和CPU/GPU渲染策略。Use for industrial automation assets, custom machines, electrical training visual models, motion and rendering.
---

# 工业实训素材与非标设备 Skill v3

## 任务
为电工、PLC、昆仑通态 HMI、工业机器人、伺服、步进、气动以及学校非标设备创建**按需加载、离线优先**的教学用资产。必须区分外观示意、厂家核验端子、教学动作与真实工业设备控制。

## 开发步骤
1. **采集证据**：先询问具体设备型号；从用户自有照片（正侧背+端子近景）、铭牌、实际尺寸、说明书、原理图、PLC I/O表和动作视频获取资料。缺资料不编造型号、端子、额定电压、接线图或安全回路。
2. **核对版权**：优先用户原创照片与自行绘制的 SVG。TraceParts、3Dfindit、EPLAN、MISUMI、厂家CAD仅作为参考，任何下载/再分发都必须核查具体许可；商业软件逆向只讨论合法接口和公开行为，**不提取受保护素材或绕过授权**。
3. **创建资产清单**：MCP `new_asset_spec` 返回 v3 JSON；填入真实资料与确认状态后，调用 `validate_asset_spec`。未核验端子标注 `reference_verified:false`；教学状态不能自动升级为 `manufacturer_reviewed`。
4. **选择表现方式**：使用 `plan_render_pipeline` 按教学电脑性能与课程需求选择 `2d_svg`、`2_5d_canvas`、`3d_webgl`。电气端子接线优先2D清晰和准确；机构空间姿态、机器人再引入GLB及WebGL。纹理尽量WebP（3D可选KTX2）；GLB按课程独立打包。
5. **生成示意外观**：必要时用 `generate_generic_svg` 创建有“示意外观”标记的占位SVG；用户提供照片/模型后再按实际外观重绘或合法导入，不得将占位图称为真实设备。
6. **建立动作**：运动模型独立于画面。`simulate_motion_step` 仅生成直线/旋转的运动学预览，不计算电流、扭矩、空气热力学、力学碰撞或安全。复杂机器人使用专业运动学与碰撞引擎验证。
7. **独立验证**：端子依据手册；状态机独立于UI；异常与限位测试、断线/短路逻辑，错误连接不写入真实设备。生成课件应附来源、许可证说明、核验状态、测试结果。

## CPU/GPU 建模原则
- CPU（浏览器JavaScript、WebAssembly或Python）负责教学 PLC扫描、I/O状态、路径/位置、网络连通性、简单碰撞；GPU主要负责Canvas/WebGL图形与贴图渲染。某些物理计算可由GPU加速，但非必需。
- 将模型更新频率（如20ms）和渲染帧率（30/60fps）解耦；慢电脑优先减少渲染帧率和细节，**不降低关键逻辑正确性**。
- 演示模型不是真实 PLC扫描时序、伺服闭环或机器人控制器仿真。硬件联动必须独立进行驱动器/急停/联锁/隔离与现场审核。
- 学生运行HTML不需安装本地 MCP，也不必有独立显卡。高级3D需要浏览器WebGL支持，复杂模型才可能要求较强GPU。

## 检验
运行 `python -m unittest discover -s tests -v` 并人工检查浏览器SVG/课件。素材包装必须包含 `spec.json`、原创图/模型、可用的许可说明、设备验证记录、测试样例，严禁把商业资源整库复制进包。

## 未覆盖
本版**未实现**照片自动三维重建、STEP到GLB转换、机器人逆运动学、物理级气动/电机求解、真实PLC/MCGS协议驱动或商业素材库自动下载。这些均需未来接入经合法验证的工具。
