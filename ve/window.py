import math
import time
from pathlib import Path

import moderngl as mgl
import moderngl_window as mglw
import moderngl_window.geometry as mglw_geometry
import moderngl_window.scene as mglw_scene
import numpy as np
from pyrr import Matrix44

from ve.chunk import Chunk
from ve.geometry import WCPosition, WVPosition, world_position_as_chunk_position
from ve.world import World


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
            far=Chunk.SIZE * 16,
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

        # Create the world
        self.world = World()

        # Create 4x4 chunks around the origin
        print("Generating chunks…")
        world_size = 16
        half_size = world_size // 2
        for x in range(-half_size, half_size):
            for z in range(-half_size, half_size):
                self.world.create_chunk(WCPosition(x, z))

        print("Generating mesh…")
        self.voxel, self.voxels_count = self.world.create_vao()

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
        # speed = 1 / 4  # rounds per second
        # self.camera.angle_x = math.degrees(time * speed * 2 * math.pi)
        mtx = self.camera.matrix

        # Render the ground
        self.ground_prog["m_camera"].write(mtx)
        self.ground_prog["color"].value = 1.0, 0.0, 1.0, 1.0
        self.ground.render(self.ground_prog)

        # Render the voxels
        self.voxel_prog["m_camera"].write(mtx)
        self.voxel.render(self.voxel_prog, instances=self.voxels_count)

    def mouse_drag_event(self, x, y, dx, dy):
        self.camera.rot_state(dx, dy)

    def mouse_scroll_event(self, x_offset: float, y_offset: float):
        self.camera.zoom_state(y_offset)
