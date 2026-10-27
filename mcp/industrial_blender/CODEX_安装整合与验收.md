# Codex Blender integration — upgraded 2026-10-20

Official upstream v2.5.0, commit `f044a019bbb97513443b24cc5ebcad111a002628`. Addon 1.10 / protocol 11.
Source: https://github.com/sixtysevenlf/dsh-blender-plugin/tree/v2.5.0

Package: `<repo>/mcp/industrial_blender`
MCP launcher: `<repo>/mcp/industrial_blender/launch_mcp.py`
Blender: `<BLENDER_EXE (Blender 4.5)>`
Installed bridge: `<Blender user scripts>/addons/dsh_blender_bridge.py`
Backend: `vendor/dsh-blender-plugin/runtime/server.mjs`, loopback 9877; addon loopback 9876.

Only `industrial_blender` is registered/enabled for Blender. Original DSH tools are mapped through this MCP; the DSH application is not installed by this upgrade. Its selection-to-draft client integration is not a Codex feature.

Two complementary skills: `industrial-blender-v3` for local host/tools, `blender-modeling` for modeling workflow and original upstream references. Original upstream workflow and MIT notices are preserved. Runtime/addon retain upstream BSD-3-Clause license.

Verify with `.venv/Scripts/python.exe tools/verify_install.py`: pinned SHA, health, doctor.kind=ok, non-stale provenance, PNG and catalog. Also inspect the image, query addon activity/collections/selection, and collect a background job. These are smoke checks, not verification of every catalog operation.

Addon 1.10 supports native object/edit-mode selection, collections, activity and a Blender N-panel AI pause/resume button. Never bypass user pause. Codex can read activity and selection through addon commands; native sending to a DSH draft requires the DSH host.

Backups: `<local backups>/upgrade-20261020-v2.5.0`. Restore the old skill and bridge, checkout old upstream commit from the archive/lock, restore adapter files, then restart only this backend and reload the bridge. Save the current .blend first; preserve other addons/preferences and unrelated MCP settings.

Skill changes are available in newly loaded sessions. MCP Python code loads on server start; reconnect/restart the MCP to load changes. Backend and addon can be refreshed separately without closing the current model.
