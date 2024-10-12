import json
from pathlib import Path
from typing import Generator

import moderngl_window.geometry as mglw_geometry
import numpy as np
from moderngl_window.opengl.vao import VAO
from pyrr import Vector3

from ve.chunk import Chunk
from ve.geometry import (
    CVPosition,
    WCPosition,
    WVPosition,
    world_position_as_chunk_position,
    world_position_from_chunk_position,
)
from ve.voxel import VoxelKind


class World:
    def __init__(
        self,
    ):
        self.chunks: dict[WCPosition, Chunk] = {}

    def create_chunk(self, position: WCPosition) -> Chunk:
        chunk = Chunk()
        chunk.generate(position)
        self.set_chunk(position, chunk)

        return chunk

    def get_chunk(self, position: WCPosition) -> Chunk | None:
        return self.chunks.get(position, None)

    def set_chunk(self, position: WCPosition, chunk: Chunk) -> None:
        self.chunks[position] = chunk

    def get_voxel(self, position: WVPosition) -> int:
        wc_position, cv_position = world_position_as_chunk_position(
            position, Chunk.SIZE
        )

        chunk = self.get_chunk(wc_position)
        if chunk is None:
            return VoxelKind.NONE

        return chunk.get_voxel(cv_position)

    def set_voxel(self, position: Vector3, voxel_kind: VoxelKind) -> None:
        wc_position, cv_position = world_position_as_chunk_position(
            position, Chunk.SIZE
        )
        chunk = self.get_chunk(wc_position)
        chunk.set_voxel(cv_position, voxel_kind)

    def __iter__(self):
        yield from self.chunks

    def iter_chunks(self) -> Generator[WCPosition, None, None]:
        yield from self.chunks

    def iter_voxels(self) -> Generator[WVPosition, None, None]:
        for wc_position, chunk in self.chunks.items():
            for cv_position in chunk.iter_voxels():
                yield world_position_from_chunk_position(
                    wc_position, cv_position, Chunk.SIZE
                )

    def create_vao(self) -> tuple[VAO, int]:
        voxels_count = 0
        positions = []
        block_ids = []

        for voxel_position in self.iter_voxels():
            voxel_kind = self.get_voxel(voxel_position)
            if voxel_kind == VoxelKind.NONE:
                continue

            # Discard voxels without any neighbors
            if (
                self.get_voxel(
                    WVPosition(
                        voxel_position.x + 1,
                        voxel_position.y,
                        voxel_position.z,
                    )
                )
                != VoxelKind.NONE
                and self.get_voxel(
                    WVPosition(voxel_position.x - 1, voxel_position.y, voxel_position.z)
                )
                != VoxelKind.NONE
                and self.get_voxel(
                    WVPosition(voxel_position.x, voxel_position.y + 1, voxel_position.z)
                )
                != VoxelKind.NONE
                and self.get_voxel(
                    WVPosition(voxel_position.x, voxel_position.y - 1, voxel_position.z)
                )
                != VoxelKind.NONE
                and self.get_voxel(
                    WVPosition(voxel_position.x, voxel_position.y, voxel_position.z + 1)
                )
                != VoxelKind.NONE
                and self.get_voxel(
                    WVPosition(voxel_position.x, voxel_position.y, voxel_position.z - 1)
                )
                != VoxelKind.NONE
            ):
                continue

            positions.append((voxel_position.x, voxel_position.y, voxel_position.z))
            block_ids.append(voxel_kind)
            voxels_count += 1

        vao = mglw_geometry.cube(size=(1, 1, 1), uvs=False)
        vao.buffer(np.array(positions, dtype="f4"), "3f/i", ["in_offset"])
        vao.buffer(np.array(block_ids, dtype="i"), "i/i", ["in_block_id"])

        return vao, voxels_count

    @classmethod
    def create(cls, size: int) -> "World":
        world = cls()
        half_size = size // 2
        for x in range(-half_size, half_size):
            for z in range(-half_size, half_size):
                world.create_chunk(WCPosition(x, z))

        return world

    def serialize(self) -> dict:
        data = []
        for position in self.iter_chunks():
            data.append(
                {
                    "position": position,
                    "chunk": self.get_chunk(position).serialize(),
                }
            )

        return data

    def save(self, path: str) -> None:
        data = self.serialize()
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
