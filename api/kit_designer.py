"""
API endpoints for the Kit Designer workbench.

Serves the single-page kit designer UI and provides endpoints to list
available kit templates, crest assets, and sponsor mask designs.
"""

import os

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/kit-designer", tags=["kit-designer"])

_GFX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "gfx")

_BROWSER_EXTS = (".png", ".jpg", ".jpeg", ".svg", ".webp")

_FULLKIT_DIR = os.path.join(_GFX_DIR, "kit_templates", "fullkit")
_TEMPLATES_DIR = os.path.join(_GFX_DIR, "kit_templates")


@router.get("/", response_class=HTMLResponse)
async def kit_designer_ui():
    """Serve the kit designer workbench page (never cached)."""
    try:
        with open("templates/kit_designer.html", "r", encoding="utf-8") as f:
            return HTMLResponse(
                content=f.read(),
                headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"},
            )
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Kit Designer not found</h1><p>Create templates/kit_designer.html</p>",
            status_code=404,
        )


@router.get("/api/collars")
async def list_collars():
    """Return available collar designs.

    Scans for subdirectories named ``collar*`` inside kit_templates/.
    """
    if not os.path.isdir(_TEMPLATES_DIR):
        return {"collars": []}
    collars = sorted(
        d
        for d in os.listdir(_TEMPLATES_DIR)
        if d.lower().startswith("collar") and os.path.isdir(os.path.join(_TEMPLATES_DIR, d))
    )
    return {"collars": collars}


_KIT_PREFIXES = ("s_", "e_", "kit")
_SHORTS_PREFIX = "shorts_"
_SOCKS_PREFIX = "socks_"

@router.get("/api/kits")
async def list_kits():
    """Return available kit design folders with their mask files.

    Scans for subdirectories starting with ``s_`` (simple), ``e_`` (exotic),
    or ``kit`` inside kit_templates/.
    Each kit folder holds shirt secondary/tertiary masks specific to that design.
    Returns a list of objects: { name, files } where *files* lists the mask PNGs
    found inside the folder so the frontend can load them dynamically.
    """
    if not os.path.isdir(_TEMPLATES_DIR):
        return {"kits": []}
    kit_dirs = sorted(
        d
        for d in os.listdir(_TEMPLATES_DIR)
        if d.lower().startswith(_KIT_PREFIXES) and os.path.isdir(os.path.join(_TEMPLATES_DIR, d))
    )
    kits = []
    for d in kit_dirs:
        folder = os.path.join(_TEMPLATES_DIR, d)
        files = sorted(
            f for f in os.listdir(folder)
            if f.lower().endswith(_BROWSER_EXTS)
        )
        kits.append({"name": d, "files": files})
    return {"kits": kits}


@router.get("/api/shorts")
async def list_shorts_styles():
    """Return available shorts design folders with their mask files."""
    if not os.path.isdir(_TEMPLATES_DIR):
        return {"shorts": []}
    style_dirs = sorted(
        d
        for d in os.listdir(_TEMPLATES_DIR)
        if d.lower().startswith(_SHORTS_PREFIX) and os.path.isdir(os.path.join(_TEMPLATES_DIR, d))
    )
    styles = []
    for d in style_dirs:
        folder = os.path.join(_TEMPLATES_DIR, d)
        files = sorted(f for f in os.listdir(folder) if f.lower().endswith(_BROWSER_EXTS))
        styles.append({"name": d, "files": files})
    return {"shorts": styles}


@router.get("/api/socks")
async def list_socks_styles():
    """Return available socks design folders with their mask files."""
    if not os.path.isdir(_TEMPLATES_DIR):
        return {"socks": []}
    style_dirs = sorted(
        d
        for d in os.listdir(_TEMPLATES_DIR)
        if d.lower().startswith(_SOCKS_PREFIX) and os.path.isdir(os.path.join(_TEMPLATES_DIR, d))
    )
    styles = []
    for d in style_dirs:
        folder = os.path.join(_TEMPLATES_DIR, d)
        files = sorted(f for f in os.listdir(folder) if f.lower().endswith(_BROWSER_EXTS))
        styles.append({"name": d, "files": files})
    return {"socks": styles}


@router.get("/api/patterns")
async def list_patterns():
    """Return a list of available pattern image filenames."""
    patterns_dir = os.path.join(_GFX_DIR, "kit_templates", "patterns")
    if not os.path.isdir(patterns_dir):
        return {"patterns": []}
    files = sorted(
        f
        for f in os.listdir(patterns_dir)
        if f.lower().endswith(_BROWSER_EXTS)
    )
    return {"patterns": files}


@router.get("/api/sponsor-designs")
async def list_sponsor_designs():
    """Return sponsor design folders with their files.

    Sponsor designs may include:
    - fixed-color layer: fixed_color.png or sponsor_fixed.png
    - tintable masks: mask_primary/secondary/tertiary.png (or sponsor_* aliases)
    """
    sponsors_dir = os.path.join(_GFX_DIR, "sponsors")
    if not os.path.isdir(sponsors_dir):
        return {"sponsor_designs": []}
    design_dirs = sorted(
        d
        for d in os.listdir(sponsors_dir)
        if os.path.isdir(os.path.join(sponsors_dir, d))
    )
    designs = []
    for d in design_dirs:
        folder = os.path.join(sponsors_dir, d)
        files = sorted(
            f for f in os.listdir(folder)
            if f.lower().endswith(_BROWSER_EXTS)
        )
        designs.append({"name": d, "files": files})
    return {"sponsor_designs": designs}


@router.get("/api/crests")
async def list_crests():
    """Return a list of available crest image filenames."""
    crests_dir = os.path.join(_GFX_DIR, "crests")
    if not os.path.isdir(crests_dir):
        return {"crests": []}
    files = sorted(
        f
        for f in os.listdir(crests_dir)
        if f.lower().endswith(_BROWSER_EXTS)
    )
    return {"crests": files}
