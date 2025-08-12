#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Dict


TRANSLATIONS: Dict[str, Dict[str, str]] = {
    'ru': {
        'btn_tent_136': 'тент 13.6',
        'btn_tent_165': 'тент 16.5',
        'btn_open': 'открыт',
        'btn_close': 'закрыт',
        'btn_ok': 'ок',
        'exit': 'Выход',
        'controls_hint': 'ЛКМ — вращать\nПКМ — двигаться вдоль сцены\nКолесо — зум\nEsc — выход',
        'zone': 'Зона {i}: {w} кг',
    },
    'en': {
        'btn_tent_136': 'tent 13.6',
        'btn_tent_165': 'tent 16.5',
        'btn_open': 'open',
        'btn_close': 'close',
        'btn_ok': 'ok',
        'exit': 'Exit',
        'controls_hint': 'LMB — rotate\nRMB — pan\nWheel — zoom\nEsc — exit',
        'zone': 'Zone {i}: {w} kg',
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    table = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    s = table.get(key, key)
    if kwargs:
        return s.format(**kwargs)
    return s


