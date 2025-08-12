# -*- coding: utf-8 -*-
from direct.gui.DirectGui import DirectButton, DirectEntry, DirectCheckButton, DirectFrame
from direct.gui import DirectGuiGlobals as DGG
from panda3d.core import TextNode, Filename
import os
import logging
from i18n import t
from config import LANG


class TabSystem:
    def __init__(self, app):
        self.app = app
        self.active_tab = 'file'
        self.tab_buttons = {}
        self.tab_panels = {}
        self.logger = logging.getLogger(__name__)
        self.ui_font = self._ensure_cyrillic_font()
        # Colors / style
        self.color_bar = (0.12, 0.12, 0.14, 1.0)
        self.color_tab_active = (0.03, 0.42, 0.64, 1.0)
        self.color_tab_hover = (0.18, 0.18, 0.22, 1.0)
        self.color_tab_idle = (0.16, 0.16, 0.18, 1.0)
        self._create_tab_bar()
        self._create_tab_panels()
        
    def _ensure_cyrillic_font(self):
        """Возвращает шрифт с поддержкой кириллицы; пытается загрузить из локальной папки или системы."""
        try:
            # Используем уже загруженный шрифт, если он есть
            font = getattr(self.app, 'ui_font', None)
            if font:
                self.logger.debug("UI font already set on app: %s", font)
                return font

            fonts_dir = os.path.join(os.path.dirname(__file__), 'fonts')
            candidates = [
                os.path.join(fonts_dir, 'arial.ttf'),
                os.path.join(fonts_dir, 'NotoSans-Regular.ttf'),
                os.path.join(fonts_dir, 'NotoSans_Condensed-Regular.ttf'),
                os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'arial.ttf'),
            ]
            for path in candidates:
                try:
                    panda_fn = Filename.fromOsSpecific(path)
                    panda_fn.makeTrueCase()
                    exists = panda_fn.exists() or os.path.exists(path)
                    if exists:
                        self.logger.info("Attempting to load UI font: %s", path)
                        font = self.app.loader.loadFont(panda_fn)
                        if font:
                            self.app.ui_font = font
                            self.logger.info("UI font loaded: %s", path)
                            return font
                        else:
                            self.logger.warning("loadFont returned None for: %s", path)
                except Exception as e:
                    self.logger.error("Error loading font %s: %s", path, e)
        except Exception as e:
            self.logger.error("Unexpected error in _ensure_cyrillic_font: %s", e)

        self.logger.warning("Failed to load a Cyrillic-capable font; UI may not render Cyrillic correctly")
        return None

    def _create_tab_bar(self):
        """Создает верхнюю панель с табами"""
        # Фон для панели табов
        self.tab_bar = DirectFrame(
            frameSize=(-2, 2, 0.85, 1.0),
            frameColor=self.color_bar,
            pos=(0, 0, 0),
            parent=self.app.aspect2d
        )
        
        # Табы
        tab_width = 0.34
        tab_start_x = -1.9
        tabs = [
            ('file', 'Файл'),
            ('edit', 'Правка'), 
            ('view', 'Вид'),
            ('truck', 'Грузовик'),
            ('boxes', 'Коробки'),
            ('help', 'Справка')
        ]
        
        for i, (tab_id, tab_name) in enumerate(tabs):
            x_pos = tab_start_x + i * tab_width
            self.tab_buttons[tab_id] = self._make_tab_button(tab_id, tab_name, x_pos, active=(tab_id == 'file'))

    def _make_tab_button(self, tab_id: str, title: str, x_pos: float, active: bool = False):
        color = self.color_tab_active if active else self.color_tab_idle
        btn = DirectButton(
            text=title,
            scale=0.05,
            pos=(x_pos, 0, 0.925),
            frameSize=(-3.8, 3.8, -0.85, 0.85),
            text_fg=(1, 1, 1, 1),
            frameColor=color,
            command=lambda tid=tab_id: self.switch_tab(tid),
            parent=self.app.aspect2d,
            relief=DGG.RAISED,
            borderWidth=(0.01, 0.01),
            text_font=self.ui_font,
            text_scale=1.0,
            pad=(0.2, 0.1)
        )
        # Hover effect
        def on_enter(_):
            if self.active_tab != tab_id:
                btn['frameColor'] = self.color_tab_hover
        def on_exit(_):
            if self.active_tab != tab_id:
                btn['frameColor'] = self.color_tab_idle
        btn.bind(DGG.ENTER, on_enter)
        btn.bind(DGG.EXIT, on_exit)
        return btn
            
    def _create_tab_panels(self):
        """Создает панели для каждого таба"""
        # Панель "Файл"
        self.tab_panels['file'] = self._create_file_panel()
        
        # Панель "Правка"
        self.tab_panels['edit'] = self._create_edit_panel()
        
        # Панель "Вид"
        self.tab_panels['view'] = self._create_view_panel()
        
        # Панель "Грузовик"
        self.tab_panels['truck'] = self._create_truck_panel()
        
        # Панель "Коробки"
        self.tab_panels['boxes'] = self._create_boxes_panel()
        
        # Панель "Справка"
        self.tab_panels['help'] = self._create_help_panel()
        
        # Показываем только активную панель
        self.switch_tab('file')
    
    def _create_file_panel(self):
        """Панель Файл"""
        panel = DirectFrame(
            frameSize=(-2, 2, 0.4, 0.85),
            frameColor=(0.15, 0.15, 0.17, 0.95),
            pos=(0, 0, 0),
            parent=self.app.aspect2d
        )
        
        # Кнопки файлового меню
        DirectButton(text='Новый', scale=0.04, pos=(-1.8, 0, 0.75), 
                    command=self._new_file, parent=panel, 
                    frameColor=(0.23, 0.62, 0.32, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        DirectButton(text='Открыть', scale=0.04, pos=(-1.5, 0, 0.75), 
                    command=self._open_file, parent=panel,
                    frameColor=(0.16, 0.46, 0.86, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        DirectButton(text='Сохранить', scale=0.04, pos=(-1.2, 0, 0.75), 
                    command=self._save_file, parent=panel,
                    frameColor=(0.86, 0.34, 0.34, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        DirectButton(text='Экспорт', scale=0.04, pos=(-0.9, 0, 0.75), 
                    command=self._export_file, parent=panel,
                    frameColor=(0.86, 0.7, 0.25, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        DirectButton(text='Настройки', scale=0.04, pos=(-0.6, 0, 0.75), 
                    command=self._settings, parent=panel,
                    frameColor=(0.35, 0.35, 0.38, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        
        return panel
    
    def _create_edit_panel(self):
        """Панель Правка"""
        panel = DirectFrame(
            frameSize=(-2, 2, 0.4, 0.85),
            frameColor=(0.15, 0.15, 0.17, 0.95),
            pos=(0, 0, 0),
            parent=self.app.aspect2d
        )
        
        DirectButton(text='Отменить', scale=0.04, pos=(-1.8, 0, 0.75), 
                    command=self._undo, parent=panel,
                    frameColor=(0.86, 0.34, 0.34, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        DirectButton(text='Повторить', scale=0.04, pos=(-1.5, 0, 0.75), 
                    command=self._redo, parent=panel,
                    frameColor=(0.23, 0.62, 0.32, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        DirectButton(text='Копировать', scale=0.04, pos=(-1.2, 0, 0.75), 
                    command=self._copy, parent=panel,
                    frameColor=(0.36, 0.42, 0.86, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        DirectButton(text='Вставить', scale=0.04, pos=(-0.9, 0, 0.75), 
                    command=self._paste, parent=panel,
                    frameColor=(0.86, 0.7, 0.25, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        
        return panel
    
    def _create_view_panel(self):
        """Панель Вид"""
        panel = DirectFrame(
            frameSize=(-2, 2, 0.4, 0.85),
            frameColor=(0.15, 0.15, 0.17, 0.95),
            pos=(0, 0, 0),
            parent=self.app.aspect2d
        )
        
        DirectButton(text='Сверху', scale=0.04, pos=(-1.8, 0, 0.75), 
                    command=self._view_top, parent=panel,
                    frameColor=(0.16, 0.46, 0.86, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        DirectButton(text='Слева', scale=0.04, pos=(-1.5, 0, 0.75), 
                    command=self._view_left, parent=panel,
                    frameColor=(0.16, 0.46, 0.86, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        DirectButton(text='Справа', scale=0.04, pos=(-1.2, 0, 0.75), 
                    command=self._view_right, parent=panel,
                    frameColor=(0.16, 0.46, 0.86, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        DirectButton(text='Сброс', scale=0.04, pos=(-0.9, 0, 0.75), 
                    command=self._view_reset, parent=panel,
                    frameColor=(0.86, 0.34, 0.34, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        DirectButton(text='Полный экран', scale=0.04, pos=(-0.6, 0, 0.75), 
                    command=self._fullscreen, parent=panel,
                    frameColor=(0.35, 0.35, 0.38, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        
        return panel
    
    def _create_truck_panel(self):
        """Панель Грузовик"""
        panel = DirectFrame(
            frameSize=(-2, 2, 0.4, 0.85),
            frameColor=(0.15, 0.15, 0.17, 0.95),
            pos=(0, 0, 0),
            parent=self.app.aspect2d
        )
        
        DirectButton(text='Тент 13.6', scale=0.04, pos=(-1.8, 0, 0.75), 
                    command=lambda: self.app.switch_truck(1360, 260, 245), parent=panel,
                    frameColor=(0.66, 0.36, 0.76, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        DirectButton(text='Тент 16.5', scale=0.04, pos=(-1.5, 0, 0.75), 
                    command=lambda: self.app.switch_truck(1650, 260, 245), parent=panel,
                    frameColor=(0.66, 0.36, 0.76, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        DirectButton(text='Мега', scale=0.04, pos=(-1.2, 0, 0.75), 
                    command=lambda: self.app.switch_truck(1360, 300, 245), parent=panel,
                    frameColor=(0.66, 0.36, 0.76, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        DirectButton(text='Открыть', scale=0.04, pos=(-0.9, 0, 0.75), 
                    command=lambda: self.app.set_tent_alpha(0.0), parent=panel,
                    frameColor=(0.23, 0.62, 0.32, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        DirectButton(text='Закрыть', scale=0.04, pos=(-0.6, 0, 0.75), 
                    command=lambda: self.app.set_tent_alpha(0.3), parent=panel,
                    frameColor=(0.86, 0.34, 0.34, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        
        return panel
    
    def _create_boxes_panel(self):
        """Панель Коробки"""
        panel = DirectFrame(
            frameSize=(-2, 2, 0.4, 0.85),
            frameColor=(0.15, 0.15, 0.17, 0.95),
            pos=(0, 0, 0),
            parent=self.app.aspect2d
        )
        
        DirectButton(text='Добавить', scale=0.04, pos=(-1.8, 0, 0.75), 
                    command=self._add_box, parent=panel,
                    frameColor=(0.23, 0.62, 0.32, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        DirectButton(text='Удалить', scale=0.04, pos=(-1.5, 0, 0.75), 
                    command=self._delete_box, parent=panel,
                    frameColor=(0.86, 0.34, 0.34, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        DirectButton(text='Копировать', scale=0.04, pos=(-1.2, 0, 0.75), 
                    command=self._copy_box, parent=panel,
                    frameColor=(0.36, 0.42, 0.86, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        DirectButton(text='Разместить', scale=0.04, pos=(-0.9, 0, 0.75), 
                    command=self._auto_place, parent=panel,
                    frameColor=(0.86, 0.7, 0.25, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        DirectButton(text='Очистить', scale=0.04, pos=(-0.6, 0, 0.75), 
                    command=self._clear_boxes, parent=panel,
                    frameColor=(0.35, 0.35, 0.38, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        
        return panel
    
    def _create_help_panel(self):
        """Панель Справка"""
        panel = DirectFrame(
            frameSize=(-2, 2, 0.4, 0.85),
            frameColor=(0.15, 0.15, 0.17, 0.95),
            pos=(0, 0, 0),
            parent=self.app.aspect2d
        )
        
        DirectButton(text='Справка', scale=0.04, pos=(-1.8, 0, 0.75), 
                    command=self._help, parent=panel,
                    frameColor=(0.16, 0.46, 0.86, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        DirectButton(text='Горячие клавиши', scale=0.04, pos=(-1.4, 0, 0.75), 
                    command=self._hotkeys, parent=panel,
                    frameColor=(0.86, 0.7, 0.25, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        DirectButton(text='О программе', scale=0.04, pos=(-1.0, 0, 0.75), 
                    command=self._about, parent=panel,
                    frameColor=(0.35, 0.35, 0.38, 1), text_fg=(1,1,1,1), relief=DGG.RAISED, text_font=self.ui_font)
        
        return panel
    
    def switch_tab(self, tab_id):
        """Переключение между табами"""
        # Скрываем все панели
        for panel in self.tab_panels.values():
            panel.hide()
        
        # Сбрасываем цвета всех кнопок табов
        for tid, button in self.tab_buttons.items():
            if tid == tab_id:
                button['frameColor'] = self.color_tab_active  # Активный
            else:
                button['frameColor'] = self.color_tab_idle  # Неактивный
        
        # Показываем выбранную панель
        if tab_id in self.tab_panels:
            self.tab_panels[tab_id].show()
        
        self.active_tab = tab_id
    
    # Методы-заглушки для функций кнопок
    def _new_file(self): print("Новый файл")
    def _open_file(self): print("Открыть файл")
    def _save_file(self): print("Сохранить файл")
    def _export_file(self): print("Экспорт")
    def _settings(self): print("Настройки")
    
    def _undo(self): print("Отменить")
    def _redo(self): print("Повторить")
    def _copy(self): print("Копировать")
    def _paste(self): print("Вставить")
    
    def _view_top(self):
        cam = self.app.arc
        cam.radius = 1400
        cam.alpha = 3.14159265 / 2
        cam.beta = 0.00001
        cam.update()
    
    def _view_left(self):
        cam = self.app.arc
        cam.radius = 1400
        cam.alpha = 3.14159265 / 2
        cam.beta = 3.14159265 / 2
        cam.update()
    
    def _view_right(self):
        cam = self.app.arc
        cam.radius = 1400
        cam.alpha = -3.14159265 / 2
        cam.beta = 3.14159265 / 2
        cam.update()
    
    def _view_reset(self):
        cam = self.app.arc
        cam.radius = 2000
        cam.alpha = 3.14159265 / 2
        cam.beta = 3.14159265 / 3
        cam.target.set(0, 300, 0)
        cam.update()
    
    def _fullscreen(self): print("Полный экран")
    
    def _add_box(self): print("Добавить коробку")
    def _delete_box(self): print("Удалить коробку")
    def _copy_box(self): print("Копировать коробку")
    def _auto_place(self): print("Автоматическое размещение")
    def _clear_boxes(self): print("Очистить коробки")
    
    def _help(self): print("Справка")
    def _hotkeys(self): print("Горячие клавиши")
    def _about(self): print("О программе")


class TrailerUI:
    """Старый DirectGUI UI. Больше не используется, если UI хостится через Qt.
    Оставлен для совместимости/отладки."""
    def __init__(self, app):
        self.app = app
        self.tab_system = TabSystem(app)
        self._build_right_panel()

    def _build_right_panel(self):
        # Правая боковая панель (сдвинута вниз, чтобы не перекрываться с табами)
        x0 = 1.15
        dx = 0.22
        y_top = 0.35  # Сдвинули вниз
        
        # Поля ввода размеров
        self.input_len = DirectEntry(text=str(self.app.truck_width), scale=0.045, pos=(1.15, 0, 0.25), initialText=str(self.app.truck_width), numLines=1, focus=0)
        self.input_wid = DirectEntry(text=str(self.app.truck_depth), scale=0.045, pos=(1.45, 0, 0.25), initialText=str(self.app.truck_depth), numLines=1, focus=0)
        self.input_hei = DirectEntry(text=str(self.app.truck_height), scale=0.045, pos=(1.75, 0, 0.25), initialText=str(self.app.truck_height), numLines=1, focus=0)

        self.button_apply_dims = DirectButton(text=t(LANG, 'btn_ok'), scale=0.045, pos=(2.0, 0, 0.25), command=self._apply_dims)

    def _on_tent_136(self):
        self.app.switch_truck(1360, 260, 245)

    def _on_tent_165(self):
        self.app.switch_truck(1650, 260, 245)

    def _on_mega(self):
        # Пример мега: высота больше
        self.app.switch_truck(1360, 300, 245)

    def _on_cont40(self):
        # Условные размеры контейнера 40 футов (примерно, как в web-кнопках)
        self.app.switch_truck(1203, 239, 235)

    def _apply_dims(self):
        try:
            w = int(float(self.input_len.get()))
            h = int(float(self.input_hei.get()))
            d = int(float(self.input_wid.get()))
            self.app.switch_truck(w, h, d)
        except Exception:
            pass

    def _open_tent(self):
        self.app.set_tent_alpha(0.0)

    def _close_tent(self):
        self.app.set_tent_alpha(0.3)

    # View handlers
    def _view_top(self):
        cam = self.app.arc
        cam.target = cam.target  # no-op
        cam.radius = 1400
        cam.alpha = 3.14159265 / 2
        cam.beta = 0.00001
        cam.update()

    def _view_left(self):
        cam = self.app.arc
        cam.radius = 1400
        cam.alpha = 3.14159265 / 2
        cam.beta = 3.14159265 / 2
        cam.update()

    def _view_right(self):
        cam = self.app.arc
        cam.radius = 1400
        cam.alpha = -3.14159265 / 2
        cam.beta = 3.14159265 / 2
        cam.update()


