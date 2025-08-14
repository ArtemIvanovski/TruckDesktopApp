import math
from panda3d.core import Point3, Vec3


class ArcCamera:
    def __init__(self, base):
        self.base = base
        self.target = Point3(0, 300, 0)
        self.radius = 2000
        self.alpha = math.pi / 2
        self.beta = math.pi / 3
        self.min_radius = 150
        self.max_radius = 3500
        self.max_beta = (math.pi / 2) * 0.99
        self.rotating = False
        self.panning = False
        self.dragging = False  # Флаг активного перемещения
        self.zoom_speed = 0.02
        self.pan_sensitivity = 5
        self.rotation_sensitivity = 5
        self.last_x = 0
        self.last_y = 0
        self._vel_alpha = 0.0
        self._vel_beta = 0.0
        self._vel_pan = Vec3(0, 0, 0)
        self._damping = 0.85
        self.update()

    def update(self):
        x = self.target.x + self.radius * math.sin(self.beta) * math.cos(self.alpha)
        y = self.target.y + self.radius * math.cos(self.beta)
        z = self.target.z + self.radius * math.sin(self.beta) * math.sin(self.alpha)
        self.base.camera.setPos(x, y, z)
        self.base.camera.lookAt(self.target)

    def on_left_down(self):
        self.rotating = True
        self.panning = False
        self.last_x = self.base.mouseWatcherNode.getMouseX()
        self.last_y = self.base.mouseWatcherNode.getMouseY()

    def on_left_up(self):
        self.rotating = False

    def on_right_down(self):
        self.panning = True
        self.rotating = False
        self.last_x = self.base.mouseWatcherNode.getMouseX()
        self.last_y = self.base.mouseWatcherNode.getMouseY()

    def on_right_up(self):
        self.panning = False

    def on_wheel_in(self):
        self.radius *= (1 - self.zoom_speed)
        self.radius = max(self.min_radius, min(self.max_radius, self.radius))
        self.update()

    def on_wheel_out(self):
        self.radius *= (1 + self.zoom_speed)
        self.radius = max(self.min_radius, min(self.max_radius, self.radius))
        self.update()

    def start_rotate(self):
        self.rotating = True
        self.dragging = True

    def stop_rotate(self):
        self.rotating = False
        self.dragging = False

    def start_pan(self):
        self.panning = True
        self.dragging = True

    def stop_pan(self):
        self.panning = False
        self.dragging = False

    def tick(self, task):
        if getattr(self.base, 'mouseWatcherNode', None) and self.base.mouseWatcherNode.hasMouse():
            mx = self.base.mouseWatcherNode.getMouseX()
            my = self.base.mouseWatcherNode.getMouseY()
            dx = (mx - self.last_x) * 5.0
            dy = (my - self.last_y) * 5.0

            if self.rotating:
                self._vel_alpha = self._vel_alpha * self._damping - dx
                self._vel_beta = self._vel_beta * self._damping + dy
                self.alpha += self._vel_alpha
                self.beta += self._vel_beta
                self.beta = max(0.1, min(self.max_beta, self.beta))
                self.update()
            elif self.panning:
                right = Vec3(math.cos(self.alpha + math.pi / 2), 0, math.sin(self.alpha + math.pi / 2))
                forward = Vec3(math.cos(self.alpha), 0, math.sin(self.alpha))
                pan_delta = right * dx * 5.0 + forward * dy * 5.0
                self._vel_pan = self._vel_pan * self._damping + pan_delta
                self.target += self._vel_pan
                self.update()
            self.last_x, self.last_y = mx, my
        return task.cont


