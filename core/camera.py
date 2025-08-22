import math
from panda3d.core import Point3, Vec3

from utils.camera_settings import CameraSettings


class ArcCamera:
    def __init__(self, base):
        self.base = base
        self.settings = CameraSettings()

        self.target = Point3(0, 0, 0)
        self.radius = 2200
        self.alpha = math.pi / 2
        self.beta = math.pi / 3

        self.rotating = False
        self.panning = False
        self.last_x = 0
        self.last_y = 0
        self.mouse_x = 0
        self.mouse_y = 0
        self.has_mouse_pos = False

        # Инерция
        self.vel_alpha = 0.0
        self.vel_beta = 0.0
        self.vel_pan = Vec3(0, 0, 0)

        self.update()

    def update(self):
        self.beta = max(0.1, min(math.pi - 0.1, self.beta))

        x = self.target.x + self.radius * math.sin(self.beta) * math.cos(self.alpha)
        z = self.target.z + self.radius * math.sin(self.beta) * math.sin(self.alpha)
        y = self.target.y + self.radius * math.cos(self.beta)

        self.base.camera.setPos(x, y, z)
        self.base.camera.lookAt(self.target)

    def zoom_to_target(self, factor):
        self.radius *= factor
        self.radius = max(self.settings.min_radius, min(self.settings.max_radius, self.radius))
        self.update()

    def on_wheel_in(self):
        self.zoom_to_target(1 - self.settings.zoom_sensitivity)

    def on_wheel_out(self):
        self.zoom_to_target(1 + self.settings.zoom_sensitivity)

    def start_rotate(self):
        self.rotating = True

    def stop_rotate(self):
        self.rotating = False

    def start_pan(self):
        self.panning = True

    def stop_pan(self):
        self.panning = False

    def tick(self, task):
        mouse_available = getattr(self.base, 'mouseWatcherNode', None) and self.base.mouseWatcherNode.hasMouse()

        if mouse_available:
            mx = self.base.mouseWatcherNode.getMouseX()
            my = self.base.mouseWatcherNode.getMouseY()
            self.mouse_x = mx
            self.mouse_y = my
            self.has_mouse_pos = True
        elif self.has_mouse_pos:
            mx = self.mouse_x
            my = self.mouse_y
        else:
            return task.cont

        if self.rotating or self.panning:
            dx = (mx - self.last_x) * 2.0
            dy = (my - self.last_y) * 2.0

            if self.rotating:
                rot_dx = dx * self.settings.rotation_sensitivity
                rot_dy = dy * self.settings.rotation_sensitivity

                if self.settings.invert_rotation_x:
                    rot_dx = -rot_dx
                if self.settings.invert_rotation_y:
                    rot_dy = -rot_dy

                self.vel_alpha += -rot_dx * 0.02
                self.vel_beta += rot_dy * 0.02

            elif self.panning:
                pan_dx = dx * self.settings.pan_sensitivity * (self.radius / 1000.0)  # Масштабируем по расстоянию
                pan_dy = dy * self.settings.pan_sensitivity * (self.radius / 1000.0)

                if self.settings.invert_pan_x:
                    pan_dx = -pan_dx
                if self.settings.invert_pan_y:
                    pan_dy = -pan_dy

                # Панорамирование в плоскости экрана
                right = Vec3(math.cos(self.alpha + math.pi / 2), 0, math.sin(self.alpha + math.pi / 2))
                up_vector = Vec3(0, 0, 1)

                pan_delta = right * pan_dx + up_vector * pan_dy
                self.vel_pan += pan_delta

        if self.settings.enable_inertia:
            self.alpha += self.vel_alpha
            self.beta += self.vel_beta

            # Ограничиваем beta здесь тоже
            self.beta = max(0.1, min(math.pi - 0.1, self.beta))

            self.target += self.vel_pan

            self.vel_alpha *= self.settings.damping
            self.vel_beta *= self.settings.damping
            self.vel_pan *= self.settings.damping

            if abs(self.vel_alpha) < self.settings.min_velocity:
                self.vel_alpha = 0
            if abs(self.vel_beta) < self.settings.min_velocity:
                self.vel_beta = 0
            if self.vel_pan.length() < self.settings.min_velocity:
                self.vel_pan = Vec3(0, 0, 0)

            self.update()

        self.last_x, self.last_y = mx, my
        return task.cont

    def get_camera_settings(self):
        return self.settings

    def update_camera_settings(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)

    def reset_camera_settings(self):
        self.settings = CameraSettings()

    def on_left_down(self):
        self.rotating = True
        self.panning = False
        if getattr(self.base, 'mouseWatcherNode', None) and self.base.mouseWatcherNode.hasMouse():
            self.last_x = self.base.mouseWatcherNode.getMouseX()
            self.last_y = self.base.mouseWatcherNode.getMouseY()

    def on_left_up(self):
        self.rotating = False

    def on_right_down(self):
        self.panning = True
        self.rotating = False
        if getattr(self.base, 'mouseWatcherNode', None) and self.base.mouseWatcherNode.hasMouse():
            self.last_x = self.base.mouseWatcherNode.getMouseX()
            self.last_y = self.base.mouseWatcherNode.getMouseY()

    def on_right_up(self):
        self.panning = False
