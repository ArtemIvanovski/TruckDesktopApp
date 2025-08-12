from panda3d.core import CardMaker, TransparencyAttrib, GeomVertexData, GeomVertexFormat, Geom, GeomVertexWriter, GeomTriangles, GeomNode


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

    def build(self):
        self._create_truck_box()
        self._create_floor()
        self._create_ground()

    def _create_truck_box(self):
        # Shared vertices
        vdata = GeomVertexData('truck', GeomVertexFormat.get_v3(), Geom.UHStatic)
        vdata.setNumRows(8)
        vw = GeomVertexWriter(vdata, 'vertex')
        w = self.truck_width
        h = self.truck_height
        d = self.truck_depth
        verts = [
            (-w/2, -d/2, 0), (w/2, -d/2, 0), (w/2, d/2, 0), (-w/2, d/2, 0),
            (-w/2, -d/2, h), (w/2, -d/2, h), (w/2, d/2, h), (-w/2, d/2, h)
        ]
        for v in verts:
            vw.addData3f(*v)

        # Faces (for closed tent fill)
        tri = GeomTriangles(Geom.UHStatic)
        faces = [(0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        for a,b,c,d2 in faces:
            tri.addVertices(a,b,c); tri.addVertices(a,c,d2)
        geom_faces = Geom(vdata)
        geom_faces.addPrimitive(tri)
        node_faces = self.app.render.attachNewNode(GeomNode("truck_faces"))
        node_faces.node().addGeom(geom_faces)
        node_faces.setPos(0, 0, h/2)
        node_faces.setTransparency(TransparencyAttrib.MAlpha)
        node_faces.setTwoSided(True)
        node_faces.hide()  # start hidden (open tent by default)

        # Edges only (no diagonals) — split bottom edges to make them thicker
        vdata2 = GeomVertexData('truck_edges', GeomVertexFormat.get_v3(), Geom.UHStatic)
        vdata2.setNumRows(8)
        vw2 = GeomVertexWriter(vdata2, 'vertex')
        for v in verts:
            vw2.addData3f(*v)
        from panda3d.core import GeomLines
        # Bottom edges (0-1-2-3-0)
        lines_bottom = GeomLines(Geom.UHStatic)
        bottom = [(0,1),(1,2),(2,3),(3,0)]
        for a,b in bottom:
            lines_bottom.addVertices(a,b)
            lines_bottom.closePrimitive()
        geom_edges_bottom = Geom(vdata2)
        geom_edges_bottom.addPrimitive(lines_bottom)
        node_edges_bottom = self.app.render.attachNewNode(GeomNode("truck_edges_bottom"))
        node_edges_bottom.node().addGeom(geom_edges_bottom)
        node_edges_bottom.setPos(0, 0, h/2)
        node_edges_bottom.setTransparency(TransparencyAttrib.MAlpha)
        node_edges_bottom.setTwoSided(True)
        node_edges_bottom.setColor(0, 0, 0, 0.5)
        node_edges_bottom.setRenderModeThickness(1.0)  # Тоньше как на картинке
        node_edges_bottom.setDepthOffset(1)

        # Other edges (top rectangle and verticals)
        lines_other = GeomLines(Geom.UHStatic)
        others = [
            (4,5),(5,6),(6,7),(7,4),
            (0,4),(1,5),(2,6),(3,7)
        ]
        for a,b in others:
            lines_other.addVertices(a,b)
            lines_other.closePrimitive()
        geom_edges_other = Geom(vdata2)
        geom_edges_other.addPrimitive(lines_other)
        node_edges_other = self.app.render.attachNewNode(GeomNode("truck_edges_other"))
        node_edges_other.node().addGeom(geom_edges_other)
        node_edges_other.setPos(0, 0, h/2)
        node_edges_other.setTransparency(TransparencyAttrib.MAlpha)
        node_edges_other.setTwoSided(True)
        node_edges_other.setColor(0, 0, 0, 0.5)
        node_edges_other.setRenderModeThickness(1.0)  # Тоньше как на картинке
        node_edges_other.setDepthOffset(1)

        # Store
        self.truck_faces = node_faces
        self.truck_edges = node_edges_other  # legacy handle
        self.truck_edges_bottom = node_edges_bottom
        self.truck_edges_other = node_edges_other
        # Main handle for API compatibility
        self.truck = node_edges_other

        self._apply_tent_state()
        # Floor should always be visible (like web): ensure it exists
        if not self.floor:
            self._create_floor()

    def _create_floor(self):
        from config import FLOOR_COLOR, FLOOR_THICKNESS
        # Пол прицепа: всегда залит цветом #c3c3c3 как в content.html
        # Пол должен быть на дне коробки грузовика (Z=0)
        cm = CardMaker('floor')
        cm.setFrame(-self.truck_width/2, self.truck_width/2, -self.truck_depth/2, self.truck_depth/2)
        self.floor = self.app.render.attachNewNode(cm.generate())
        # Пол на дне коробки (Z=0), как на картинке
        self.floor.setPos(0, 0, 0)
        self.floor.setP(-90)  # Поворачиваем горизонтально
        # Сплошная заливка, без сетки/проволоки
        self.floor.setTransparency(TransparencyAttrib.MNone)
        self.floor.setColor(*FLOOR_COLOR)
        self.floor.setTwoSided(True)

    def _create_ground(self):
        cm = CardMaker('ground')
        cm.setFrame(-2400, 2400, -2400, 2400)
        self.ground = self.app.render.attachNewNode(cm.generate())
        self.ground.setP(-90)
        self.ground.setTransparency(TransparencyAttrib.MAlpha)
        self.ground.setColor(0.2, 0.2, 0.2, 0.0)

    def set_tent_alpha(self, a: float):
        # Map alpha to closed/open state and apply
        self.tent_closed = a >= 0.29
        self._apply_tent_state()

    def set_tent_closed(self, closed: bool):
        self.tent_closed = closed
        self._apply_tent_state()

    def _apply_tent_state(self):
        from config import TRUCK_CLOSED_COLOR
        if not (self.truck_faces and self.truck_edges_other and self.truck_edges_bottom):
            return
        # Always show edges; keep them black, with thicker bottom
        self.truck_edges_other.show()
        self.truck_edges_other.setColor(0, 0, 0, 0.5)
        self.truck_edges_bottom.show()
        self.truck_edges_bottom.setColor(0, 0, 0, 0.5)
        self.truck_edges_bottom.setRenderModeThickness(1.0)  # Тоньше как на картинке
        self.truck_edges_other.setRenderModeThickness(1.0)  # Тоньше как на картинке

        if self.tent_closed:
            r, g, b, _ = TRUCK_CLOSED_COLOR
            self.truck_faces.show()
            # Match web: alphaMatTruck ~ 0.3
            self.truck_faces.setTransparency(TransparencyAttrib.MAlpha)
            self.truck_faces.setColor(r, g, b, 0.3)
        else:
            self.truck_faces.hide()

    def resize(self, w: int, h: int, d: int):
        self.truck_width, self.truck_height, self.truck_depth = w, h, d
        # Rebuild truck geometry to avoid diagonals and keep sizes
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
        self._create_truck_box()
        if self.floor:
            self.floor.removeNode()
            self._create_floor()


