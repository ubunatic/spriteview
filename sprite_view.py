# SPDX-FileCopyrightText: 2026 Uwe Jugel
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import sys
import re
import gi
from typing import List

gi.require_version('Notify', '0.7')
gi.require_version('Gtk', '4.0')

for version in ['4.0', '4.1', '3.0']:
    try:
        getattr(gi, 'require_version')('Nautilus', version)
        break
    except Exception:
        pass

try:
    Nautilus = __import__('gi.repository', fromlist=['Nautilus']).Nautilus
except ImportError:
    Nautilus = None

from gi.repository import GObject, Notify, Gtk

from sprite_view.utils import find_sprite_frames
from sprite_view.ui.preview import ImagePreviewWindow
from sprite_view.settings import load_settings
from sprite_view.ui.about import AboutWindow
from sprite_view.ui.settings import SettingsWindow

if Nautilus is not None:
    class NautilusPreview(GObject.GObject, Nautilus.MenuProvider):
        def __init__(self) -> None:
            super().__init__()
            Notify.init("NautilusPreview")
            self.preview_windows: List[Gtk.Window] = []

        def _show_notification(self, title: str, message: str) -> None:
            notification = Notify.Notification.new(title, message, "info")
            notification.show()

        def _on_preview_activated(self, menu: Nautilus.MenuItem, files: List[Nautilus.FileInfo]) -> None:
            if len(files) == 1:
                file = files[0]
                name = file.get_name()
                location = file.get_location()
                if not location:
                    self._show_notification("Preview Error", f"Could not get location for {name}")
                    return

                file_path = location.get_path()
                if not file_path or not os.path.exists(file_path):
                    self._show_notification("Preview Error", f"File path does not exist: {file_path}")
                    return

                # Find all sprite frames using configured separators and patterns
                settings = load_settings()
                seps = settings.get("sequence_separators", ["_", "-"])
                pats = settings.get("sequence_patterns", [])
                frames = find_sprite_frames(file_path, separators=seps, patterns=pats)
                selected_file_path = file_path
                title = f"Preview: {os.path.basename(file_path)}"
            else:
                frames = []
                for file in files:
                    location = file.get_location()
                    if location:
                        path = location.get_path()
                        if path and os.path.exists(path):
                            frames.append(path)

                if not frames:
                    self._show_notification("Preview Error", "No valid files found for preview")
                    return

                # Sort the frames alphabetically so they play in the correct chronological/numerical sequence
                frames.sort()
                selected_file_path = frames[0]
                title = f"Preview: {len(frames)} Selected Frames"

            try:
                win = ImagePreviewWindow(frames, selected_file_path, title)
                self.preview_windows.append(win)
                win.connect("destroy", lambda w: self.preview_windows.remove(w))
                win.present()
            except Exception as e:
                self._show_notification("Preview Error", f"Failed to open preview: {str(e)}")

        def get_file_items(self, *args) -> List[Nautilus.MenuItem]:
            files = args[-1]
            if not files:
                return []

            # Verify all selected items are valid image files (none are directories)
            image_files = []
            for file in files:
                if file.is_directory():
                    return []
                name = file.get_name().lower()
                if not name.endswith(('.png', '.gif', '.bmp', '.jpg', '.jpeg', '.webp')):
                    return []
                location = file.get_location()
                if not location or not location.get_path():
                    return []
                image_files.append(file)

            if len(image_files) == 1:
                file = image_files[0]
                file_path = file.get_location().get_path()
                label = "Preview Image"
                settings = load_settings()
                seps = settings.get("sequence_separators", ["_", "-"])
                pats = settings.get("sequence_patterns", [])
                if len(find_sprite_frames(file_path, separators=seps, patterns=pats)) > 1:
                    label = "Preview Sprite Sheet"

                item = Nautilus.MenuItem(
                    name="NautilusPreview::preview_image",
                    label=label,
                    tip=f"Open preview for {file.get_name()}"
                )
                item.connect("activate", self._on_preview_activated, [file])
                return [item]
            elif len(image_files) > 1:
                item = Nautilus.MenuItem(
                    name="NautilusPreview::preview_image",
                    label="Preview Animation",
                    tip="Open animation preview for selected frames"
                )
                item.connect("activate", self._on_preview_activated, image_files)
                return [item]

            return []

        def get_background_items(self, *args) -> List[Nautilus.MenuItem]:
            return []
