from collections import namedtuple
from dataclasses import dataclass
from typing import Union

from pyrr import Vector3


class VEVector3:
    def __init__(self, x: float, y: float, z: float):
        self.x, self.y, self.z = x, y, z

    def to_pyrr(self) -> Vector3:
        return Vector3((self.x, self.y, self.z))

    @classmethod
    def from_pyrr(cls, vector: Vector3):
        return cls(vector.x, vector.y, vector.z)

    def __hash__(self):
        return hash((self.x, self.y, self.z))

    def __add__(self, other: Union["VEVector3", float]) -> "VEVector3":
        if isinstance(other, float):
            return VEVector3(self.x + other, self.y + other, self.z + other)

        return VEVector3(self.x + other.x, self.y + other.y, self.z + other.z)


class Direction:
    UP = VEVector3(0, 1, 0)
    DOWN = VEVector3(0, -1, 0)
    LEFT = VEVector3(-1, 0, 0)
    RIGHT = VEVector3(1, 0, 0)
    FORWARD = VEVector3(0, 0, 1)
    BACKWARD = VEVector3(0, 0, -1)
