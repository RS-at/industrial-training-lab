---
name: industrial-asset-modeling
description: 处理电工及工业自动化虚拟实训设备素材与非标机台建模，适用于用户照片、尺寸、端子、CAD、SVG、STEP、气路、PLC/HMI、机器人设备的素材来源核查、建档、授权确认、轻量教学示意图生成和后续仿真需求设计。
---

# 工业设备素材与非标建模 Skill · v3

## 应用场景
老师提供一台非标教学装置的照片、铭牌/尺寸/手册，要求制作可复用的 2D/2.5D/3D 元件素材、接线课堂演示和课程素材包；或教师只需工业元件厂商资料索引和来源许可证审查。

## 操作步骤
1. 使用 MCP `list_material_sources` 获取材料检索入口，始终按厂商型号与资料版本核实，**不得未经许可抓取、复制、修改和公开散发商业 CAD/图纸**。
2. 对于非标设备，先调用 `get_asset_intake_checklist`，根据照片、尺寸、铭牌、端子特写、原理图、时序和权属情况收集证据。无证据部分统一为 UNKNOWN。
3. 调用 `new_nonstandard_asset` 产生私有 JSON 模板；填写 `source_files`、`evidence`、`rights`、`verification` 和每个端子 `source_ref`。绝不能根据外观猜真实电压、端子号、气路含义或 PLC 接线。
4. 调用 `validate_asset_manifest` 检查结构与资料是否足够：只有示意外观准备好时，**不可宣称已准备好接线与动作仿真**。状态的真实性仍需要教师核对。
5. 使用 `render_nonstandard_svg` 返回简洁 SVG 外壳与示意端子，可进一步美化为独立 2D 课件；涉及复杂机构才另行使用 Blender/CAD 对经许可的结构进行建模。
6. 进入动作仿真前，必须结合 `electrical-training` Skill 的信号映射和实训测试流程，先创建独立状态机与故障单元测试，验证后才能标注为已模拟。
7. 成果应按设备建立独立包（JSON、SVG、证据文件索引、测试、权限说明、版本）。用户要求上云时，明确目标云盘与分享状态；涉密校内图纸默认私有。

## 具体命令
```powershell
py -3 nonstandard_assets.py validate .\materials\非标设备建档_样例.json
py -3 nonstandard_assets.py svg .\materials\非标设备建档_样例.json .\materials\非标设备示意图.svg
```

另需阅读 `references/素材与非标设备建模工作流.md`。用于实际带电设备、伺服、PLC、机器人前必须额外由教师与安全人员核对厂家资料、接地、急停、危险能量隔离和机械安全。

## 不能做到的事
当前 MCP 没有自动联网搜图/爬站、没有分析照片自动生成精确尺寸、没有从 STEP 自动逆向运动机构、没有商业软件破解或素材提取能力；它负责可审计的素材建档和示意图生成。
