class CameraSettings:
    def __init__(self):
        self.rotation_sensitivity = 1.0
        self.pan_sensitivity = 0.5
        self.zoom_sensitivity = 0.02

        self.enable_inertia = True
        self.damping = 0.85
        self.min_velocity = 0.001

        self.min_radius = 150
        self.max_radius = 3500
        self.max_beta = 1.5708  # π/2 (90 градусов)

        self.invert_rotation_x = False
        self.invert_rotation_y = False
        self.invert_pan_x = True
        self.invert_pan_y = True