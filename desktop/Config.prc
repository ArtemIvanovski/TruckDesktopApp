# Конфигурация Panda3D для TruckLoadingApp

# Настройки окна
win-size 1920 1080
window-title Truck Loading Application
show-frame-rate-meter #t
sync-video #t

# Настройки рендеринга
multisamples 4
framebuffer-multisample #t
depth-bits 24
color-bits 32

# Настройки производительности
gl-check-errors #f
gl-force-no-error #t
basic-shaders-only #f

# Настройки моделей
model-cache-dir models/cache
model-cache-textures #t

# Настройки аудио (отключаем, так как не используем)
audio-library-name null

# Настройки отладки
default-directnotify-level warning
notify-level warning