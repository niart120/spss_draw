"""SPSS (Simple Perfect Squared Square) library."""

from spss_draw.bouwkamp import bouwkamp_to_tiles, validate
from spss_draw.coloring import build_adjacency, four_color
from spss_draw.data import DUIJVESTIJN_BOUWKAMP, DUIJVESTIJN_SIZE
from spss_draw.draw_2d import draw_dual
from spss_draw.transforms import transform_tiles

__all__ = [
    "DUIJVESTIJN_BOUWKAMP",
    "DUIJVESTIJN_SIZE",
    "bouwkamp_to_tiles",
    "build_adjacency",
    "draw_dual",
    "four_color",
    "transform_tiles",
    "validate",
]
