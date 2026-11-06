"""Compile the SVG logo into PNG files for PWA icons using CairoSVG."""

from pathlib import Path

import cairosvg
from PIL import Image

ROOT_DIR = Path(__file__).resolve().parents[1]
DST_DIR = ROOT_DIR / "src" / "app" / "templates" / "static" / "img" / "icons"

SIZES = {
    "icon-72x72.png": 72,
    "icon-96x96.png": 96,
    "icon-128x128.png": 128,
    "icon-144x144.png": 144,
    "icon-152x152.png": 152,
    "icon-192x192.png": 192,
    "icon-384x384.png": 384,
    "icon-512x512.png": 512,
    "apple-touch-icon.png": 180,
}

# The clean GitLab logo with an integrated neon ECG pulse line on a dark-gray background.
# Matches Photo 2, but adds the glowing "Pulse" line to establish brand identity.
CLEAN_PWA_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
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

  <!-- Solid GitLab Dark Gray Background with Rounded Corners -->
  <rect width="48" height="48" rx="10" fill="#30353e" />

  <!-- GitLab Tanuki with Gradients -->
  <g opacity="0.85">
    <!-- Left Cheek -->
    <path d="M6 27.4152L17.9932 18.9935L23.9627 42Z" fill="url(#gpGradLeftCheek)" />
    <!-- Right Cheek -->
    <path d="M42 27.4152L30.9661 18.9935L23.9627 42Z" fill="url(#gpGradRightCheek)" />
    <!-- Left Ear -->
    <path d="M11.0151 6L17.9932 18.9935L6 27.4152Z" fill="url(#gpGradLeftEar)" />
    <!-- Right Ear -->
    <path d="M36.9957 6L30.9661 18.9935L42 27.4152Z" fill="url(#gpGradRightEar)" />
    <!-- Center Triangle -->
    <path d="M17.9932 18.9935H30.9661L23.9627 42Z" fill="url(#gpGradCenter)" />
  </g>

  <!-- Glowing ECG Pulse Line -->
  <!-- Cyan Glow Halo -->
  <path d="M2 24H16L18 27L21.5 10L24.5 38L27.5 21L30 24H46" fill="none" stroke="#00f0ff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" opacity="0.55" />
  <!-- Dark background contrast guard -->
  <path d="M2 24H16L18 27L21.5 10L24.5 38L27.5 21L30 24H46" fill="none" stroke="#18171d" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" opacity="0.72" />
  <!-- White Core -->
  <path d="M2 24H16L18 27L21.5 10L24.5 38L27.5 21L30 24H46" fill="none" stroke="#ffffff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
</svg>"""

# Transparent version for email (no solid background rectangle)
TRANSPARENT_LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
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
    <!-- Left Cheek -->
    <path d="M6 27.4152L17.9932 18.9935L23.9627 42Z" fill="url(#gpGradLeftCheek)" />
    <!-- Right Cheek -->
    <path d="M42 27.4152L30.9661 18.9935L23.9627 42Z" fill="url(#gpGradRightCheek)" />
    <!-- Left Ear -->
    <path d="M11.0151 6L17.9932 18.9935L6 27.4152Z" fill="url(#gpGradLeftEar)" />
    <!-- Right Ear -->
    <path d="M36.9957 6L30.9661 18.9935L42 27.4152Z" fill="url(#gpGradRightEar)" />
    <!-- Center Triangle -->
    <path d="M17.9932 18.9935H30.9661L23.9627 42Z" fill="url(#gpGradCenter)" />
  </g>

  <!-- Glowing ECG Pulse Line -->
  <!-- Cyan Glow Halo -->
  <path d="M2 24H16L18 27L21.5 10L24.5 38L27.5 21L30 24H46" fill="none" stroke="#00f0ff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" opacity="0.55" />
  <!-- Dark background contrast guard -->
  <path d="M2 24H16L18 27L21.5 10L24.5 38L27.5 21L30 24H46" fill="none" stroke="#18171d" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" opacity="0.72" />
  <!-- White Core -->
  <path d="M2 24H16L18 27L21.5 10L24.5 38L27.5 21L30 24H46" fill="none" stroke="#ffffff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
</svg>"""


def main():
    # Ensure output directory exists
    DST_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating PWA icons...")
    for name, size in SIZES.items():
        out_path = DST_DIR / name

        # Render the SVG to PNG using CairoSVG
        cairosvg.svg2png(
            bytestring=CLEAN_PWA_SVG.encode("utf-8"),
            write_to=str(out_path),
            output_width=size,
            output_height=size,
        )

        # Optimize with PIL
        with Image.open(out_path) as img:
            img = img.convert("RGBA")
            img.save(out_path, "PNG", optimize=True)

        print(f"  OK {name} ({size}x{size})")

    # Generate email notification logo (144x144) - TRANSPARENT
    email_path = ROOT_DIR / "src" / "app" / "templates" / "static" / "img" / "email-logo.png"
    email_path.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2png(
        bytestring=TRANSPARENT_LOGO_SVG.encode("utf-8"),
        write_to=str(email_path),
        output_width=144,
        output_height=144,
    )
    with Image.open(email_path) as img:
        img = img.convert("RGBA")
        img.save(email_path, "PNG", optimize=True)
    print("  OK email-logo.png (144x144, transparent)")

    print("\nAll PWA PNG icons and email logo generated successfully!")


if __name__ == "__main__":
    main()
