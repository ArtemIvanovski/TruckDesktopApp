from panda3d.core import DirectionalLight

from config import HEMISPHERIC_LIGHT_INTENSITY


class LightingManager:
    def __init__(self, app):
        self.app = app

    def setup_hemispheric_lighting(self):
        dlight = DirectionalLight('hemispheric')
        dlight.setColor((HEMISPHERIC_LIGHT_INTENSITY, HEMISPHERIC_LIGHT_INTENSITY, HEMISPHERIC_LIGHT_INTENSITY, 1))
        dlnp = self.app.render.attachNewNode(dlight)
        dlnp.setHpr(-45, -45, 0)
        self.app.render.setLight(dlnp)
