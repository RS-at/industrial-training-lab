---
name: electrical-training
description: "Create or review offline HTML industrial electrical training laboratories with a manufacturer-aware catalog and MCP checks, covering basic wiring, fluorescent starter/ballast, Siemens S7-1200/S7-1500 PLCs, Inovance PLCs, MCGS HMI, ABB and KUKA robots, servo, stepper, motors, relay/MCB, sensors and pneumatic valves. Use for 电工实训、工业自动化、机器人、PLC、触摸屏、气动、接线仿真、HTML 实训课件."
---

迁移到 Claude 的副本。先读取 [Claude 适配说明](CLAUDE-ADAPTER.md)，再执行以下工作流。

# 工业自动化与机器人实训开发 Skill v2

## 目标和边界

为职业院校教师生成 **真实端子逻辑 + 可拖动实物外观 + 可手工接线 + 检查 + 启停 + 故障定位** 的离线 HTML 课件。

本工具包内置的已实现实训为 **传统单管荧光灯：电感镇流器 + 辉光启辉器 + 双灯丝灯管**。未实现真实的220V交流瞬态仿真，也**不能**用于指导未经审核的市电带电接线；工程实物使用前必须核对设备铭牌、厂家端子资料和学校安全规程。不能将本模块套用为电子镇流器线路。

## 使用现成工具

1. 先用 MCP 的 `list_components` 和 `get_fluorescent_lab` 获取确定的端子、元件关系和示范连接。
2. 新增/修改线路时，用 `validate_wiring` 对每套标准/错误案例作断言，缺接、多接、重复导线和电源 L-N 直通应失败。**不得仅凭图像判断接线正确。**
3. 用 `simulate_fluorescent` 验证正常和每个故障状态的时间顺序，并在 HTML 中同步展现灯丝、启辉器和灯管状态。
4. 保留离线 HTML 打开、元件拖动、导线连接/删除、通电检查、断电/复位、故障注入及课堂可投屏的样式。`examples/荧光灯_自由接线_教学版.html` 是优先参考；`旧版v3参考.html` 保存原先的动画视觉参考。
5. 每个新项目提供可独立运行 HTML、元件表、端子定义、标准接线、3 个以上错误/故障案例、测试结果和教学安全提示。

## 强制校验

- **元件属性**：检查元件名称、端子编号、常态接点状态、所需触点联动、工作电压及控制方式；缺厂家资料时须标注“示意端子/待实物核对”，绝不编造精确型号参数。
- **接线语义**：开关应作用于相线，镇流器串接，启辉器跨接两组灯丝的非供电端以形成启动预热回路；任何直接 L-N 短接必须标危险并阻止演示通电。
- **动作**：启辉器辉光放电→双金属片闭合→灯丝预热→触点断开→电感感生启辉电压→灯管放电点亮→启辉器保持断开。时间仅用于演示，不是设备实测参数。
- **故障**：启辉器无法闭合、触点粘连、镇流器断路、任一灯丝断路、灯管老化均显示可区分的行为，不可统一简单弹窗。
- **交互**：断电之后才能修改线路；自由拖动不应破坏已连接导线；清空、重置和故障切换不得遗留待执行计时器；手机触摸和 Windows 鼠标均应支持。
- **测试**：运行 `python -m unittest discover -s tests -v`；交付前人工在 Edge/Chrome 打开 HTML，分别试标准接线、缺线、额外导线、短路、正常点亮和两种启辉器故障。

## 扩展到其他实训

对交流接触器自锁/互锁、电动机正反转、星三角起动、热继电器等**先新增独立实验模型及测试**；未完成独立模型前，不能声称 MCP 能验证这些回路。若用户需要真实频域/瞬态仿真，应额外接入合适的 SPICE/机电仿真引擎，并重新验证模型边界。

## 参考资料

- Signify / Philips Electromagnetic Lamp Technical Application Guide (starter preheat sequence): https://www.docs.lighting.philips.com/en_gb/oem/download/Technical_Application_Guide_Fluorescent_Gear.pdf
- Signify 安全启辉器型号资料：https://www.lighting.philips.com/prof/conventional-lamps-and-tubes/fluorescent-lamps-and-starters/starters-for-fluorescent-lamps/safety-starters/LP_CF_STARTS_EU/family

