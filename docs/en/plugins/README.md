# Cortex Hub plugins

DCC add-ons live under `plugins/`. The hub does **not** load them as a Python package. A launcher writes `CORTEX_*` into the process environment, then starts the DCC so that DCC runs the matching startup script.

Regenerate the HTML API (needs PySide6; DCC apps are stubbed):

```
python tools/build_docs.py
```

Human overview is this page. Per-module HTML:

| DCC | HTML | Source folder |
| --- | --- | --- |
| 3ds Max | [3dsmax/](3dsmax/index.html) | `plugins/3dsmax/` |
| Blender | [blender/](blender/index.html) | `plugins/blender/` |
| Maya | [maya/](maya/index.html) | `plugins/maya/` |
| Houdini | [houdini/](houdini/index.html) | `plugins/houdini/scripts/` |
| Photoshop | [photoshop/](photoshop/index.html) | `plugins/photoshop/` |
| Shared 2D | [common/](common/index.html) | `plugins/common/` |

Persian studio guide: [../../fa/plugins.md](../../fa/plugins.md).

## How a task reaches a plugin

1. Artist launches a task from the hub dashboard.
2. `app.core.launcher` sets work folder + env (see below) and starts the executable from **Settings > Utilities**.
3. Empty executable path = that DCC is unused; the launcher refuses instead of calling `Popen([""])`.
4. Department software lock: if the task is locked to one DCC, the others return access denied.

### Environment the hub always sets

| Variable | Meaning |
| --- | --- |
| `CORTEX_PROJECT_ROOT` | Project root on disk |
| `CORTEX_PROJECT_NAME` | Project name |
| `CORTEX_TASK_ID` | Task id in SQLite |
| `CORTEX_TASK_NAME` | Safe task name |
| `CORTEX_USER` | Username |
| `CORTEX_DEPT_NAME` | Department |
| `CORTEX_RENDER_ENGINE` | Project renderer |
| `CORTEX_FPS` / `CORTEX_RES_W` / `CORTEX_RES_H` | Frame rate and resolution |
| `CORTEX_FRAME_START` / `CORTEX_FRAME_END` | Optional range |
| `CORTEX_ENTITY_TYPE` / `CORTEX_ENTITY_NAME` | Shot or Asset |
| `CORTEX_WORK_PATH` | Task work directory |

## 3ds Max (`plugins/3dsmax/`)

Launch: `3dsmax.exe -U PythonHost plugins/3dsmax/startup.py`.

| File | Role |
| --- | --- |
| `startup.py` | Writes a clean `.mxp` under `_max_system`, clears leftover Max folders at project root, then shows the dock |
| `cortex_ui.py` | Qt dock: Latest, Loader, Publish, Save View |
| `loader.py` | `LoaderWindow` — pick published versions into the scene |
| `publisher_max.py` | `MaxPublisher` — versioned scene publish |
| `publisher_mat_max.py` | Material library publish |
| `save_view.py` | Save current work file into `CORTEX_WORK_PATH` |
| `style.py` | Shared Qt stylesheet for the Max tools |
| `converters/manager.py` | Placeholder (empty) |

## Blender (`plugins/blender/`)

Launch: `blender.exe --python plugins/blender/startup.py`.

| File | Role |
| --- | --- |
| `startup.py` | Applies FPS/resolution from env, ensures PySide6, shows the floating bar |
| `cortex_ui.py` | `CortexBlenderBar` |
| `loader.py` | `BlenderLoader` |
| `publisher_blender.py` | `BlenderPublisher` |
| `publisher_mat_blender.py` | Material publish |
| `save_view.py` | Save work file |
| `style.py` | Qt stylesheet |

## Maya (`plugins/maya/`)

Launch: Maya with `PYTHONPATH` prepended to `plugins/maya/` so Maya auto-runs `userSetup.py`.

| File | Role |
| --- | --- |
| `userSetup.py` | FPS, resolution, workspace; builds the native **Cortex** shelf (Latest, Loader, Publish, …) |
| `loader.py` | `MayaLoader` |
| `publisher_maya.py` | `MayaPublisher` |
| `publisher_mat_maya.py` | Material publish |
| `save_view.py` | Save work file |
| `style.py` | Qt stylesheet |

## Houdini (`plugins/houdini/`)

Launch: Houdini with `HOUDINI_PACKAGE_DIR` = `plugins/houdini`, `PYTHONPATH` = `plugins/houdini/scripts`, `JOB` = work path, `CORTEX_HOUDINI` = plugin root. Package file `cortex_houdini.json` adds those paths. `456.py` runs when a hip is created/opened (Houdini naming; not a valid Python identifier, so it is not in the pdoc HTML).

| File | Role |
| --- | --- |
| `cortex_houdini.json` | Houdini package env |
| `scripts/456.py` | Status bar, FPS/res, show Cortex shelf tab |
| `scripts/loader.py` | `LoaderWindow` |
| `scripts/publisher_houdini.py` | Publish from a node (`run_publish_logic`) |
| `scripts/publisher_mat_houdini.py` | Material publish |
| `scripts/save_view.py` | Save hip into the task folder |
| `scripts/open_latest.py` | Open latest hip for the task |
| `scripts/hda_creator.py` | Create Cortex HDA / loader nodes |
| `toolbar/cortex.shelf` | Shelf definitions |

## Photoshop (`plugins/photoshop/`)

Launch: Photoshop EXE, then a **separate** Python process: `python plugins/photoshop/startup.py` (floating bar, not inside Photoshop’s interpreter).

| File | Role |
| --- | --- |
| `startup.py` | Installs `photoshop-python-api` if missing; shows the bar |
| `cortex_ui.py` | `PhotoshopCortexBar` |
| `photoshop_publisher.py` | `PhotoshopPublisher` |
| `save_view.py` | Save current document into the task folder |
| `style.py` | Qt stylesheet |

## Shared 2D (`plugins/common/`)

`publisher_2d.py` — hub-side dialog to pick a PSD/PNG/XCF and register it. Used when publishing 2D from the hub rather than from the DCC bar.
