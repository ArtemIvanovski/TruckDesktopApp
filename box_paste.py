import sys
from typing import List, Tuple, Set
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import time
import logging
import random
from packing import Container, BoxItem, Packer, PackingConfig

# Настройка логирования добавь сетку
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Отключаем логи matplotlib
plt.set_loglevel('WARNING')


class Octree:
    def __init__(self, bounds, capacity=4):
        self.bounds = bounds
        self.capacity = capacity
        self.boxes = []
        self.divided = False
        self.children = []

    def subdivide(self):
        min_x, min_y, min_z, max_x, max_y, max_z = self.bounds
        mid_x = (min_x + max_x) / 2
        mid_y = (min_y + max_y) / 2
        mid_z = (min_z + max_z) / 2

        self.children = [
            Octree((min_x, min_y, min_z, mid_x, mid_y, mid_z), self.capacity),
            Octree((mid_x, min_y, min_z, max_x, mid_y, mid_z), self.capacity),
            Octree((min_x, mid_y, min_z, mid_x, max_y, mid_z), self.capacity),
            Octree((mid_x, mid_y, min_z, max_x, max_y, mid_z), self.capacity),
            Octree((min_x, min_y, mid_z, mid_x, mid_y, max_z), self.capacity),
            Octree((mid_x, min_y, mid_z, max_x, mid_y, max_z), self.capacity),
            Octree((min_x, mid_y, mid_z, mid_x, max_y, max_z), self.capacity),
            Octree((mid_x, mid_y, mid_z, max_x, max_y, max_z), self.capacity)
        ]
        self.divided = True

    def insert(self, box):
        if not self.overlaps(box):
            return False

        if len(self.boxes) < self.capacity and not self.divided:
            self.boxes.append(box)
            return True

        if not self.divided:
            self.subdivide()

        for child in self.children:
            child.insert(box)
        return True

    def overlaps(self, box):
        box_bounds = box[:6]
        return not (box_bounds[3] <= self.bounds[0] or box_bounds[0] >= self.bounds[3] or
                    box_bounds[4] <= self.bounds[1] or box_bounds[1] >= self.bounds[4] or
                    box_bounds[5] <= self.bounds[2] or box_bounds[2] >= self.bounds[5])

    def query(self, box):
        if not self.overlaps(box):
            return []

        result = self.boxes.copy()
        if self.divided:
            for child in self.children:
                result.extend(child.query(box))
        return result


def generate_test_data():
    """Генерация тестовых данных"""
    length = random.randint(4, 10)
    width = random.randint(4, 10)
    height = random.randint(4, 10)

    # Вершины параллелепипеда
    container_points = [
        (0, 0, 0), (length, 0, 0), (length, width, 0), (0, width, 0),
        (0, 0, height), (length, 0, height), (length, width, height), (0, width, height)
    ]

    # 12 случайных коробок
    num_boxes = 12
    boxes = []

    for i in range(num_boxes):
        # Случайные размеры от 1 до 3 (чтобы больше поместилось)
        l = random.randint(2, 5)
        w = random.randint(2, 5)
        h = random.randint(2, 5)

        # Генерация 24 случайных координат вершин (не используются в алгоритме)
        vertices = [random.randint(0, 1) for _ in range(24)]

        # Маркировки отключены
        flag = None
        arrow_axis = None

        boxes.append((l, w, h, vertices, flag, arrow_axis))

    # Форматирование данных для ввода
    data = []
    for point in container_points:
        data.extend([str(point[0]), str(point[1]), str(point[2])])

    data.append(str(num_boxes))

    for box in boxes:
        l, w, h, vertices, flag, arrow_axis = box
        data.extend([str(l), str(w), str(h)])
        data.extend([str(v) for v in vertices])
        data.append(flag if flag else 'none')
        data.append(arrow_axis if arrow_axis else 'none')

    return data


def read_input(data: List[str]) -> Tuple[Tuple[float, ...], List[Tuple]]:
    logger.info("Чтение входных данных")
    points = []
    index = 0

    for _ in range(8):
        x, y, z = map(float, data[index:index + 3])
        points.append((x, y, z))
        index += 3

    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    min_z = min(p[2] for p in points)
    max_z = max(p[2] for p in points)

    n = int(data[index]);
    index += 1
    boxes = []

    for i in range(n):
        l, w, h = map(float, data[index:index + 3])
        index += 3
        # Пропускаем вершины коробок (24 значения)
        index += 24
        flag = None
        arrow_axis = None
        # Читаем опциональные поля если есть
        if index + 2 <= len(data):
            f = data[index]; a = data[index + 1]
            if f in ('none', 'no_stack', 'fragile', 'alcohol', 'this_way_up'):
                flag = None if f == 'none' else f
                arrow_axis = None if a == 'none' else a
                index += 2
        boxes.append((l, w, h, i, flag, arrow_axis))

    logger.info(f"Прочитано: контейнер ({min_x},{min_y},{min_z})-({max_x},{max_y},{max_z}), {n} коробок")
    return (min_x, min_y, min_z, max_x, max_y, max_z), boxes


def generate_orientations(l: float, w: float, h: float) -> List[Tuple]:
    # Если коробка является кубом, нет смысла генерировать все ориентации
    if abs(l - w) < 1e-6 and abs(l - h) < 1e-6 and abs(w - h) < 1e-6:
        return [(l, w, h)]

    return [
        (l, w, h), (l, h, w),
        (w, l, h), (w, h, l),
        (h, l, w), (h, w, l)
    ]


