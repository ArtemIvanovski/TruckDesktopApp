#!/usr/bin/env python3

import sys
import os
import json
import random
import logging
import time
from typing import List, Tuple, Dict, Any
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
from matplotlib.widgets import Button

# Импортируем алгоритм упаковки
try:
    from box_paste import generate_test_data, read_input, pack_boxes
    from packing import Container, BoxItem, Packer, PackingConfig
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("💡 Убедитесь, что все файлы находятся в одной папке")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Отключаем логи matplotlib
plt.set_loglevel('WARNING')

# Настраиваем matplotlib для интерактивности
import matplotlib
matplotlib.use('Qt5Agg')  # Используем Qt backend для лучшей интерактивности
plt.ion()  # Включаем интерактивный режим


class AlgorithmTester:
    def __init__(self):
        self.current_container = None
        self.current_boxes = None
        self.current_result = None
        self.fig = None
        self.ax_main = None
        self.ax_stats = None
        self.test_results = []
        self._prefer_small = False
        self._objective = "count"
        self._allow_stacking = True
        self._stack_same_face_only = False
        
    def generate_test_data(self):
        """Генерация тестовых данных"""
        data = generate_test_data()
        container, boxes = read_input(data)
        return container, boxes
    
    def run_algorithm_packing(self, container, boxes, prefer_small=False, objective="count", allow_stacking=True, stack_same_face_only=False):
        """Запуск алгоритма упаковки"""
        logger.info("📐 Запуск алгоритма упаковки...")
        
        start_time = time.time()
        # Переопределяем конфиг через прямой вызов Packer, чтобы задать цель и приоритет
        c = Container(container[0], container[1], container[2], container[3], container[4], container[5])
        def to_flags(flag):
            return frozenset([flag]) if flag else frozenset()
        items = [BoxItem(l, w, h, i, to_flags(flag), arrow_axis) for (l, w, h, i, flag, arrow_axis) in boxes]
        cfg = PackingConfig()
        cfg.objective = objective
        cfg.prefer_small_boxes = prefer_small
        cfg.allow_stacking = allow_stacking
        cfg.stack_same_face_only = stack_same_face_only
        packer = Packer(c, cfg)
        placed_objs = packer.pack(items)
        result = [(p.x1, p.y1, p.z1, p.x2, p.y2, p.z2, p.index) for p in placed_objs]
        end_time = time.time()
        
        # Конвертируем результат в нужный формат
        placed_boxes = []
        for x1, y1, z1, x2, y2, z2, idx in result:
            placed_box = {
                "id": idx,
                "length": int(x2 - x1),
                "width": int(y2 - y1),
                "height": int(z2 - z1),
                "position": {
                    "x": int((x1 + x2) / 2),
                    "y": int((y1 + y2) / 2),
                    "z": int((z1 + z2) / 2)
                },
                "bounds": {
                    "x1": int(x1), "y1": int(y1), "z1": int(z1),
                    "x2": int(x2), "y2": int(y2), "z2": int(z2)
                },
                "label": self._find_label_for_idx(idx, boxes)
            }
            placed_boxes.append(placed_box)
        
        execution_time = end_time - start_time
        logger.info(f"Алгоритм разместил {len(placed_boxes)} коробок за {execution_time:.3f}с")
        
        return placed_boxes, execution_time
    
    def create_visualization(self, container, result, boxes, execution_time):
        """Создание интерактивной визуализации"""
        self.fig = plt.figure(figsize=(18, 10))
        
        # Основная 3D визуализация (слева)
        self.ax_main = self.fig.add_subplot(121, projection='3d')
        self.draw_packing_result(self.ax_main, container, result, "Алгоритм Упаковки")
        
        # Статистика и нераспределенные коробки (справа)
        self.ax_stats = self.fig.add_subplot(122)
        self.draw_statistics(self.ax_stats, container, result, boxes, execution_time)
        # Плашка с текущими настройками
        settings_text = (
            f"Настройки: приоритет={'мелкие' if getattr(self, '_prefer_small', False) else 'крупные'}, "
            f"цель={'количество' if getattr(self, '_objective', 'count')=='count' else 'объем'}, "
            f"штабелирование={'да' if getattr(self, '_allow_stacking', True) else 'нет'}, "
            f"только одинаковые поверхности={'да' if getattr(self, '_stack_same_face_only', False) else 'нет'}"
        )
        self.fig.text(0.02, 0.88, settings_text, fontsize=10, bbox=dict(boxstyle="round,pad=0.4", facecolor="#eef", alpha=0.6))
        
        # Сохраняем данные для кнопок
        self.current_container = container
        self.current_result = result
        self.current_boxes = boxes
        
        # Добавляем кнопки
        self.add_interactive_buttons()
        
        # Настраиваем отображение
        plt.subplots_adjust(bottom=0.1)
        plt.show(block=True)
    
    def draw_packing_result(self, ax, container, placed_boxes, title):
        """Отрисовка результата упаковки"""
        # Контейнер
        if isinstance(container, tuple):
            # Формат box_paste
            x_size = int(container[3] - container[0])
            y_size = int(container[4] - container[1])
            z_size = int(container[5] - container[2])
        else:
            # Формат ИИ
            x_size = container["x"]
            y_size = container["y"]
            z_size = container["z"]
        
        self.draw_container(ax, x_size, y_size, z_size, 'lightblue')
        
        # Коробки
        colors = plt.cm.Set3(np.linspace(0, 1, len(placed_boxes)))
        for i, box in enumerate(placed_boxes):
            self.draw_box(ax, box, colors[i])
        
        ax.set_xlabel('X (см)')
        ax.set_ylabel('Y (см)')
        ax.set_zlabel('Z (см)')
        ax.set_xlim([0, x_size])
        ax.set_ylim([0, y_size])
        ax.set_zlim([0, z_size])
        ax.set_title(f'{title}\n{len(placed_boxes)} коробок размещено')
    
    def draw_container(self, ax, x_size, y_size, z_size, color):
        """Отрисовка контейнера"""
        container_points = [
            [0, 0, 0], [x_size, 0, 0], [x_size, y_size, 0], [0, y_size, 0],
            [0, 0, z_size], [x_size, 0, z_size], [x_size, y_size, z_size], [0, y_size, z_size]
        ]
        
        faces = [
            [container_points[0], container_points[1], container_points[2], container_points[3]],
            [container_points[4], container_points[5], container_points[6], container_points[7]],
            [container_points[0], container_points[1], container_points[5], container_points[4]],
            [container_points[2], container_points[3], container_points[7], container_points[6]],
            [container_points[0], container_points[3], container_points[7], container_points[4]],
            [container_points[1], container_points[2], container_points[6], container_points[5]]
        ]
        
        ax.add_collection3d(Poly3DCollection(faces, facecolors=color, 
                                           linewidths=2, edgecolors='navy', alpha=0.1))
    
    def draw_box(self, ax, box, color):
        """Отрисовка коробки"""
        bounds = box["bounds"]
        x1, y1, z1 = bounds["x1"], bounds["y1"], bounds["z1"]
        x2, y2, z2 = bounds["x2"], bounds["y2"], bounds["z2"]
        
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
        
        face_color = color
        label = box.get("label")
        if label in ("no_stack", "fragile", "alcohol"):
            face_color = (1.0, 0.6, 0.6, 0.9)
        if label == "this_way_up":
            face_color = (0.6, 0.6, 1.0, 0.9)
        ax.add_collection3d(Poly3DCollection(faces, facecolors=face_color, 
                                           linewidths=1, edgecolors='black', alpha=0.8))
        # Подпись
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        cz = (z1 + z2) / 2
        if label:
            ax.text(cx, cy, z2 + 0.2, label, fontsize=8, color='black')
            if label == 'this_way_up':
                # Рисуем стрелку вверх
                ax.plot([cx, cx], [cy, cy], [z2, z2 + 0.5], color='red', linewidth=2)
    
    def draw_statistics(self, ax, container, result, all_boxes, execution_time):
        """Отрисовка статистики и информации"""
        ax.clear()
        ax.axis('off')
        
        # Контейнер параметры
        if isinstance(container, tuple):
            cx = int(container[3] - container[0])
            cy = int(container[4] - container[1])
            cz = int(container[5] - container[2])
        else:
            cx, cy, cz = container["x"], container["y"], container["z"]
        
        container_volume = cx * cy * cz
        
        # Объем размещенных коробок
        placed_volume = 0
        for box in result:
            bounds = box["bounds"]
            placed_volume += (bounds["x2"] - bounds["x1"]) * (bounds["y2"] - bounds["y1"]) * (bounds["z2"] - bounds["z1"])
        
        # Статистика
        efficiency = len(result) / len(all_boxes) * 100 if all_boxes else 0
        fill_ratio = placed_volume / container_volume * 100 if container_volume > 0 else 0
        free_space = 100 - fill_ratio
        
        # Нераспределенные коробки
        placed_ids = set(box["id"] for box in result)
        unplaced_boxes = [box for box in all_boxes if box[3] not in placed_ids]
        
        # Создаем текстовую статистику
        stats_text = f"""СТАТИСТИКА АЛГОРИТМА

Контейнер: {cx}x{cy}x{cz} см
Объем контейнера: {container_volume} см3

Размещено коробок: {len(result)} из {len(all_boxes)}
Эффективность размещения: {efficiency:.1f}%
Заполненность по объему: {fill_ratio:.1f}%
Свободное место: {free_space:.1f}%
Время выполнения: {execution_time:.3f}с

Не размещено: {len(unplaced_boxes)} коробок"""

        if unplaced_boxes:
            stats_text += f"\n\nНЕРАСПРЕДЕЛЕННЫЕ КОРОБКИ:"
            for i, box in enumerate(unplaced_boxes[:8]):  # Показываем только первые 8
                l, w, h, idx, flag, arrow_axis = box
                volume = l * w * h
                label = flag if flag else '-'
                stats_text += f"\n  ID {idx}: {l}x{w}x{h} (V={volume}) [{label}]"
            if len(unplaced_boxes) > 8:
                stats_text += f"\n  ... и еще {len(unplaced_boxes) - 8} коробок"
        
        # Последние результаты тестов
        if self.test_results:
            stats_text += f"\n\nПОСЛЕДНИЕ ТЕСТЫ:"
            for i, test in enumerate(self.test_results[-5:]):  # Последние 5 тестов
                stats_text += f"\n  Тест {i+1}: {test['placed']}/{test['total']} ({test['efficiency']:.1f}%) за {test['time']:.3f}с"
        
        ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, fontsize=9,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8),
                wrap=True)
    
    def add_interactive_buttons(self):
        """Добавление интерактивных кнопок"""
        # Переключатели целей
        ax_toggle_small = plt.axes([0.05, 0.92, 0.18, 0.05])
        self.btn_small = Button(ax_toggle_small, 'Приоритет: Мелкие', color='lightgray', hovercolor='gray')
        self.btn_small.on_clicked(self.on_prefer_small)

        ax_toggle_large = plt.axes([0.25, 0.92, 0.18, 0.05])
        self.btn_large = Button(ax_toggle_large, 'Приоритет: Крупные', color='lightgray', hovercolor='gray')
        self.btn_large.on_clicked(self.on_prefer_large)

        ax_obj_count = plt.axes([0.45, 0.92, 0.18, 0.05])
        self.btn_obj_count = Button(ax_obj_count, 'Цель: Кол-во', color='lightgray', hovercolor='gray')
        self.btn_obj_count.on_clicked(self.on_objective_count)

        ax_obj_volume = plt.axes([0.65, 0.92, 0.18, 0.05])
        self.btn_obj_volume = Button(ax_obj_volume, 'Цель: Объем', color='lightgray', hovercolor='gray')
        self.btn_obj_volume.on_clicked(self.on_objective_volume)

        ax_stack_toggle = plt.axes([0.83, 0.92, 0.14, 0.05])
        self.btn_stack = Button(ax_stack_toggle, 'Штаб.: да/нет', color='lightgray', hovercolor='gray')
        self.btn_stack.on_clicked(self.on_toggle_stacking)

        # Переключатель: штаб. только одинаковые поверхности
        ax_same_face = plt.axes([0.65, 0.86, 0.32, 0.05])
        self.btn_same_face = Button(ax_same_face, 'Только одинаковые поверхности: да/нет', color='lightgray', hovercolor='gray')
        self.btn_same_face.on_clicked(self.on_toggle_same_face)

        # Кнопка "Новый тест"
        ax_new = plt.axes([0.05, 0.02, 0.15, 0.05])
        self.btn_new = Button(ax_new, 'Новый тест', color='lightgreen', hovercolor='green')
        self.btn_new.on_clicked(self.on_new_test_clicked)
        
        # Кнопка "Настройки алгоритма"
        ax_settings = plt.axes([0.22, 0.02, 0.15, 0.05])
        self.btn_settings = Button(ax_settings, 'Настройки', color='lightblue', hovercolor='blue')
        self.btn_settings.on_clicked(self.on_settings_clicked)
        
        # Кнопка "Массовый тест"
        ax_mass = plt.axes([0.39, 0.02, 0.15, 0.05])
        self.btn_mass = Button(ax_mass, 'Массовый тест', color='lightyellow', hovercolor='orange')
        self.btn_mass.on_clicked(self.on_mass_test_clicked)
        
        # Кнопка "Сохранить результаты"
        ax_save = plt.axes([0.56, 0.02, 0.15, 0.05])
        self.btn_save = Button(ax_save, 'Сохранить', color='lightcoral', hovercolor='red')
        self.btn_save.on_clicked(self.on_save_clicked)
        
        # Кнопка "Выход"
        ax_exit = plt.axes([0.73, 0.02, 0.15, 0.05])
        self.btn_exit = Button(ax_exit, 'Выход', color='lightgray', hovercolor='gray')
        self.btn_exit.on_clicked(self.on_exit_clicked)
        
        # Сохраняем ссылки на кнопки, чтобы они не удалились
        self.buttons = [
            self.btn_small, self.btn_large, self.btn_obj_count, self.btn_obj_volume,
            self.btn_stack, self.btn_same_face, self.btn_new, self.btn_settings, self.btn_mass, self.btn_save, self.btn_exit
        ]

    def _rerun_with_settings(self):
        try:
            if self.fig:
                plt.close(self.fig)
            container, boxes = self.current_container, self.current_boxes
            if container is None or boxes is None:
                container, boxes = self.generate_test_data()
            result, exec_time = self.run_algorithm_packing(
                container, boxes,
                prefer_small=self._prefer_small,
                objective=self._objective,
                allow_stacking=self._allow_stacking,
                stack_same_face_only=self._stack_same_face_only
            )
            self.create_visualization(container, result, boxes, exec_time)
        except Exception as e:
            print(f"Ошибка: {e}")

    def on_prefer_small(self, event):
        self._prefer_small = True
        self._rerun_with_settings()

    def on_prefer_large(self, event):
        self._prefer_small = False
        self._rerun_with_settings()

    def on_objective_count(self, event):
        self._objective = "count"
        self._rerun_with_settings()

    def on_objective_volume(self, event):
        self._objective = "volume"
        self._rerun_with_settings()

    def on_toggle_stacking(self, event):
        self._allow_stacking = not self._allow_stacking
        self._rerun_with_settings()

    def on_toggle_same_face(self, event):
        self._stack_same_face_only = not self._stack_same_face_only
        self._rerun_with_settings()
    
    def on_new_test_clicked(self, event):
        """Обработчик кнопки нового теста"""
        try:
            print("Генерация нового теста...")
            if self.fig:
                plt.close(self.fig)
            self.run_test()
        except Exception as e:
            print(f"Ошибка: {e}")
    
    def on_settings_clicked(self, event):
        """Обработчик кнопки настроек"""
        try:
            print("Настройки алгоритма:")
            print("1. Время выполнения: 10.0с")
            print("2. Ширина луча: 8")
            print("3. Альтернативные старты: 3")
            print("4. Диверсификация: включена")
            print("Измените параметры в packing/core/packer.py в классе PackingConfig")
        except Exception as e:
            print(f"Ошибка: {e}")
    
    def on_mass_test_clicked(self, event):
        """Обработчик кнопки массового тестирования"""
        try:
            print("Запуск массового тестирования...")
            results = []
            for i in range(10):
                print(f"  Тест {i+1}/10...")
                container, boxes = self.generate_test_data()
                result, exec_time = self.run_algorithm_packing(container, boxes)
                efficiency = len(result) / len(boxes) * 100 if boxes else 0
                results.append({
                    'test': i+1,
                    'placed': len(result),
                    'total': len(boxes),
                    'efficiency': efficiency,
                    'time': exec_time
                })
                self.test_results.append({
                    'placed': len(result),
                    'total': len(boxes),
                    'efficiency': efficiency,
                    'time': exec_time
                })
            
            # Статистика массового тестирования
            avg_efficiency = sum(r['efficiency'] for r in results) / len(results)
            avg_time = sum(r['time'] for r in results) / len(results)
            print(f"\nРЕЗУЛЬТАТЫ МАССОВОГО ТЕСТИРОВАНИЯ:")
            print(f"   Средняя эффективность: {avg_efficiency:.1f}%")
            print(f"   Среднее время: {avg_time:.3f}с")
            print(f"   Лучший результат: {max(r['efficiency'] for r in results):.1f}%")
            print(f"   Худший результат: {min(r['efficiency'] for r in results):.1f}%")
            
        except Exception as e:
            print(f"Ошибка: {e}")
    
    def on_save_clicked(self, event):
        """Обработчик кнопки сохранения"""
        try:
            if self.test_results:
                with open("algorithm_test_results.json", "w", encoding="utf-8") as f:
                    json.dump(self.test_results, f, ensure_ascii=False, indent=2)
                print(f"Сохранено {len(self.test_results)} результатов тестирования")
            else:
                print("Нет результатов для сохранения")
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
    
    def on_exit_clicked(self, event):
        """Обработчик кнопки выхода"""
        try:
            print("Завершение работы...")
            if self.fig:
                plt.close(self.fig)
            else:
                plt.close('all')
            sys.exit(0)
        except Exception as e:
            print(f"Ошибка: {e}")
    
    def run_test(self):
        """Запуск одиночного теста"""
        # Генерируем данные
        container, boxes = self.generate_test_data()
        
        print(f"Контейнер: {container[3]-container[0]}x{container[4]-container[1]}x{container[5]-container[2]} см")
        print(f"Коробок: {len(boxes)}")
        
        # Запускаем алгоритм
        result, exec_time = self.run_algorithm_packing(container, boxes)
        
        # Сохраняем результат
        efficiency = len(result) / len(boxes) * 100 if boxes else 0
        self.test_results.append({
            'placed': len(result),
            'total': len(boxes),
            'efficiency': efficiency,
            'time': exec_time
        })
        
        # Создаем визуализацию
        self.create_visualization(container, result, boxes, exec_time)

    def _find_label_for_idx(self, idx: int, boxes: List[Tuple]):
        for l, w, h, bid, flag, arrow_axis in boxes:
            if bid == idx:
                return flag
        return None


def main():
    """Главная функция"""
    print("Тестер алгоритма упаковки")
    print("=" * 50)
    print("Возможности:")
    print("  - Тестирование алгоритма на случайных данных")
    print("  - Визуализация результатов")
    print("  - Статистика эффективности")
    print("  - Массовое тестирование")
    print("  - Настройка параметров алгоритма")
    print("=" * 50)
    
    # Запускаем тестер
    tester = AlgorithmTester()
    tester.run_test()


if __name__ == "__main__":
    main()
