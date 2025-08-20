import logging
import math
import os
import sys
import traceback
from typing import Optional, Tuple

from direct.showbase.ShowBase import ShowBase
from panda3d.core import Material, Point3, TextNode
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
        from setting_deploy import get_resource_path

        markings = box_data.get('cargo_markings', [])
        if not markings:
            return

        marking_size = min(width, height, depth) * 0.25  # Увеличиваем размер маркировок
        markings_per_row = 2  # Уменьшаем количество в ряду для лучшей видимости
        start_x = -marking_size / 2  # Центрируем по X

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

                pos_x = start_x + col * marking_size * 1.2  # Больше расстояние между маркировками
                pos_z = height / 2 - 0.1 - row * marking_size * 1.2  # На верхней грани

                marking_node.setPos(pos_x, -depth / 2 - 0.01, pos_z)
                marking_node.setH(0)
                marking_node.setP(-90)
                marking_node.setLightOff(1)
                marking_node.setDepthOffset(2)  # Поверх коробки

            except Exception as e:
                logging.warning(f"Failed to load marking {marking}: {e}")

    def convert_svg_to_texture(self, svg_path, width, height):
        """Создание текстуры из SVG файла с fallback на простые символы"""
        # Сразу используем fallback текстуры для избежания проблем с cairo
        marking_name = os.path.basename(svg_path).replace('.svg', '')
        logging.info(f"Creating fallback texture for marking: {marking_name}")
        return self.create_fallback_marking_texture(marking_name)

    def create_fallback_marking_texture(self, marking_name):
        from panda3d.core import Texture, PNMImage, LColor

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
        pnm_image = PNMImage(64, 64, 4)
        pnm_image.fill(0.0, 0.0, 0.0, 0.0)  # прозрачный фон

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
                    pnm_image.setXel(x, y, LColor(r, g, b))
                    pnm_image.setAlpha(x, y, 1.0)
                elif distance <= radius + 2:
                    # Граница круга - черная обводка
                    pnm_image.setXel(x, y, LColor(0, 0, 0))
                    pnm_image.setAlpha(x, y, 1.0)

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
        """Создание 3D коробки точно как в content.html"""
        from panda3d.core import (CardMaker, Material, Vec4, GeomNode, Geom, GeomVertexFormat,
                                  GeomVertexData, GeomVertexWriter, GeomTriangles, TextNode)
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

        # Система цветов как в content.html (boxColors Map)
        box_color_key = f"{width}_{depth}_{height}"
        if not hasattr(self, 'box_colors'):
            self.box_colors = {}
            
        if box_color_key not in self.box_colors:
            # Генерируем цвет как в content.html: new BABYLON.Color3(Math.random(), Math.random(), Math.random())
            self.box_colors[box_color_key] = (random.random(), random.random(), random.random())
        
        box_color = self.box_colors[box_color_key]
        r, g, b = box_color
        
        # Материал как в content.html - правильно применяем цвет коробки
        material = Material()
        material.setDiffuse(Vec4(r, g, b, 1.0))  # Основной цвет коробки
        material.setSpecular(Vec4(0.3, 0.3, 0.3, 1.0))  # Небольшие блики
        material.setEmission(Vec4(0.1, 0.1, 0.1, 1.0))  # Слабое свечение
        material.setShininess(32)
        
        box_geom_np.setMaterial(material)
        # Включаем освещение для правильного отображения цвета
        box_geom_np.setRenderModeWireframe()
        box_geom_np.clearRenderMode()
        box_geom_np.setColorScale(1, 1, 1, 1)

        # Окантовка как в content.html: enableEdgesRendering()
        self.create_box_wireframe(box_node, width, height, depth)
        
        # Создаем надписи как в content.html
        self.create_box_text_labels_static(box_node, box_data, width, height, depth)

        # Добавляем коллизионное тело для возможности выделения мышью
        from panda3d.core import CollisionNode, CollisionBox
        collision_node = CollisionNode('box_collision')
        collision_node.addSolid(CollisionBox(Point3(0, 0, 0), width/2, depth/2, height/2))
        collision_node.setFromCollideMask(0)
        collision_node.setIntoCollideMask(1)
        collision_np = box_geom_np.attachNewNode(collision_node)

        # Позиционирование
        world_x, world_y, world_z = world_pos
        box_node.setPos(world_x, world_y, world_z + height / 2)

        box_node.setPythonTag('box_data', box_data)

        # Добавляем в список коробок как в content.html
        if not hasattr(self, 'scene_boxes'):
            self.scene_boxes = []
        self.scene_boxes.append(box_node)

        # Маркировки груза
        self.create_box_markings(box_node=box_node, box_data=box_data, width=width, height=height, depth=depth)
        
        print(f"Box created: {label}, size: {width}x{height}x{depth}, weight: {weight}kg, color: {box_color}")
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

    def create_box_text_labels_static(self, box_node, box_data, width, height, depth):
        """Создание надписей на коробке точно как в content.html"""
        
        # Загружаем шрифт с поддержкой русских символов
        try:
            from panda3d.core import DynamicTextFont
            font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'NotoSans-Regular.ttf')
            # Конвертируем Windows путь в Unix стиль для Panda3D
            font_path_unix = font_path.replace('\\', '/')
            if os.path.exists(font_path):
                font = self.loader.loadFont(font_path_unix)
                if font:
                    logging.info(f"Loaded font: {font_path_unix}")
                else:
                    font = None
            else:
                font = None
        except Exception as e:
            logging.warning(f"Error loading font: {e}")
            font = None
        
        # Основная метка (название коробки) - на передней стенке как в content.html
        main_label_node = TextNode('main_label')
        main_label_node.setText(box_data['label'])
        main_label_node.setAlign(TextNode.ACenter)
        if font:
            main_label_node.setFont(font)
        main_label_np = box_node.attachNewNode(main_label_node)
        
        # Размер шрифта уменьшен для PO# меток
        font_size = min(width, height) * 0.15  # еще меньший размер для лучшей читаемости
        main_label_np.setScale(font_size)
        main_label_np.setPos(0, -depth / 2 - 0.1, 0)  # Ближе к поверхности
        main_label_np.setHpr(0, 0, 0)
        main_label_np.setColor(0, 0, 0, 1)  # черный текст
        main_label_np.setDepthOffset(1)
        main_label_np.setLightOff(1)  # Отключаем освещение для текста
        main_label_np.setBillboardPointEye()  # Всегда повернут к камере
        
        # Функция для создания размерных надписей (аналогично createTextSizeBoxes из content.html)
        def create_size_label(text, x, y, z, h, p, r):
            label_node = TextNode('size_label')
            label_node.setText(str(int(text)))
            label_node.setAlign(TextNode.ACenter)
            if font:
                label_node.setFont(font)
            label_np = box_node.attachNewNode(label_node)
            
            # Масштаб как в content.html (30 для font_size, размер плоскости от высоты коробки)
            font_size_label = 30
            plane_height = text / 5  # как в content.html: boxWidth_f[i] / 5
            scale_factor = plane_height / (1.5 * font_size_label) * 0.1  # коэффициент для Panda3D
            label_np.setScale(scale_factor)
            
            # Позиция как в content.html (с учетом смещений x - 4, y, z + 4)
            label_np.setPos(x - 4, y, z + 4)
            label_np.setHpr(h, p, r)
            label_np.setColor(0, 0, 0, 1)  # черный текст как в content.html
            label_np.setDepthOffset(1)
            return label_np
        
        # Надпись ширины (как meshWidth в content.html)
        # createTextSizeBoxes(30, boxWidth_f[i] / 5, boxWidth_f[i], 0, boxHeight_f[i] / 2 + 0.4, - boxDepth_f[i] / 2 + boxWidth_f[i] / 10, Math.PI / 2, Math.PI, 0)
        width_label = create_size_label(
            width, 
            0, 
            height / 2 + 0.4, 
            -depth / 2 + width / 10,
            90,  # Math.PI / 2 в градусах
            180, # Math.PI в градусах 
            0
        )
        
        # Надпись глубины (как meshDepth в content.html)
        # createTextSizeBoxes(30, boxDepth_f[i] / 5, boxDepth_f[i], boxWidth_f[i] / 2 - boxDepth_f[i] / 10, boxHeight_f[i] / 2 + 0.4, 0, Math.PI / 2, -Math.PI / 2, 0)
        depth_label = create_size_label(
            depth, 
            width / 2 - depth / 10, 
            height / 2 + 0.4, 
            0,
            90,   # Math.PI / 2 в градусах
            -90,  # -Math.PI / 2 в градусах
            0
        )

        # Отключаем освещение для текстовых меток
        main_label_np.setLightOff(1)
        width_label.setLightOff(1)
        depth_label.setLightOff(1)

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
        # Мышь
        self.accept("mouse1", self.on_mouse_left_click)
        self.accept("mouse1-up", self.arc.on_left_up)
        self.accept("mouse3", self.arc.on_right_down)
        self.accept("mouse3-up", self.arc.on_right_up)
        self.accept("wheel_up", self.arc.on_wheel_in)
        self.accept("wheel_down", self.arc.on_wheel_out)
        
        # Модификаторы
        self.accept("shift", self.shift_down)
        self.accept("shift-up", self.shift_up)
        
        # Горячие клавиши для управления коробками
        self.accept("r", self.rotate_selected_box)
        self.accept("к", self.rotate_selected_box)  # русская к
        self.accept("backspace", self.delete_selected_box)
        self.accept("delete", self.delete_selected_box)
        
        # Дополнительные клавиши (как в content.html)
        self.accept("q", self.rotate_selected_box)
        
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
                    
                    # Пересоздаем коробку
                    old_pos = self.selected_box.getPos()
                    self.selected_box.removeNode()
                    
                    # Создаем новую коробку с повернутыми размерами
                    new_box = self.create_3d_box_from_data(box_data, (old_pos.x, old_pos.y, old_pos.z))
                    self.selected_box = new_box
                    
                    print(f"Box rotated: {old_width}x{old_depth} -> {box_data['width']}x{box_data['depth']}")
            except Exception as e:
                logging.error(f"Error rotating box: {e}")
    
    def delete_selected_box(self):
        """Удалить выбранную коробку"""
        if self.selected_box:
            try:
                box_data = self.selected_box.getPythonTag('box_data')
                if box_data:
                    print(f"Deleting box: {box_data.get('label', 'Unknown')}")
                
                # Удаляем из списка коробок в сцене
                if hasattr(self, 'scene_boxes') and self.selected_box in self.scene_boxes:
                    self.scene_boxes.remove(self.selected_box)
                
                # Удаляем узел из сцены
                self.selected_box.removeNode()
                self.selected_box = None
                
                print("Box deleted successfully")
            except Exception as e:
                logging.error(f"Error deleting box: {e}")
    
    def set_selected_box(self, box_node):
        """Установить выбранную коробку"""
        if self.selected_box:
            # Убираем выделение с предыдущей коробки
            self.selected_box.clearColorScale()
        
        self.selected_box = box_node
        
        if self.selected_box:
            # Подсвечиваем выбранную коробку
            self.selected_box.setColorScale(1.2, 1.2, 1.0, 1.0)
    
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

    def init_first_truck(self):
        first_truck = {
            'width': self.truck_width,
            'height': self.truck_height,
            'depth': self.truck_depth
        }
        self.trucks.append(first_truck)
