import math
from pathlib import Path

import moderngl as mgl
import moderngl_window as mglw
import moderngl_window.geometry as mglw_geometry
import moderngl_window.scene as mglw_scene
from pyrr import Matrix44

from ve.geometry import VEVector3
from ve.world import World, generate_world


class MainWindow(mglw.WindowConfig):
    title = "Jojo's Vortex Engine"
    gl_version = (3, 3)
    window_size = (800, 600)
    resizable = False
    aspect_ratio = window_size[0] / window_size[1]
    resource_dir = (Path(__file__).parent / "resources").resolve()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Create the world
        print("Generating world…")
        size = 32 * 8
        world = World(VEVector3(size, 32, size))
        generate_world(world)

        # Create an orbit camera that orbits around the chunk
        world_size = max(world.size.x, world.size.z, world.size.y)
        self.camera = mglw_scene.camera.OrbitCamera(
            target=(world.size.x / 2, world.size.y / 2, world.size.z / 2),
            radius=world_size * 2,
            aspect_ratio=self.aspect_ratio,
            angles=(0.0, 45.0),
            far=world_size * 16,
        )

        # Create a reference ground
        self.ground = mglw_geometry.quad_2d(
            size=(32, 32),
        )
        self.ground_prog = self.load_program("programs/solid_color.glsl")
        self.ground_prog["color"].value = 1.0, 1.0, 1.0, 1.0
        self.ground_prog["m_proj"].write(self.camera.projection.matrix)
        # The default quad is a vertical plane. Rotate it to be horizontal
        self.ground_prog["m_model"].write(
            Matrix44.from_x_rotation(math.pi / 2, dtype="f4")
        )

        # Create the voxels
        print("Generating mesh…")
        self.voxel, self.voxels_count = world.create_vao()

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
