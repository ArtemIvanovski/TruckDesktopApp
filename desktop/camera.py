import math
from panda3d.core import Point3, Vec3


class ArcCamera:
    def __init__(self, base):
        self.base = base
        # Точные параметры из content.html
        self.target = Point3(0, 300, 0)  # new BABYLON.Vector3(0, 300, 0)
        self.radius = 2000  # начальный радиус
        self.alpha = math.pi / 2  # Math.PI / 2
        self.beta = math.pi / 3  # Math.PI / 3

        # Ограничения как в JS
        self.min_radius = 150  # camera.lowerRadiusLimit = 150
        self.max_radius = 3500  # camera.upperRadiusLimit = 3500
        self.max_beta = (math.pi / 2) * 0.99  # camera.upperBetaLimit = (Math.PI / 2) * 0.99

        # Чувствительность как в JS
        self.wheel_delta_percentage = 0.02  # camera.wheelDeltaPercentage = 0.02
        self.panning_sensibility = 5  # camera.panningSensibility = 5

        self.dragging = False
        self.panning = False
        self.last_x = 0
        self.last_y = 0
        self.update()

    def update(self):
        # Точная формула позиционирования как в Babylon.js ArcRotateCamera
        x = self.target.x + self.radius * math.sin(self.beta) * math.cos(self.alpha)
        y = self.target.y + self.radius * math.cos(self.beta)
        z = self.target.z + self.radius * math.sin(self.beta) * math.sin(self.alpha)
        self.base.camera.setPos(x, y, z)
        self.base.camera.lookAt(self.target)

    def on_wheel_in(self):
        self.radius *= (1 - self.wheel_delta_percentage)
        self.radius = max(self.min_radius, min(self.max_radius, self.radius))
        self.update()

    def on_wheel_out(self):
        self.radius *= (1 + self.wheel_delta_percentage)
        self.radius = max(self.min_radius, min(self.max_radius, self.radius))
        self.update()

    def tick(self, task):
        if getattr(self.base, 'mouseWatcherNode', None) and self.base.mouseWatcherNode.hasMouse():
            mx = self.base.mouseWatcherNode.getMouseX()
            my = self.base.mouseWatcherNode.getMouseY()

            if self.dragging or self.panning:
                dx = (mx - self.last_x) * self.panning_sensibility
                dy = (my - self.last_y) * self.panning_sensibility

                if self.dragging:
                    self.alpha -= dx
                    self.beta += dy
                    self.beta = max(0.1, min(self.max_beta, self.beta))
                elif self.panning:
                    right = Vec3(math.cos(self.alpha + math.pi / 2), 0, math.sin(self.alpha + math.pi / 2))
                    forward = Vec3(math.cos(self.alpha), 0, math.sin(self.alpha))
                    pan_delta = right * dx + forward * dy
                    self.target += pan_delta

                self.update()

            self.last_x, self.last_y = mx, my
        return task.cont

    def on_left_down(self):
        """Начало вращения камеры"""
        self.dragging = True
        self.panning = False
        if getattr(self.base, 'mouseWatcherNode', None) and self.base.mouseWatcherNode.hasMouse():
            self.last_x = self.base.mouseWatcherNode.getMouseX()
            self.last_y = self.base.mouseWatcherNode.getMouseY()

    def on_left_up(self):
        """Конец вращения камеры"""
        self.dragging = False

    def on_right_down(self):
        """Начало панорамирования"""
        self.panning = True
        self.dragging = False
        if getattr(self.base, 'mouseWatcherNode', None) and self.base.mouseWatcherNode.hasMouse():
            self.last_x = self.base.mouseWatcherNode.getMouseX()
            self.last_y = self.base.mouseWatcherNode.getMouseY()

    def on_right_up(self):
        """Конец панорамирования"""
        self.panning = False

    def start_rotate(self):
        self.dragging = True

    def stop_rotate(self):
        self.dragging = False

    def start_pan(self):
        self.panning = True

    def stop_pan(self):
        self.panning = False