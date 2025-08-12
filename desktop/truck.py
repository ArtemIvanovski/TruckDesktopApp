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
        # Start box at configured lift height above ground
        from config import BOX_LIFT_HEIGHT
        lift = BOX_LIFT_HEIGHT
        # Фиксированная высота подъема нижних вершин: всегда 130 см
        fixed_lift = 130
        verts = [
            (-w/2, -d/2, lift + fixed_lift), (w/2, -d/2, lift + fixed_lift), (w/2, d/2, lift + fixed_lift), (-w/2, d/2, lift + fixed_lift),
            (-w/2, -d/2, h+lift + fixed_lift), (w/2, -d/2, h+lift + fixed_lift), (w/2, d/2, h+lift + fixed_lift), (-w/2, d/2, h+lift + fixed_lift)
        ]
        for v in verts:
            vw.addData3f(*v)

        # Faces (for closed tent fill) - solid areas without lines
        tri = GeomTriangles(Geom.UHStatic)
        # Exclude bottom face (0,1,2,3) so the bottom is controlled separately by floor
        faces = [(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        for a,b,c,d2 in faces:
            tri.addVertices(a,b,c); tri.addVertices(a,c,d2)
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
        node_edges_bottom.setPos(0, 0, 0)  # Position at origin (vertices already include lift)
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
        node_edges_other.setPos(0, 0, 0)  # Position at origin (vertices already include lift)
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

    def _create_bottom_face(self, vdata):
        """Create always-visible bottom face with 10cm thickness"""
        from config import FLOOR_COLOR, BOX_LIFT_HEIGHT
        
        # Create vertices for a thick bottom face (10cm = 0.1 units in our scale)
        bottom_thickness = 10  # 10cm
        w = self.truck_width
        d = self.truck_depth
        lift = BOX_LIFT_HEIGHT  # Use the same lift height as the box
        
        # Bottom face vertex data
        bottom_vdata = GeomVertexData('bottom_face', GeomVertexFormat.get_v3(), Geom.UHStatic)
        bottom_vdata.setNumRows(8)
        bottom_vw = GeomVertexWriter(bottom_vdata, 'vertex')
        
        # 8 vertices for thick bottom face - positioned at the bottom of the lifted box
        # Фиксированная высота подъема: всегда 130 см
        fixed_lift = 130
        bottom_level = lift + fixed_lift  # уровень дна грузовика
        bottom_verts = [
            (-w/2, -d/2, bottom_level),                    # 0: top front left (at box bottom level)
            (w/2, -d/2, bottom_level),                     # 1: top front right  
            (w/2, d/2, bottom_level),                      # 2: top back right
            (-w/2, d/2, bottom_level),                     # 3: top back left
            (-w/2, -d/2, bottom_level-bottom_thickness),  # 4: bottom front left (10cm below box)
            (w/2, -d/2, bottom_level-bottom_thickness),   # 5: bottom front right
            (w/2, d/2, bottom_level-bottom_thickness),    # 6: bottom back right 
            (-w/2, d/2, bottom_level-bottom_thickness)    # 7: bottom back left
        ]
        
        for v in bottom_verts:
            bottom_vw.addData3f(*v)
        
        # Create all 6 faces of the thick bottom
        bottom_tri = GeomTriangles(Geom.UHStatic)
        # Top face (0,1,2,3) - the one that touches the truck bottom
        bottom_tri.addVertices(0,1,2); bottom_tri.addVertices(0,2,3)
        # Bottom face (4,5,6,7)
        bottom_tri.addVertices(4,7,6); bottom_tri.addVertices(4,6,5)
        # Side faces
        bottom_tri.addVertices(0,4,5); bottom_tri.addVertices(0,5,1)  # front
        bottom_tri.addVertices(1,5,6); bottom_tri.addVertices(1,6,2)  # right
        bottom_tri.addVertices(2,6,7); bottom_tri.addVertices(2,7,3)  # back
        bottom_tri.addVertices(3,7,4); bottom_tri.addVertices(3,4,0)  # left
        
        bottom_geom = Geom(bottom_vdata)
        bottom_geom.addPrimitive(bottom_tri)
        
        self.bottom_face_node = self.app.render.attachNewNode(GeomNode("truck_bottom_face"))
        self.bottom_face_node.node().addGeom(bottom_geom)
        self.bottom_face_node.setPos(0, 0, 0)
        self.bottom_face_node.setTransparency(TransparencyAttrib.MAlpha)
        self.bottom_face_node.setTwoSided(True)
        self.bottom_face_node.clearRenderMode()
        self.bottom_face_node.setLightOff(1)
        # Set color like floor but fully opaque
        r, g, b, _ = FLOOR_COLOR
        self.bottom_face_node.setColor(r, g, b, 1.0)  # Fully opaque
        self.bottom_face_node.show()

    def _create_floor(self):
        from config import FLOOR_COLOR, FLOOR_THICKNESS, FLOOR_ALPHA, FLOOR_Z_OFFSET
        # Пол прицепа: всегда как в web (заливка #c3c3c3 с прозрачностью)
        cm = CardMaker('floor')
        cm.setFrame(-self.truck_width/2, self.truck_width/2, -self.truck_depth/2, self.truck_depth/2)
        self.floor = self.app.render.attachNewNode(cm.generate())
        self.floor.setPos(0, 0, FLOOR_Z_OFFSET)
        self.floor.setP(-90)
        self.floor.setTransparency(TransparencyAttrib.MAlpha)
        r,g,b,_ = FLOOR_COLOR
        self.floor.setColor(r, g, b, FLOOR_ALPHA)
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
        self.truck_edges_other.show()
        self.truck_edges_other.setColor(0, 0, 0, 0.5)
        self.truck_edges_bottom.show()
        self.truck_edges_bottom.setColor(0, 0, 0, 0.5)
        self.truck_edges_bottom.setRenderModeThickness(1.0)
        self.truck_edges_other.setRenderModeThickness(1.0)

        r, g, b, _ = TRUCK_CLOSED_COLOR
        alpha = 0.3 if self.tent_closed else 0.0
        self.truck_faces.setTransparency(TransparencyAttrib.MAlpha)
        self.truck_faces.clearRenderMode()
        self.truck_faces.setLightOff(1)
        self.truck_faces.setDepthWrite(False)
        self.truck_faces.setColor(r, g, b, alpha)

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
        if hasattr(self, 'bottom_face_node') and self.bottom_face_node:
            self.bottom_face_node.removeNode()
            self.bottom_face_node = None
        self._create_truck_box()
        if self.floor:
            self.floor.removeNode()
            self._create_floor()


