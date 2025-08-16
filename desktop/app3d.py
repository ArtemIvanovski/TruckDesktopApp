import logging
import math
import os
import sys
import traceback
from typing import Optional, Tuple

from direct.showbase.ShowBase import ShowBase
from panda3d.core import Material, Point3
from panda3d.core import (
    WindowProperties,
    AntialiasAttrib,
)

from camera import ArcCamera
from config import BACKGROUND_COLOR, WHEEL_CABIN_HEIGHT
from graphics_settings import GraphicsManager
from truck import TruckScene

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

    def create_box_wireframe(self, box_node, width, height, depth):
        from panda3d.core import LineSegs

        w, h, d = width / 2, height / 2, depth / 2

        lines = LineSegs()
        lines.setThickness(2.0)
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

    def create_box_markings(self, box_node, box_data, width, height, depth):
        from panda3d.core import CardMaker, TransparencyAttrib
        import os
        from setting_deploy import get_resource_path

        markings = box_data.get('cargo_markings', [])
        if not markings:
            return

        marking_size = min(width, height, depth) * 0.15
        markings_per_row = 3
        start_x = width / 2 - (markings_per_row * marking_size) / 2

        for i, marking in enumerate(markings[:6]):
            svg_path = get_resource_path(f"assets/markings/{marking}.svg")

            if not os.path.exists(svg_path):
                continue

            try:
                texture = self.convert_svg_to_texture(svg_path, 64, 64)
                if not texture:
                    continue

                cm = CardMaker(f'marking_{marking}_{i}')
                cm.setFrame(-marking_size / 2, marking_size / 2, -marking_size / 2, marking_size / 2)

                marking_node = box_node.attachNewNode(cm.generate())
                marking_node.setTexture(texture)
                marking_node.setTransparency(TransparencyAttrib.MAlpha)

                row = i // markings_per_row
                col = i % markings_per_row

                pos_x = start_x + col * marking_size
                pos_z = height / 2 + 0.005 - row * marking_size

                marking_node.setPos(pos_x, -depth / 2 - 0.005, pos_z)
                marking_node.setH(0)
                marking_node.setP(-90)
                marking_node.setLightOff(1)

            except Exception as e:
                logging.warning(f"Failed to load marking {marking}: {e}")

    def convert_svg_to_texture(self, svg_path, width, height):
        from panda3d.core import Texture, PNMImage
        import os

        try:
            try:
                import cairosvg
                from PIL import Image
                import io

                png_data = cairosvg.svg2png(url=svg_path, output_width=width, output_height=height)

                pil_image = Image.open(io.BytesIO(png_data))
                if pil_image.mode != 'RGBA':
                    pil_image = pil_image.convert('RGBA')

                pnm_image = PNMImage(width, height, 4)

                for y in range(height):
                    for x in range(width):
                        r, g, b, a = pil_image.getpixel((x, y))
                        pnm_image.setXelA(x, y, r / 255.0, g / 255.0, b / 255.0, a / 255.0)

                texture = Texture()
                texture.load(pnm_image)
                texture.setFormat(Texture.FRgba)
                return texture

            except ImportError:
                logging.warning("cairosvg not available, trying rsvg-convert")

                png_path = svg_path.replace('.svg', 'logo.png')
                os.system(f'rsvg-convert -w {width} -h {height} "{svg_path}" -o "{png_path}"')

                if os.path.exists(png_path):
                    texture = self.loader.loadTexture(png_path)
                    os.remove(png_path)
                    return texture

        except Exception as e:
            logging.warning(f"Failed to convert SVG {svg_path}: {e}")

        return self.create_fallback_marking_texture(os.path.basename(svg_path).replace('.svg', ''))

    def create_fallback_marking_texture(self, marking_name):
        from panda3d.core import Texture, PNMImage

        marking_symbols = {
            'fragile': '🍷',
            'this_way_up': '⬆️',
            'no_stack': '⛔',
            'keep_dry': '☔',
            'center_gravity': '⊕',
            'alcohol': '🍺',
            'no_hooks': '🚫',
            'temperature': '🌡️'
        }

        symbol = marking_symbols.get(marking_name, '?')

        pnm_image = PNMImage(64, 64, 4)
        pnm_image.fill(1.0, 1.0, 1.0)

        texture = Texture()
        texture.load(pnm_image)
        texture.setFormat(Texture.FRgba)

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
        from panda3d.core import (CardMaker, Material, Vec4, GeomNode, Geom, GeomVertexFormat,
                                  GeomVertexData, GeomVertexWriter, GeomTriangles, TextNode)

        if world_pos is None:
            world_pos = (0, 0, 0)

        width = box_data['width'] / 100.0
        height = box_data['height'] / 100.0
        depth = box_data['depth'] / 100.0

        box_node = self.render.attachNewNode(f"box_{box_data['id']}")

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

        material = Material()
        if box_data['color']:
            r, g, b = box_data['color']
            material.setDiffuse(Vec4(r, g, b, 1.0))
            material.setSpecular(Vec4(0.1, 0.1, 0.1, 1.0))
        else:
            material.setDiffuse(Vec4(0.7, 0.7, 0.7, 1.0))

        box_geom_np.setMaterial(material)

        self.create_box_text_labels_babylonjs_style(box_node, box_data, width, height, depth)

        world_x, world_y, world_z = world_pos
        box_node.setPos(world_x, world_y, world_z + height / 2)

        box_node.setPythonTag('box_data', box_data)

        if not hasattr(self, 'scene_boxes'):
            self.scene_boxes = []
        self.scene_boxes.append(box_node)

        box_node.setLightOff(1)
        box_geom_np.setLightOff(1)
        self.create_box_wireframe(box_node, width, height, depth)
        self.create_box_markings(box_node, box_data, width, height, depth)

        return box_node

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

    def create_box_text_labels_babylonjs_style(self, box_node, box_data, width, height, depth):
        from panda3d.core import TextNode, CardMaker

        main_label_node = TextNode('main_label')
        main_label_node.setText(box_data['label'])
        main_label_node.setAlign(TextNode.ACenter)
        main_label_node.setFont(self.loader.loadFont("fonts/arial.ttf") if hasattr(self, 'loader') else None)
        main_label_np = box_node.attachNewNode(main_label_node)
        main_label_np.setScale(height * 0.15)
        main_label_np.setPos(0, -depth / 2 - 0.01, 0)
        main_label_np.setColor(0, 0, 0, 1)
        main_label_np.setBillboardAxis()

        width_label_node = TextNode('width_label')
        width_label_node.setText(str(int(box_data['width'])))
        width_label_node.setAlign(TextNode.ACenter)
        width_label_np = box_node.attachNewNode(width_label_node)
        width_label_np.setScale(height * 0.08)
        width_label_np.setPos(0, depth / 2 + 0.02, height / 2 + 0.02)
        width_label_np.setH(0)
        width_label_np.setP(90)
        width_label_np.setColor(0, 0, 0, 1)

        depth_label_node = TextNode('depth_label')
        depth_label_node.setText(str(int(box_data['depth'])))
        depth_label_node.setAlign(TextNode.ACenter)
        depth_label_np = box_node.attachNewNode(depth_label_node)
        depth_label_np.setScale(height * 0.08)
        depth_label_np.setPos(width / 2 + 0.02, 0, height / 2 + 0.02)
        depth_label_np.setH(-90)
        depth_label_np.setP(90)
        depth_label_np.setColor(0, 0, 0, 1)

        weight_label_node = TextNode('weight_label')
        weight_label_node.setText(f"{box_data['weight']}kg")
        weight_label_node.setAlign(TextNode.ACenter)
        weight_label_np = box_node.attachNewNode(weight_label_node)
        weight_label_np.setScale(height * 0.06)
        weight_label_np.setPos(-width / 2 - 0.01, 0, -height / 4)
        weight_label_np.setH(90)
        weight_label_np.setColor(0, 0, 0, 1)

        main_label_np.setLightOff(1)
        width_label_np.setLightOff(1)
        depth_label_np.setLightOff(1)
        weight_label_np.setLightOff(1)

    def remove_material_specular(self, model):
        if not model or model.isEmpty():
            return

        if self.graphics_manager:
            enabled = self.graphics_manager.settings.enable_specular
            self.graphics_manager._update_model_specular(model, enabled)

    def load_models(self):
        logger.info("Starting models loading...")

        model_formats = [
            ("models/weel.obj", "models/lorry.obj"),
            ("weel.obj", "lorry.obj"),
        ]

        wheel_path = None
        lorry_path = None

        # Ищем доступные файлы моделей
        for wheel_file, lorry_file in model_formats:
            if os.path.exists(wheel_file) and os.path.exists(lorry_file):
                wheel_path = wheel_file
                lorry_path = lorry_file
                logger.info(f"Found model files: {wheel_file}, {lorry_file}")
                break

        if not wheel_path:
            logger.warning("No model files found, using placeholders")
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
        print("Setting up controls...")
        self.accept("mouse1", self.arc.on_left_down)
        self.accept("mouse1-up", self.arc.on_left_up)
        self.accept("mouse3", self.arc.on_right_down)
        self.accept("mouse3-up", self.arc.on_right_up)
        self.accept("wheel_up", self.arc.on_wheel_in)
        self.accept("wheel_down", self.arc.on_wheel_out)
        self.accept("shift", self.shift_down)
        self.accept("shift-up", self.shift_up)

        print("Controls setup complete")

    def focus_on_truck(self):
        self.arc.target = Point3(0, 0, 200)
        self.arc.radius = 1500
        self.arc.update()

    def reset_camera_view(self):
        self.arc.target = Point3(0, 0, 0)
        self.arc.radius = 2000
        self.arc.alpha = math.pi / 2
        self.arc.beta = math.pi / 4
        self.arc.update()

    def shift_down(self):
        self.is_shift_down = True

    def shift_up(self):
        self.is_shift_down = False

    def init_first_truck(self):
        first_truck = {
            'width': self.truck_width,
            'height': self.truck_height,
            'depth': self.truck_depth
        }
        self.trucks.append(first_truck)
