---
name: electrical-training
description: |
  Create or review offline HTML industrial electrical training laboratories with a manufacturer-aware catalog and MCP checks, covering basic wiring, fluorescent starter/ballast, Siemens S7-1200/S7-1500 PLCs, Inovance PLCs, MCGS HMI, ABB and KUKA robots, servo, stepper, motors, relay/MCB, sensors and pneumatic valves. Use for 电工实训、工业自动化、机器人、PLC、触摸屏、气动、接线仿真、HTML 实训课件. 
---

# 工业自动化与机器人实训开发 Skill v3

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


## v3 素材库与非标设备专项流程

当任务涉及素材、厂家 CAD、SVG、照片、教学实物图、非标定制装置时，必须先阅读 `references/素材与非标设备建模工作流.md`。

1. 先调用 `list_material_sources` 找厂家与 CAD 数据检索入口；**不得自动爬取网站、登录、下载受限制内容或把付费/商业素材加入可分发资源包**。
2. 先问用户是否拥有设备照片/测绘资料；如有，调用 `get_asset_intake_checklist` 返回最小资料清单。用户图片来源于学校/企业时默认私有，敏感图纸需授权后才能公开。
3. 为每台非标设备调用 `new_nonstandard_asset` 建立独立 JSON 档案。**禁止凭照片编造 220/380V 端子、PLC 端口、机器人安全通道或阀芯机能**。
4. 填入来源和逐端子核验资料后，用 `validate_asset_manifest` 检查证据、状态和许可；只得到 `illustrative_svg=True` 不能当成可运行工业仿真。
5. 使用 `render_nonstandard_svg` 制作轻量 2D 示意器件。输出 SVG 的端子未核实则带警告，不得自动转为工程使用状态。
6. 复杂 3D/机构运动按需由 CAD/Blender 等工具处理；本包目前不会自行解读 STEP/DXF/视频/照片并自动生成精确 3D 或行为模型。
7. 端子准备充分且经过教师核查后，才继续编写场景级状态机、接线校验、故障注入、测试用例。实际设备远程操作另行实现有门禁的连接层。
8. 每次生成的设备元件打包为独立目录并记录模型版本、来源 URL、文档型号/版本、许可/共享范围、工程验证标记；不把商业 CAD/SVG 以未经授权的方式合并为公开库。

**本包 v3 能做**：素材来源索引、建档清单、非标 JSON 模板、资料一致性检查、示意 SVG 生成、旧版 11 个 MCP 工具。**本包还不能做**：自动照片尺寸量测、受保护 CAD 逆向、真实模拟 46 类工业设备、PLC 实机连接、认证级电气安全判断。
