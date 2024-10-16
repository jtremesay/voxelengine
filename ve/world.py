import math
from typing import Generator

import moderngl_window.geometry as mglw_geometry
import numpy as np
from moderngl_window.opengl.vao import VAO
from opensimplex import OpenSimplex
from pyrr import Vector3

from ve.geometry import Direction, VEVector3
from ve.voxel import VoxelKind


class World:
    def __init__(self, size: VEVector3):
        self.size = size
        self.voxels: dict[VEVector3, VoxelKind] = {}

    def get_voxel(self, position: VEVector3) -> int:
        return self.voxels.get(position, VoxelKind.NONE)

    def set_voxel(self, position: VEVector3, voxel_kind: VoxelKind) -> None:
        self.voxels[position] = voxel_kind

    def iter_voxels(self) -> Generator[Vector3, None, None]:
        yield from self.voxels

    def create_vao(self) -> tuple[VAO, int]:
        voxels_count = 0
        positions = []
        block_ids = []

        for voxel_position in self.iter_voxels():
            voxel_kind = self.get_voxel(voxel_position)
            if voxel_kind == VoxelKind.NONE:
                continue

            directions = [
                Direction.UP,
                Direction.DOWN,
                Direction.LEFT,
                Direction.RIGHT,
                Direction.FORWARD,
                Direction.BACKWARD,
            ]
            if all(self.get_voxel(voxel_position + d) for d in directions):
                continue

            positions.append(voxel_position.to_pyrr())
            block_ids.append(voxel_kind)
            voxels_count += 1

        vao = mglw_geometry.cube(size=(1, 1, 1), uvs=False)
        vao.buffer(np.array(positions, dtype="f4"), "3f/i", ["in_offset"])
        vao.buffer(np.array(block_ids, dtype="i"), "i/i", ["in_block_id"])

        return vao, voxels_count


def generate_world(world: World) -> None:
    noise = OpenSimplex(seed=42)

    half_height = world.size.y // 2
    for z in range(world.size.z):
        for x in range(world.size.x):
            y = half_height  # base height
            y += (
                noise.noise2(
                    z / 32,
                    x / 32,
                )
                * half_height
            )
            y = math.floor(y)  # truncate to integer

            # 0 to y - 1 is dirt
            # y is grass
            # y to half_height is water
            for i in range(y):
                world.set_voxel(VEVector3(x, i, z), VoxelKind.DIRT)

            if y < half_height:
                for i in range(y, half_height):
                    world.set_voxel(VEVector3(x, i, z), VoxelKind.WATER)
            else:
                world.set_voxel(VEVector3(x, y, z), VoxelKind.GRASS)