def overlaps(box1: Tuple, box2: Tuple) -> bool:
    # Проверяем, перекрываются ли два бокса
    return not (box1[3] <= box2[0] or box1[0] >= box2[3] or
                box1[4] <= box2[1] or box1[1] >= box2[4] or
                box1[5] <= box2[2] or box1[2] >= box2[5])


def point_inside_box(p: Tuple, box: Tuple, tol: float = 1e-6) -> bool:
    x, y, z = p
    # Исправленная проверка: точка считается внутри, если она находится строго внутри коробки
    return (box[0] + tol < x < box[3] - tol and
            box[1] + tol < y < box[4] - tol and
            box[2] + tol < z < box[5] - tol)


def pack_boxes(container: Tuple, boxes: List[Tuple], timeout: float = 30.0) -> List[Tuple]:
    c = Container(container[0], container[1], container[2], container[3], container[4], container[5])
    def to_flags(flag):
        return frozenset([flag]) if flag else frozenset()
    items = [BoxItem(l, w, h, i, to_flags(flag), arrow_axis) for (l, w, h, i, flag, arrow_axis) in boxes]
    packer = Packer(c, PackingConfig())
    placed = packer.pack(items)
    return [(p.x1, p.y1, p.z1, p.x2, p.y2, p.z2, p.index) for p in placed]


def visualize(container, boxes):
    logger.info("Визуализация результата")
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')

    min_x, min_y, min_z, max_x, max_y, max_z = container
    container_points = [
        [min_x, min_y, min_z],
        [max_x, min_y, min_z],
        [max_x, max_y, min_z],
        [min_x, max_y, min_z],
        [min_x, min_y, max_z],
        [max_x, min_y, max_z],
        [max_x, max_y, max_z],
        [min_x, max_y, max_z]
    ]

    faces = [
        [container_points[0], container_points[1], container_points[2], container_points[3]],
        [container_points[4], container_points[5], container_points[6], container_points[7]],
        [container_points[0], container_points[1], container_points[5], container_points[4]],
        [container_points[2], container_points[3], container_points[7], container_points[6]],
        [container_points[0], container_points[3], container_points[7], container_points[4]],
        [container_points[1], container_points[2], container_points[6], container_points[5]]
    ]

    ax.add_collection3d(Poly3DCollection(faces, facecolors='cyan', linewidths=1, edgecolors='r', alpha=0.1))

    colors = plt.cm.tab20(np.linspace(0, 1, len(boxes)))

    for i, box in enumerate(boxes):
        x1, y1, z1, x2, y2, z2, idx = box
        vertices = [
            [x1, y1, z1], [x2, y1, z1], [x2, y2, z1], [x1, y2, z1],
            [x1, y1, z2], [x2, y1, z2], [x2, y2, z2], [x1, y2, z2]
        ]
        faces = [
            [vertices[0], vertices[1], vertices[2], vertices[3]],
            [vertices[4], vertices[5], vertices[6], vertices[7]],
            [vertices[0], vertices[1], vertices[5], vertices[4]],
            [vertices[2], vertices[3], vertices[7], vertices[6]],
            [vertices[0], vertices[3], vertices[7], vertices[4]],
            [vertices[1], vertices[2], vertices[6], vertices[5]]
        ]
        ax.add_collection3d(Poly3DCollection(faces, facecolors=colors[i % len(colors)],
                                             linewidths=1, edgecolors='k', alpha=0.7))

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_xlim([min_x, max_x])
    ax.set_ylim([min_y, max_y])
    ax.set_zlim([min_z, max_z])
    plt.title(f"Размещено {len(boxes)} коробок")
    plt.show()


def main():
    # Определяем, использовать ли тестовые данные
    use_test_data = True
    visualize_flag = True
    debug_mode = False

    # Обработка аргументов командной строки
    args = sys.argv[1:]
    if '--test' in args:
        use_test_data = True
        args.remove('--test')
    if '--visualize' in args:
        visualize_flag = True
        args.remove('--visualize')
    if '--debug' in args:
        debug_mode = True
        args.remove('--debug')

    # Установка уровня логирования
    if debug_mode:
        logging.getLogger().setLevel(logging.DEBUG)

    # Получение данных
    if use_test_data:
        logger.info("Использование тестовых данных")
        data = generate_test_data()
    else:
        data = sys.stdin.read().split()
        if not data:
            print(0)
            return

    # Чтение и обработка данных
    container, boxes = read_input(data)

    # Стратегии сортировки коробок
    strategies = [
        lambda x: x[0] * x[1] * x[2],  # По объему (убывание)
        lambda x: -x[0] * x[1] * x[2],  # По объему (возрастание)
        lambda x: max(x[:3]),  # По максимальному размеру
        lambda x: min(x[:3]),  # По минимальному размеру
    ]

    best_result = []

    # Перебор различных стратегий сортировки
    for i, strategy in enumerate(strategies):
        logger.info(f"Тестирование стратегии {i + 1}/{len(strategies)}")
        sorted_boxes = sorted(boxes, key=strategy, reverse=True)
        result = pack_boxes(container, sorted_boxes)
        if len(result) > len(best_result):
            best_result = result

    # Вывод результатов
    print(len(best_result))
    for box in best_result:
        print(f"{box[6]} {box[0]} {box[1]} {box[2]}")

    # Визуализация при необходимости
    if visualize_flag:
        visualize(container, best_result)


if __name__ == "__main__":
    main()