class TruckModel:
    def __init__(self, truck_id: int, name: str, width: int, height: int, depth: int):
        self.id = truck_id
        self.name = name
        self.width = width
        self.height = height
        self.depth = depth
        self.ready = False
        self.show_overlay = False
        self.boxes = []
        self.tent_alpha = 0.0
        self.tent_open = True
        # Per-truck load calculation/settings (populated by UI widget)
        self.load_settings = {}

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'width': self.width,
            'height': self.height,
            'depth': self.depth,
            'ready': self.ready,
            'show_overlay': self.show_overlay,
            'boxes': list(self.boxes or []),
            'tent_alpha': self.tent_alpha,
            'tent_open': self.tent_open,
            'load_settings': dict(self.load_settings or {}),
        }

    @staticmethod
    def from_dict(data: dict) -> 'TruckModel':
        model = TruckModel(
            truck_id=int(data.get('id', 1)),
            name=str(data.get('name', 'Грузовик 1')),
            width=int(data.get('width', 1650)),
            height=int(data.get('height', 260)),
            depth=int(data.get('depth', 245)),
        )
        model.ready = bool(data.get('ready', False))
        model.show_overlay = bool(data.get('show_overlay', False))
        model.boxes = list(data.get('boxes', []))
        model.tent_alpha = float(data.get('tent_alpha', 0.0))
        model.tent_open = bool(data.get('tent_open', True))
        model.load_settings = dict(data.get('load_settings', {}))
        return model

