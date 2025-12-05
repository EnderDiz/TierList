# tiles_from_clipboard.py
# Ctrl+V -> взять изображение из буфера, нарезать на 256x256 и сохранить в WebP
# Выход из программы: ESC

import os
from datetime import datetime

from PIL import ImageGrab, Image
import keyboard

TILE_SIZE = 180a
OUT_DIR = "out_tiles"

os.makedirs(OUT_DIR, exist_ok=True)


def slice_to_tiles(img: Image.Image, base_name: str):
    w, h = img.size
    tiles_x = w // TILE_SIZE
    tiles_y = h // TILE_SIZE

    if tiles_x == 0 or tiles_y == 0:
        print("Изображение меньше 256x256, нарезать нельзя.")
        return

    print(f"Размер: {w}x{h}px, плитки: {tiles_x}x{tiles_y} ({tiles_x * tiles_y} шт.)")

    for ty in range(tiles_y):
        for tx in range(tiles_x):
            left = tx * TILE_SIZE
            top = ty * TILE_SIZE
            box = (left, top, left + TILE_SIZE, top + TILE_SIZE)
            tile = img.crop(box)

            filename = f"{base_name}_y{ty}_x{tx}.webp"
            path = os.path.join(OUT_DIR, filename)
            tile.save(path, "WEBP", lossless=True)

    print("Готово.")


def process_clipboard():
    grabbed = ImageGrab.grabclipboard()
    if not isinstance(grabbed, Image.Image):
        print("В буфере нет изображения.")
        return

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"img_{ts}"

    slice_to_tiles(grabbed.convert("RGBA"), base_name)


def main():
    print("Скрипт запущен.")
    print("Сделайте скриншот, скопируйте его (Copy) и нажмите Ctrl+V.")
    print("Файлы сохраняются в папку:", OUT_DIR)
    print("ESC — выход.")

    keyboard.add_hotkey("a", process_clipboard)
    keyboard.wait("esc")


if __name__ == "__main__":
    main()
