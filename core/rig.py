"""Small 2D forward-kinematics rig, in master-image coordinates."""
from __future__ import annotations

import json
import math
from pathlib import Path


def identity():
    return (1., 0., 0., 1., 0., 0.)


def multiply(a, b):
    """Compose column-vector affine matrices: apply b, then a."""
    return (
        a[0]*b[0]+a[2]*b[1], a[1]*b[0]+a[3]*b[1],
        a[0]*b[2]+a[2]*b[3], a[1]*b[2]+a[3]*b[3],
        a[0]*b[4]+a[2]*b[5]+a[4], a[1]*b[4]+a[3]*b[5]+a[5],
    )


def apply(matrix, point):
    a, b, c, d, x, y = matrix
    return (a*point[0]+c*point[1]+x, b*point[0]+d*point[1]+y)


def local_matrix(x=0., y=0., rotation=0., sx=1., sy=1.):
    radians = math.radians(rotation)
    c, s = math.cos(radians), math.sin(radians)
    return (c*sx, s*sx, -s*sy, c*sy, x, y)


def chain_weights(y, chain):
    if y <= chain[0][0]:
        return {chain[0][1]: 1.}
    for (ya, a), (yb, b) in zip(chain, chain[1:]):
        if y <= yb:
            t = (y-ya)/(yb-ya)
            return {a: 1-t, b: t}
    return {chain[-1][1]: 1.}


def affine_triangle(source, target):
    """Affine map between two triangles, used for textured mesh cells."""
    (u, v), (u1, v1), (u2, v2) = source
    (x, y), (x1, y1), (x2, y2) = target
    du1, dv1, du2, dv2 = u1-u, v1-v, u2-u, v2-v
    determinant = du1*dv2-du2*dv1
    if abs(determinant) < 1e-10:
        raise ValueError("Degenerate texture triangle")
    a = ((x1-x)*dv2-(x2-x)*dv1)/determinant
    c = (du1*(x2-x)-du2*(x1-x))/determinant
    b = ((y1-y)*dv2-(y2-y)*dv1)/determinant
    d = (du1*(y2-y)-du2*(y1-y))/determinant
    return (a, b, c, d, x-a*u-c*v, y-b*u-d*v)


class Rig:
    def __init__(self, data):
        self.data = data
        self.bones = {bone["id"]: bone for bone in data["bones"]}
        if len(self.bones) != len(data["bones"]):
            raise ValueError("Duplicate bone id")
        self.order = []
        visiting, visited = set(), set()

        def visit(name):
            if name not in self.bones:
                raise ValueError(f"Unknown bone parent: {name}")
            if name in visiting:
                raise ValueError(f"Cyclic bone hierarchy at {name}")
            if name in visited:
                return
            visiting.add(name)
            parent = self.bones[name].get("parent")
            if parent:
                visit(parent)
            visiting.remove(name)
            visited.add(name)
            self.order.append(name)

        for name in self.bones:
            visit(name)

    @classmethod
    def from_file(cls, path):
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def skin_matrices(self, pose):
        worlds, skin = {}, {}
        for name in self.order:
            bone = self.bones[name]
            parent = bone.get("parent")
            x, y = bone["pivot"]
            px, py = self.bones[parent]["pivot"] if parent else (0, 0)
            channel = pose.get(name, {})
            local = local_matrix(
                x-px+channel.get("x", 0), y-py+channel.get("y", 0),
                channel.get("rotation", 0), channel.get("sx", 1), channel.get("sy", 1),
            )
            worlds[name] = multiply(worlds[parent], local) if parent else local
            skin[name] = multiply(worlds[name], local_matrix(-x, -y))
        return skin

    @staticmethod
    def deform(point, weights, matrices):
        if abs(sum(weights.values())-1.) > 1e-6 or any(w < 0 for w in weights.values()):
            raise ValueError("Skin weights must be nonnegative and sum to one")
        x, y = 0., 0.
        for bone, weight in weights.items():
            px, py = apply(matrices[bone], point)
            x += px*weight
            y += py*weight
        return x, y
