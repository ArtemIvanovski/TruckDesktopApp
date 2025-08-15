import json
import os
from PyQt5.QtCore import QObject, pyqtSignal


class UnitsManager(QObject):
    units_changed = pyqtSignal()

    DISTANCE_UNITS = {
        'cm': {'name': 'Сантиметры', 'factor': 1.0, 'symbol': 'см'},
        'm': {'name': 'Метры', 'factor': 100.0, 'symbol': 'м'},
        'ft': {'name': 'Футы', 'factor': 30.48, 'symbol': 'фт'},
        'yd': {'name': 'Ярды', 'factor': 91.44, 'symbol': 'ярд'}
    }

    WEIGHT_UNITS = {
        'kg': {'name': 'Килограммы', 'factor': 1.0, 'symbol': 'кг'},
        'lb': {'name': 'Фунты', 'factor': 0.453592, 'symbol': 'фунт'},
        'st': {'name': 'Стоуны', 'factor': 6.35029, 'symbol': 'стоун'}
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
        return self.DISTANCE_UNITS[self.distance_unit]['symbol']

    def get_weight_symbol(self):
        return self.WEIGHT_UNITS[self.weight_unit]['symbol']

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