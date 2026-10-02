# Cortex Hub documentation

Two languages. Plugin HTML is generated; do not flatten this tree into `docs/` root.

| Language | Path | Contents |
| --- | --- | --- |
| English | [en/app.html](en/app.html) | Hub API (`app`, pdoc) |
| English | [en/plugins/README.md](en/plugins/README.md) | Plugin overview + per-DCC HTML |
| فارسی | [fa/README.md](fa/README.md) | راهنمای نصب و کار |
| فارسی | [fa/plugins.md](fa/plugins.md) | راهنمای افزونه‌ها |

Source comments stay English. Regenerate API HTML with `python tools/build_docs.py` (same Python that has PySide6).
