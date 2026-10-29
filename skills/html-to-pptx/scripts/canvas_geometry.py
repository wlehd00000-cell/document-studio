"""Shared canvas geometry for measurement, assembly and visual QA."""
import math
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

LEGACY_CANVAS = (794, 1123)
LEGACY_EMU = (7560000, 10692000)
EMU_PER_PX = LEGACY_EMU[0] / LEGACY_CANVAS[0]
STANDARD_EMU_PER_PX = 9525  # 914400 EMU/inch / 96 CSS px/inch


def checked_canvas(width, height):
    """PowerPoint supports page edges from 1 to 56 inches."""
    values = tuple(float(v) for v in (width, height))
    if any(not math.isfinite(v) or not 96 <= v <= 5376 for v in values):
        raise ValueError(f"Invalid canvas {values}: use 96–5376 CSS pixels per edge")
    return tuple(round(v) for v in values)


def uniform_canvas(dimensions, fallback=LEGACY_CANVAS):
    sizes = [checked_canvas(*size) for size in dimensions]
    if not sizes:
        return checked_canvas(*fallback)
    first = sizes[0]
    if any(size != first for size in sizes[1:]):
        raise ValueError(f"Mixed page sizes {sorted(set(sizes))}; use one canvas per PPTX")
    return first


def measurement_canvas(data):
    slides = data.get('slides', [data])
    dimensions = []
    for item in slides:
        slide = item.get('slide', {})
        if ('width' in slide) != ('height' in slide):
            raise ValueError('Slide geometry must contain both width and height')
        dimensions.append((slide.get('width', LEGACY_CANVAS[0]),
                           slide.get('height', LEGACY_CANVAS[1])))
    return uniform_canvas(dimensions)


def canvas_emu(size):
    size = checked_canvas(*size)
    if size == LEGACY_CANVAS:
        return LEGACY_EMU  # Preserve exact existing A4 file dimensions.
    if size == tuple(reversed(LEGACY_CANVAS)):
        return tuple(reversed(LEGACY_EMU))
    return tuple(round(v * STANDARD_EMU_PER_PX) for v in size)


def pptx_pixel_size(path: Path):
    with ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read('ppt/presentation.xml'))
    size = root.find('{http://schemas.openxmlformats.org/presentationml/2006/main}sldSz')
    if size is None:
        raise ValueError('PPTX has no slide dimensions')
    dimensions=(int(size.attrib['cx']),int(size.attrib['cy']))
    if dimensions == LEGACY_EMU:return LEGACY_CANVAS
    if dimensions == tuple(reversed(LEGACY_EMU)):return tuple(reversed(LEGACY_CANVAS))
    return checked_canvas(*(v / STANDARD_EMU_PER_PX for v in dimensions))