else:
    class NautilusPreview:
        pass


def export_cli(files: List[str], fmt: str) -> None:
    if not files:
        print("Error: No files specified for export.", file=sys.stderr)
        sys.exit(1)

    fmt = fmt.lower()
    if fmt not in ["png", "gif", "webm", "ico"]:
        print(f"Error: Unsupported export format '{fmt}'", file=sys.stderr)
        sys.exit(1)

    # Resolve frame list
    if len(files) == 1:
        file_path = os.path.abspath(files[0])
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        settings = load_settings()
        seps = settings.get("sequence_separators", ["_", "-"])
        pats = settings.get("sequence_patterns", [])
        frames = find_sprite_frames(file_path, separators=seps, patterns=pats)
    else:
        frames = []
        for f in files:
            path = os.path.abspath(f)
            if os.path.exists(path):
                frames.append(path)
        frames.sort()

    if not frames:
        print("Error: No valid input files found.", file=sys.stderr)
        sys.exit(1)

    if len(frames) == 1:
        if fmt not in ["png", "gif", "ico"]:
            print(f"Error: Format '{fmt}' is not supported for single image export. Use 'png', 'gif', or 'ico'.", file=sys.stderr)
            sys.exit(1)

        from PIL import Image
        img = Image.open(frames[0])
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        base = os.path.basename(frames[0])
        name, _ = os.path.splitext(base)
        out_name = f"{name}.{fmt}"
        out_path = os.path.join(os.getcwd(), out_name)

        if fmt == "png":
            img.save(out_path, "PNG")
        elif fmt == "gif":
            img.save(out_path, "GIF")
        elif fmt == "ico":
            w, h = img.size
            if w > 256 or h > 256:
                ratio = min(256 / w, 256 / h)
                new_w, new_h = int(w * ratio), int(h * ratio)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            img.save(out_path, format="ICO")

        print(f"Exported to {out_path}")
    else:
        if fmt not in ["gif", "webm"]:
            print(f"Error: Format '{fmt}' is not supported for animation export. Use 'gif' or 'webm'.", file=sys.stderr)
            sys.exit(1)

        from PIL import Image
        settings = load_settings()

        widths = []
        heights = []
        loaded_images = []
        for path in frames:
            img = Image.open(path)
            widths.append(img.size[0])
            heights.append(img.size[1])
            loaded_images.append(img)

        has_mixed_sizes = len(set(widths)) > 1 or len(set(heights)) > 1
        canvas_size = (max(widths), max(heights))

        padded_images = []
        for img in loaded_images:
            if img.mode != "RGBA":
                img = img.convert("RGBA")

            if has_mixed_sizes:
                canvas_w, canvas_h = canvas_size
                src_w, src_h = img.size
                canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
                align = 4
                row, col = align // 3, align % 3
                dx = (canvas_w - src_w) * col // 2
                dy = (canvas_h - src_h) * row // 2
                canvas.paste(img, (dx, dy))
                padded_images.append(canvas)
            else:
                padded_images.append(img)

        first_file = os.path.basename(frames[0])
        out_name = f"animation.{fmt}"

        patterns = settings.get("sequence_patterns", [])
        matched = False
        if patterns:
            for pat_str in patterns:
                try:
                    from sprite_view.utils import template_to_regex
                    pat_regex_str = template_to_regex(pat_str)
                    pat = re.compile(pat_regex_str, re.IGNORECASE)
                    match = pat.match(first_file)
                    if match and "prefix" in pat.groupindex:
                        prefix = match.group("prefix")
                        if prefix:
                            out_name = f"{prefix}.{fmt}"
                            matched = True
                            break
                except Exception:
                    pass

        if not matched:
            seps = settings.get("sequence_separators", ["_", "-"])
            sep_alts = "|".join(re.escape(s) for s in seps)
            match = re.match(rf"^(.*)({sep_alts})([0-9]{{2,4}})\.(png|gif|bmp|jpg|jpeg|webp)$", first_file, re.IGNORECASE)
            if match:
                prefix = match.group(1)
                out_name = f"{prefix}.{fmt}"

        out_path = os.path.join(os.getcwd(), out_name)

        if fmt == "gif":
            fps = settings.get("default_fps", 15.0)
            duration_ms = int(1000.0 / fps)
            padded_images[0].save(
                out_path,
                "GIF",
                save_all=True,
                append_images=padded_images[1:],
                duration=duration_ms,
                loop=0
            )
            print(f"Exported to {out_path}")
        elif fmt == "webm":
            import tempfile
            import subprocess
            fps = settings.get("default_fps", 15.0)
            with tempfile.TemporaryDirectory() as tmpdir:
                for i, img in enumerate(padded_images):
                    frame_path = os.path.join(tmpdir, f"frame_{i:04d}.png")
                    img.save(frame_path, "PNG")

                cmd = [
                    "ffmpeg", "-y",
                    "-framerate", str(fps),
                    "-i", os.path.join(tmpdir, "frame_%04d.png"),
                    "-c:v", "libvpx-vp9",
                    "-pix_fmt", "yuva420p",
                    out_path
                ]
                res = subprocess.run(cmd, capture_output=True)
                if res.returncode != 0:
                    print(f"Error: ffmpeg failed with code {res.returncode}", file=sys.stderr)
                    print(res.stderr.decode(), file=sys.stderr)
                    sys.exit(1)
                print(f"Exported to {out_path}")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Standalone sprite sheet and animation previewer CLI")
    parser.add_argument("files", nargs="*", help="Sprite image file(s) or sheet image file")
    parser.add_argument("--settings", action="store_true", help="Open the settings window")
    parser.add_argument("--about", action="store_true", help="Open the about dialog")
    parser.add_argument("--export", help="Export format (png, gif, webm, ico) without opening GUI")

    args = parser.parse_args()

    if args.export:
        export_cli(args.files, args.export)
        return

    if not args.settings and not args.about and not args.files:
        parser.print_help()
        sys.exit(1)

    try:
        Notify.init("SpriteView")
    except Exception:
        pass

    app = Gtk.Application(application_id="org.nautilus.SpriteView")

    def on_activate(app_inst):
        if args.settings:
            win = SettingsWindow(None)
            app_inst.add_window(win)
            win.present()
        elif args.about:
            win = AboutWindow(None)
            app_inst.add_window(win)
            win.present()
        else:
            if len(args.files) == 1:
                file_path = os.path.abspath(args.files[0])
                if not os.path.exists(file_path):
                    print(f"Error: File not found: {file_path}", file=sys.stderr)
                    sys.exit(1)

                settings = load_settings()
                seps = settings.get("sequence_separators", ["_", "-"])
                pats = settings.get("sequence_patterns", [])
                frames = find_sprite_frames(file_path, separators=seps, patterns=pats)
                selected_file_path = file_path
                title = f"Preview: {os.path.basename(file_path)}"
            else:
                frames = []
                for f in args.files:
                    path = os.path.abspath(f)
                    if os.path.exists(path):
                        frames.append(path)
                frames.sort()
                if not frames:
                    print("Error: No valid input files found.", file=sys.stderr)
                    sys.exit(1)
                selected_file_path = frames[0]
                title = f"Preview: {len(frames)} Selected Frames"

            win = ImagePreviewWindow(frames, selected_file_path, title)
            app_inst.add_window(win)
            win.present()

    app.connect("activate", on_activate)
    app.run([sys.argv[0]])


if __name__ == "__main__":
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    main()
