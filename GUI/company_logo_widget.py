from PyQt5 import QtWidgets, QtCore, QtGui
import os


class CompanyLogoWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self._pixmap = None
        self._size_percent = 25
        self._rotation = 0
        self._logo_path = ""
        self.hide()

    def apply(self, logo_path: str, size_percent: int, rotation: int = 0):
        self._logo_path = logo_path or ""
        self._size_percent = max(5, min(200, int(size_percent or 25)))
        self._rotation = int(rotation or 0) % 360
        if not self._logo_path or not os.path.exists(self._logo_path):
            self._pixmap = None
            self.hide()
            return
        self._pixmap = self._load_pixmap(self._logo_path, self._target_size())
        if self._rotation:
            transform = QtGui.QTransform()
            transform.rotate(self._rotation)
            self._pixmap = self._pixmap.transformed(transform, QtCore.Qt.SmoothTransformation)
        self.resize(self._pixmap.size())
        self.show()
        self.update()

    def _target_size(self) -> QtCore.QSize:
        parent = self.parentWidget()
        base = 0
        if parent:
            base = max(parent.width(), parent.height())
        target = int(max(64, min(300, (base * 0.2) * (self._size_percent / 100.0))))
        return QtCore.QSize(target, target)

    def _load_pixmap(self, path: str, size: QtCore.QSize) -> QtGui.QPixmap:
        if path.lower().endswith(".svg"):
            # First try QtSvg renderer
            try:
                from PyQt5.QtSvg import QSvgRenderer
                img = QtGui.QImage(size, QtGui.QImage.Format_ARGB32_Premultiplied)
                img.fill(0)
                p = QtGui.QPainter(img)
                renderer = QSvgRenderer(path)
                if renderer.isValid():
                    renderer.render(p)
                    p.end()
                    return QtGui.QPixmap.fromImage(img)
            except Exception:
                pass
            # Fallback: convert SVG to PNG with CairoSVG and load
            try:
                import tempfile
                import cairosvg
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp_path = tmp.name
                cairosvg.svg2png(url=path, write_to=tmp_path, output_width=size.width(), output_height=size.height())
                pm = QtGui.QPixmap(tmp_path)
                if not pm.isNull():
                    return pm.scaled(size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            except Exception:
                pass
        pm = QtGui.QPixmap(path)
        if pm.isNull():
            pm = QtGui.QPixmap(size)
            pm.fill(QtCore.Qt.transparent)
        return pm.scaled(size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

    def position_bottom_right(self, anchor_widget: QtWidgets.QWidget):
        parent = self.parentWidget()
        if not parent or not anchor_widget:
            return
        top_left = anchor_widget.mapTo(parent, QtCore.QPoint(0, 0))
        x = top_left.x() + anchor_widget.width() - self.width() - 10
        y = top_left.y() + anchor_widget.height() - self.height() - 10
        self.move(x, y)
        self.raise_()

    def paintEvent(self, event):
        if not self._pixmap:
            return
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
        p.drawPixmap(0, 0, self._pixmap)
        p.end()


