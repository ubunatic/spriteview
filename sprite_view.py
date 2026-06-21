# SPDX-FileCopyrightText: 2026 Uwe Jugel
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import gi
from typing import List

gi.require_version('Notify', '0.7')
gi.require_version('Gtk', '4.0')
from gi.repository import Nautilus, GObject, Notify, Gtk

from sprite_view.utils import find_sprite_frames
from sprite_view.ui.preview import ImagePreviewWindow

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

            # Find all sprite frames
            frames = find_sprite_frames(file_path)
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
            if len(find_sprite_frames(file_path)) > 1:
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
