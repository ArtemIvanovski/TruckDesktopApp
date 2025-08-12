# Truck Desktop (Qt Quick 3D, PySide6)

This is a high-performance desktop implementation scaffold of your Babylon.js app using Python + PySide6 + Qt Quick 3D. It will be extended to mirror all features (truck presets, GLB models, boxes creation/drag/rotate/delete, multi-truck management, and live load distribution) while keeping original look & feel.

## Prerequisites
- Python 3.10+ (64-bit)
- Windows 10+

## Install
```powershell
cd desktop
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install PySide6==6.7.2
```

## Run
```powershell
python main.py
```

Ensure `lorry.glb` and `weel.glb` remain in the project root so `desktop/Main.qml` can load them using relative paths.
