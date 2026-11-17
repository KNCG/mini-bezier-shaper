"""Build the two install zips for Mini Bezier Shaper into dist/.

- mini_bezier_shaper_4.2+.zip  : Blender 4.2+ extension (files at the zip root, with manifest)
- mini_bezier_shaper_legacy.zip: Blender 3.0-4.1 add-on (files inside a mini_bezier_shaper/ folder)
"""

import pathlib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "mini_bezier_shaper"
DIST = ROOT / "dist"

EXTENSION_FILES = ["__init__.py", "blender_manifest.toml", "README.md"]
LEGACY_FILES = ["__init__.py", "README.md"]


def build():
    DIST.mkdir(exist_ok=True)
    ext = DIST / "mini_bezier_shaper_4.2+.zip"
    legacy = DIST / "mini_bezier_shaper_legacy.zip"
    with zipfile.ZipFile(ext, "w", zipfile.ZIP_DEFLATED) as z:
        for name in EXTENSION_FILES:
            z.write(SRC / name, name)
    with zipfile.ZipFile(legacy, "w", zipfile.ZIP_DEFLATED) as z:
        for name in LEGACY_FILES:
            z.write(SRC / name, f"mini_bezier_shaper/{name}")
    for p in (ext, legacy):
        print(p.relative_to(ROOT))


if __name__ == "__main__":
    build()
