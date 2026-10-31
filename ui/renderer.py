"""One renderer shared by the transparent pet, rig inspector and video export."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPen, QPolygonF, QTransform

from core.rig import Rig, affine_triangle, apply, chain_weights, local_matrix, multiply
from ui.face import Eyelids, neck_texture
from ui.effects import draw_effects
from core.weapon import weapon_rest_point


class Renderer:
    def __init__(self, rig_path):
        self.path = Path(rig_path)
        self.rig = Rig.from_file(self.path)
        self.viewport = self.rig.data["viewport"]
        self.layers = []
        for source in sorted(self.rig.data["layers"], key=lambda item: item["z"]):
            item = dict(source)
            if item.get("procedural_shape") == "neck":
                full = neck_texture()
                bbox = (0, 0, full.width(), full.height())
            else:
                path = self.path.parent / item["file"]
                with Image.open(path) as check:
                    bbox = check.getchannel("A").point(lambda a: 255 if a >= 8 else 0).getbbox()
                full = QImage(str(path))
            if not bbox:
                raise ValueError(f"Empty part: {path}")
            # Crop is an in-memory sampling operation. Source PNG is never rewritten.
            item["image"] = full.copy(bbox[0], bbox[1], bbox[2]-bbox[0], bbox[3]-bbox[1])
            if item.get('mask_source'):
                mask = QImage(item['image'].size(), QImage.Format.Format_ARGB32_Premultiplied)
                mask.fill(Qt.GlobalColor.transparent)
                p = QPainter(mask)
                p.setRenderHint(QPainter.RenderHint.Antialiasing)
                p.translate(-bbox[0], -bbox[1])
                for polygon in item['mask_source']:
                    path = QPainterPath()
                    path.addPolygon(QPolygonF([QPointF(*point) for point in polygon]))
                    p.fillPath(path, Qt.GlobalColor.white)
                p.end()
                item['image'] = item['image'].convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
                p = QPainter(item['image'])
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
                p.drawImage(0,0,mask)
                p.end()
            if item["id"] == "head":
                item["eyelids"] = Eyelids(full)
            if item["image"].isNull():
                raise ValueError(f"Cannot decode PNG: {path}")
            item["source_bbox"] = bbox
            x, y, w, h = item["rect"]
            image = item["image"]
            if item.get('grip_source'):
                w, h = image.width()*item['texture_scale'], image.height()*item['texture_scale']
                x = item['grip_world'][0]-(item['grip_source'][0]-bbox[0])*item['texture_scale']
                y = item['grip_world'][1]-(item['grip_source'][1]-bbox[1])*item['texture_scale']
            if item.get('anchor_source'):
                x = item['anchor_world'][0]-(item['anchor_source'][0]-bbox[0])*w/image.width()
                y = item['anchor_world'][1]-(item['anchor_source'][1]-bbox[1])*h/image.height()
            item['rect'] = [x,y,w,h]
            texture_map = (w/image.width(), 0., 0., h/image.height(), x, y)
            if "rest_rotation" in item:
                px, py = item["rest_pivot"]
                rotation = multiply(local_matrix(px, py, item["rest_rotation"]), local_matrix(-px, -py))
                texture_map = multiply(rotation, texture_map)
            item["texture_map"] = texture_map
            if "mesh" in item:
                mesh = item["mesh"]
                vertices, texcoords, weights = [], [], []
                rows, cols = mesh["rows"], mesh["columns"]
                row_y = sorted(set([y+h*row/rows for row in range(rows+1)]+[v for v,_ in mesh['chain'] if y < v < y+h]))
                rows = len(row_y)-1
                for py in row_y:
                    for col in range(cols+1):
                        point = (x+w*col/cols, py)
                        vertices.append(point)
                        texcoords.append((image.width()*col/cols, image.height()*(py-y)/h))
                        weights.append(chain_weights(point[1], mesh["chain"]))
                triangles = []
                for row in range(rows):
                    for col in range(cols):
                        a = row*(cols+1)+col
                        b, c, d = a+1, a+cols+1, a+cols+2
                        triangles.extend([(a, b, d), (a, d, c)])
                item.update(vertices=vertices, texcoords=texcoords, weights=weights, triangles=triangles)
            if item.get('compact_handle'):
                # Compact the oversized generated hilt while preserving the blade.
                ys = sorted(set([image.height()*i/30 for i in range(31)]+[
                    item['compact_handle']['start']-bbox[1],item['grip_source'][1]-bbox[1]]))
                cols = 2
                vertices,texcoords,weights,triangles = [],[],[],[]
                for py in ys:
                    for col in range(cols+1):
                        px = image.width()*col/cols
                        texcoords.append((px,py))
                        vertices.append(weapon_rest_point((px+bbox[0],py+bbox[1]),item))
                        weights.append({item['bone']:1.})
                for row in range(len(ys)-1):
                    for col in range(cols):
                        a=row*(cols+1)+col
                        triangles.extend([(a,a+1,a+cols+2),(a,a+cols+2,a+cols+1)])
                item.update(mesh={},vertices=vertices,texcoords=texcoords,weights=weights,triangles=triangles)
            self.layers.append(item)

    def visible_layers(self, weapon, weights=None):
        weights = weights if weights is not None else {weapon: 1}
        return [item for item in self.layers if "weapon" not in item or weights.get(item['weapon'], 0) > .00001]

    def draw(self, painter, pose, weapon="slender", bones=False):
        matrices = self.rig.skin_matrices(pose)
        weights = pose.get('_weapon_weights', {weapon:1})
        reveal = pose.get('_weapon_reveal', {})
        draw_effects(painter, self.rig, matrices, pose.get('_fx', {}), foreground=False)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        for item in self.visible_layers(weapon, weights):
            if "mesh" in item:
                points = [self.rig.deform(point, weights, matrices)
                          for point, weights in zip(item["vertices"], item["weights"])]
                for triangle in item["triangles"]:
                    destination = [points[i] for i in triangle]
                    source = [item["texcoords"][i] for i in triangle]
                    mapping = affine_triangle(source, destination)
                    path = QPainterPath()
                    path.addPolygon(QPolygonF([QPointF(*p) for p in destination]))
                    painter.save()
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
                    painter.setClipPath(path, Qt.ClipOperation.IntersectClip)
                    painter.setWorldTransform(QTransform(*mapping), True)
                    if item.get('weapon'):
                        painter.setOpacity(weights.get(item['weapon'],0))
                        amount = reveal.get(item['weapon'],1)
                        if amount < 1:
                            texture = item['image']
                            painter.setClipRect(QRectF(0,texture.height()*(1-amount),texture.width(),texture.height()*amount),Qt.ClipOperation.IntersectClip)
                    painter.drawImage(QPointF(0, 0), item["image"])
                    painter.restore()
            else:
                transform = multiply(matrices[item["bone"]], item["texture_map"])
                painter.save()
                painter.setWorldTransform(QTransform(*transform), True)
                if item.get('weapon'):
                    painter.setOpacity(weights.get(item['weapon'], 0))
                    amount = reveal.get(item['weapon'], 1)
                    if amount < 1:
                        image = item['image']
                        painter.setClipRect(QRectF(0, image.height()*(1-amount), image.width(), image.height()*amount), Qt.ClipOperation.IntersectClip)
                painter.drawImage(QPointF(0, 0), item["image"])
                if "eyelids" in item:
                    painter.translate(-item["source_bbox"][0], -item["source_bbox"][1])
                    item["eyelids"].draw(painter, pose.get("head", {}).get("blink", 0))
                painter.restore()
        draw_effects(painter, self.rig, matrices, pose.get('_fx', {}), foreground=True)
        if bones:
            self.draw_bones(painter, matrices)

    def draw_bones(self, painter, matrices):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        positions = {name: apply(matrices[name], bone["pivot"]) for name, bone in self.rig.bones.items()}
        font = QFont("Segoe UI", 17)
        painter.setFont(font)
        for name in self.rig.order:
            bone = self.rig.bones[name]
            point = QPointF(*positions[name])
            painter.setPen(QPen(QColor("#33d7df"), 3))
            if bone.get("parent"):
                painter.drawLine(QPointF(*positions[bone["parent"]]), point)
            painter.setBrush(QColor("#fff0a6"))
            painter.setPen(QPen(QColor("#13304a"), 2))
            painter.drawEllipse(point, 7, 7)
            painter.setPen(QColor("#15384f"))
            painter.drawText(point+QPointF(10, -9), name)
        painter.restore()

    def frame(self, pose, size=(600, 708), weapon="slender", bones=False, background=None):
        image = QImage(size[0], size[1], QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(QColor(background) if background else Qt.GlobalColor.transparent)
        painter = QPainter(image)
        self.draw_fitted(painter, QRectF(0, 0, *size), pose, weapon, bones)
        painter.end()
        return image

    def draw_fitted(self, painter, target, pose, weapon="slender", bones=False):
        x, y, w, h = self.viewport
        scale = min(target.width()/w, target.height()/h)
        painter.save()
        painter.setClipRect(target, Qt.ClipOperation.IntersectClip)
        painter.translate(target.x()+(target.width()-w*scale)/2, target.y()+(target.height()-h*scale)/2)
        painter.scale(scale, scale)
        painter.translate(-x, -y)
        self.draw(painter, pose, weapon, bones)
        painter.restore()

    def pose_bounds(self, pose, weapon="slender"):
        matrices = self.rig.skin_matrices(pose)
        all_points = []
        for item in self.visible_layers(weapon, pose.get('_weapon_weights')):
            if "mesh" in item:
                all_points += [self.rig.deform(p, w, matrices) for p, w in zip(item["vertices"], item["weights"])]
            else:
                mapping = multiply(matrices[item["bone"]], item["texture_map"])
                image = item["image"]
                all_points += [apply(mapping, p) for p in [(0, 0), (image.width(), 0), (0, image.height()), (image.width(), image.height())]]
        return [min(p[0] for p in all_points), min(p[1] for p in all_points),
                max(p[0] for p in all_points), max(p[1] for p in all_points)]
