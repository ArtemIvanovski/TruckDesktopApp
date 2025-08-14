from panda3d.core import DirectionalLight
import math


class LightingManager:
    def __init__(self, app):
        self.app = app

    def setup_hemispheric_lighting(self):
        self.app.render.clearLight()
        dlight1 = DirectionalLight('hemispheric_main')
        dlight1.setColor((1.5, 1.5, 1.5, 1))
        dlnp1 = self.app.render.attachNewNode(dlight1)
        dlnp1.setHpr(-45, -45, 0)
        self.app.render.setLight(dlnp1)

        dlight2 = DirectionalLight('hemispheric_fill')
        dlight2.setColor((0.8, 0.8, 0.8, 1))
        dlnp2 = self.app.render.attachNewNode(dlight2)
        dlnp2.setHpr(135, 45, 0)
        self.app.render.setLight(dlnp2)

