import logging
try:
    import panda3d_gltf
except Exception:
    pass
import math
import os
import sys
import traceback
from typing import Optional, Tuple


from direct.showbase.ShowBase import ShowBase
from panda3d.core import Material, Point3, Point2, Vec3, TextNode
from panda3d.core import (
    WindowProperties,
    AntialiasAttrib,
)

from config.config import BACKGROUND_COLOR, WHEEL_CABIN_HEIGHT
from core.camera import ArcCamera
from core.truck import TruckScene
from graphics.graphics_manager import GraphicsManager

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_gltf_support():
    try:
        logger.info("Доступные загрузчики моделей:")
        for ext in ['.glb', '.gltf', '.bam', '.egg']:
            logger.info(f"  {ext}: supported")
        return True
    except Exception as e:
        logger.error(f"Error checking glTF support: {e}")
        return False


class TruckLoadingApp(ShowBase):
    def __init__(self,
                 window_type: str = 'onscreen',
                 embed_parent_window: Optional[int] = None,
                 embed_size: Optional[Tuple[int, int]] = None,
                 enable_direct_gui: bool = True):
        self.graphics_manager = None
        try:
            logger.info("Starting application...")
            if embed_parent_window is not None or window_type == 'none':
                ShowBase.__init__(self, windowType='none')
            else:
                ShowBase.__init__(self)
            logger.info("ShowBase initialized")
            self.is_embedded = embed_parent_window is not None or window_type == 'none'

            if embed_parent_window is not None:
                logger.info("Opening embedded Panda3D window...")
                self._open_embedded_window(embed_parent_window, embed_size)
            else:
                logger.info("Setting up standalone window...")
                self._setup_window_standalone()
            logger.info("Window configured")

            logger.info("Setting up scene...")
            self.setup_scene()
            logger.info("Scene configured")

            logger.info("Setting up camera...")
            self.setup_camera()
            logger.info("Camera configured")

            logger.info("Setting up graphics...")
            self.setup_graphics()
            self.graphics_manager.apply_all_settings()
            logger.info("Graphics configured")

            logger.info("Setting up truck...")
            self.setup_truck()
            logger.info("Truck configured")

            logger.info("Checking format support...")
            check_gltf_support()
            logger.info("Format support check completed")

            logger.info("Loading models...")
            self.load_models()
            logger.info("Models loaded")

            logger.info("Setting up controls...")
            self.setup_controls()
            self.current_truck_index = 0
            self.trucks = []
            self.boxes = []
            self.selected_box = None
            self.is_shift_down = False
            logger.info("Controls configured")

            logger.info("Initializing first truck...")
            self.init_first_truck()
            logger.info("First truck initialized")

            logger.info("Initialization completed")
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            logger.error(traceback.format_exc())
            sys.exit(1)
        self.marking_size_factor = 0.20
        self.marking_padding_factor = 0.25
        self.marking_raster_scale = 3
        self.drag_active = False
        self._drag_target = None
        self._drag_plane_point = Point3(0, 0, 0)
        self._drag_plane_normal = Vec3(0, 1, 0)
        self._drag_offset = Vec3(0, 0, 0)
        self._drag_last_mouse = Point2(0, 0)
        self._drag_last_valid_pos = None
        self.ground_level = 135.0

    def create_box_wireframe(self, box_node, width, height, depth):
        from panda3d.core import LineSegs

        w, h, d = width / 2, height / 2, depth / 2

        lines = LineSegs()
        lines.setThickness(1.0)
        lines.setColor(0, 0, 0, 1)

        vertices = [
            (-w, -d, -h), (w, -d, -h), (w, d, -h), (-w, d, -h),
            (-w, -d, h), (w, -d, h), (w, d, h), (-w, d, h)
        ]

        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)
        ]

        for start_idx, end_idx in edges:
            start_pos = vertices[start_idx]
            end_pos = vertices[end_idx]
            lines.moveTo(*start_pos)
            lines.drawTo(*end_pos)

        wireframe_node = lines.create()
        wireframe_np = box_node.attachNewNode(wireframe_node)
        wireframe_np.setRenderModeThickness(2.0)
        wireframe_np.setColor(0, 0, 0, 1)
        wireframe_np.setLightOff(1)
        wireframe_np.setDepthOffset(2)

    def create_box_markings(self, box_node, box_data, width, height, depth):
        from panda3d.core import CardMaker, TransparencyAttrib
        import os
        from utils.setting_deploy import get_resource_path

        markings = box_data.get('cargo_markings', [])
        if not markings:
            return

        size = max(10.0, min(width, height, depth) * float(self.marking_size_factor))
        padding = size * float(self.marking_padding_factor)
        cols = 2

        def load_marking_texture(mark_name: str, px: int):
            tex = None
            for ext in (".png", ".jpg", ".jpeg"):
                rp = get_resource_path(f"assets/markings/{mark_name}{ext}")
                if os.path.exists(rp):
                    tex = self._load_texture_file(rp)
                    if tex:
                        return tex
            sp = get_resource_path(f"assets/markings/{mark_name}.svg")
            if os.path.exists(sp):
                tex = self.convert_svg_to_texture(sp, px, px)
            return tex

        faces = [
            ("front",  lambda c, r: (-width/2 + padding + size/2 + c*(size+padding), -depth/2 - 0.5,  height/2 - padding - size/2 - r*(size+padding)), (0,   0,   0)),
            ("back",   lambda c, r: ( width/2 - padding - size/2 - c*(size+padding),  depth/2 + 0.5,  height/2 - padding - size/2 - r*(size+padding)), (180, 0,   0)),
            ("left",   lambda c, r: (-width/2 - 0.5, -depth/2 + padding + size/2 + c*(size+padding), height/2 - padding - size/2 - r*(size+padding)), (90,  0,   0)),
            ("right",  lambda c, r: ( width/2 + 0.5,  depth/2 - padding - size/2 - c*(size+padding), height/2 - padding - size/2 - r*(size+padding)), (-90, 0,   0)),
            ("top",    lambda c, r: (-width/2 + padding + size/2 + c*(size+padding), 0,               depth/2 - padding - size/2 - r*(size+padding)), (0,  -90, 0)),
            ("bottom", lambda c, r: (-width/2 + padding + size/2 + c*(size+padding), 0,              -depth/2 + padding + size/2 + r*(size+padding)), (0,   90, 0)),
        ]

        per_face = min(len(markings), 4)
        raster_px = int(max(32, size * float(self.marking_raster_scale)))

        for face_name, pos_fn, hpr in faces:
            for i, marking in enumerate(markings[:per_face]):
                try:
                    texture = load_marking_texture(marking, raster_px)
                    if not texture:
                        continue
                    cm = CardMaker(f'marking_{face_name}_{marking}_{i}')
                    cm.setFrame(-size / 2, size / 2, -size / 2, size / 2)
                    node = box_node.attachNewNode(cm.generate())
                    node.setTexture(texture)
                    node.setTransparency(TransparencyAttrib.MAlpha)
                    node.setLightOff(1)
                    node.setDepthOffset(2)
                    col = i % cols
                    row = i // cols
                    x, y, z = pos_fn(col, row)
                    node.setPos(x, y, z)
                    node.setHpr(*hpr)
                    try:
                        from panda3d.core import Texture
                        texture.setMinfilter(Texture.FTLinearMipmapLinear)
                        texture.setMagfilter(Texture.FTLinear)
                        texture.setAnisotropicDegree(2)
                    except Exception:
                        pass
                except Exception as e:
                    logging.warning(f"[Marking] Failed '{marking}' on {face_name}: {e}")

    def convert_svg_to_texture(self, svg_path, width, height):
        from panda3d.core import Texture
        try:
            from PyQt5.QtSvg import QSvgRenderer
            from PyQt5.QtGui import QImage, QPainter
            from PyQt5.QtCore import QSize
            import hashlib
            import tempfile

            width = max(8, int(width))
            height = max(8, int(height))

            svg_abs = svg_path
            cache_dir = os.path.join(tempfile.gettempdir(), "truck_markings_cache")
            os.makedirs(cache_dir, exist_ok=True)
            key = f"{svg_abs}|{os.path.getmtime(svg_abs)}|{width}x{height}"
            digest = hashlib.md5(key.encode("utf-8")).hexdigest()
            png_path = os.path.join(cache_dir, f"{digest}.png")

            if not os.path.exists(png_path):
                renderer = QSvgRenderer(svg_abs)
                if not renderer.isValid():
                    raise RuntimeError("Invalid SVG")
                image = QImage(width, height, QImage.Format_ARGB32)
                image.fill(0)
                painter = QPainter(image)
                renderer.render(painter)
                painter.end()
                image.save(png_path, "PNG")

            panda_path = self._to_panda_path(png_path)
            logging.info(f"[SVG] Rasterized '{svg_abs}' -> '{png_path}', panda_path='{panda_path}'")

            tex = self.loader.loadTexture(panda_path)
            if tex and tex.getXSize() > 0 and tex.getYSize() > 0:
                tex.setFormat(Texture.FRgba)
                logging.info(f"[SVG] Loaded texture OK: {panda_path}")
                return tex
        except Exception as e:
            logging.warning(f"SVG rasterization failed, using fallback: {e}")

        marking_name = os.path.basename(svg_path).replace('.svg', '')
        return self.create_fallback_marking_texture(marking_name)

    def _to_panda_path(self, path: str) -> str:
        p = path.replace('\\', '/')
        if len(p) >= 2 and p[1] == ':':
            drive = p[0].lower()
            p = f"/{drive}{p[2:]}"
        return p

    def _load_texture_file(self, file_path: str):
        from panda3d.core import Texture
        try:
            panda_path = self._to_panda_path(file_path)
            tex = self.loader.loadTexture(panda_path)
            if tex and tex.getXSize() > 0 and tex.getYSize() > 0:
                tex.setFormat(Texture.FRgba)
                logging.info(f"[Texture] Loaded file texture: {panda_path}")
                return tex
            logging.warning(f"[Texture] Failed to load file texture: {panda_path}")
        except Exception as e:
            logging.warning(f"[Texture] Exception loading '{file_path}': {e}")
        return None

    def create_fallback_marking_texture(self, marking_name):
        from panda3d.core import Texture, PNMImage

        # Создаем простые цветные текстуры для маркировок
        marking_colors = {
            'fragile': (1.0, 0.0, 0.0),  # красный
            'this_way_up': (0.0, 1.0, 0.0),  # зеленый
            'no_stack': (1.0, 1.0, 0.0),  # желтый
            'keep_dry': (0.0, 0.0, 1.0),  # синий
            'center_gravity': (1.0, 0.5, 0.0),  # оранжевый
            'alcohol': (0.5, 0.0, 1.0),  # фиолетовый
            'no_hooks': (1.0, 0.0, 1.0),  # пурпурный
            'temperature': (0.0, 1.0, 1.0)  # циан
        }

        color = marking_colors.get(marking_name, (0.5, 0.5, 0.5))
        r, g, b = color

        # Создаем изображение с цветным кругом
        pnm_image = PNMImage(64, 64, 4)  # 4 канала (RGBA)
        
        # Заполняем прозрачным фоном (правильно вызываем fill для RGBA)
        for y in range(64):
            for x in range(64):
                pnm_image.setXelA(x, y, 0, 0, 0, 0)  # прозрачный фон

        # Рисуем цветной круг
        center_x, center_y = 32, 32
        radius = 25
        
        for y in range(64):
            for x in range(64):
                dx = x - center_x
                dy = y - center_y
                distance = (dx * dx + dy * dy) ** 0.5
                
                if distance <= radius:
                    # Внутри круга - устанавливаем цвет маркировки
                    pnm_image.setXelA(x, y, r, g, b, 1.0)
                elif distance <= radius + 2:
                    # Граница круга - черная обводка
                    pnm_image.setXelA(x, y, 0, 0, 0, 1.0)

        texture = Texture()
        texture.load(pnm_image)
        texture.setFormat(Texture.FRgba)
        
        logging.info(f"Created fallback texture for marking: {marking_name} with color {color}")
        return texture

    def _setup_window_standalone(self):
        self.windowType = 'onscreen'
        props = WindowProperties()
        props.setTitle("Загрузка грузовика")
        props.setSize(1280, 800)
        self.win.requestProperties(props)
        self.setBackgroundColor(*BACKGROUND_COLOR)
        try:
            if not getattr(self, 'mouseWatcherNode', None):
                self.setupMouse(self.win)
        except Exception:
            pass

    def _open_embedded_window(self, parent_handle: int, size: Optional[Tuple[int, int]]):
        props = WindowProperties()
        props.setParentWindow(int(parent_handle))
        props.setOrigin(0, 0)
        if size:
            w, h = size
            props.setSize(int(w), int(h))
        else:
            props.setSize(1280, 800)
        logger.info(f"[Panda] openWindow in parent={parent_handle}, size={props.getXSize()}x{props.getYSize()}")
        self.win = self.openWindow(props=props)
        self.setBackgroundColor(*BACKGROUND_COLOR)
        try:
            if not getattr(self, 'mouseWatcherNode', None):
                self.setupMouse(self.win)
        except Exception:
            pass

    def resize_window(self, width: int, height: int):
        if self.win:
            props = WindowProperties()
            props.setOrigin(0, 0)
            props.setSize(int(width), int(height))
            self.win.requestProperties(props)

    def create_3d_box_from_data(self, box_data, world_pos=None):
        """Создание 3D коробки точно как в content.html"""
        from panda3d.core import (Material, Vec4, GeomNode, Geom, GeomVertexFormat,
                                  GeomVertexData, GeomVertexWriter, GeomTriangles)
        import random

        if world_pos is None:
            world_pos = (0, 0, 0)

        width = box_data['width']
        height = box_data['height']
        depth = box_data['depth']
        label = box_data.get('label', f'PO#{len(getattr(self, "scene_boxes", []))}')
        weight = box_data.get('weight', 1.0)

        # Создаем узел коробки как в content.html (randomBox[mCyrcle])
        box_id = len(getattr(self, "scene_boxes", []))
        box_node = self.render.attachNewNode(f"randomBox{box_id}")
        
        # Теги как в content.html
        box_node.setPythonTag('box_id', box_id)
        box_node.setPythonTag('truck_index', None)
        box_node.setPythonTag('is_shift', False)
        box_node.setPythonTag('is_rotated', False)
        box_node.setPythonTag('weight', weight)

        # Создаем геометрию коробки
        vdata = GeomVertexData('box', GeomVertexFormat.get_v3n3(), Geom.UHStatic)
        vdata.setNumRows(24)
        vwriter = GeomVertexWriter(vdata, 'vertex')
        nwriter = GeomVertexWriter(vdata, 'normal')

        self.create_box_geometry(vwriter, nwriter, width, height, depth)

        geom = Geom(vdata)
        tri = GeomTriangles(Geom.UHStatic)

        for i in range(0, 24, 4):
            tri.addVertices(i, i + 1, i + 2)
            tri.addVertices(i, i + 2, i + 3)

        geom.addPrimitive(tri)
        geom_node = GeomNode('box_geom')
        geom_node.addGeom(geom)

        box_geom_np = box_node.attachNewNode(geom_node)

        import json
        
        box_color_key = json.dumps([width, depth, height])
        
        if not hasattr(self, 'box_colors'):
            self.box_colors = {}
        
        if box_color_key not in self.box_colors:
            hash_val = hash(box_color_key) & 0x7FFFFFFF
            random.seed(hash_val)
            new_color = (random.random(), random.random(), random.random())
            self.box_colors[box_color_key] = new_color
        
        box_color = self.box_colors[box_color_key]
        r, g, b = box_color
        
        material = Material()
        material.setDiffuse(Vec4(0, 0, 0, 1.0))
        material.setSpecular(Vec4(0, 0, 0, 1.0))
        material.setEmission(Vec4(r, g, b, 1.0))
        material.setShininess(1.0)
        
        box_geom_np.setMaterial(material)
        box_geom_np.setLightOff(1)
        box_geom_np.setColor(r, g, b, 1.0)
        box_geom_np.clearRenderMode()
        box_geom_np.setColorScale(1, 1, 1, 1)

        self.create_box_wireframe(box_node, width, height, depth)
        self.create_box_text_labels_static(box_node, box_data, width, height, depth)

        from panda3d.core import CollisionNode, CollisionBox
        collision_node = CollisionNode('box_collision')
        collision_node.addSolid(CollisionBox(Point3(0, 0, 0), width/2, depth/2, height/2))
        collision_node.setFromCollideMask(0)
        collision_node.setIntoCollideMask(1)
        collision_np = box_geom_np.attachNewNode(collision_node)

        world_x, world_y, world_z = world_pos
        final_pos = self.find_non_overlapping_position(world_x, world_y, world_z, width, height, depth)
        box_node.setPos(final_pos[0], final_pos[1], final_pos[2] + height / 2)

        box_node.setPythonTag('box_data', box_data)

        if not hasattr(self, 'scene_boxes'):
            self.scene_boxes = []
        self.scene_boxes.append(box_node)

        try:
            self.create_box_markings(box_node=box_node, box_data=box_data, width=width, height=height, depth=depth)
        except Exception as e:
            logging.warning(f"Could not create markings for {label}: {e}")
        
        logging.info(f"Successfully dropped box: {label}")
        try:
            self.update_side_loads()
        except Exception:
            pass
        return box_node
    
    def find_non_overlapping_position(self, start_x, start_y, start_z, box_width, box_height, box_depth):
        """Умный алгоритм размещения коробок перед грузовиком в сетке"""
        
        min_gap = 20
        grid_step = 80
        
        truck_front_y = self.truck_depth / 2
        placement_zone_y_start = truck_front_y + 150
        placement_zone_y_end = truck_front_y + 1000
        placement_zone_x_left = -800
        placement_zone_x_right = 800
        ground_level = 135
        
        if not hasattr(self, 'scene_boxes') or not self.scene_boxes:
            safe_x = max(-400, min(400, start_x))
            safe_y = placement_zone_y_start + 100
            safe_z = ground_level
            return (safe_x, safe_y, safe_z)
            
        max_stack_levels = 3
        test_positions = []
        
        for level in range(max_stack_levels):
            level_z = ground_level + level * (150 + min_gap)
            
            x_positions = list(range(int(placement_zone_x_left), int(placement_zone_x_right) + 1, grid_step))
            y_positions = list(range(int(placement_zone_y_start), int(placement_zone_y_end) + 1, grid_step))
            
            grid_positions = []
            for x in x_positions:
                for y in y_positions:
                    distance = math.sqrt((x - start_x)**2 + (y - start_y)**2)
                    grid_positions.append((distance, x, y, level_z))
            
            grid_positions.sort(key=lambda pos: pos[0])
            
            for distance, x, y, z in grid_positions:
                test_positions.append((x, y, z))
        
        for i, (test_x, test_y, test_z) in enumerate(test_positions):
            if self.is_position_free(test_x, test_y, test_z, box_width, box_height, box_depth, min_gap):
                return (test_x, test_y, test_z)
        
        logging.warning("No space in primary placement zone, searching in extended area")
        extended_positions = []
        
        for level in range(max_stack_levels):
            level_z = ground_level + level * (150 + min_gap)
            
            for radius in range(grid_step, 1500, grid_step):
                for angle_deg in range(0, 360, 30):
                    angle = math.radians(angle_deg)
                    test_x = start_x + radius * math.cos(angle)
                    test_y = start_y + radius * math.sin(angle)
                    
                    if test_y > truck_front_y:
                        extended_positions.append((test_x, test_y, level_z))
        
        for test_x, test_y, test_z in extended_positions[:50]:
            if self.is_position_free(test_x, test_y, test_z, box_width, box_height, box_depth, min_gap):
                return (test_x, test_y, test_z)
        
        fallback_x = placement_zone_x_right + 200 + box_width
        fallback_y = placement_zone_y_start + 200
        fallback_z = ground_level
        logging.warning(f"Using fallback position: ({fallback_x:.1f}, {fallback_y:.1f}, {fallback_z:.1f})")
        return (fallback_x, fallback_y, fallback_z)

    def is_position_free(self, test_x, test_y, test_z, box_width, box_height, box_depth, min_gap):
        """Проверяет, свободна ли позиция для размещения коробки с учетом минимального зазора"""
        
        new_min_x = test_x - box_width / 2
        new_max_x = test_x + box_width / 2
        new_min_y = test_y - box_depth / 2
        new_max_y = test_y + box_depth / 2
        new_min_z = test_z
        new_max_z = test_z + box_height
        
        for existing_box in self.scene_boxes:
            if existing_box.isEmpty():
                continue
                
            existing_pos = existing_box.getPos()
            existing_data = existing_box.getPythonTag('box_data')
            if not existing_data:
                continue
            
            existing_width = existing_data.get('width', 100)
            existing_height = existing_data.get('height', 100)  
            existing_depth = existing_data.get('depth', 100)
            
            exist_min_x = existing_pos.x - existing_width / 2
            exist_max_x = existing_pos.x + existing_width / 2
            exist_min_y = existing_pos.y - existing_depth / 2
            exist_max_y = existing_pos.y + existing_depth / 2
            exist_min_z = existing_pos.z - existing_height / 2
            exist_max_z = existing_pos.z + existing_height / 2
            
            if (new_max_x + min_gap > exist_min_x and new_min_x - min_gap < exist_max_x and
                new_max_y + min_gap > exist_min_y and new_min_y - min_gap < exist_max_y and
                new_max_z + min_gap > exist_min_z and new_min_z - min_gap < exist_max_z):
                return False
        
        return True

    def create_box_geometry(self, vwriter, nwriter, width, height, depth):
        w, h, d = width / 2, height / 2, depth / 2

        vertices = [
            # Front face
            (-w, -d, -h), (w, -d, -h), (w, -d, h), (-w, -d, h),
            # Back face
            (w, d, -h), (-w, d, -h), (-w, d, h), (w, d, h),
            # Left face
            (-w, d, -h), (-w, -d, -h), (-w, -d, h), (-w, d, h),
            # Right face
            (w, -d, -h), (w, d, -h), (w, d, h), (w, -d, h),
            # Top face
            (-w, -d, h), (w, -d, h), (w, d, h), (-w, d, h),
            # Bottom face
            (-w, d, -h), (w, d, -h), (w, -d, -h), (-w, -d, -h)
        ]

        normals = [
            (0, -1, 0), (0, -1, 0), (0, -1, 0), (0, -1, 0),
            (0, 1, 0), (0, 1, 0), (0, 1, 0), (0, 1, 0),
            (-1, 0, 0), (-1, 0, 0), (-1, 0, 0), (-1, 0, 0),
            (1, 0, 0), (1, 0, 0), (1, 0, 0), (1, 0, 0),
            (0, 0, 1), (0, 0, 1), (0, 0, 1), (0, 0, 1),
            (0, 0, -1), (0, 0, -1), (0, 0, -1), (0, 0, -1)
        ]

        for i, (vertex, normal) in enumerate(zip(vertices, normals)):
            vwriter.addData3f(*vertex)
            nwriter.addData3f(*normal)



    def create_box_text_labels_static(self, box_node, box_data, width, height, depth):
        """Создание надписей на коробке на всех гранях с размерами"""
        from panda3d.core import TextNode
        
        label = box_data['label']
        main_text_scale = width * 0.080
        
        # Загружаем жирный шрифт
        font = None
        try:
            from utils.setting_deploy import get_resource_path
            import os
            font_path = get_resource_path('assets/fonts/NotoSans-Bold.ttf')
            if os.path.exists(font_path):
                font_path_unix = font_path.replace('\\', '/').replace('E:/', '/e/')
                font = self.loader.loadFont(font_path_unix)
        except:
            pass
        
        # Основные надписи на всех 6 гранях
        faces = [
            ("front", (0, -depth/2 - 2, 0), (0, 0, 0)),
            ("back", (0, depth/2 + 2, 0), (180, 0, 0)),
            ("left", (-width/2 - 2, 0, 0), (90, 0, 0)),
            ("right", (width/2 + 2, 0, 0), (-90, 0, 0)),
            ("top", (0, 0, height/2 + 2), (0, -90, 0)),
            ("bottom", (0, 0, -height/2 - 2), (0, 90, 0))
        ]
        
        for face_name, pos, rotation in faces:
            face_text_node = TextNode(f'main_text_{face_name}')
            face_text_node.setText(label)
            face_text_node.setAlign(TextNode.ACenter)
            if font:
                face_text_node.setFont(font)
            
            face_text_np = box_node.attachNewNode(face_text_node)
            face_text_np.setScale(main_text_scale)
            face_text_np.setPos(*pos)
            face_text_np.setHpr(*rotation)
            face_text_np.setColor(0, 0, 0, 1)
            face_text_np.setLightOff(1)
            face_text_np.setDepthOffset(5)
        
        # Размеры на соответствующих гранях
        dimension_text_scale = main_text_scale * 0.7
        
        # Ширина на левой и правой гранях
        width_positions = [
            ("left_width", (-width/2 - 5, 0, -height/3), (90, 0, 0)),
            ("right_width", (width/2 + 5, 0, -height/3), (-90, 0, 0))
        ]
        
        for dim_name, pos, rotation in width_positions:
            width_text_node = TextNode(dim_name)
            width_text_node.setText(f"W:{int(width)}")
            width_text_node.setAlign(TextNode.ACenter)
            if font:
                width_text_node.setFont(font)
            
            width_text_np = box_node.attachNewNode(width_text_node)
            width_text_np.setScale(dimension_text_scale)
            width_text_np.setPos(*pos)
            width_text_np.setHpr(*rotation)
            width_text_np.setColor(0, 0, 0, 1)
            width_text_np.setLightOff(1)
            width_text_np.setDepthOffset(5)
        
        # Высота на передней и задней гранях
        height_positions = [
            ("front_height", (-width/3, -depth/2 - 5, 0), (0, 0, 0)),
            ("back_height", (-width/3, depth/2 + 5, 0), (180, 0, 0))
        ]
        
        for dim_name, pos, rotation in height_positions:
            height_text_node = TextNode(dim_name)
            height_text_node.setText(f"H:{int(height)}")
            height_text_node.setAlign(TextNode.ACenter)
            if font:
                height_text_node.setFont(font)
            
            height_text_np = box_node.attachNewNode(height_text_node)
            height_text_np.setScale(dimension_text_scale)
            height_text_np.setPos(*pos)
            height_text_np.setHpr(*rotation)
            height_text_np.setColor(0, 0, 0, 1)
            height_text_np.setLightOff(1)
            height_text_np.setDepthOffset(5)
        
        # Глубина на передней и задней гранях
        depth_positions = [
            ("front_depth", (width/3, -depth/2 - 5, 0), (0, 0, 0)),
            ("back_depth", (width/3, depth/2 + 5, 0), (180, 0, 0))
        ]
        
        for dim_name, pos, rotation in depth_positions:
            depth_text_node = TextNode(dim_name)
            depth_text_node.setText(f"D:{int(depth)}")
            depth_text_node.setAlign(TextNode.ACenter)
            if font:
                depth_text_node.setFont(font)
            
            depth_text_np = box_node.attachNewNode(depth_text_node)
            depth_text_np.setScale(dimension_text_scale)
            depth_text_np.setPos(*pos)
            depth_text_np.setHpr(*rotation)
            depth_text_np.setColor(0, 0, 0, 1)
            depth_text_np.setLightOff(1)
            depth_text_np.setDepthOffset(5)

    def remove_material_specular(self, model):
        if not model or model.isEmpty():
            return

        if self.graphics_manager:
            enabled = self.graphics_manager.settings.enable_specular
            self.graphics_manager._update_model_specular(model, enabled)

    def load_models(self):
        from utils.setting_deploy import get_resource_path
        from panda3d.core import getModelPath
        logger.info("Starting models loading...")

        # Добавляем путь к assets/models в model path Panda3D
        models_dir = get_resource_path("assets/models")
        if os.path.exists(models_dir):
            # Конвертируем Windows путь в Unix стиль для Panda3D
            models_dir_unix = models_dir.replace('\\', '/').replace('E:/', '/e/')
            getModelPath().appendPath(models_dir_unix)
            logger.info(f"Added to model path: {models_dir_unix}")
            logger.info(f"Current model path: {getModelPath()}")

        # Проверяем доступные форматы моделей в правильном порядке приоритета
        model_formats = [
            ("weel.obj", "lorry.obj"),  # OBJ формат (надежный)
            ("weel.glb", "lorry.glb"),  # GLB формат (fallback)
        ]

        wheel_path = None
        lorry_path = None

        # Ищем доступные файлы моделей с использованием get_resource_path
        for wheel_file, lorry_file in model_formats:
            wheel_full_path = get_resource_path(f"assets/models/{wheel_file}")
            lorry_full_path = get_resource_path(f"assets/models/{lorry_file}")
            
            if os.path.exists(wheel_full_path) and os.path.exists(lorry_full_path):
                wheel_path = wheel_file  # Используем относительный путь для Panda3D
                lorry_path = lorry_file  # Используем относительный путь для Panda3D
                logger.info(f"Found model files: {wheel_full_path}, {lorry_full_path}")
                logger.info(f"Will load using relative paths: {wheel_path}, {lorry_path}")
                break

        if not wheel_path:
            logger.warning("No model files found, using fallback paths")
            wheel_path = "weel.glb"
            lorry_path = "lorry.glb"

        self.wheel_model = None
        try:
            logger.info(f"Loading wheel model from {wheel_path}...")

            if wheel_path.endswith('.obj'):
                mtl_path = wheel_path.replace('.obj', '.mtl')
                if os.path.exists(mtl_path):
                    logger.info(f"Found wheel material file: {mtl_path}")
                else:
                    logger.warning(f"Wheel material file not found: {mtl_path}")

            self.wheel_model = self.loader.loadModel(wheel_path)

            if self.wheel_model and not self.wheel_model.isEmpty():
                logger.info("Wheel model loaded successfully!")
            else:
                logger.error("Wheel model is empty or invalid")
                self.wheel_model = None
        except Exception as e:
            logger.error(f"Error loading wheel model: {e}")

        if self.wheel_model and not self.wheel_model.isEmpty():
            logger.info("Configuring wheel model...")

            self.box_weel_move = self.render.attachNewNode("boxWeelMove")
            truck_long = max(1000, self.truck_width)
            weel_position = 50
            self.box_weel_move.setPos(weel_position - truck_long / 2, WHEEL_CABIN_HEIGHT, 0)

            self.wheel_model.reparentTo(self.box_weel_move)
            self.wheel_model.setScale(100, 100, 100)
            self.wheel_model.setTwoSided(True)
            self.wheel_model.setHpr(0, 90, 0)
            self.wheel_model.setPos(0, 125, 0)

            materials = self.wheel_model.findAllMaterials()
            if materials:
                logger.info(f"Wheel has {len(materials)} materials, keeping original")
            else:
                logger.warning("No materials found for wheel, creating default")
                wheel_mat = Material()
                wheel_mat.setShininess(12.8)
                wheel_mat.setSpecular((0.3, 0.3, 0.3, 1))
                wheel_mat.setDiffuse((0.2, 0.2, 0.2, 1))
                wheel_mat.setEmission((0.36, 0.36, 0.36, 1))
                self.wheel_model.setMaterial(wheel_mat, 1)
            self.remove_material_specular(self.wheel_model)
            logger.info("Wheel configured successfully")

        self.lorry_model = None
        try:
            logger.info(f"Loading cabin model from {lorry_path}...")

            if lorry_path.endswith('.obj'):
                mtl_path = lorry_path.replace('.obj', '.mtl')
                if os.path.exists(mtl_path):
                    logger.info(f"Found cabin material file: {mtl_path}")
                else:
                    logger.warning(f"Cabin material file not found: {mtl_path}")

            self.lorry_model = self.loader.loadModel(lorry_path)

            if self.lorry_model and not self.lorry_model.isEmpty():
                logger.info("Cabin model loaded successfully!")
            else:
                logger.error("Cabin model is empty or invalid")
                self.lorry_model = None
        except Exception as e:
            logger.error(f"Error loading cabin model: {e}")

        if self.lorry_model and not self.lorry_model.isEmpty():
            logger.info("Configuring cabin model...")

            self.box_lorry_move = self.render.attachNewNode("boxLorryMove")
            truck_long = max(1000, self.truck_width)
            lorry_position = -400
            self.box_lorry_move.setPos(lorry_position + truck_long / 2, WHEEL_CABIN_HEIGHT, 0)

            self.lorry_model.reparentTo(self.box_lorry_move)
            self.lorry_model.setScale(100, 100, 100)
            self.lorry_model.setTwoSided(True)
            self.lorry_model.setHpr(0, 90, 0)
            self.lorry_model.setPos(0, 125, 0)

            materials = self.lorry_model.findAllMaterials()
            if materials:
                logger.info(f"Cabin has {len(materials)} materials, keeping original")
            else:
                logger.warning("No materials found for cabin, creating default")
                cabin_mat = Material()
                cabin_mat.setShininess(12.8)
                cabin_mat.setSpecular((0.3, 0.3, 0.3, 1))
                cabin_mat.setDiffuse((0.3, 0.35, 0.4, 1))
                cabin_mat.setEmission((0.54, 0.63, 0.72, 1))
                self.lorry_model.setMaterial(cabin_mat, 1)
            self.remove_material_specular(self.lorry_model)
            logger.info("Cabin configured successfully")

        logger.info("Models loading completed")

        if self.graphics_manager:
            logger.info("Applying saved graphics settings to loaded models...")
            self.graphics_manager.apply_all_settings()

    def setup_scene(self):
        self.render.setAntialias(AntialiasAttrib.MMultisample)
        self.setBackgroundColor(*BACKGROUND_COLOR)
        self.disableMouse()

    def setup_camera(self):
        self.camLens.setFov(45.8)
        self.arc = ArcCamera(self)
        self.taskMgr.add(self.arc.tick, "camera_update")

    def setup_graphics(self):
        self.graphics_manager = GraphicsManager(self)
        self.graphics_manager.setup_lighting()

    def setup_truck(self):
        self.scene = TruckScene(self)
        self.scene.build()
        self.truck_width = self.scene.truck_width
        self.truck_height = self.scene.truck_height
        self.truck_depth = self.scene.truck_depth

    def set_tent_alpha(self, alpha: float):
        self.scene.set_tent_alpha(alpha)

    def switch_truck(self, t_w: int, t_h: int, t_d: int):
        self.truck_width = t_w
        self.truck_height = t_h
        self.truck_depth = t_d
        self.scene.resize(t_w, t_h, t_d)

        truck_long = max(1000, t_w)
        weel_position = 50
        lorry_position = -400

        if hasattr(self, 'box_weel_move'):
            self.box_weel_move.setPos(weel_position - truck_long / 2, WHEEL_CABIN_HEIGHT, 0)
        if hasattr(self, 'box_lorry_move'):
            self.box_lorry_move.setPos(lorry_position + truck_long / 2, WHEEL_CABIN_HEIGHT, 0)

        # Preserve tent open/close state across size changes
        if hasattr(self.scene, 'tent_closed'):
            self.scene.set_tent_closed(self.scene.tent_closed)

    def set_background_color(self, r: float, g: float, b: float):
        """Установить цвет фона"""
        if self.graphics_manager:
            self.graphics_manager.set_background_color(r, g, b)

    def set_specular_enabled(self, enabled: bool):
        """Включить/выключить блики"""
        if self.graphics_manager:
            self.graphics_manager.set_specular_enabled(enabled)

    def set_truck_color(self, r: float, g: float, b: float):
        """Установить цвет тягача"""
        if self.graphics_manager:
            self.graphics_manager.set_truck_color(r, g, b)

    def set_lighting_intensity(self, main_intensity: float, fill_intensity: float):
        if self.graphics_manager:
            self.graphics_manager.set_light_intensity(main_intensity, fill_intensity)

    def set_lighting_mode(self, mode: str):
        if self.graphics_manager:
            self.graphics_manager.set_lighting_mode(mode)

    def setup_controls(self):
        self.accept("mouse1", self.on_left_down)
        self.accept("mouse1-up", self.on_left_up)
        self.accept("mouse3", self.arc.on_right_down)
        self.accept("mouse3-up", self.arc.on_right_up)
        self.accept("wheel_up", self.on_wheel_in)
        self.accept("wheel_down", self.on_wheel_out)
        
        self.accept("shift", self.shift_down)
        self.accept("shift-up", self.shift_up)
        
        self.accept("r", self.on_r_key)
        self.accept("к", self.on_r_key)
        self.accept("backspace", self.on_backspace_key_direct)
        self.accept("delete", self.delete_selected_box)
        # Изменили enter на H и русское Р для возврата коробки в список
        self.accept("h", self.on_hide_box_key_direct)
        self.accept("р", self.on_hide_box_key_direct)  # русское Р
        self.accept("q", self.on_r_key)
        self.accept("w", lambda: self.on_rotate_key(0, 90))
        self.accept("s", lambda: self.on_rotate_key(0, -90))
        self.accept("a", lambda: self.on_rotate_key(-90, 0))
        self.accept("d", lambda: self.on_rotate_key(90, 0))
        self.accept("ц", lambda: self.on_rotate_key(0, 90))
        self.accept("ы", lambda: self.on_rotate_key(0, -90))
        self.accept("ф", lambda: self.on_rotate_key(-90, 0))
        self.accept("в", lambda: self.on_rotate_key(90, 0))
        self.accept("space", lambda: logging.info("[KeyPress] Space key pressed"))
        self.accept("escape", lambda: logging.info("[KeyPress] Escape key pressed"))
        
        self.hovered_box = None
        self.deleted_boxes = []
        logging.info("[Controls] Adding mouse_hover_task to taskMgr")
        self.taskMgr.add(self.mouse_hover_task, "mouse_hover_task")
        logging.info("[Controls] Controls setup completed with hover tracking and key handlers")

    def focus_on_truck(self):
        self.arc.target = Point3(0, 0, 200)
        self.arc.radius = 1500
        self.arc.update()

    def reset_camera_view(self):
        self.arc.target = Point3(0, 0, 0)
        self.arc.radius = 3000  # Соответствует начальному расстоянию
        self.arc.alpha = math.pi / 2
        self.arc.beta = math.pi / 4
        self.arc.update()

    def shift_down(self):
        self.is_shift_down = True

    def shift_up(self):
        self.is_shift_down = False
    
    def on_wheel_in(self):
        if getattr(self, 'drag_active', False):
            try:
                step = 100.0
                cam_forward = self.camera.getQuat(self.render).getForward()
                self._drag_plane_point = self._drag_plane_point + cam_forward * (-step)
                logging.info(f"[Drag] Wheel in: plane_point={self._drag_plane_point}")
            except Exception:
                pass
            return
        self.arc.on_wheel_in()

    def on_wheel_out(self):
        if getattr(self, 'drag_active', False):
            step = 100.0
            cam_forward = self.camera.getQuat(self.render).getForward()
            self._drag_plane_point = self._drag_plane_point + cam_forward * (step)
            logging.info(f"[Drag] Wheel out: plane_point={self._drag_plane_point}")
            return
        self.arc.on_wheel_out()

    def on_right_down(self):
        self.drag_active = False
        if not self.mouseWatcherNode.hasMouse():
            return
        mouse_x = self.mouseWatcherNode.getMouseX()
        mouse_y = self.mouseWatcherNode.getMouseY()
        from panda3d.core import CollisionTraverser, CollisionNode, CollisionRay, CollisionHandlerQueue
        picker = CollisionTraverser()
        pq = CollisionHandlerQueue()
        pickerNode = CollisionNode('moveRay')
        pickerNP = self.camera.attachNewNode(pickerNode)
        pickerNode.setFromCollideMask(1)
        pickerNode.setIntoCollideMask(0)
        ray = CollisionRay()
        pickerNode.addSolid(ray)
        picker.addCollider(pickerNP, pq)
        ray.setFromLens(self.camNode, mouse_x, mouse_y)
        picker.traverse(self.render)
        target = None
        if pq.getNumEntries() > 0:
            pq.sortEntries()
            for i in range(pq.getNumEntries()):
                picked_obj = pq.getEntry(i).getIntoNodePath()
                cur = picked_obj
                while cur:
                    if cur.getName().startswith('randomBox'):
                        target = cur
                        break
                    cur = cur.getParent()
                if target:
                    break
        pickerNP.removeNode()
        if target is None:
            return
        self.set_selected_box(target)
        self.drag_active = True
        self._drag_target = target
        self._drag_last_mouse = Point2(mouse_x, mouse_y)
        self._drag_plane_point = target.getPos(self.render)
        self._drag_plane_normal = self.camera.getQuat(self.render).getForward()
        pick_point = self._ray_plane_intersection(mouse_x, mouse_y, self._drag_plane_point, self._drag_plane_normal)
        if pick_point is None:
            pick_point = self._drag_plane_point
        self._drag_offset = self._drag_plane_point - pick_point
        logging.info(f"[Drag] Start target={target.getName()} plane_point={self._drag_plane_point} normal={self._drag_plane_normal} offset={self._drag_offset}")
        self.taskMgr.add(self._drag_task, "box_drag_task")

    def on_right_up(self):
        if getattr(self, 'drag_active', False):
            self.drag_active = False
            self._drag_target = None
            self.taskMgr.remove("box_drag_task")
        else:
            self.arc.on_right_up()

    def _drag_task(self, task):
        try:
            if not getattr(self, 'drag_active', False) or not self._drag_target or self._drag_target.isEmpty():
                return task.done
            if not self.mouseWatcherNode.hasMouse():
                return task.cont
            mx = self.mouseWatcherNode.getMouseX()
            my = self.mouseWatcherNode.getMouseY()
            hit = self._ray_plane_intersection(mx, my, self._drag_plane_point, self._drag_plane_normal)
            if hit is not None:
                new_pos = hit + self._drag_offset
                self._drag_target.setPos(self.render, new_pos)
                try:
                    self.update_side_loads()
                except Exception:
                    pass
            self._drag_last_mouse = Point2(mx, my)
            return task.cont
        except Exception as e:
            logging.error(f"[Drag] Error: {e}")
            return task.done

    def _ray_plane_intersection(self, mouse_x: float, mouse_y: float, plane_point: Point3, plane_normal: Vec3):
        try:
            from panda3d.core import LPoint3f, LVector3f
            near = LPoint3f()
            far = LPoint3f()
            if not self.camLens.extrude(Point2(mouse_x, mouse_y), near, far):
                return None
            p0 = self.render.getRelativePoint(self.camera, near)
            p1 = self.render.getRelativePoint(self.camera, far)
            ray_dir = (p1 - p0)
            denom = plane_normal.dot(ray_dir)
            if abs(denom) < 1e-6:
                return None
            t = plane_normal.dot(plane_point - p0) / denom
            if t < 0:
                return None
            hit = p0 + ray_dir * t
            return hit
        except Exception as e:
            logging.error(f"[Drag] Ray-plane error: {e}")
            return None

    def _is_position_allowed(self, box_np, new_center_world: Point3) -> bool:
        try:
            box_data = box_np.getPythonTag('box_data')
            if not box_data:
                return False
            w = float(box_data.get('width', 100))
            h = float(box_data.get('height', 100))
            d = float(box_data.get('depth', 100))
            min_z = new_center_world.z - h / 2.0
            if min_z < self.ground_level:
                return False
            half_w = w / 2.0
            half_d = d / 2.0
            half_h = h / 2.0
            new_min_x = new_center_world.x - half_w
            new_max_x = new_center_world.x + half_w
            new_min_y = new_center_world.y - half_d
            new_max_y = new_center_world.y + half_d
            new_min_z = new_center_world.z - half_h
            new_max_z = new_center_world.z + half_h
            for other in getattr(self, 'scene_boxes', []):
                if other is box_np or other.isEmpty():
                    continue
                data = other.getPythonTag('box_data')
                if not data:
                    continue
                ow = float(data.get('width', 100))
                oh = float(data.get('height', 100))
                od = float(data.get('depth', 100))
                op = other.getPos(self.render)
                o_min_x = op.x - ow / 2.0
                o_max_x = op.x + ow / 2.0
                o_min_y = op.y - od / 2.0
                o_max_y = op.y + od / 2.0
                o_min_z = op.z - oh / 2.0
                o_max_z = op.z + oh / 2.0
                if (new_max_x > o_min_x and new_min_x < o_max_x and
                    new_max_y > o_min_y and new_min_y < o_max_y and
                    new_max_z > o_min_z and new_min_z < o_max_z):
                    return False
            if hasattr(self, 'truck_width') and hasattr(self, 'truck_depth') and hasattr(self, 'truck_height'):
                t_half_w = self.truck_width / 2.0
                t_half_d = self.truck_depth / 2.0
                t_min_x = -t_half_w
                t_max_x = t_half_w
                t_min_y = -t_half_d
                t_max_y = t_half_d
                t_min_z = 0.0
                t_max_z = self.truck_height
                if not (new_min_x >= t_min_x and new_max_x <= t_max_x and
                        new_min_y >= t_min_y and new_max_y <= t_max_y and
                        new_min_z >= t_min_z and new_max_z <= t_max_z):
                    return False
            return True
        except Exception as e:
            logging.error(f"[Drag] Collision check error: {e}")
            return False

    def rotate_selected_box(self):
        """Повернуть выбранную коробку (поменять ширину и глубину)"""
        if self.selected_box:
            try:
                # Получаем данные коробки
                box_data = self.selected_box.getPythonTag('box_data')
                if box_data:
                    # Меняем местами ширину и глубину
                    old_width = box_data.get('width', 100)
                    old_depth = box_data.get('depth', 100)
                    
                    box_data['width'] = old_depth
                    box_data['depth'] = old_width
                    box_data['is_rotated'] = not box_data.get('is_rotated', False)
                    
                    old_pos = self.selected_box.getPos()
                    self.selected_box.removeNode()
                    
                    new_box = self.create_3d_box_from_data(box_data, (old_pos.x, old_pos.y, old_pos.z))
                    self.selected_box = new_box
            except Exception as e:
                logging.error(f"Error rotating box: {e}")

    def get_active_box(self):
        return self.hovered_box or self.selected_box

    def on_rotate_key(self, delta_h: float, delta_p: float):
        box = self.get_active_box()
        if not box or box.isEmpty():
            return
        try:
            h, p, r = box.getHpr()
            if delta_h != 0:
                h = self._snap_angle(h + delta_h)
            if delta_p != 0:
                p = self._snap_angle(p + delta_p)
            box.setHpr(h, p, r)
        except Exception as e:
            logging.error(f"[Rotate] Error rotating box: {e}")

    def _snap_angle(self, angle: float) -> float:
        normalized = (angle + 180.0) % 360.0 - 180.0
        snapped = round(normalized / 90.0) * 90.0
        if snapped == -180.0:
            return 180.0
        return snapped
    
    def delete_selected_box(self):
        """Удалить выбранную коробку"""
        if self.selected_box:
            try:
                if hasattr(self, 'scene_boxes') and self.selected_box in self.scene_boxes:
                    self.scene_boxes.remove(self.selected_box)
                
                self.selected_box.removeNode()
                self.selected_box = None
            except Exception as e:
                logging.error(f"Error deleting box: {e}")
    
    def set_selected_box(self, box_node):
        """Установить выбранную коробку"""
        self.selected_box = box_node
    
    def on_mouse_left_click(self):
        """Обработка клика левой кнопкой мыши для выделения коробок"""
        # Получаем позицию мыши
        if self.mouseWatcherNode.hasMouse():
            mouse_x = self.mouseWatcherNode.getMouseX()
            mouse_y = self.mouseWatcherNode.getMouseY()
            
            # Создаем луч от камеры через позицию мыши
            from panda3d.core import CollisionTraverser, CollisionNode, CollisionRay, CollisionHandlerQueue
            
            picker = CollisionTraverser()
            pq = CollisionHandlerQueue()
            
            pickerNode = CollisionNode('mouseRay')
            pickerNP = self.camera.attachNewNode(pickerNode)
            pickerNode.setFromCollideMask(1)
            pickerNode.setIntoCollideMask(0)  # Исправляем проблему с коллизией CollisionRay в CollisionRay
            pickerRay = CollisionRay()
            pickerNode.addSolid(pickerRay)
            picker.addCollider(pickerNP, pq)
            
            # Направляем луч от камеры через мышь
            pickerRay.setFromLens(self.camNode, mouse_x, mouse_y)
            
            # Ищем пересечения с коробками
            picker.traverse(self.render)
            
            if pq.getNumEntries() > 0:
                # Сортируем по расстоянию
                pq.sortEntries()
                entry = pq.getEntry(0)
                picked_obj = entry.getIntoNodePath()
                
                # Ищем коробку среди родителей
                while picked_obj:
                    if picked_obj.getName().startswith('randomBox'):
                        self.set_selected_box(picked_obj)
                        return
                    picked_obj = picked_obj.getParent()
            
            # Если ничего не выбрали, убираем выделение
            self.set_selected_box(None)
        
        # Также вызываем оригинальный обработчик камеры
        self.arc.on_left_down()

    def on_left_down(self):
        if not self.mouseWatcherNode.hasMouse():
            return
        mouse_x = self.mouseWatcherNode.getMouseX()
        mouse_y = self.mouseWatcherNode.getMouseY()
        from panda3d.core import CollisionTraverser, CollisionNode, CollisionRay, CollisionHandlerQueue
        picker = CollisionTraverser()
        pq = CollisionHandlerQueue()
        pickerNode = CollisionNode('moveRayL')
        pickerNP = self.camera.attachNewNode(pickerNode)
        pickerNode.setFromCollideMask(1)
        pickerNode.setIntoCollideMask(0)
        ray = CollisionRay()
        pickerNode.addSolid(ray)
        picker.addCollider(pickerNP, pq)
        ray.setFromLens(self.camNode, mouse_x, mouse_y)
        picker.traverse(self.render)
        target = None
        if pq.getNumEntries() > 0:
            pq.sortEntries()
            for i in range(pq.getNumEntries()):
                picked_obj = pq.getEntry(i).getIntoNodePath()
                cur = picked_obj
                while cur:
                    if cur.getName().startswith('randomBox'):
                        target = cur
                        break
                    cur = cur.getParent()
                if target:
                    break
        pickerNP.removeNode()
        if target is None:
            self.arc.on_left_down()
            return
        self.set_selected_box(target)
        self.drag_active = True
        self._drag_target = target
        self._drag_start_mouse = Point2(mouse_x, mouse_y)
        self._drag_distance = (target.getPos(self.render) - self.camera.getPos(self.render)).length()
        self._drag_last_mouse = Point2(mouse_x, mouse_y)
        self.taskMgr.add(self._drag_task, "box_drag_task")

    def on_left_up(self):
        if getattr(self, 'drag_active', False):
            self.drag_active = False
            self._drag_target = None
            self.taskMgr.remove("box_drag_task")
        self.arc.on_left_up()

    def init_first_truck(self):
        first_truck = {
            'width': self.truck_width,
            'height': self.truck_height,
            'depth': self.truck_depth
        }
        self.trucks.append(first_truck)
        
    def mouse_hover_task(self, task):
        try:
            if not hasattr(self, 'last_mouse_check_time'):
                self.last_mouse_check_time = 0
            
            current_time = task.time
            if current_time - self.last_mouse_check_time < 0.1:
                return task.cont
            
            self.last_mouse_check_time = current_time
            
            if not self.mouseWatcherNode.hasMouse():
                if self.hovered_box:
                    logging.debug("[MouseHover] Mouse not available, hiding box info")
                    self.hovered_box = None
                    self.hide_box_info()
                return task.cont
                
            mouse_x = self.mouseWatcherNode.getMouseX()
            mouse_y = self.mouseWatcherNode.getMouseY()
            
            from panda3d.core import CollisionTraverser, CollisionNode, CollisionRay, CollisionHandlerQueue
            
            picker = CollisionTraverser()
            pq = CollisionHandlerQueue()
            
            pickerNode = CollisionNode('mouseHoverRay')
            pickerNP = self.camera.attachNewNode(pickerNode)
            pickerNode.setFromCollideMask(1)
            pickerNode.setIntoCollideMask(0)
            pickerRay = CollisionRay()
            pickerNode.addSolid(pickerRay)
            picker.addCollider(pickerNP, pq)
            
            pickerRay.setFromLens(self.camNode, mouse_x, mouse_y)
            picker.traverse(self.render)
            
            new_hovered_box = None
            
            if pq.getNumEntries() > 0:
                if not hasattr(self, 'collision_debug_logged'):
                    logging.info(f"[MouseHover] First collision detection: Found {pq.getNumEntries()} collision entries")
                    self.collision_debug_logged = True
                
                pq.sortEntries()
                
                for i in range(pq.getNumEntries()):
                    entry = pq.getEntry(i)
                    picked_obj = entry.getIntoNodePath()
                    
                    current_obj = picked_obj
                    while current_obj:
                        if current_obj.getName().startswith('randomBox'):
                            new_hovered_box = current_obj
                            break
                        current_obj = current_obj.getParent()
                    
                    if new_hovered_box:
                        break
            
            if new_hovered_box != self.hovered_box:
                logging.info(f"[MouseHover] Hover changed from {self.hovered_box.getName() if self.hovered_box else 'None'} to {new_hovered_box.getName() if new_hovered_box else 'None'}")
                self.hovered_box = new_hovered_box
                if self.hovered_box:
                    box_data = self.hovered_box.getPythonTag('box_data')
                    if box_data:
                        logging.info(f"[MouseHover] Showing info for box: {box_data.get('label', 'Unknown')}")
                        self.show_box_info(box_data)
                    else:
                        logging.warning(f"[MouseHover] Box {self.hovered_box.getName()} has no box_data")
                else:
                    logging.debug("[MouseHover] Hiding box info")
                    self.hide_box_info()
            
            pickerNP.removeNode()
            return task.cont
            
        except Exception as e:
            logging.error(f"[MouseHover] Error in mouse_hover_task: {e}")
            return task.cont
    
    def show_box_info(self, box_data):
        logging.debug(f"[ShowBoxInfo] Attempting to show info for box: {box_data.get('label', 'Unknown')}")
        if hasattr(self, 'panda_widget') and self.panda_widget:
            logging.debug(f"[ShowBoxInfo] panda_widget found, calling show_box_info")
            self.panda_widget.show_box_info(box_data)
        else:
            logging.warning(f"[ShowBoxInfo] panda_widget not found or not set")
    
    def hide_box_info(self):
        logging.debug(f"[HideBoxInfo] Attempting to hide box info")
        if hasattr(self, 'panda_widget') and self.panda_widget:
            logging.debug(f"[HideBoxInfo] panda_widget found, calling hide")
            self.panda_widget.box_info_widget.hide()
        else:
            logging.warning(f"[HideBoxInfo] panda_widget not found or not set")
    
    def on_r_key(self):
        logging.info(f"[KeyPress] R/Q key pressed")
        self.rotate_selected_box()
    
    def on_hide_box_key_direct(self):
        logging.info(f"[KeyPress] H/Р key pressed directly")
        self.on_hide_box_key()
    
    def on_backspace_key_direct(self):
        logging.info(f"[KeyPress] Backspace key pressed directly")
        self.on_backspace_key()
    
    def on_backspace_key(self):
        target = self.hovered_box or self.selected_box
        logging.info(f"[Backspace] Key pressed - target: {target.getName() if target else 'None'}")
        if target:
            try:
                box_data = target.getPythonTag('box_data')
                box_name = target.getName()
                if box_data:
                    self.deleted_boxes.append({
                        'box_data': box_data,
                        'position': target.getPos(),
                        'node': target
                    })
                    logging.info(f"[Backspace] Added box {box_data.get('label', 'Unknown')} to deleted list")
                
                if hasattr(self, 'scene_boxes') and target in self.scene_boxes:
                    self.scene_boxes.remove(target)
                    logging.debug(f"[Backspace] Removed box from scene_boxes list")
                
                self.hide_box_info()
                target.removeNode()
                if target is self.hovered_box:
                    self.hovered_box = None
                if target is self.selected_box:
                    self.selected_box = None
                
                logging.info(f"[Backspace] Box {box_name} completely removed from scene and moved to deleted list")
                
            except Exception as e:
                logging.error(f"[Backspace] Error removing box: {e}")
        else:
            logging.debug(f"[Backspace] No box to delete")
    
    def on_hide_box_key(self):
        target = self.hovered_box or self.selected_box
        logging.info(f"[HideBox] H/Р key pressed - target: {target.getName() if target else 'None'}")
        if target:
            try:
                box_data = target.getPythonTag('box_data')
                box_name = target.getName()
                if box_data:
                    if hasattr(self, 'scene_boxes') and target in self.scene_boxes:
                        self.scene_boxes.remove(target)
                        logging.debug(f"[HideBox] Removed box from scene_boxes list")
                    
                    self.hide_box_info()
                    target.removeNode()
                    if target is self.hovered_box:
                        self.hovered_box = None
                    if target is self.selected_box:
                        self.selected_box = None
                    
                    self.return_box_to_list(box_data)
                    
                    logging.info(f"[HideBox] Box {box_name} hidden and returned to BoxListWidget")
                
            except Exception as e:
                logging.error(f"[HideBox] Error hiding box: {e}")
        else:
            logging.debug(f"[HideBox] No box to hide")

    def hide_selected_box(self):
        if not self.selected_box:
            return
        try:
            box_data = self.selected_box.getPythonTag('box_data')
            node_name = self.selected_box.getName()
            if hasattr(self, 'scene_boxes') and self.selected_box in self.scene_boxes:
                self.scene_boxes.remove(self.selected_box)
            self.hide_box_info()
            self.selected_box.removeNode()
            self.selected_box = None
            if box_data:
                self.return_box_to_list(box_data)
            logging.info(f"[HideSelected] Box {node_name} returned to list")
        except Exception as e:
            logging.error(f"[HideSelected] Error: {e}")
    
    def return_box_to_list(self, box_data):
        logging.info(f"[ReturnBox] Returning box {box_data.get('label', 'Unknown')} to BoxListWidget")
        try:
            if hasattr(self, 'panda_widget') and self.panda_widget:
                parent_window = self.panda_widget.parent()
                while parent_window and not hasattr(parent_window, 'sidebar'):
                    parent_window = parent_window.parent()
                
                if parent_window and hasattr(parent_window, 'sidebar'):
                    logging.debug(f"[ReturnBox] Found sidebar, getting box_manager")
                    box_manager = parent_window.sidebar.get_box_manager()
                    
                    if box_manager:
                        from core.box.box import Box
                        new_box = Box(
                            width=box_data.get('width', 100),
                            height=box_data.get('height', 100), 
                            depth=box_data.get('depth', 100),
                            label=box_data.get('label', 'Unknown'),
                            weight=box_data.get('weight', 1.0),
                            quantity=1,
                            additional_info=box_data.get('additional_info', ''),
                            cargo_markings=box_data.get('cargo_markings', [])
                        )
                        
                        box_manager.add_box(new_box)
                        logging.info(f"[ReturnBox] Successfully added box {box_data.get('label', 'Unknown')} to BoxManager")
                    else:
                        logging.error(f"[ReturnBox] get_box_manager() returned None")
                else:
                    logging.error(f"[ReturnBox] Could not find sidebar")
            else:
                logging.error(f"[ReturnBox] panda_widget not found")
                
        except Exception as e:
            logging.error(f"[ReturnBox] Error returning box to list: {e}")
            import traceback
            logging.error(f"[ReturnBox] Traceback: {traceback.format_exc()}")
    
    def set_panda_widget(self, widget):
        self.panda_widget = widget
        try:
            self.update_side_loads()
        except Exception:
            pass

    def update_side_loads(self):
        try:
            if not hasattr(self, 'scene_boxes'):
                return
            total_weights = [0.0, 0.0, 0.0, 0.0]
            if self.truck_depth <= 0:
                return
            quarter = self.truck_depth / 4.0
            for node in self.scene_boxes:
                if not node or node.isEmpty():
                    continue
                data = node.getPythonTag('box_data')
                if not data:
                    continue
                w = float(data.get('weight', 0.0))
                pos = node.getPos(self.render)
                local_y = pos.y
                idx = int((local_y + self.truck_depth / 2.0) // quarter)
                if idx < 0:
                    idx = 0
                if idx > 3:
                    idx = 3
                total_weights[idx] += w / 1000.0
            if hasattr(self, 'panda_widget') and self.panda_widget:
                parent_window = self.panda_widget.parent()
                while parent_window and not hasattr(parent_window, 'sidebar'):
                    parent_window = parent_window.parent()
                if parent_window and hasattr(parent_window, 'sidebar'):
                    lcw = getattr(parent_window.sidebar, 'load_calculation', None)
                    if lcw and hasattr(lcw, 'calculator'):
                        lcw.calculator.update_setting('Mg1', total_weights[0])
                        lcw.calculator.update_setting('Mg2', total_weights[1])
                        lcw.calculator.update_setting('Mg3', total_weights[2])
                        lcw.calculator.update_setting('Mg4', total_weights[3])
        except Exception as e:
            logging.error(f"[Loads] update_side_loads error: {e}")
