# Cortex Hub

Desktop pipeline hub for 3D/2D studios. Assign tasks, launch DCC tools with project context, and publish versions from inside the DCC.

Repository: https://github.com/imanshirani/CORTEXHUB

## Requirements

- Windows
- Python 3.10+
- pip packages in `requirements.txt`

```
pip install -r requirements.txt
```

## Run

Double-click `Start_Cortex.bat`, or:

```
python app/main.py
```

First-run default admin (change it in Settings after login):

- user: `iman`
- password: `1234`

Set each DCC executable path in **Settings > Utilities**. Empty paths are unused tools — fill only what your studio uses.

## Layout

| Path | Role |
| --- | --- |
| `app/` | Hub UI (PySide6) and SQLite core |
| `plugins/` | DCC plugins: 3ds Max, Maya, Blender, Houdini, Photoshop |
| `resource/icons/` | App and software icons |
| `docs/` | Generated API HTML |

A local SQLite file is created under `app/core/` on first launch. Postgres is reserved for a later server/cloud setup.

## Plugins

Launch a task from the dashboard. The hub writes `CORTEX_*` environment variables and a work folder, then starts the DCC with the matching plugin.

Supported launchers: 3ds Max, Maya, Blender, Houdini, Photoshop.
