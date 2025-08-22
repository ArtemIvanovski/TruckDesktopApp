import json
import os
from PyQt5.QtCore import QObject, pyqtSignal


class LoadCalculator(QObject):
    settings_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.settings_file = 'load_calculation_settings.json'
        self.default_settings = {
            'Mt': 8.0,
            'Nt_data': 2.5,
            'Lt': 3.5,
            'L_data': 0.4,
            'Mp': 8.0,
            'LC': 4.2,
            'LB': 1.7,
            'Ntp': 1.6,
            'Mg1': 4.0,
            'Mg2': 4.0,
            'Mg3': 4.0,
            'Mg4': 4.0,
            'season_limit': False,
            'show_on_main_screen': False
        }
        self.settings = self.default_settings.copy()
        self.load_settings()

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                self.settings.update(loaded)
            except:
                pass

    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f)
        self.settings_changed.emit()

    def update_setting(self, key, value):
        if key in self.settings:
            self.settings[key] = value
            self.save_settings()

    def get_setting(self, key):
        return self.settings.get(key, self.default_settings.get(key, 0))

    def set_trailer_length(self, length_cm):
        self.settings['LA'] = length_cm / 100.0
        self.save_settings()

    def get_trailer_length(self):
        return self.settings.get('LA', 13.6)

    def calculate_loads(self):
        if self.settings['season_limit']:
            N1_max, N2_max = 9, 9
            N1_max_kz, N2_max_kz = 8, 8
            NPP_max, NPP_max_kz = 22.5, 18
            Map_max, Map_max_kz = 40, 32
        else:
            N1_max, N2_max = 9, 9
            N1_max_kz, N2_max_kz = 10, 10
            NPP_max, NPP_max_kz = 22.5, 24
            Map_max, Map_max_kz = 40, 40

        Mt = self.settings['Mt']
        Lt = self.settings['Lt']
        L_data = self.settings['L_data']
        Nt_data = self.settings['Nt_data']
        Mp = self.settings['Mp']
        LA = self.get_trailer_length()
        LC = self.settings['LC']
        LB0 = self.settings['LB']
        LB = LA - LB0 - LC
        Ntp = self.settings['Ntp']
        Mg1 = self.settings['Mg1']
        Mg2 = self.settings['Mg2']
        Mg3 = self.settings['Mg3']
        Mg4 = self.settings['Mg4']

        if Mt > 0 and Lt > 0 and Mp > 0 and LA > 0 and LC > 0 and LB > 0:
            if Nt_data > 0:
                N2t = Nt_data
                Xt = N2t * Lt / Mt
            else:
                N2t = 0.3 * Mt
                Xt = N2t * Lt / Mt

            L2 = L_data
            L1 = Lt - L2

            if Ntp == 0:
                Ntp = 0.2 * Mp

            Xp = Ntp * LB / Mp
            Lb = LA / 4
            X1 = 3 * Lb + (Lb / 2) - LC
            X2 = 2 * Lb + (Lb / 2) - LC
            X3 = Lb + (Lb / 2) - LC
            X4 = (Lb / 2) - LC

            Mg = Mg1 + Mg2 + Mg3 + Mg4
            a = (Mg1 * X1 + Mg2 * X2 + Mg3 * X3 + Mg4 * X4) / Mg if Mg > 0 else 0
            Map = Mg + Mt + Mp

            N = (Mg * a + Mp * Xp) / LB
            N2 = (Mt * Xt + N * L1) / Lt
            N1 = Mt + N - N2
            N3 = Mg + Mp - N

            return {
                'N1': round(N1, 3),
                'N2': round(N2, 3),
                'N3': round(N3, 3),
                'Mg': round(Mg, 3),
                'Map': round(Map, 3),
                'N1_max': N1_max,
                'N2_max': N2_max,
                'NPP_max': NPP_max,
                'Map_max': Map_max,
                'N1_max_kz': N1_max_kz,
                'N2_max_kz': N2_max_kz,
                'NPP_max_kz': NPP_max_kz,
                'Map_max_kz': Map_max_kz,
                'N1_exceeded': N1 > N1_max,
                'N2_exceeded': N2 > N2_max,
                'N3_exceeded': N3 > NPP_max,
                'Map_exceeded': Map > Map_max
            }
        else:
            return None
