"""Deterministic, lightweight frost/crescent accents drawn around the held sword."""
import math
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPolygonF, QRadialGradient
from core.rig import apply


def draw_effects(painter, rig, matrices, effect, foreground=False):
    style = effect.get('style', '')
    phase = effect.get('phase', 0.)
    swap = effect.get('swap')
    pulse = math.sin(math.pi*min(1., max(0., phase)))**2 if style else 0.
    burst = math.sin(math.pi*min(1., max(0., swap))) if swap is not None else 0.
    strength = max(pulse, burst)
    if strength < .001:
        return
    grip = rig.bones['weapon']['pivot']
    gx, gy = apply(matrices['weapon'], grip)
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    if not foreground:
        glow = QRadialGradient(QPointF(gx,gy), 135)
        glow.setColorAt(0, QColor(124,223,255,round(45*strength)))
        glow.setColorAt(1, QColor(124,223,255,0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(QPointF(gx,gy),135,135)
        if style in ('summon', 'moon_arc'):
            center = QPointF(430,1080)
            arc = QPainterPath()
            angle = 205 + phase*35
            arc.arcMoveTo(QRectF(center.x()-395, center.y()-265,790,530),angle)
            arc.arcTo(QRectF(center.x()-395,center.y()-265,790,530),angle,-240*strength)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for width, alpha in ((17,25),(7,65),(2.2,180)):
                painter.setPen(QPen(QColor(153,224,255,round(alpha*strength)),width,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
                painter.drawPath(arc)
        # Short icy sword trails stay behind the arm, hilt and character.
        if style in ('salute','moon_arc'):
            for delta, alpha in ((-12,45),(-24,20)):
                angle = math.radians(-135+delta*strength)
                tip = (grip[0]+math.sin(angle)*365, grip[1]-math.cos(angle)*365)
                tx,ty = apply(matrices['weapon'],tip)
                painter.setPen(QPen(QColor(144,226,255,round(alpha*strength)),7,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
                painter.drawLine(QPointF(gx,gy),QPointF(tx,ty))
    else:
        local_phase = swap if swap is not None else phase
        for i in range(15):
            angle = i*2.39996+local_phase*.7
            radius = 20+(i%5)*18+math.sin(math.pi*local_phase)*43
            x,y = gx+math.cos(angle)*radius, gy+math.sin(angle)*radius
            size = (2.5+(i%3)*1.5)*strength
            alpha = round((100+(i%4)*35)*strength)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(181,237,255,alpha))
            painter.drawPolygon(QPolygonF([QPointF(x,y-size*1.8),QPointF(x+size*.6,y),QPointF(x,y+size*1.8),QPointF(x-size*.6,y)]))
    painter.restore()
