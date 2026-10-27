---
name: industrial-blender-v3
description: Operate the single local Blender MCP with official DSH backend, native modeling, visual iteration, asset reuse, and task-specific industrial validation.
---

# Blender integration — DSH 2.5.0

Use only the registered `industrial_blender` MCP. Node HTTP 9877 and addon TCP 9876 are internal services on loopback, not additional MCPs. Read `AGENTS.md` and `CODEX_安装整合与验收.md` in this directory for deployment details. For modeling stages and recipes, read companion `blender-modeling/SKILL.md`.

## Before editing

- Prefer assets in `<local asset library>/industrial-models/index.json` and the user's own cloud model library, if any, then search licensed models before building. Preserve sources and licenses.
- Inspect the approved reference and existing scene. Save a separate .blend checkpoint before mutations. Never overwrite the only original.
- Call `blender_status` and `blender_dsh_status`; require doctor.kind=ok and non-stale provenance. Discover `blender_dsh_commands` and relevant `blender_dsh_catalog` entries rather than guessing names.

## Modeling and feedback

- Follow reference/specification → scene preparation → blockout → coarse refinement → modifiers → cleanup → handoff. For characters: silhouette/proportions first, then face, hair, clothing and materials.
- Honor this user's native Blender/plugin preference. Do not build whole characters with Python. Native edit/sculpt/modifier operations and installed plugins are preferred; scripts may diagnose, install, audit and export.
- Make small scoped edits. After each step use `blender_dsh_view_image` or `blender_preview` plus `blender_image`; actually inspect front/side/three-quarter images and compare to the reference. A PNG filename is not visual evidence.
- `get_selection`, `get_activity_state` and `get_collections` are available via discovered addon commands; include edit-mode sub-selection when present. Pause state is controlled by the user in Blender: never bypass or resume AI pause through code.
- `blender_dsh_plan` exposes the runtime catalog dynamically; an available operation is not a tested operation. Use `/job` for long tasks and collect final stdout/stderr/artifacts; do not resubmit merely because a client timed out. File-level txn snapshots are needed for topology rollback, and do not replace saved backups.
- For Blender 4.5 background jobs use valid engine names or `engine="keep"`; `scriptFile` and `factoryStartup` are camelCase job keys. Discover current schemas before calling.

## Completion depends on the requested artifact

- All: known source version, connected bridge, inspected images, requested files that actually exist, and clear remaining visual defects. Do not claim fidelity from polygon counts or file size.
- Character/static model: shape, likeness, topology and materials; no unsolicited animation, electrical audit or FPS requirement.
- Electrical: real tagged terminal objects, measured reference and electrical logic checks; visual topology alone is insufficient.
- Interactive web asset: valid GLB, actual browser loading and target-machine hardware FPS evidence when required. Offline rendering is not a browser FPS test.

DSH host draft insertion and its client UI are not provided by Codex. Read selection directly by MCP. Preserve unrelated MCPs and never forcefully steal leases.
