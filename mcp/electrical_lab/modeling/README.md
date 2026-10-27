# 工业自动化与机器人虚拟实训开发工具包 · v3.0

**下载后用于 Windows / Codex 的 Skill + MCP，同时保留独立离线 HTML 演示。** 本工具包自己编写的 Python 脚本仅使用标准库；除浏览器与 Python 外不依赖云服务。

## 本版交付内容

1. `skills/electrical-training/SKILL.md` 和 `skills/industrial-asset-modeling/SKILL.md` — 两个可复用的 AI 开发规范：端子来源、型号边界、逻辑状态机、安全、回归测试。
2. `mcp_server.py` — 本地 stdio MCP；**16 个工具**（v1 5 个 + 工业目录/规范/信号映射/HMI变量 6 个）。
3. `assets/industrial_device_catalog.json` — **46 条工业设备家族索引**，10 类；只有荧光灯为 `teaching_logic_simulation`，其余是 `catalog_only`。
4. `industrial_catalog.py` — 查询、实验草案、声明信号方向/类型/电压校验、HMI 变量校验。
5. `examples/工业元件教学目录_离线版.html` — 不需安装，直接打开、搜索、分类、查看元件收录情况。
6. `examples/荧光灯_自由接线_教学版.html` — 唯一已经有完整可运行接线与灯丝预热故障教学状态机的实验。
7. `扩展路线与验证要求.md` — 分阶段增加接触器、电机、PLC、HMI、气动、机器人等。
8. `tests/` — 自动测试；原始荧光灯课程参考文件也保留。

**注意：这个是用于帮 AI 可靠开发的工具包，不是已经能真实仿真 ABB/KUKA 机器人、S7-1500 或汇川 PLC 的工业软件。** 元件收录 ≠ 端子规格已核实 ≠ 可交互仿真 ≠ 厂家级验证。

## 在电脑上安装（Windows 10/11）

- 下载 ZIP 并解压到一个固定目录，例如 `D:\AI_Tools\industrial_training_kit_v2`。不要直接在 ZIP 里面运行。
- 直接双击 `examples\工业元件教学目录_离线版.html` 看到设备分类；双击 `examples\荧光灯_自由接线_教学版.html` 进入能实际接线的课件。
- 已装 Codex 的话，用 PowerShell 在解压目录执行 `powershell -ExecutionPolicy Bypass -File .\install_skill.ps1`，然后重新启动 Codex。也可手动复制 `skills\electrical-training` 到 `%USERPROFILE%\.codex\skills\electrical-training`。
- 安装 Python 3.10 或更高版本后，编辑 `%USERPROFILE%\.codex\config.toml`，加入以下内容，**按实际目录修改绝对路径**：

```toml
[mcp_servers.electrical_lab]
command = "py"
args = ["-3", "D:\\AI_Tools\\industrial_training_kit_v2\\mcp_server.py"]
```

- 在工具包根目录执行 `py -3 -m unittest discover -s tests -v` 验证；使用 `codex mcp list` 检查 MCP 是否被加载。
- 对 Codex 说：`使用 electrical-training Skill，通过 electrical_lab MCP 检索西门子 S7-1200 和昆仑通态 HMI 设备，先做一个端子和信号映射的教学规范，不要编造厂家端子编号；生成可离线打开的 HTML 原型，并运行测试。`

## 16 个 MCP 工具

**荧光灯（可运行教学逻辑）**：`list_components`, `get_fluorescent_lab`, `validate_wiring`, `simulate_fluorescent`, `list_faults`

**多设备扩展（当前为元件查询、规格草案、抽象校验，不执行设备仿真）**：`list_device_categories`, `search_industrial_devices`, `get_industrial_device`, `scaffold_industrial_lab`, `validate_signal_links`, `validate_hmi_tags`

## 参考及安全

官方资料索引见 `扩展路线与验证要求.md`。设备库不包含未经授权的厂商 CAD 图、手册复制件、厂家型号端子表或协议密钥。严禁依据当前抽象设备模型接入实际市电、伺服或工业机器人；现场接线/机器人运行应使用具体硬件手册、隔离与 E-stop 保护、安全评估。

## 云端备份说明

ZIP 可以放在 Google Drive，也可以保存 ChatGPT 文件资料库。云存储仅保存文件，不会使远程 ChatGPT 自动运行本地 MCP。需要使用时在 Windows 安装 Skill 和 MCP 并由本地 Codex 加载。


## v3 新增：素材与非标设备工作流（5 个 MCP 工具）

- `list_material_sources`：厂家/CAD/非标素材检索源目录，标注授权和转载限制；**不下载第三方资产**。
- `get_asset_intake_checklist`：给定设备类型和用途，列照片、铭牌、尺寸、端子、动作及授权材料清单。
- `new_nonstandard_asset`：新建私有非标设备 JSON 档案，**不给不存在的厂家参数“补脑”**。
- `validate_asset_manifest`：检查设备档案、端子核验和授权声明是否一致，并给出示意图/接线/仿真/公开权限状态。
- `render_nonstandard_svg`：根据声明的宽高和端子位置生成示意 SVG。**不是逆向照片，更不是 CAD 精准模型**。

目录中的 `nonstandard_assets.py` 可在本地直接使用（标准库、无依赖）。

```powershell
py -3 nonstandard_assets.py validate .\materials\非标设备建档_样例.json
py -3 nonstandard_assets.py svg .\materials\非标设备建档_样例.json .\materials\示意模型.svg
py -3 -m unittest discover -s tests -v
```

资料规范：`skills/electrical-training/references/素材与非标设备建模工作流.md`。示例档案：`materials/非标设备建档_样例.json`。来源目录：`assets/material_sources.json`。

### 关键限制
当前新增的是 **素材工作流与教学示意 SVG 生成能力**，不是自动从照片/STEP 逆向生成参数正确的可运行设备模型。真实端子、电源与气路必须逐型号核查；非标机器安全互锁须由人工确认。云端保存 ZIP 不代表 ChatGPT 自动安装了本地 MCP。


## v3 两个 Skill 安装说明
`install_skill.ps1` 安装 `electrical-training` 和 `industrial-asset-modeling` 两个 Skill；目录已存在时跳过。`upgrade_skill.ps1` 将两个现有 Skill 先备份再安装 v3，**不会修改你已有的 Codex config.toml**。

对于本地 MCP，请在 `config.toml` 更新成实际解压后的 v3 `mcp_server.py` 绝对路径；Windows 推荐 Python 3.10+。MCP 不能被远程聊天窗口自动加载，必须在支持 stdio MCP 的本地客户端启动。

请将从厂家下载的商业 CAD、校内保密设备照片放在你自己的受控文件夹，不要直接塞到公开工具包 ZIP；本发布包不包含这些第三方素材。
