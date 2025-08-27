from panda3d.core import CardMaker, TransparencyAttrib, GeomVertexData, GeomVertexFormat, Geom, GeomVertexWriter, \
    GeomTriangles, GeomNode

from config.config import BOX_LIFT_HEIGHT, FLOOR_COLOR, TRUCK_CLOSED_COLOR


class TruckScene:
    def __init__(self, app):
        self.app = app
        self.truck_width = 1650
        self.truck_height = 260
        self.truck_depth = 245
        self.truck = None
        self.truck_edges = None
        self.truck_edges_bottom = None
        self.truck_edges_other = None
        self.truck_faces = None
        self.floor = None
        self.ground = None
        self.tent_closed = False
        self.grid_node = None

    def build(self):
        self._create_truck_box()
        self._create_ground()

    def _create_truck_box(self):
        # Shared vertices
        vdata = GeomVertexData('truck', GeomVertexFormat.get_v3(), Geom.UHStatic)
        vdata.setNumRows(8)
        vw = GeomVertexWriter(vdata, 'vertex')
        w = self.truck_width
        h = self.truck_height
        d = self.truck_depth
        lift = BOX_LIFT_HEIGHT
        fixed_lift = 130
        verts = [
            (-w / 2, -d / 2, lift + fixed_lift), (w / 2, -d / 2, lift + fixed_lift), (w / 2, d / 2, lift + fixed_lift),
            (-w / 2, d / 2, lift + fixed_lift),
            (-w / 2, -d / 2, h + lift + fixed_lift), (w / 2, -d / 2, h + lift + fixed_lift),
            (w / 2, d / 2, h + lift + fixed_lift), (-w / 2, d / 2, h + lift + fixed_lift)
        ]
        for v in verts:
            vw.addData3f(*v)

        tri = GeomTriangles(Geom.UHStatic)
        faces = [(4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        for a, b, c, d2 in faces:
            tri.addVertices(a, b, c);
            tri.addVertices(a, c, d2)
        geom_faces = Geom(vdata)
        geom_faces.addPrimitive(tri)
        node_faces = self.app.render.attachNewNode(GeomNode("truck_faces"))
        node_faces.node().addGeom(geom_faces)
        node_faces.setPos(0, 0, 0)  # Position at origin (vertices already include lift)
        node_faces.setTransparency(TransparencyAttrib.MAlpha)
        node_faces.setTwoSided(True)
        node_faces.clearRenderMode()
        node_faces.setLightOff(1)
        node_faces.setDepthWrite(False)
        node_faces.show()

        # Create bottom face (always visible, 10cm thick)
        self._create_bottom_face(vdata)

        vdata2 = GeomVertexData('truck_edges', GeomVertexFormat.get_v3(), Geom.UHStatic)
        vdata2.setNumRows(8)
        vw2 = GeomVertexWriter(vdata2, 'vertex')
        for v in verts:
            vw2.addData3f(*v)
        from panda3d.core import GeomLines

        lines_bottom = GeomLines(Geom.UHStatic)
        bottom = [(0, 1), (1, 2), (2, 3), (3, 0)]
        for a, b in bottom:
            lines_bottom.addVertices(a, b)
            lines_bottom.closePrimitive()
        geom_edges_bottom = Geom(vdata2)
        geom_edges_bottom.addPrimitive(lines_bottom)
        node_edges_bottom = self.app.render.attachNewNode(GeomNode("truck_edges_bottom"))
        node_edges_bottom.node().addGeom(geom_edges_bottom)
        node_edges_bottom.setPos(0, 0, 0)
        node_edges_bottom.setTransparency(TransparencyAttrib.MAlpha)
        node_edges_bottom.setTwoSided(True)

        r, g, b, _ = FLOOR_COLOR
        node_edges_bottom.setColor(0, 0, 0, 1.0)
        node_edges_bottom.setRenderModeThickness(1.0)
        node_edges_bottom.setDepthOffset(1)

        lines_other = GeomLines(Geom.UHStatic)
        others = [
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)
        ]
        for a, b in others:
            lines_other.addVertices(a, b)
            lines_other.closePrimitive()
        geom_edges_other = Geom(vdata2)
        geom_edges_other.addPrimitive(lines_other)
        node_edges_other = self.app.render.attachNewNode(GeomNode("truck_edges_other"))
        node_edges_other.node().addGeom(geom_edges_other)
        node_edges_other.setPos(0, 0, 0)  # Position at origin (vertices already include lift)
        node_edges_other.setTransparency(TransparencyAttrib.MAlpha)
        node_edges_other.setTwoSided(True)
        # Set color like floor to make lines invisible
        r, g, b, _ = FLOOR_COLOR
        node_edges_other.setColor(0, 0, 0, 1.0)  # Черный цвет
        node_edges_other.setRenderModeThickness(1.0)  # Тоньше как на картинке
        node_edges_other.setDepthOffset(1)

        # Store
        self.truck_faces = node_faces
        self.truck_edges = node_edges_other  # legacy handle
        self.truck_edges_bottom = node_edges_bottom
        self.truck_edges_other = node_edges_other
        self.truck = node_edges_other

        # Отключаем освещение для всех объектов truck
        node_faces.setLightOff(1)
        node_edges_other.setLightOff(1)
        node_edges_bottom.setLightOff(1)

        self._apply_tent_state()

    def _create_bottom_face(self, vdata):
        bottom_thickness = 10
        w = self.truck_width
        d = self.truck_depth
        lift = BOX_LIFT_HEIGHT

        bottom_vdata = GeomVertexData('bottom_face', GeomVertexFormat.get_v3(), Geom.UHStatic)
        bottom_vdata.setNumRows(8)
        bottom_vw = GeomVertexWriter(bottom_vdata, 'vertex')

        fixed_lift = 130
        bottom_level = lift + fixed_lift
        bottom_verts = [
            (-w / 2, -d / 2, bottom_level),
            (w / 2, -d / 2, bottom_level),
            (w / 2, d / 2, bottom_level),
            (-w / 2, d / 2, bottom_level),
            (-w / 2, -d / 2, bottom_level - bottom_thickness),
            (w / 2, -d / 2, bottom_level - bottom_thickness),
            (w / 2, d / 2, bottom_level - bottom_thickness),
            (-w / 2, d / 2, bottom_level - bottom_thickness)
        ]

        for v in bottom_verts:
            bottom_vw.addData3f(*v)

        bottom_tri = GeomTriangles(Geom.UHStatic)
        bottom_tri.addVertices(0, 1, 2)
        bottom_tri.addVertices(0, 2, 3)
        bottom_tri.addVertices(4, 7, 6)
        bottom_tri.addVertices(4, 6, 5)

        bottom_tri.addVertices(0, 4, 5)
        bottom_tri.addVertices(0, 5, 1)
        bottom_tri.addVertices(1, 5, 6)
        bottom_tri.addVertices(1, 6, 2)
        bottom_tri.addVertices(2, 6, 7)
        bottom_tri.addVertices(2, 7, 3)
        bottom_tri.addVertices(3, 7, 4)
        bottom_tri.addVertices(3, 4, 0)

        bottom_geom = Geom(bottom_vdata)
        bottom_geom.addPrimitive(bottom_tri)

        self.bottom_face_node = self.app.render.attachNewNode(GeomNode("truck_bottom_face"))
        self.bottom_face_node.node().addGeom(bottom_geom)
        self.bottom_face_node.setPos(0, 0, 0)
        self.bottom_face_node.setTransparency(TransparencyAttrib.MAlpha)
        self.bottom_face_node.setTwoSided(True)
        self.bottom_face_node.clearRenderMode()
        self.bottom_face_node.setLightOff(1)
        r, g, b, _ = FLOOR_COLOR
        self.bottom_face_node.setColor(r, g, b, 1.0)
        self.bottom_face_node.show()

    def _create_ground(self):
        cm = CardMaker('ground')
        cm.setFrame(-2400, 2400, -2400, 2400)
        self.ground = self.app.render.attachNewNode(cm.generate())
        self.ground.setP(-90)
        self.ground.setTransparency(TransparencyAttrib.MAlpha)
        self.ground.setColor(0.2, 0.2, 0.2, 0.0)
        # Отключаем освещение для ground
        self.ground.setLightOff(1)

    def _remove_grid(self):
        if self.grid_node:
            try:
                self.grid_node.removeNode()
            except Exception:
                pass
            self.grid_node = None

    def update_grid(self, enabled: bool, color, opacity: float, spacing_x_cm: int, spacing_y_cm: int):
        try:
            self._remove_grid()
            if not enabled:
                return
            from panda3d.core import LineSegs, TransparencyAttrib
            segs = LineSegs()
            segs.setThickness(1.0)
            r, g, b = color
            a = max(0.0, min(1.0, float(opacity)))
            segs.setColor(float(r), float(g), float(b), float(a))

            extent = 2000
            z = 135.0 + 0.05
            step_x = max(1, int(spacing_x_cm))
            step_y = max(1, int(spacing_y_cm))

            x_min, x_max = -extent, extent
            y_min, y_max = -extent, extent

            y = y_min - (y_min % step_y)
            while y <= y_max:
                segs.moveTo(x_min, y, z)
                segs.drawTo(x_max, y, z)
                y += step_y

            x = x_min - (x_min % step_x)
            while x <= x_max:
                segs.moveTo(x, y_min, z)
                segs.drawTo(x, y_max, z)
                x += step_x

            node = segs.create()
            self.grid_node = self.app.render.attachNewNode(node)
            self.grid_node.setTransparency(TransparencyAttrib.MAlpha)
            self.grid_node.setLightOff(1)
            self.grid_node.setDepthWrite(False)
        except Exception:
            self._remove_grid()

    def set_tent_alpha(self, a: float):
        self.tent_closed = a >= 0.29
        self._apply_tent_state()

    def set_tent_closed(self, closed: bool):
        self.tent_closed = closed
        self._apply_tent_state()

    def _apply_tent_state(self):
        if not (self.truck_faces and self.truck_edges_other and self.truck_edges_bottom):
            return
        self.truck_edges_other.show()
        r, g, b, _ = FLOOR_COLOR

        self.truck_edges_other.setColor(0, 0, 0, 1.0)
        self.truck_edges_bottom.show()
        self.truck_edges_bottom.setColor(0, 0, 0, 1.0)
        self.truck_edges_bottom.setRenderModeThickness(1.0)
        self.truck_edges_other.setRenderModeThickness(1.0)

        r, g, b, _ = TRUCK_CLOSED_COLOR
        alpha = 0.3 if self.tent_closed else 0.0
        self.truck_faces.setTransparency(TransparencyAttrib.MAlpha)
        self.truck_faces.clearRenderMode()
        self.truck_faces.setColorScale(1.5, 1.5, 1.5, 1.0)
        self.truck_faces.setDepthWrite(False)
        self.truck_faces.setColor(r, g, b, alpha)

    def resize(self, w: int, h: int, d: int):
        self.truck_width, self.truck_height, self.truck_depth = w, h, d
        if self.truck_edges:
            self.truck_edges.removeNode()
            self.truck_edges = None
        if self.truck_edges_bottom:
            self.truck_edges_bottom.removeNode()
            self.truck_edges_bottom = None
        if self.truck_edges_other:
            self.truck_edges_other.removeNode()
            self.truck_edges_other = None
        if self.truck_faces:
            self.truck_faces.removeNode()
            self.truck_faces = None
        if hasattr(self, 'bottom_face_node') and self.bottom_face_node:
            self.bottom_face_node.removeNode()
            self.bottom_face_node = None
        self._create_truck_box()
        if self.floor:
            self.floor.removeNode()
