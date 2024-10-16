import math
from typing import Generator

import moderngl_window.geometry as mglw_geometry
import numpy as np
from moderngl_window.opengl.vao import VAO
from opensimplex import OpenSimplex
from pyrr import Vector3

from ve.geometry import Direction
from ve.voxel import VoxelKind

type VoxelKey = tuple[float, float, float]
import random
import sys


class World:
    def __init__(self, size: Vector3):
        self.size = size
        self.voxels: dict[VoxelKey, VoxelKind] = {}

    def get_voxel(self, position: Vector3) -> int:
        return self.voxels.get((position.x, position.y, position.z), VoxelKind.NONE)

    def set_voxel(self, position: Vector3, voxel_kind: VoxelKind) -> None:
        self.voxels[(position.x, position.y, position.z)] = voxel_kind

    def iter_voxels(self) -> Generator[Vector3, None, None]:
        for key in self.voxels.keys():
            yield Vector3(key)

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

            positions.append(voxel_position)
            block_ids.append(voxel_kind)
            voxels_count += 1

        vao = mglw_geometry.cube(size=(1, 1, 1), uvs=False)
        vao.buffer(np.array(positions, dtype="f4"), "3f/i", ["in_offset"])
        vao.buffer(np.array(block_ids, dtype="i"), "i/i", ["in_block_id"])

        return vao, voxels_count

    def get_height(self, x: int, z: int) -> int:
        y = self.size.y - 1
        for y in range(self.size.y - 1, -1, -1):
            voxel_kind = self.get_voxel(Vector3((x, y, z)))
            if voxel_kind != VoxelKind.NONE:
                return y

        raise ValueError("No voxel found")


def generate_tree(world: World, position: Vector3) -> None:
    for y in range(5):
        world.set_voxel(position + Vector3((0, y, 0)), VoxelKind.TRUNK)

    for x in range(-2, 3):
        for z in range(-2, 3):
            for y in range(5, 8):
                world.set_voxel(position + Vector3((x, y, z)), VoxelKind.LEAF)

    for x in range(-1, 2):
        for z in range(-1, 2):
            world.set_voxel(position + Vector3((x, 8, z)), VoxelKind.LEAF)


def generate_world(world: World, seed=None) -> None:
    if seed is None:
        seed = random.randint(0, sys.maxsize)
    noise = OpenSimplex(seed)

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
                world.set_voxel(Vector3((x, i, z)), VoxelKind.DIRT)

            if y < half_height:
                for i in range(y, half_height):
                    world.set_voxel(Vector3((x, i, z)), VoxelKind.WATER)
            else:
                world.set_voxel(Vector3((x, y, z)), VoxelKind.GRASS)

    # Generate a tree per ~x*x tiles
    for i in range(world.size.x * world.size.z // (16**2)):
        voxel_kind = VoxelKind.NONE
        while voxel_kind != VoxelKind.GRASS:
            x = random.randint(0, world.size.x - 1)
            z = random.randint(0, world.size.z - 1)
            position = Vector3((x, 0, z))
            position.y = world.get_height(position.x, position.z)
            voxel_kind = world.get_voxel(position)

        generate_tree(world, position)
