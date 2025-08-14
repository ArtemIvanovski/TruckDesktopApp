import math


class CameraSettings:
    def __init__(self):
        self.rotation_sensitivity = 2.0  # Увеличил для более отзывчивого вращения
        self.pan_sensitivity = 1.0  # Увеличил для панорамирования
        self.zoom_sensitivity = 0.1  # Увеличил для более быстрого зума

        self.enable_inertia = True
        self.damping = 0.9  # Более плавное затухание
        self.min_velocity = 0.001

        self.min_radius = 50  # Минимальное расстояние
        self.max_radius = 5000
        self.max_beta = math.pi - 0.1  # Почти до 180 градусов
        self.min_beta = 0.1  # Минимальный угол над землей

        self.invert_rotation_x = False
        self.invert_rotation_y = False
        self.invert_pan_x = False
        self.invert_pan_y = True  # Y панорамирование инвертирован для удобства