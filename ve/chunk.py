import math
from typing import Generator

import numpy as np
from pyrr import Vector3

from ve.geometry import Direction
from ve.voxel import VoxelKind


class Chunk:
    """A chunk of blocks in the world

    Implemented as a vertical stack of XZ slices.
    Y is the vertical axis. 0 = bottom, SIZE-1 = top.
    """

    SIZE = 32

    def __init__(self, default_voxel_kind: int = VoxelKind.NONE):
        # [Y][Z][X]
        self.voxels = np.zeros((self.SIZE, self.SIZE, self.SIZE), dtype=np.uint8)
        self.voxels.fill(default_voxel_kind)

    def get_slice(self, y: int) -> np.ndarray:
        return self.voxels[y]

    def get_voxel(self, position: Vector3) -> VoxelKind:
        return self.voxels[position.y][position.z][position.x]

    def set_slice(self, y: int, slice: np.ndarray) -> None:
        self.voxels[y] = slice

    def set_voxel(self, position: Vector3, voxel_kind: VoxelKind) -> None:
        self.voxels[position.y][position.z][position.x] = voxel_kind

    def fill_slice(self, y: int, voxel_kind: VoxelKind) -> None:
        self.voxels[y].fill(voxel_kind)

    def __iter__(self) -> Generator[Vector3, None, None]:
        for y in range(self.SIZE):
            for z in range(self.SIZE):
                for x in range(self.SIZE):
                    yield Vector3((x, y, z))


def generate_chunk() -> Chunk:
    chunk = Chunk()
    half_size = Chunk.SIZE // 2

    # Fill the bottom half with water
    water_1 = half_size
    for y in range(water_1):
        chunk.fill_slice(y, VoxelKind.WATER)

    for z in range(Chunk.SIZE):
        for x in range(Chunk.SIZE):
            # Use sin and cos to create a simple terrain
            # Y is the 1 of the terrain
            # Top of Y is air
            y = math.floor(
                (
                    math.cos(x / Chunk.SIZE * 2 * math.pi)
                    + math.sin(z / Chunk.SIZE * 2 * math.pi)
                )
                * 3
                + half_size
            )

            # Fill the bottom blocks with dirt
            for i in range(y):
                chunk.set_voxel(Vector3((x, i, z)), VoxelKind.DIRT)

            # Top block is grass
            chunk.set_voxel(Vector3((x, y, z)), VoxelKind.GRASS)

    return chunk


def filter_chunk(chunk: Chunk) -> Generator[Vector3, None, None]:
    for position in chunk:
        block_id = chunk.get_voxel(position)
        if block_id == VoxelKind.NONE:
            continue

        if (
            (position.x > 0 and position.x < Chunk.SIZE - 1)
            and (position.z > 0 and position.z < Chunk.SIZE - 1)
            and (position.y > 0 and position.y < Chunk.SIZE - 1)
        ):
            if (
                chunk.get_voxel(position + Direction.UP) != VoxelKind.NONE
                and chunk.get_voxel(position + Direction.DOWN) != VoxelKind.NONE
                and chunk.get_voxel(position + Direction.LEFT) != VoxelKind.NONE
                and chunk.get_voxel(position + Direction.RIGHT) != VoxelKind.NONE
                and chunk.get_voxel(position + Direction.FORWARD) != VoxelKind.NONE
                and chunk.get_voxel(position + Direction.BACKWARD) != VoxelKind.NONE
            ):
                continue

        yield position
