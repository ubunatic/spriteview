# SPDX-FileCopyrightText: 2026 Uwe Jugel
# SPDX-License-Identifier: AGPL-3.0-or-later

import base64
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gdk, GdkPixbuf, GLib


def pixbuf_to_texture(pb: GdkPixbuf.Pixbuf) -> Gdk.Texture:
    """Convert a GdkPixbuf to a Gdk.Texture without using the deprecated
    Gdk.Texture.new_for_pixbuf (deprecated since GTK 4.20)."""
    fmt = Gdk.MemoryFormat.R8G8B8A8 if pb.get_has_alpha() else Gdk.MemoryFormat.R8G8B8
    builder = Gdk.MemoryTextureBuilder()
    builder.set_bytes(GLib.Bytes.new(pb.get_pixels()))
    builder.set_width(pb.get_width())
    builder.set_height(pb.get_height())
    builder.set_stride(pb.get_rowstride())
    builder.set_format(fmt)
    return builder.build()

# The base64 representation of sprites/banner.png
EMBEDDED_BANNER_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAATBJREFUS"
    "IntlDFqwzAYhT/XXpvEJCAMgUKHjF26d8qQpVv2jjmAz9EDpGfI1iVDL5AbFA+FQsEYYlyaK"
    "YNxh1ZGliUnwYZSyLdYEvZ7kv+nHxSuLm8KWqJrXLQVPMT/N3AArsV9kc4mnQoP1xFvybPjA"
    "aSzCcN1RO4HnYi7WfyjlYAnF3M/gLvbTgzSfcRgswMMNZgvR8yXo9pYhAIRinIM0JuOy+960"
    "3FlLjEWebXYGneWPCaVp25iomawWmzLXduQJwD4evkwjq0GurjtNBL9N+k4AP2HsBhsdp0V+"
    "fO3yO+vT87f3WQ1SUAlQbYUnWSgoybnFI42UJOjx7QpqlYDGVdTiqTZoYiC0ipsJhLTJWsSr"
    "hm4WUy6jxpfPha1cXrqgmxQbcn9ADeLO9E6055vfaxsHuTYIiAAAAAASUVORK5CYII="
)

# Alias for backwards compatibility
EMBEDDED_LOGO_B64 = EMBEDDED_BANNER_B64

def get_embedded_banner() -> Gdk.Texture:
    try:
        img_data = base64.b64decode(EMBEDDED_BANNER_B64)
        loader = GdkPixbuf.PixbufLoader.new_with_type("png")
        loader.write(img_data)
        loader.close()
        pixbuf = loader.get_pixbuf()
        # Scale up using nearest-neighbor to prevent blurriness
        scaled_pixbuf = pixbuf.scale_simple(128, 128, GdkPixbuf.InterpType.NEAREST)
        return pixbuf_to_texture(scaled_pixbuf)
    except Exception as e:
        print(f"Error loading embedded banner: {e}")
        return None

def get_embedded_logo() -> Gdk.Texture:
    return get_embedded_banner()
