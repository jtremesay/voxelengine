from pyrr import Vector3


class Direction:
    UP = Vector3((0, 1, 0))
    DOWN = Vector3((0, -1, 0))
    LEFT = Vector3((-1, 0, 0))
    RIGHT = Vector3((1, 0, 0))
    FORWARD = Vector3((0, 0, 1))
    BACKWARD = Vector3((0, 0, -1))
