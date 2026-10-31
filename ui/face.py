"""Live eyelid deformation and a vector neck connector; original PNGs stay intact."""
from collections import deque
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPainterPath, QPen


def neck_texture():
    image = QImage(160, 180, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    p = QPainter(image)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    shape = QPainterPath(QPointF(34, 0))
    shape.cubicTo(38, 55, 30, 115, 8, 180)
    shape.lineTo(154, 180)
    shape.cubicTo(124, 112, 120, 55, 126, 0)
    shape.closeSubpath()
    gradient = QLinearGradient(0, 0, 0, 180)
    gradient.setColorAt(0, QColor('#edb9a4'))
    gradient.setColorAt(.45, QColor('#ffddc6'))
    gradient.setColorAt(1, QColor('#ffe4ce'))
    p.fillPath(shape, gradient)
    p.setPen(QPen(QColor('#55313c'), 4))
    sides = QPainterPath(QPointF(34, 0))
    sides.cubicTo(38, 55, 30, 115, 8, 180)
    sides.moveTo(126, 0)
    sides.cubicTo(120, 55, 124, 112, 154, 180)
    p.drawPath(sides)
    p.end()
    return image


class Eyelids:
    def __init__(self, full_head):
        self.eyes = []
        contours = []
        left = QPainterPath(QPointF(218, 621))
        left.cubicTo(272, 592, 377, 609, 411, 637)
        left.cubicTo(435, 691, 398, 750, 366, 757)
        left.cubicTo(303, 774, 254, 744, 218, 621)
        contours.append((left, (208, 585, 229, 195), 711))
        right = QPainterPath(QPointF(505, 651))
        right.cubicTo(556, 601, 675, 587, 755, 603)
        right.cubicTo(767, 669, 740, 724, 707, 747)
        right.cubicTo(651, 779, 559, 770, 538, 713)
        right.cubicTo(526, 691, 518, 674, 505, 651)
        right.closeSubpath()
        contours.append((right, (496, 582, 272, 198), 701))
        for contour, rect, closed_y in contours:
            x, y, w, h = rect
            mask = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
            mask.fill(Qt.GlobalColor.transparent)
            p = QPainter(mask)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.translate(-x, -y)
            p.fillPath(contour, Qt.GlobalColor.white)
            p.end()
            # Preserve blue/white fringe and its navy outline where it occludes an eye.
            blue = set()
            for py in range(h):
                for px in range(w):
                    c = full_head.pixelColor(x+px, y+py)
                    is_highlight = min(c.red(), c.green(), c.blue()) > 235 and y+py > 674
                    if not is_highlight and (c.blue() > c.red()+1 or (c.blue() >= c.red() and c.green() > c.red())):
                        blue.add((px, py))
            # Only blue regions connected to the patch boundary are fringe.
            # Isolated blue-white eye reflections must be covered by the eyelid.
            pending = deque(point for point in blue if point[0] in (0,w-1) or point[1] in (0,h-1))
            visited = set(pending)
            while pending:
                px, py = pending.popleft()
                mask.setPixelColor(px, py, QColor(0, 0, 0, 0))
                for adjacent in ((px-1,py),(px+1,py),(px,py-1),(px,py+1)):
                    if adjacent in blue and adjacent not in visited:
                        visited.add(adjacent)
                        pending.append(adjacent)
            original = full_head.copy(x, y, w, h)
            original = original.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
            p = QPainter(original)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
            p.drawImage(0, 0, mask)
            p.end()
            self.eyes.append(dict(rect=rect, mask=mask, original=original, closed_y=closed_y-y))

    def draw(self, painter, closure):
        closure = min(1., max(0., closure))
        if closure < .0001:
            return
        for eye in self.eyes:
            x, y, w, h = eye['rect']
            cy = eye['closed_y']
            patch = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
            patch.fill(Qt.GlobalColor.transparent)
            p = QPainter(patch)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            skin = QLinearGradient(0, 0, 0, h)
            skin.setColorAt(0, QColor('#ffe0cc'))
            skin.setColorAt(1, QColor('#ffdbc5'))
            p.fillRect(QRectF(0, 0, w, h), skin)
            height = h*(1-closure)
            if height > .2:
                # Compress only the eye region, anchored toward the lower eyelid.
                top = cy-height*.6
                p.drawImage(QRectF(0, top, w, height), eye['original'])
            if closure > .5:
                p.setOpacity((closure-.5)*2)
                lid = QPainterPath(QPointF(w*.12, cy-4))
                lid.cubicTo(w*.35, cy+12, w*.67, cy+12, w*.88, cy-10)
                p.setPen(QPen(QColor('#54151e'), 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawPath(lid)
                p.drawLine(QPointF(w*.84, cy-5), QPointF(w*.91, cy-15))
                p.setOpacity(1)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
            p.drawImage(0, 0, eye['mask'])
            p.end()
            painter.drawImage(QPointF(x, y), patch)
