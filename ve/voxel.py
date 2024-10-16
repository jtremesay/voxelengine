from collections import namedtuple
from enum import IntEnum


class VoxelKind(IntEnum):
    # Also update `resources/voxel.glsl` when changing this
    NONE = 0
    GRASS = 1
    DIRT = 2
    WATER = 3
    TRUNK = 4
    LEAF = 5
