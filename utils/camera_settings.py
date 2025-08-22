import math


class CameraSettings:
    def __init__(self):
        self.rotation_sensitivity = 1.4
        self.pan_sensitivity = 0.9
        self.zoom_sensitivity = 0.08

        self.enable_inertia = True
        self.damping = 0.92
        self.min_velocity = 0.0008

        self.min_radius = 80
        self.max_radius = 8000
        self.max_beta = math.pi - 0.1
        self.min_beta = 0.1

        self.invert_rotation_x = False
        self.invert_rotation_y = False
        self.invert_pan_x = False
        self.invert_pan_y = False