## 提醒

MCP 是开发时供 AI 调用的工具，不会被塞进离线 HTML 文件。学生播放 HTML 不需要安装 Python、MCP、插件或联网。


## v2 工业设备扩展原则（必读）

- **已完成**：传统荧光灯实验自由接线与教学状态机，8 项旧测试 + 8 项扩展测试通过。
- **仅有条目（不可冒充已仿真）**：ABB、KUKA 工业机器人；西门子 S7-1200/1500；汇川 H3U/H5U/AM600；昆仑通态 MCGS HMI；伺服、步进、变频器、交流电机；接触器、继电器、空开、剩余电流保护装置；电磁阀、气缸、FRL、节流阀；传感器与网络。
- 通过 `list_device_categories` → `search_industrial_devices` → `get_industrial_device` 选择元件族。不能把“模型族”当作厂家现货具体 SKU，更不能捏造端子号码、额定电压、通讯寄存器或机器人运动参数。
- 用 `scaffold_industrial_lab` 建立开发计划，清楚写出当前仅是规范，不是可运行仿真。
- 使用 `validate_signal_links` 验证**抽象逻辑信号流**。只有用户自行提供经过厂家文件确认的端口定义，才能验证方向、信号类型、声明电压。该工具不能验证接线安全、接地、供电分组、安全回路或实时总线。
- 使用 `validate_hmi_tags` 检查用户提供的 HMI 变量与 PLC 符号声明。不运行真实通讯协议，不替代昆仑通态组态软件或西门子 TIA Portal。
- 对 ABB/KUKA 等机器人，若涉及实际轨迹、可达性、碰撞、虚拟控制器，需要厂家仿真器（如 ABB RobotStudio、KUKA 仿真软件）；网页可先做空间布局和 I/O 时序教学模型，但不得称为已验证离线编程。
- 新增器件至少落实以下 5 件事：具体型号及权威手册；带来源的端子表；电/气/逻辑状态机；故障与错误输入测试；独立 HTML 示例。未完成前 `implementation_status` 仍为 `catalog_only`。
- 禁止直接向真实 PLC/机器人/伺服发送写入/启动/使能/动作命令；接入实物需要另行设计人工确认、隔离、权限与风险评估。

### 新项目优先开发顺序
1. 三相电机点动/自锁（通用接触器与热继电器）
2. 正反转互锁与电机保护
3. PLC（S7-1200、汇川）虚拟 DI/DO 与教学扫描周期
4. 昆仑通态 HMI 变量映射、画面按钮与报警
5. 5/2 阀、双作用气缸及磁性开关
6. 伺服/步进基础脉冲与限位
7. ABB / KUKA 机器人 I/O 工位联动，运动学使用专用引擎和机械模型

### 官方资料检索入口
- 西门子 S7-1200/1500 编程指南：https://www.ad.siemens.com.cn/download/documentdetail_12472.html
- ABB RobotStudio：https://www.abb.com/global/en/areas/robotics/products/software/robotstudio-suite/robotstudio-desktop
- KUKA iiQWorks.Sim：https://www.kuka.com/en-gb/products/robotics-system/software/simulation-planning-optimization/iiqworks-sim-robot-simulation-software

详见 `扩展路线与验证要求.md` 和 `assets/industrial_device_catalog.json`。


## v3 素材与非标建模
请联用 `industrial-assets` Skill 与 MCP `new_asset_spec`、`validate_asset_spec`、`plan_render_pipeline`。CPU用于控制状态计算，GPU按需用于3D渲染，原有示例与46类目录不等于厂家级模型。


## Local installation (2026-10-14)

All tool names in this skill are provided by the `electrical_lab` MCP server.
Toolkit root (scripts, examples, tests and root-level documentation): `<repo>/mcp/electrical_lab/current`. Resolve toolkit references against this directory; skill references/ files remain beside this SKILL.md.
Python: `python (3.10+)`; set PYTHONUTF8=1 when testing on Windows.
