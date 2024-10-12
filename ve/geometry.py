from collections import namedtuple

from pyrr import Vector3


class Direction:
    UP = Vector3((0, 1, 0))
    DOWN = Vector3((0, -1, 0))
    LEFT = Vector3((-1, 0, 0))
    RIGHT = Vector3((1, 0, 0))
    FORWARD = Vector3((0, 0, 1))
    BACKWARD = Vector3((0, 0, -1))


WCPosition = namedtuple("WCPosition", ["x", "z"])
WVPosition = namedtuple("WVPosition", ["x", "y", "z"])
CVPosition = namedtuple("CVPosition", ["x", "y", "z"])


def world_position_as_chunk_position(
    position: WVPosition, chunk_size: int
) -> tuple[WCPosition, CVPosition]:
    return (
        WCPosition(position.x // chunk_size, position.z // chunk_size),
        CVPosition(position.x % chunk_size, position.y, position.z % chunk_size),
    )


def world_position_from_chunk_position(
    wc_position: WCPosition, cv_position: CVPosition, chunk_size: int
) -> WVPosition:
    return WVPosition(
        x=wc_position.x * chunk_size + cv_position.x,
        y=cv_position.y,
        z=wc_position.z * chunk_size + cv_position.z,
    )
