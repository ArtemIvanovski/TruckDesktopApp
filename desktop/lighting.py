from graphics_settings import GraphicsManager


# Legacy alias
class LightingManager:
    def __init__(self, app):
        print("Warning: LightingManager is deprecated. Use GraphicsManager instead.")
        self.graphics_manager = GraphicsManager(app)

    def setup_hemispheric_lighting(self):
        return self.graphics_manager.setup_lighting()
