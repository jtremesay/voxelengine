#!/usr/bin/env python3
import math
import random
import time
from enum import Enum, IntEnum
from pathlib import Path
from typing import Generator

import moderngl as mgl
import moderngl_window as mglw
import moderngl_window.geometry as mglw_geometry
import moderngl_window.scene as mglw_scene
import numpy as np
from moderngl_window.geometry import AttributeNames
from moderngl_window.opengl.vao import VAO
from pyrr import Matrix44, Vector3

# Coordinate system:
# Left-handed: +X right, +Y up, +Z forward
#
#             y (up)
#             |
#             |
# (forward) z |
#           \ |
#            \|
#             *---------- x (right)
#


class Direction:
    UP = Vector3((0, 1, 0))
    DOWN = Vector3((0, -1, 0))
    LEFT = Vector3((-1, 0, 0))
    RIGHT = Vector3((1, 0, 0))
    FORWARD = Vector3((0, 0, 1))
    BACKWARD = Vector3((0, 0, -1))


# Block IDs
class BlockID(IntEnum):
    NONE = 0
    GRASS = 1
    DIRT = 2
    WATER = 3


class Chunk:
    """A chunk of blocks in the world

    Implemented as a vertical stack of XZ slices.
    Y is the vertical axis. 0 = bottom, SIZE-1 = top.
    """

    SIZE = 32

    def __init__(self, default_block_id: int = BlockID.NONE):
        # [Y][Z][X]
        self.voxels = np.zeros((self.SIZE, self.SIZE, self.SIZE), dtype=np.uint8)
        self.voxels.fill(default_block_id)

    def get_slice(self, y: int) -> np.ndarray:
        return self.voxels[y]

    def get_voxel(self, position: Vector3) -> int:
        return self.voxels[position.y][position.z][position.x]

    def set_slice(self, y: int, slice: np.ndarray) -> None:
        self.voxels[y] = slice

    def set_voxel(self, position: Vector3, block_id: int) -> None:
        self.voxels[position.y][position.z][position.x] = block_id

    def fill_slice(self, y: int, block_id: int) -> None:
        self.voxels[y].fill(block_id)

    def __iter__(self) -> Generator[Vector3, None, None]:
        for y in range(self.SIZE):
            for z in range(self.SIZE):
                for x in range(self.SIZE):
                    yield Vector3((x, y, z))


def generate_chunk() -> Chunk:
    chunk = Chunk()
    half_size = Chunk.SIZE // 2
    water_1 = half_size
    for y in range(water_1):
        chunk.fill_slice(y, BlockID.WATER)

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
                chunk.set_voxel(Vector3((x, i, z)), BlockID.DIRT)

            # Top block is grass
            chunk.set_voxel(Vector3((x, y, z)), BlockID.GRASS)

    return chunk


def filter_chunk(chunk: Chunk) -> Generator[Vector3, None, None]:
    for position in chunk:
        block_id = chunk.get_voxel(position)
        if block_id == BlockID.NONE:
            continue

        if (
            (position.x > 0 and position.x < Chunk.SIZE - 1)
            and (position.z > 0 and position.z < Chunk.SIZE - 1)
            and (position.y > 0 and position.y < Chunk.SIZE - 1)
        ):
            if (
                chunk.get_voxel(position + Direction.UP) != BlockID.NONE
                and chunk.get_voxel(position + Direction.DOWN) != BlockID.NONE
                and chunk.get_voxel(position + Direction.LEFT) != BlockID.NONE
                and chunk.get_voxel(position + Direction.RIGHT) != BlockID.NONE
                and chunk.get_voxel(position + Direction.FORWARD) != BlockID.NONE
                and chunk.get_voxel(position + Direction.BACKWARD) != BlockID.NONE
            ):
                continue

        yield position


class MainWindow(mglw.WindowConfig):
    title = "Hello World"
    gl_version = (3, 3)
    window_size = (800, 600)
    resizable = False
    aspect_ratio = window_size[0] / window_size[1]
    resource_dir = (Path(__file__).parent / "resources").resolve()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Create an orbit camera that orbits around the chunk
        self.camera = mglw_scene.camera.OrbitCamera(
            radius=Chunk.SIZE * 2,
            aspect_ratio=self.aspect_ratio,
            angles=(0.0, 45.0),
            far=Chunk.SIZE * 4,
        )

        # Create a reference ground
        self.ground = mglw_geometry.quad_2d(
            size=(Chunk.SIZE, Chunk.SIZE),
        )
        self.ground_prog = self.load_program("programs/solid_color.glsl")
        self.ground_prog["color"].value = 1.0, 1.0, 1.0, 1.0
        self.ground_prog["m_proj"].write(self.camera.projection.matrix)
        # The default quad is a vertical plane. Rotate it to be horizontal
        self.ground_prog["m_model"].write(
            Matrix44.from_x_rotation(math.pi / 2, dtype="f4")
        )

        # Create a chunk
        print("Generating chunk…")
        start = time.monotonic()
        chunk = generate_chunk()
        duration = time.monotonic() - start
        print("Chunk generated in", duration, "seconds")

        print("Generating mesh…")
        start = time.monotonic()
        positions = []
        block_ids = []
        self.voxels_count = 0
        for position in filter_chunk(chunk):
            self.voxels_count += 1
            positions.append(position)
            block_ids.append(chunk.get_voxel(position))
        duration = time.monotonic() - start
        print("Mesh generated in", duration, "seconds")

        self.voxel = mglw_geometry.cube(size=(1, 1, 1), uvs=False)
        self.voxel.buffer(np.array(positions, dtype="f4"), "3f/i", ["in_offset"])
        self.voxel.buffer(np.array(block_ids, dtype="i"), "i/i", ["in_block_id"])

        self.voxel_prog = self.load_program("programs/voxel.glsl")
        self.voxel_prog["m_model"].write(Matrix44.identity(dtype="f4"))
        self.voxel_prog["m_proj"].write(self.camera.projection.matrix)

    def render(self, time, frame_time):
        print(
            "render -",
            # "voxels count:",
            # len(self.voxels),
            "duration:",
            frame_time,
            "fps:",
            1 / frame_time,
        )

        self.ctx.enable_only(mgl.DEPTH_TEST | mgl.CULL_FACE)

        # Update camera the camera
        speed = 1 / 4  # rounds per second
        self.camera.angle_x = math.degrees(time * speed * 2 * math.pi)
        mtx = self.camera.matrix

        # Render the ground
        self.ground_prog["m_camera"].write(mtx)
        self.ground_prog["color"].value = 1.0, 0.0, 1.0, 1.0
        self.ground.render(self.ground_prog)

        # Render the voxels
        self.voxel_prog["m_camera"].write(mtx)
        self.voxel.render(self.voxel_prog, instances=self.voxels_count)


def main():
    mglw.run_window_config(MainWindow)


if __name__ == "__main__":
    main()
