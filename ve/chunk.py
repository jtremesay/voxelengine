import math
from typing import Generator

import opensimplex

from ve.geometry import CVPosition, WCPosition
from ve.voxel import VoxelKind


class Chunk:
    """A chunk of blocks in the world

    Implemented as a vertical stack of XZ slices.
    Y is the vertical axis. 0 = bottom, SIZE-1 = top.
    """

    # Position of a voxel in the chunk
    # x, y, z >= 0 and < SIZE
    SIZE = 32

    def __init__(self, default_voxel_kind: int = VoxelKind.NONE):
        # [Y][Z][X]
        self.voxels: dict[CVPosition, VoxelKind] = {}
        self.default_voxel_kind = default_voxel_kind

    def clear(self) -> None:
        self.voxels.clear()

    def get_voxel(self, position: CVPosition) -> VoxelKind:
        return self.voxels.get(position, self.default_voxel_kind)

    def set_voxel(self, position: CVPosition, voxel_kind: VoxelKind) -> None:
        if voxel_kind == self.default_voxel_kind:
            del self.voxels[position]
        else:
            self.voxels[position] = voxel_kind

    def fill_slice(self, y: int, voxel_kind: VoxelKind) -> None:
        for z in range(Chunk.SIZE):
            for x in range(Chunk.SIZE):
                position = CVPosition(x, y, z)
                self.set_voxel(position, voxel_kind)

    def iter_voxels(self) -> Generator[CVPosition, None, None]:
        yield from self.voxels

    def generate(self, position: WCPosition) -> None:
        half_size = Chunk.SIZE // 2
        self.clear()

        # Fill the bottom half with water
        water_1 = half_size // 2
        for y in range(water_1):
            self.fill_slice(y, VoxelKind.WATER)

        noise = opensimplex.OpenSimplex(seed=42)

        for z in range(Chunk.SIZE):
            for x in range(Chunk.SIZE):
                # Use sin and cos to create a simple terrain
                # Y is the 1 of the terrain
                # Top of Y is air

                y = half_size  # base height
                y += (
                    noise.noise2(
                        (position.x * Chunk.SIZE + x) / 32,
                        (position.z * Chunk.SIZE + z) / 32,
                    )
                    * 16
                )
                y = math.floor(y)  # truncate to integer

                # Fill the bottom blocks with dirt
                for i in range(y):
                    self.set_voxel(CVPosition(x, i, z), VoxelKind.DIRT)

                # Top block is grass
                if y >= water_1:
                    self.set_voxel(CVPosition(x, y, z), VoxelKind.GRASS)

    def serialize(self) -> dict:
        return {
            "voxels": [
                {
                    "position": position,
                    "voxel_kind": voxel_kind,
                }
                for position, voxel_kind in self.voxels.items()
            ],
            "default_voxel_kind": self.default_voxel_kind,
        }
