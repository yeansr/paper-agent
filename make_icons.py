"""
生成 PWA 应用图标
=================

用 PIL 生成 192x192 与 512x512 两档 PNG 图标（安卓 PWA 需要）。

设计：品牌蓝圆角底 + 白色文档图形（文档上有文字行），在小尺寸下也清晰可辨。
为适配安卓"自适应图标"（maskable），主体内容放在中间约 75% 安全区内，
避免被系统圆形/圆角遮罩裁切。

运行：
    python make_icons.py
"""

from __future__ import annotations

import pathlib

from PIL import Image, ImageDraw

STATIC_DIR = pathlib.Path(__file__).resolve().parent / "static"
BRAND_BLUE = (47, 111, 237)      # #2f6fed
WHITE = (255, 255, 255)
LINE_BLUE = (47, 111, 237)


def _rounded_rect(draw: ImageDraw.ImageDraw, box, radius: int, fill) -> None:
    """兼容多版本 Pillow 的圆角矩形绘制。"""
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def make_icon(size: int) -> Image.Image:
    # 透明背景，图标本身画圆角矩形（也可由系统再遮罩）
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 1) 背景圆角方块（半径约为边长 22%）
    _rounded_rect(d, (0, 0, size - 1, size - 1), radius=int(size * 0.22), fill=BRAND_BLUE)

    # 2) 中间白色文档（占中间约 44% 宽、52% 高，保证在安全区内）
    doc_w = int(size * 0.44)
    doc_h = int(size * 0.52)
    x0 = (size - doc_w) // 2
    y0 = int(size * 0.24)
    x1, y1 = x0 + doc_w, y0 + doc_h
    _rounded_rect(d, (x0, y0, x1, y1), radius=int(size * 0.05), fill=WHITE)

    # 3) 文档上的文字行（蓝色短横线），共 4 条，宽度递减
    line_h = max(3, int(size * 0.022))
    gap = int(size * 0.055)
    line_x0 = x0 + int(size * 0.08)
    line_x1 = x1 - int(size * 0.08)
    ly = y0 + int(size * 0.10)
    for i in range(4):
        end = line_x1 if i < 3 else line_x0 + int((line_x1 - line_x0) * 0.6)
        _rounded_rect(
            d, (line_x0, ly, end, ly + line_h),
            radius=line_h // 2, fill=LINE_BLUE,
        )
        ly += gap + line_h

    return img


def main() -> None:
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    for size in (192, 512):
        out = STATIC_DIR / f"icon-{size}.png"
        make_icon(size).save(out, format="PNG")
        print(f"已生成 {out}（{size}x{size}）")

    # 额外生成一个 512 maskable 版本（满幅背景，供安卓自适应图标使用）
    maskable = STATIC_DIR / "icon-512-maskable.png"
    make_icon(512).save(maskable, format="PNG")
    print(f"已生成 {maskable}")


if __name__ == "__main__":
    main()
