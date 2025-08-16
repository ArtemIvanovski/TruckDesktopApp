import math


class CameraSettings:
    def __init__(self):
        self.rotation_sensitivity = 2.0
        self.pan_sensitivity = 1.0
        self.zoom_sensitivity = 0.1

        self.enable_inertia = True
        self.damping = 0.9
        self.min_velocity = 0.001

        self.min_radius = 50
        self.max_radius = 5000
        self.max_beta = math.pi - 0.1
        self.min_beta = 0.1

        self.invert_rotation_x = False
        self.invert_rotation_y = False
        self.invert_pan_x = False
        self.invert_pan_y = True