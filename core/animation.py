from panda3d.core import LerpFunc
from direct.interval.IntervalGlobal import *
import math


class CubicEase:
    @staticmethod
    def ease_in_out(t):
        if t < 0.5:
            return 4 * t * t * t
        p = 2 * t - 2
        return 1 + p * p * p


def spin_mesh(mesh, axis, rads, speed):
    duration = 120.0 / speed

    if axis == 'y':
        start_h = mesh.getH()
        end_h = start_h + math.degrees(rads)

        def ease_func(t):
            eased_t = CubicEase.ease_in_out(t)
            return start_h + (end_h - start_h) * eased_t

        interval = LerpFunc(ease_func,
                            fromData=0, toData=1,
                            duration=duration,
                            blendType='easeInOut')
        interval.setDoneEvent('spin_complete')

        def update_rotation(t):
            mesh.setH(ease_func(t))

        sequence = Sequence(
            LerpFunc(update_rotation, fromData=0, toData=1, duration=duration)
        )
        sequence.start()
        return sequence
