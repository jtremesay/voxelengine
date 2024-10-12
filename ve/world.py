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
)
from ve.voxel import VoxelKind


class World:
    def __init__(
        self,
    ):
        self.chunks: dict[WCPosition, Chunk] = {}

    def get_chunk(self, position: WCPosition) -> Chunk:
        try:
            chunk = self.chunks[position]
        except KeyError:
            chunk = Chunk()
            chunk.generate(position)

            self.chunks[position] = chunk

        return chunk

    def set_chunk(self, position: WCPosition, chunk: Chunk) -> None:
        self.chunks[position] = chunk

    def get_voxel(self, position: WVPosition) -> int:
        wc_position, cv_position = world_position_as_chunk_position(
            position, Chunk.SIZE
        )
        chunk = self.get_chunk(wc_position)
        return chunk.get_voxel(cv_position)

    def set_voxel(self, position: Vector3, voxel_kind: VoxelKind) -> None:
        wc_position, cv_position = world_position_as_chunk_position(
            position, Chunk.SIZE
        )
        chunk = self.get_chunk(wc_position)
        chunk.set_voxel(cv_position, voxel_kind)

    def __iter__(self):
        yield from self.chunks

    def create_vao(self) -> tuple[VAO, int]:
        voxels_count = 0
        positions = []
        block_ids = []

        # TODO: Implement this

        # TODO: Only iterate over currently visible chunks

        for wc_position, chunk in self.chunks.items():
            for cv_position, voxel_kind in chunk.voxels.items():
                if voxel_kind == VoxelKind.NONE:
                    continue

                # Discard invisible voxels (e.g. below the ground)
                if (
                    cv_position.x > 0
                    and cv_position.x < Chunk.SIZE - 1
                    and cv_position.z > 0
                    and cv_position.z < Chunk.SIZE - 1
                    and cv_position.y > 0
                    and cv_position.y < Chunk.SIZE - 1
                ):
                    if (
                        chunk.get_voxel(
                            CVPosition(cv_position.x - 1, cv_position.y, cv_position.z)
                        )
                        != VoxelKind.NONE
                        and chunk.get_voxel(
                            CVPosition(cv_position.x + 1, cv_position.y, cv_position.z)
                        )
                        != VoxelKind.NONE
                        and chunk.get_voxel(
                            CVPosition(cv_position.x, cv_position.y - 1, cv_position.z)
                        )
                        != VoxelKind.NONE
                        and chunk.get_voxel(
                            CVPosition(cv_position.x, cv_position.y + 1, cv_position.z)
                        )
                        != VoxelKind.NONE
                        and chunk.get_voxel(
                            CVPosition(cv_position.x, cv_position.y, cv_position.z - 1)
                        )
                        != VoxelKind.NONE
                        and chunk.get_voxel(
                            CVPosition(cv_position.x, cv_position.y, cv_position.z + 1)
                        )
                        != VoxelKind.NONE
                    ):
                        continue

                positions.append(
                    (
                        wc_position.x * Chunk.SIZE + cv_position.x,
                        cv_position.y,
                        wc_position.z * Chunk.SIZE + cv_position.z,
                    )
                )
                block_ids.append(voxel_kind)
                voxels_count += 1

        vao = mglw_geometry.cube(size=(1, 1, 1), uvs=False)
        vao.buffer(np.array(positions, dtype="f4"), "3f/i", ["in_offset"])
        vao.buffer(np.array(block_ids, dtype="i"), "i/i", ["in_block_id"])

        return vao, voxels_count
