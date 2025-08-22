import json
import os
from PyQt5.QtCore import QObject, pyqtSignal
from core.i18n import tr


class UnitsManager(QObject):
    units_changed = pyqtSignal()

    DISTANCE_UNITS = {
        'cm': {'name_key': 'Сантиметры', 'factor': 1.0, 'symbol_key': 'см'},
        'm': {'name_key': 'Метры', 'factor': 100.0, 'symbol_key': 'м'},
        'ft': {'name_key': 'Футы', 'factor': 30.48, 'symbol_key': 'фт'},
        'yd': {'name_key': 'Ярды', 'factor': 91.44, 'symbol_key': 'ярд'}
    }

    WEIGHT_UNITS = {
        'kg': {'name_key': 'Килограммы', 'factor': 1.0, 'symbol_key': 'кг'},
        'lb': {'name_key': 'Фунты', 'factor': 0.453592, 'symbol_key': 'фунт'},
        'st': {'name_key': 'Стоуны', 'factor': 6.35029, 'symbol_key': 'стоун'}
    }

    def __init__(self):
        super().__init__()
        self.distance_unit = 'cm'
        self.weight_unit = 'kg'
        self.settings_file = 'units_settings.json'
        self.load_settings()

    def to_internal_distance(self, value, unit=None):
        unit = unit or self.distance_unit
        return value * self.DISTANCE_UNITS[unit]['factor']

    def from_internal_distance(self, value, unit=None):
        unit = unit or self.distance_unit
        return value / self.DISTANCE_UNITS[unit]['factor']

    def to_internal_weight(self, value, unit=None):
        unit = unit or self.weight_unit
        return value * self.WEIGHT_UNITS[unit]['factor']

    def from_internal_weight(self, value, unit=None):
        unit = unit or self.weight_unit
        return value / self.WEIGHT_UNITS[unit]['factor']

    def get_distance_symbol(self):
        return tr(self.DISTANCE_UNITS[self.distance_unit]['symbol_key'])

    def get_weight_symbol(self):
        return tr(self.WEIGHT_UNITS[self.weight_unit]['symbol_key'])
    
    def get_distance_name(self, unit=None):
        unit = unit or self.distance_unit
        return tr(self.DISTANCE_UNITS[unit]['name_key'])
    
    def get_weight_name(self, unit=None):
        unit = unit or self.weight_unit
        return tr(self.WEIGHT_UNITS[unit]['name_key'])

    def set_units(self, distance_unit=None, weight_unit=None):
        if distance_unit and distance_unit in self.DISTANCE_UNITS:
            self.distance_unit = distance_unit
        if weight_unit and weight_unit in self.WEIGHT_UNITS:
            self.weight_unit = weight_unit
        self.save_settings()
        self.units_changed.emit()

    def save_settings(self):
        settings = {
            'distance_unit': self.distance_unit,
            'weight_unit': self.weight_unit
        }
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f)

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                self.distance_unit = settings.get('distance_unit', 'cm')
                self.weight_unit = settings.get('weight_unit', 'kg')
            except:
                pass