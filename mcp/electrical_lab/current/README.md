# 工业自动化/机器人实训 Skill + MCP 资产工具包 v3.0

本压缩包包含之前 v2 的 **11 个 MCP 工具、46类设备目录和荧光灯离线HTML**，新增 `industrial-assets` Skill 与 6 个资产工具，共17个 MCP 工具。保持 Python 3.10+ 标准库运行。

## 新增的内容
- `skills/industrial-assets/SKILL.md`：标准/非标设备素材采集、许可、建模与校验规范。
- `asset_tools.py`：非标设备 JSON 清单、端子/尺寸/版权核验、2D SVG 草模、CPU/GPU方案和简单运动学预览。
- `mcp_server.py`：加入 `list_asset_sources`、`new_asset_spec`、`validate_asset_spec`、`plan_render_pipeline`、`generate_generic_svg`、`simulate_motion_step`。
- `assets/custom_pneumatic_fixture_v3.json`：**非标教学示例草案**，尺寸和端子没有实物核实，不可直接实训接线。
- `examples/自制气动设备_教学外观占位.svg`：原创通用占位图，**不代表实物精度**。
- `tests/test_assets.py`：新增自动测试。

## Windows / Codex 安装
1. 解压 ZIP 到固定路径，如 `D:\AI_Tools\industrial_training_kit_v3`，不要在压缩包内运行。
2. `py -3 -m unittest discover -s tests -v` 测试；无需第三方pip依赖。
3. 使用 PowerShell 运行 `powershell -ExecutionPolicy Bypass -File .\install_skill.ps1`；如旧版已安装，先备份原Skill再使用 `upgrade_skill.ps1`。安装两个独立Skill：`electrical-training` 和 `industrial-assets`。
4. 在 `%USERPROFILE%\.codex\config.toml` 设置，**修改为你本机真实路径**：

```toml
[mcp_servers.electrical_lab]
command = "py"
args = ["-3", "D:\\AI_Tools\\industrial_training_kit_v3\\mcp_server.py"]
```

5. 重启 Codex 后执行 `codex mcp list`。让 Codex 使用 industrial-assets Skill 与 electrical_lab MCP 生成非标设备资产说明书；先用 `new_asset_spec` 建模，再用 `validate_asset_spec` 校验，必要时用 `generate_generic_svg` 生成带明显警告的占位图。

## CPU/GPU/轻量化
- 普通接线教学：浏览器SVG，无独立显卡要求。
- 电机与气缸：CPU计算运动状态，Canvas/SVG显示；简单运动无需GPU物理引擎。
- 机器人/三维非标设备：需要浏览器WebGL与GPU进行模型和贴图渲染（集成GPU可能足够），CPU进行常规控制逻辑/运动学计算；更复杂场景可使用专业物理引擎。
- 运动计算可固定时间步 20ms，渲染独立30/60fps，都是设计参考值，非设备性能承诺。

## 不能声称已实现
本版本没有深度视觉识别实物端子、专业三维CAD重建、真实机械动力学、工控安全认证或直接通信/写入真实PLC/机器人，也不负责批量爬取、破解或再分发商业贴图/CAD库。

素材应优先用用户原创、可明确再分发的文件；第三方来源仅作核对，许可证需逐项审核。`README_v2_存档.md` 保留旧版详情。
