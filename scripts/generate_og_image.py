#!/usr/bin/env python3
"""Generate OG image (1200x630) for GitPulse social-media preview.

Clean, centered design optimised for Google/social previews.
Large elements stay readable even at small thumbnail sizes.
Uses Pillow only - no external fonts.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630

# Brand palette
BG = (10, 10, 15)
SURFACE = (18, 18, 24)
CARD_BG = (20, 22, 30)
INDIGO = (99, 102, 241)
BLUE = (79, 139, 255)
WHITE = (255, 255, 255)
GRAY_1 = (200, 205, 215)
GRAY_2 = (140, 148, 165)
GRAY_3 = (80, 86, 100)
ACCENT_GLOW = (99, 102, 241, 40)


def _font(names: list[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _lerp_color(a: tuple[int, ...], b: tuple[int, ...], t: float) -> tuple[int, ...]:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(min(len(a), len(b))))


def _draw_gradient_rect(
    img: Image.Image,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    c1: tuple[int, ...],
    c2: tuple[int, ...],
    vertical: bool = True,
) -> None:
    draw = ImageDraw.Draw(img)
    if vertical:
        for y in range(y1, y2):
            t = (y - y1) / max(1, y2 - y1 - 1)
            draw.line([(x1, y), (x2 - 1, y)], fill=_lerp_color(c1, c2, t))
    else:
        for x in range(x1, x2):
            t = (x - x1) / max(1, x2 - x1 - 1)
            draw.line([(x, y1), (x, y2 - 1)], fill=_lerp_color(c1, c2, t))


def _draw_rounded_gradient_rect(
    img: Image.Image,
    x: int,
    y: int,
    w: int,
    h: int,
    radius: int,
    c1: tuple[int, ...],
    c2: tuple[int, ...],
) -> None:
    block = Image.new("RGB", (w, h), BG)
    _draw_gradient_rect(block, 0, 0, w, h, c1, c2, vertical=False)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
    img.paste(block, (x, y), mask)


def _draw_glow_line(
    img: Image.Image,
    points: list[tuple[int, int]],
    color: tuple[int, ...],
    width: int = 3,
    glow_radius: int = 8,
) -> None:
    """Draw a line with a soft glow effect."""
    # Draw glow layers (wider, more transparent)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(overlay)
    for r in range(glow_radius, 0, -1):
        alpha = int(18 * (1 - r / glow_radius))
        glow_color = (*color[:3], alpha)
        glow_draw.line(points, fill=glow_color, width=width + r * 2, joint="curve")
    img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"))
    # Draw crisp main line
    draw = ImageDraw.Draw(img)
    draw.line(points, fill=color, width=width, joint="curve")


def main() -> None:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # -- Fonts ------------------------------------------------------------
    bold = ["segoeuib", "arialbd", "Helvetica-Bold", "DejaVuSans-Bold"]
    semi = ["seguisb", "segoeuib", "arialbd", "Helvetica-Bold", "DejaVuSans-Bold"]
    reg = ["segoeui", "arial", "Helvetica", "DejaVuSans"]

    f_name = _font(bold, 80)
    f_tagline = _font(reg, 26)
    f_domain = _font(semi, 16)

    cx = W // 2  # horizontal centre

    # -- Soft radial glow behind logo area --------------------------------
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    for r in range(300, 0, -2):
        alpha = int(12 * (1 - r / 300))
        glow_draw.ellipse(
            [cx - r, 200 - r, cx + r, 200 + r],
            fill=(99, 102, 241, alpha),
        )
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(img)

    # -- Top accent line (3px, gradient indigo -> blue -> indigo) -----------
    for x in range(W):
        t = x / W
        c = (
            _lerp_color(INDIGO, BLUE, t * 2)
            if t < 0.5
            else _lerp_color(BLUE, INDIGO, (t - 0.5) * 2)
        )
        draw.line([(x, 0), (x, 2)], fill=c)

    # -- Logo icon (centred, 180x180) -------------------------------------
    icon_s = 180
    icon_x = cx - icon_s // 2
    icon_y = 90

    # Render the newest GitLab tanuki tile with gradients using CairoSVG
    logo_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
      <defs>
        <!-- Shading Gradients for GitLab Tanuki Triangles -->
        <linearGradient id="gpGradCenter" x1="18" y1="19" x2="31" y2="42" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#ff7a00"/>
          <stop offset="100%" stop-color="#e24329"/>
        </linearGradient>
        <linearGradient id="gpGradLeftEar" x1="11" y1="6" x2="18" y2="27" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#fc6d26"/>
          <stop offset="100%" stop-color="#e24329"/>
        </linearGradient>
        <linearGradient id="gpGradRightEar" x1="37" y1="6" x2="31" y2="27" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#fc6d26"/>
          <stop offset="100%" stop-color="#e24329"/>
        </linearGradient>
        <linearGradient id="gpGradLeftCheek" x1="6" y1="27" x2="24" y2="42" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#fca326"/>
          <stop offset="100%" stop-color="#fc6d26"/>
        </linearGradient>
        <linearGradient id="gpGradRightCheek" x1="42" y1="27" x2="24" y2="42" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#fca326"/>
          <stop offset="100%" stop-color="#fc6d26"/>
        </linearGradient>
      </defs>

      <!-- GitLab Tanuki with Gradients -->
      <g opacity="0.85">
        <path d="M6 27.4152L17.9932 18.9935L23.9627 42Z" fill="url(#gpGradLeftCheek)" />
        <path d="M42 27.4152L30.9661 18.9935L23.9627 42Z" fill="url(#gpGradRightCheek)" />
        <path d="M11.0151 6L17.9932 18.9935L6 27.4152Z" fill="url(#gpGradLeftEar)" />
        <path d="M36.9957 6L30.9661 18.9935L42 27.4152Z" fill="url(#gpGradRightEar)" />
        <path d="M17.9932 18.9935H30.9661L23.9627 42Z" fill="url(#gpGradCenter)" />
      </g>

      <!-- Glowing ECG Pulse Line -->
      <path d="M2 24H16L18 27L21.5 10L24.5 38L27.5 21L30 24H46" fill="none" stroke="#00f0ff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" opacity="0.55" />
      <path d="M2 24H16L18 27L21.5 10L24.5 38L27.5 21L30 24H46" fill="none" stroke="#18171d" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" opacity="0.38" />
      <path d="M2 24H16L18 27L21.5 10L24.5 38L27.5 21L30 24H46" fill="none" stroke="#ffffff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
    </svg>"""

    import io

    import cairosvg

    png_bytes = cairosvg.svg2png(
        bytestring=logo_svg.encode("utf-8"), output_width=icon_s, output_height=icon_s
    )
    logo_img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    img.paste(logo_img, (icon_x, icon_y), logo_img)
    draw = ImageDraw.Draw(img)  # re-acquire after paste

    # -- App name (centred below icon) ------------------------------------
    name = "GitPulse"
    name_bbox = f_name.getbbox(name)
    name_w = name_bbox[2] - name_bbox[0]
    name_y = icon_y + icon_s + 20
    draw.text(
        (cx - name_w // 2 - name_bbox[0], name_y - name_bbox[1]), name, fill=WHITE, font=f_name
    )

    # -- Short separator line (centred, 120px) ----------------------------
    sep_w = 120
    sep_y = name_y + (name_bbox[3] - name_bbox[1]) + 24
    for x in range(cx - sep_w // 2, cx + sep_w // 2):
        t = abs(x - cx) / (sep_w // 2)
        alpha = int(200 * (1 - t))
        draw.point((x, sep_y), fill=_lerp_color(INDIGO, BG, t))

    # -- Tagline (centred, single line) -----------------------------------
    tagline = "DevOps Teaching Assistant for GitLab"
    tag_bbox = f_tagline.getbbox(tagline)
    tag_w = tag_bbox[2] - tag_bbox[0]
    tag_y = sep_y + 20
    draw.text(
        (cx - tag_w // 2 - tag_bbox[0], tag_y - tag_bbox[1]), tagline, fill=GRAY_1, font=f_tagline
    )

    # -- Bottom strip -----------------------------------------------------
    bar_h = 44
    bar_y = H - bar_h
    draw.rectangle([0, bar_y, W, H], fill=SURFACE)
    for x in range(W):
        t = x / W
        c = (
            _lerp_color(INDIGO, BLUE, t * 2)
            if t < 0.5
            else _lerp_color(BLUE, INDIGO, (t - 0.5) * 2)
        )
        draw.point((x, bar_y), fill=c)

    domain = "gitpulse.kpi.fei.tuke.sk"
    dom_bbox = f_domain.getbbox(domain)
    dom_w = dom_bbox[2] - dom_bbox[0]
    draw.text((cx - dom_w // 2 - dom_bbox[0], bar_y + 13), domain, fill=INDIGO, font=f_domain)

    # -- Save -------------------------------------------------------------
    app_path = Path(__file__).resolve().parent.parent / "src/app/templates/static/img/og-image.png"
    app_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(app_path, "PNG", optimize=True)
    print(f"  app: {app_path} ({app_path.stat().st_size:,} bytes)")

    docs_path = (
        Path(__file__).resolve().parent.parent / "docs-site/content/assets/images/og-image.png"
    )
    docs_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(docs_path, "PNG", optimize=True)
    print(f"  docs: {docs_path}")

    # Save docs og-cover.png as well
    docs_cover_path = (
        Path(__file__).resolve().parent.parent / "docs-site/content/assets/images/og-cover.png"
    )
    img.save(docs_cover_path, "PNG", optimize=True)
    print(f"  docs cover: {docs_cover_path}")

    site_dir = Path(__file__).resolve().parent.parent / "docs-site/public/assets/images"
    if site_dir.exists():
        (site_dir / "og-image.png").write_bytes(app_path.read_bytes())
        (site_dir / "og-cover.png").write_bytes(app_path.read_bytes())

    print("Done.")


if __name__ == "__main__":
    main()
