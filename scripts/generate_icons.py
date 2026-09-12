#!/usr/bin/env python3
"""
Hermes WebApp - Generate PWA Icons
===================================
Creates all required icon sizes for Telegram Mini App / PWA.
Uses Pillow to generate icons from a base SVG or creates placeholder.

Usage:
    python scripts/generate_icons.py
"""

import os
import sys
from pathlib import Path

# Check for Pillow
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("❌ Pillow not installed. Run: pip install pillow")
    sys.exit(1)


def create_base_icon(size):
    """Create a base Hermes OS icon."""
    img = Image.new('RGBA', (size, size), (2, 6, 23, 255))  # #020617 background
    draw = ImageDraw.Draw(img)
    
    # Draw shield shape (Hermes OS logo concept)
    margin = size // 8
    shield_points = [
        (size // 2, margin),                                    # Top center
        (size - margin, size // 4),                             # Right top
        (size - margin, size * 3 // 4),                         # Right bottom
        (size // 2, size - margin),                             # Bottom center
        (margin, size * 3 // 4),                                # Left bottom
        (margin, size // 4),                                    # Left top
    ]
    
    # Draw shield background
    draw.polygon(shield_points, fill=(22, 163, 74, 255))  # #16A34A green
    
    # Draw inner shield
    inner_margin = margin * 2
    inner_points = [
        (size // 2, inner_margin),
        (size - inner_margin, size // 3),
        (size - inner_margin, size * 2 // 3),
        (size // 2, size - inner_margin),
        (inner_margin, size * 2 // 3),
        (inner_margin, size // 3),
    ]
    draw.polygon(inner_points, fill=(2, 6, 23, 255))  # #020617
    
    # Draw circuit pattern lines
    line_color = (22, 163, 74, 200)
    line_width = max(1, size // 64)
    
    # Horizontal lines
    for y in [size // 3, size // 2, size * 2 // 3]:
        draw.line([(inner_margin, y), (size - inner_margin, y)], fill=line_color, width=line_width)
    
    # Vertical line center
    draw.line([(size // 2, inner_margin), (size // 2, size - inner_margin)], fill=line_color, width=line_width)
    
    # Draw "H" in center for small sizes
    if size >= 64:
        try:
            font_size = size // 3
            # Use default font
            draw.text((size // 2 - font_size // 4, size // 2 - font_size // 2), "H", fill=line_color)
        except:
            pass
    
    return img


def generate_icons():
    """Generate all required icon sizes."""
    
    base_dir = Path(__file__).parent.parent
    icons_dir = base_dir / "static" / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)
    
    # Required sizes for Telegram Mini App / PWA
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    print("🎨 Generating Hermes OS icons...")
    print(f"   Output: {icons_dir}")
    
    for size in sizes:
        img = create_base_icon(size)
        output_path = icons_dir / f"icon-{size}.png"
        img.save(output_path, "PNG", optimize=True)
        print(f"   ✅ icon-{size}.png ({size}x{size})")
    
    # Create shortcut icons (96x96)
    shortcut_icons = ["terminal", "browser", "swarm", "stats"]
    for name in shortcut_icons:
        img = create_base_icon(96)
        draw = ImageDraw.Draw(img)
        # Add small label indicator
        draw.rectangle([70, 70, 94, 94], fill=(22, 163, 74, 255))
        output_path = icons_dir / f"{name}-96.png"
        img.save(output_path, "PNG", optimize=True)
        print(f"   ✅ {name}-96.png")
    
    # Create splash screens (optional)
    splash_sizes = [(1080, 1920), (1170, 2532), (1242, 2688)]
    for w, h in splash_sizes:
        img = Image.new('RGBA', (w, h), (2, 6, 23, 255))
        draw = ImageDraw.Draw(img)
        
        # Centered logo
        logo_size = min(w, h) // 3
        logo = create_base_icon(logo_size)
        x = (w - logo_size) // 2
        y = (h - logo_size) // 2 - 100
        img.paste(logo, (x, y), logo)
        
        # Title text
        try:
            draw.text((w // 2 - 150, y + logo_size + 40), "HERMES OS", fill=(248, 250, 252, 255))
            draw.text((w // 2 - 200, y + logo_size + 80), "Remote PC Control & AI Command Center", fill=(148, 163, 184, 255))
        except:
            pass
        
        output_path = icons_dir / f"splash-{w}x{h}.png"
        img.save(output_path, "PNG", optimize=True)
        print(f"   ✅ splash-{w}x{h}.png")
    
    print(f"\n✅ All icons generated in {icons_dir}")
    print("   Add to git: git add static/icons/")


if __name__ == "__main__":
    generate_icons()