"""make_logo.py — generate Kofty logo PNGs and ICO from pure PIL."""
from PIL import Image, ImageDraw

SIZES = [512, 256, 128, 64, 32, 16]
REF = 512.0  # reference size for coordinates below

BLUE = (30, 58, 138, 255)     # #1E3A8A
WHITE = (255, 255, 255, 255)


def draw_kofty(size: int) -> Image.Image:
    s = size / REF
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Rounded square background
    r = max(1, int(96 * s))
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=BLUE)

    # Top bar (input edge)
    d.rounded_rectangle(
        [int(112 * s), int(128 * s), int(400 * s), int(176 * s)],
        radius=max(1, int(16 * s)),
        fill=WHITE,
    )

    # Middle chevron (funnel)
    chev = [
        (int(112 * s), int(240 * s)),
        (int(256 * s), int(336 * s)),
        (int(400 * s), int(240 * s)),
        (int(400 * s), int(304 * s)),
        (int(256 * s), int(400 * s)),
        (int(112 * s), int(304 * s)),
    ]
    d.polygon(chev, fill=WHITE)

    # Bottom circle (output spark)
    cx, cy, rad = int(256 * s), int(432 * s), max(1, int(28 * s))
    d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=WHITE)

    return img


def main():
    for size in SIZES:
        img = draw_kofty(size)
        img.save(f"kofty_{size}.png")
        print(f"wrote kofty_{size}.png")

    # Multi-resolution ICO from the 512 PNG
    Image.open("kofty_512.png").save(
        "kofty.ico",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print("wrote kofty.ico")


if __name__ == "__main__":
    main()
