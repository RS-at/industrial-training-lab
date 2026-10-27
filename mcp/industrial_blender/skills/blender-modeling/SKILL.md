---
name: blender-modeling
description: Reference-driven Blender modeling, staged blockout and refinement, topology and visual checks. Use for creating or editing characters, objects and assemblies in Blender.
---

# Blender modeling on this machine

Read the companion `industrial-blender-v3` skill for the installed MCP and host mapping. Use the original workflow in [UPSTREAM_WORKFLOW.md](UPSTREAM_WORKFLOW.md) by relevant section, and its `references/` recipes as needed. Original text, MIT LICENSE and NOTICE are preserved from official DSH v2.5.0.

User instructions override upstream examples: prefer existing licensed assets; for this user's character work use native Blender mesh/sculpt/modifier tools and installed plugins. Do not generate the whole character with Python. Scripts remain appropriate for diagnostics, installation, export and non-geometric checks. Multi-agent examples are optional, not authorization to spawn agents.

1. Inspect the approved reference. Record visible silhouette, proportions, facial features, hair masses, clothing and colors. Missing views and dimensions stay unknown; image pixels do not imply physical units.
2. Inspect the existing scene and local/cloud model library before building. Save an independent copy before changes.
3. Work through silhouette/blockout → head and face → hair → clothing/accessories → materials → cleanup. Finish one stage before spending effort on small details.
4. For each small edit, capture and actually inspect front, side and three-quarter views at consistent camera settings. Record concrete mismatches; correct them before progressing. Numerical checks complement visual similarity.
5. Check topology and modifier results with criteria appropriate to the asset. Open hair/clothing surfaces need not be watertight; electrical terminal and browser FPS checks apply only to those deliverables.
6. Save checkpoints and requested artifacts. Do animation only when requested; do not equate a large file or high polygon count with fidelity.

Map upstream `blender_rt_see` to `blender_dsh_view_image`, `blender_rt_plan` to `blender_dsh_plan`, `blender_rt_do` to `blender_dsh_execute_python` (respect restrictions above), and job/txn/loop to `blender_dsh_control` with the matching HTTP route. Discover actual commands and catalog parameters first. Do not assume DSH-host draft insertion exists in Codex.
