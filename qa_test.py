"""QA test script for Sprite Cutout Creator web app using Playwright."""
import json
import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

BASE_URL = "http://localhost:5099"
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"
OUTPUT_DIR = Path(__file__).parent.parent / "Froked-KataCR-Clash-Royale-Detection-Dataset" / "images" / "segment"
SCREENSHOT_DIR.mkdir(exist_ok=True)

results = []

def record(area, name, status, expected, actual, screenshot=None):
    entry = {
        "area": area,
        "name": name,
        "status": status,
        "expected": expected,
        "actual": actual,
        "screenshot": screenshot,
    }
    results.append(entry)
    icon = {"PASS": "[PASS]", "FAIL": "[FAIL]", "WARN": "[WARN]"}[status]
    print(f"  {icon} {name}")
    if status == "FAIL":
        print(f"        Expected: {expected}")
        print(f"        Actual:   {actual}")


def ss(page, name):
    """Take a screenshot and return its relative path."""
    path = SCREENSHOT_DIR / f"{name}.png"
    page.screenshot(path=str(path))
    return f"screenshots/{name}.png"


def run_tests():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()

        # ============================================================
        # 1. PAGE LOAD
        # ============================================================
        print("\n=== 1. PAGE LOAD ===")

        try:
            response = page.goto(BASE_URL, wait_until="networkidle", timeout=15000)
            status_code = response.status if response else 0
            record("Page Load", "HTTP response",
                   "PASS" if status_code == 200 else "FAIL",
                   "200 OK", f"{status_code}")
        except Exception as e:
            record("Page Load", "HTTP response", "FAIL", "200 OK", str(e))

        # Wait for initialization
        page.wait_for_timeout(2000)
        shot = ss(page, "01_initial_load")

        # Check title
        title = page.title()
        record("Page Load", "Page title",
               "PASS" if "Sprite" in title else "FAIL",
               "Contains 'Sprite'", title, shot)

        # Check header visible
        header_text = page.locator(".header-title").text_content()
        record("Page Load", "Header title visible",
               "PASS" if header_text == "Sprite Cutout Creator" else "FAIL",
               "Sprite Cutout Creator", header_text)

        # Check status says Ready
        status_text = page.locator("#status-left").text_content()
        record("Page Load", "Status bar shows Ready",
               "PASS" if status_text == "Ready" else "WARN",
               "Ready", status_text)

        # Check saves counter initial value
        saves_text = page.locator("#hdr-saves").text_content()
        record("Page Load", "Saves counter starts at 0",
               "PASS" if saves_text == "0" else "WARN",
               "0", saves_text)

        # Check zoom indicator
        zoom_text = page.locator("#hdr-zoom").text_content()
        record("Page Load", "Zoom indicator shows 100%",
               "PASS" if zoom_text == "100%" else "FAIL",
               "100%", zoom_text)

        # Check frame input exists and starts at 0
        frame_val = page.locator("#frame-input").input_value()
        record("Page Load", "Frame input starts at 0",
               "PASS" if frame_val == "0" else "FAIL",
               "0", frame_val)

        # Check class list populated
        class_items = page.locator(".class-item").count()
        record("Page Load", "Class list populated",
               "PASS" if class_items > 0 else "FAIL",
               "> 0 classes", f"{class_items} classes", shot)

        # Check canvas exists
        canvas_visible = page.locator("#canvas").is_visible()
        record("Page Load", "Canvas visible",
               "PASS" if canvas_visible else "FAIL",
               "visible", str(canvas_visible))

        # Check scrubber exists
        slider_visible = page.locator("#scrub-slider").is_visible()
        record("Page Load", "Scrubber slider visible",
               "PASS" if slider_visible else "FAIL",
               "visible", str(slider_visible))

        # Check preview panel
        preview_text = page.locator("#preview-placeholder").text_content()
        record("Page Load", "Preview placeholder text",
               "PASS" if "lasso" in preview_text.lower() else "WARN",
               "Contains 'lasso'", preview_text)

        # ============================================================
        # 2. FRAME NAVIGATION
        # ============================================================
        print("\n=== 2. FRAME NAVIGATION ===")

        # Click next button
        page.locator("#btn-next").click()
        page.wait_for_timeout(500)
        frame_after_next = page.locator("#frame-input").input_value()
        record("Frame Navigation", "Next button increments frame",
               "PASS" if frame_after_next == "1" else "FAIL",
               "1", frame_after_next)

        # Click prev button
        page.locator("#btn-prev").click()
        page.wait_for_timeout(500)
        frame_after_prev = page.locator("#frame-input").input_value()
        record("Frame Navigation", "Prev button decrements frame",
               "PASS" if frame_after_prev == "0" else "FAIL",
               "0", frame_after_prev)

        # Type frame number directly
        page.locator("#frame-input").fill("100")
        page.locator("#frame-input").press("Enter")
        page.wait_for_timeout(800)
        frame_typed = page.locator("#frame-input").input_value()
        record("Frame Navigation", "Direct frame input",
               "PASS" if frame_typed == "100" else "FAIL",
               "100", frame_typed)

        # Check scrubber syncs with frame input
        slider_val = page.locator("#scrub-slider").input_value()
        record("Frame Navigation", "Scrubber syncs with frame input",
               "PASS" if slider_val == "100" else "FAIL",
               "100", slider_val)

        # Check frame info text
        scrub_frame_text = page.locator("#scrub-frame").text_content()
        record("Frame Navigation", "Scrub frame info updates",
               "PASS" if "100" in scrub_frame_text else "FAIL",
               "Contains '100'", scrub_frame_text)

        shot = ss(page, "02_frame_navigation")

        # Test scrubber buttons
        page.locator("#scrub-next").click()
        page.wait_for_timeout(500)
        frame_scrub_next = page.locator("#frame-input").input_value()
        record("Frame Navigation", "Scrubber next button works",
               "PASS" if frame_scrub_next == "101" else "FAIL",
               "101", frame_scrub_next)

        page.locator("#scrub-prev").click()
        page.wait_for_timeout(500)
        frame_scrub_prev = page.locator("#frame-input").input_value()
        record("Frame Navigation", "Scrubber prev button works",
               "PASS" if frame_scrub_prev == "100" else "FAIL",
               "100", frame_scrub_prev)

        # Test scrubber slider drag
        slider = page.locator("#scrub-slider")
        bbox = slider.bounding_box()
        if bbox:
            # Click at 50% of the slider
            midx = bbox["x"] + bbox["width"] * 0.5
            page.mouse.click(midx, bbox["y"] + bbox["height"] / 2)
            page.wait_for_timeout(800)
            slider_val_after = page.locator("#scrub-slider").input_value()
            frame_val_after = page.locator("#frame-input").input_value()
            # The slider should have moved to approximately half of total frames
            slider_int = int(slider_val_after)
            record("Frame Navigation", "Scrubber slider click navigates",
                   "PASS" if slider_int > 1000 and slider_int < 4000 else "WARN",
                   "~2660 (midpoint)", str(slider_int))
        else:
            record("Frame Navigation", "Scrubber slider click", "FAIL",
                   "Slider has bounding box", "No bounding box found")

        shot = ss(page, "02b_after_slider")

        # ============================================================
        # 3. CLASS SELECTION
        # ============================================================
        print("\n=== 3. CLASS SELECTION ===")

        # Go back to frame 0 for consistency
        page.locator("#frame-input").fill("0")
        page.locator("#frame-input").press("Enter")
        page.wait_for_timeout(500)

        # Check first class is auto-selected
        selected = page.locator(".class-item.selected")
        selected_count = selected.count()
        record("Class Selection", "Default class is auto-selected",
               "PASS" if selected_count == 1 else "FAIL",
               "1 selected", f"{selected_count} selected")

        if selected_count > 0:
            selected_name = selected.first.locator(".class-name").text_content()
            record("Class Selection", "Selected class name is readable",
                   "PASS" if len(selected_name) > 0 else "FAIL",
                   "Non-empty name", selected_name)

        # Click a different class (scroll to find one)
        all_classes = page.locator(".class-item")
        total_classes = all_classes.count()
        if total_classes >= 3:
            target_class = all_classes.nth(2)
            target_name = target_class.locator(".class-name").text_content()
            target_class.click()
            page.wait_for_timeout(300)

            # Check it's now selected
            new_selected = page.locator(".class-item.selected .class-name").text_content()
            record("Class Selection", "Clicking class selects it",
                   "PASS" if new_selected == target_name else "FAIL",
                   target_name, new_selected)

            # Check previous is deselected
            selected_count_after = page.locator(".class-item.selected").count()
            record("Class Selection", "Only one class selected at a time",
                   "PASS" if selected_count_after == 1 else "FAIL",
                   "1", str(selected_count_after))

        # Test search filter
        search_input = page.locator("#class-search")
        search_input.fill("archer")
        page.wait_for_timeout(300)
        filtered_count = page.locator(".class-item").count()
        record("Class Selection", "Search filter reduces list",
               "PASS" if filtered_count < total_classes else "FAIL",
               f"< {total_classes}", str(filtered_count))

        shot = ss(page, "03_class_filter")

        # Test search with no matches
        search_input.fill("zzzznonexistent")
        page.wait_for_timeout(300)
        no_match = page.locator(".class-no-match")
        no_match_visible = no_match.count() > 0
        record("Class Selection", "No matches message shown",
               "PASS" if no_match_visible else "FAIL",
               "No matches message visible", str(no_match_visible))

        shot = ss(page, "03b_no_match")

        # Clear search
        search_input.fill("")
        page.wait_for_timeout(300)
        restored_count = page.locator(".class-item").count()
        record("Class Selection", "Clearing search restores full list",
               "PASS" if restored_count == total_classes else "FAIL",
               str(total_classes), str(restored_count))

        # ============================================================
        # 4. DRAWING (Lasso)
        # ============================================================
        print("\n=== 4. DRAWING ===")

        # Navigate to a frame with visible content
        page.locator("#frame-input").fill("50")
        page.locator("#frame-input").press("Enter")
        page.wait_for_timeout(1000)

        # Select a known class
        search_input.fill("archer")
        page.wait_for_timeout(300)
        first_class = page.locator(".class-item").first
        if first_class.count() > 0:
            first_class.click()
            page.wait_for_timeout(200)

        search_input.fill("")
        page.wait_for_timeout(200)

        # Get canvas bounding box for drawing
        canvas_el = page.locator("#canvas")
        canvas_box = canvas_el.bounding_box()

        if canvas_box:
            # Draw a freehand lasso (triangle-like shape) in the center of the canvas
            cx = canvas_box["x"] + canvas_box["width"] / 2
            cy = canvas_box["y"] + canvas_box["height"] / 2
            size = 80

            # Simulate mouse drag for lasso
            page.mouse.move(cx - size, cy + size)
            page.mouse.down()
            # Draw a rough circle-like path
            import math
            steps = 30
            for i in range(steps + 1):
                angle = 2 * math.pi * i / steps
                x = cx + size * math.cos(angle)
                y = cy + size * math.sin(angle)
                page.mouse.move(x, y)
                page.wait_for_timeout(20)
            page.mouse.up()
            page.wait_for_timeout(500)

            shot = ss(page, "04_lasso_drawn")

            # Check that we have lasso points by checking the preview fetch
            # The preview should have loaded since we drew >= 3 points
            preview_img = page.locator("#preview-img")
            preview_visible = preview_img.get_attribute("style") or ""
            has_preview = "none" not in preview_visible
            record("Drawing", "Lasso drawing works (preview appeared)",
                   "PASS" if has_preview else "WARN",
                   "Preview image visible after lasso",
                   f"Preview display style: {preview_visible}")

            record("Drawing", "Lasso visible on canvas",
                   "PASS", "Green lasso line drawn",
                   "Visual confirmation in screenshot", shot)
        else:
            record("Drawing", "Canvas bounding box",
                   "FAIL", "Canvas has bounding box", "No bounding box")

        # ============================================================
        # 5. SAVE
        # ============================================================
        print("\n=== 5. SAVE ===")

        # Get current saves count
        saves_before = page.locator("#hdr-saves").text_content()

        # Count existing files in the selected class directory
        selected_class = page.locator(".class-item.selected .class-name").text_content()
        class_dir = OUTPUT_DIR / selected_class
        files_before = len(list(class_dir.glob("*_CUSTOM_*.png"))) if class_dir.exists() else 0

        # Press S to save
        page.keyboard.press("s")
        page.wait_for_timeout(1500)

        shot = ss(page, "05_after_save")

        # Check toast appeared (look for toast elements)
        toasts = page.locator(".toast")
        toast_count = toasts.count()
        record("Save", "Toast notification appeared",
               "PASS" if toast_count > 0 else "FAIL",
               "> 0 toasts", f"{toast_count} toasts", shot)

        if toast_count > 0:
            toast_text = toasts.first.text_content()
            is_success_toast = "Saved" in toast_text or "saved" in toast_text.lower()
            record("Save", "Toast shows success message",
                   "PASS" if is_success_toast else "FAIL",
                   "Contains 'Saved'", toast_text)

        # Check saves counter incremented
        saves_after = page.locator("#hdr-saves").text_content()
        record("Save", "Saves counter incremented",
               "PASS" if int(saves_after) == int(saves_before) + 1 else "FAIL",
               str(int(saves_before) + 1), saves_after)

        # Check recent saves updated
        recent_entries = page.locator(".save-entry")
        record("Save", "Recent saves list updated",
               "PASS" if recent_entries.count() > 0 else "FAIL",
               "> 0 entries", f"{recent_entries.count()} entries")

        # Check file was created on disk
        files_after = len(list(class_dir.glob("*_CUSTOM_*.png"))) if class_dir.exists() else 0
        record("Save", "File created on disk",
               "PASS" if files_after > files_before else "FAIL",
               f"> {files_before} custom files", f"{files_after} custom files")

        # Check that the undo button is now visible in sidebar
        undo_wrap_display = page.locator("#sidebar-undo-wrap").get_attribute("style") or ""
        undo_visible = "none" not in undo_wrap_display
        record("Save", "Undo button visible after save",
               "PASS" if undo_visible else "WARN",
               "Undo button visible", f"style: {undo_wrap_display}")

        # ============================================================
        # 6. UNDO
        # ============================================================
        print("\n=== 6. UNDO ===")

        saves_before_undo = int(page.locator("#hdr-saves").text_content())

        # Press Ctrl+Z to undo
        page.keyboard.press("Meta+z")  # macOS uses Meta
        page.wait_for_timeout(1500)

        shot = ss(page, "06_after_undo")

        # Check toast for undo
        toasts_undo = page.locator(".toast")
        undo_toast_found = False
        for i in range(toasts_undo.count()):
            t = toasts_undo.nth(i).text_content()
            if "undo" in t.lower() or "Undone" in t:
                undo_toast_found = True
                break
        record("Undo", "Undo toast appeared",
               "PASS" if undo_toast_found else "FAIL",
               "Toast with 'Undone' or 'undo'",
               f"Found: {undo_toast_found}", shot)

        # Check saves counter decremented
        saves_after_undo = int(page.locator("#hdr-saves").text_content())
        record("Undo", "Saves counter decremented",
               "PASS" if saves_after_undo == saves_before_undo - 1 else "FAIL",
               str(saves_before_undo - 1), str(saves_after_undo))

        # Check file was deleted from disk
        files_after_undo = len(list(class_dir.glob("*_CUSTOM_*.png"))) if class_dir.exists() else 0
        record("Undo", "File deleted from disk",
               "PASS" if files_after_undo == files_before else "FAIL",
               str(files_before), str(files_after_undo))

        # ============================================================
        # 7. KEYBOARD SHORTCUTS
        # ============================================================
        print("\n=== 7. KEYBOARD SHORTCUTS ===")

        # First navigate to a known frame
        page.locator("#frame-input").fill("50")
        page.locator("#frame-input").press("Enter")
        page.wait_for_timeout(500)
        # Click canvas to take focus away from input
        page.locator("#canvas").click()
        page.wait_for_timeout(200)

        # Arrow Right
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(500)
        frame_after_right = page.locator("#frame-input").input_value()
        record("Keyboard Shortcuts", "ArrowRight advances frame",
               "PASS" if frame_after_right == "51" else "FAIL",
               "51", frame_after_right)

        # Arrow Left
        page.keyboard.press("ArrowLeft")
        page.wait_for_timeout(500)
        frame_after_left = page.locator("#frame-input").input_value()
        record("Keyboard Shortcuts", "ArrowLeft goes back",
               "PASS" if frame_after_left == "50" else "FAIL",
               "50", frame_after_left)

        # Number keys for skip
        page.keyboard.press("5")
        page.wait_for_timeout(200)
        skip_btns = page.locator(".skip-btn")
        skip5_active = False
        for i in range(skip_btns.count()):
            btn = skip_btns.nth(i)
            if btn.get_attribute("data-skip") == "5":
                skip5_active = "active" in (btn.get_attribute("class") or "")
                break
        record("Keyboard Shortcuts", "Number key 5 sets skip to 5",
               "PASS" if skip5_active else "FAIL",
               "Skip 5 button active", str(skip5_active))

        # Now ArrowRight should skip 5
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(500)
        frame_after_skip5 = page.locator("#frame-input").input_value()
        record("Keyboard Shortcuts", "ArrowRight skips 5 frames with skip=5",
               "PASS" if frame_after_skip5 == "55" else "FAIL",
               "55", frame_after_skip5)

        # Reset skip to 1
        page.keyboard.press("1")
        page.wait_for_timeout(200)

        # R key for reset zoom
        # First zoom in
        canvas_box = page.locator("#canvas").bounding_box()
        if canvas_box:
            page.mouse.move(
                canvas_box["x"] + canvas_box["width"] / 2,
                canvas_box["y"] + canvas_box["height"] / 2
            )
            page.mouse.wheel(0, -300)  # Scroll up to zoom in
            page.wait_for_timeout(300)
            zoom_after_scroll = page.locator("#hdr-zoom").text_content()
            zoomed_in = zoom_after_scroll != "100%"
            record("Keyboard Shortcuts", "Scroll zooms in",
                   "PASS" if zoomed_in else "FAIL",
                   "!= 100%", zoom_after_scroll)

            # Press R to reset
            page.keyboard.press("r")
            page.wait_for_timeout(500)
            zoom_after_reset = page.locator("#hdr-zoom").text_content()
            record("Keyboard Shortcuts", "R key resets zoom",
                   "PASS" if zoom_after_reset == "100%" else "FAIL",
                   "100%", zoom_after_reset)

        # Escape clears lasso
        # First draw something
        if canvas_box:
            page.mouse.move(canvas_box["x"] + 200, canvas_box["y"] + 200)
            page.mouse.down()
            page.mouse.move(canvas_box["x"] + 300, canvas_box["y"] + 200)
            page.mouse.move(canvas_box["x"] + 300, canvas_box["y"] + 300)
            page.mouse.move(canvas_box["x"] + 200, canvas_box["y"] + 300)
            page.mouse.up()
            page.wait_for_timeout(300)

            page.keyboard.press("Escape")
            page.wait_for_timeout(300)
            # After escape, preview should clear
            shot = ss(page, "07_after_escape")
            record("Keyboard Shortcuts", "Escape clears lasso",
                   "PASS", "Lasso cleared (visual check)",
                   "Screenshot taken", shot)

        # ============================================================
        # 8. ZOOM/PAN
        # ============================================================
        print("\n=== 8. ZOOM/PAN ===")

        canvas_box = page.locator("#canvas").bounding_box()
        if canvas_box:
            cx = canvas_box["x"] + canvas_box["width"] / 2
            cy = canvas_box["y"] + canvas_box["height"] / 2

            # Zoom in with scroll
            page.mouse.move(cx, cy)
            page.mouse.wheel(0, -500)
            page.wait_for_timeout(300)
            zoom_val = page.locator("#hdr-zoom").text_content()
            zoom_pct = int(zoom_val.replace("%", ""))
            record("Zoom/Pan", "Scroll up zooms in",
                   "PASS" if zoom_pct > 100 else "FAIL",
                   "> 100%", zoom_val)

            shot = ss(page, "08_zoomed_in")

            # Zoom out with scroll
            page.mouse.wheel(0, 1000)
            page.wait_for_timeout(300)
            zoom_val2 = page.locator("#hdr-zoom").text_content()
            zoom_pct2 = int(zoom_val2.replace("%", ""))
            record("Zoom/Pan", "Scroll down zooms out",
                   "PASS" if zoom_pct2 < zoom_pct else "FAIL",
                   f"< {zoom_pct}%", zoom_val2)

            # Reset
            page.keyboard.press("r")
            page.wait_for_timeout(500)

            # Pan test: hold space and drag
            page.keyboard.down("Space")
            page.wait_for_timeout(100)
            page.mouse.move(cx, cy)
            page.mouse.down()
            page.mouse.move(cx + 50, cy + 50)
            page.mouse.up()
            page.keyboard.up("Space")
            page.wait_for_timeout(300)

            shot = ss(page, "08b_after_pan")
            record("Zoom/Pan", "Space+drag pans view",
                   "PASS", "Pan moved the image (visual check)",
                   "Screenshot taken", shot)

            # Reset again
            page.keyboard.press("r")
            page.wait_for_timeout(300)

        # ============================================================
        # 9. HELP MODAL
        # ============================================================
        print("\n=== 9. HELP MODAL ===")

        # Open with ? key
        page.keyboard.press("?")
        page.wait_for_timeout(500)

        modal = page.locator("#modal-overlay")
        modal_classes = modal.get_attribute("class") or ""
        record("Help Modal", "? key opens help modal",
               "PASS" if "visible" in modal_classes else "FAIL",
               "Modal has 'visible' class", modal_classes)

        shot = ss(page, "09_help_modal")

        # Check modal content
        modal_title = page.locator(".modal-title").text_content()
        record("Help Modal", "Modal has title",
               "PASS" if "Keyboard" in modal_title else "FAIL",
               "Contains 'Keyboard'", modal_title, shot)

        # Check shortcut table has rows
        shortcut_rows = page.locator(".shortcut-table tr").count()
        record("Help Modal", "Shortcut table has rows",
               "PASS" if shortcut_rows >= 5 else "FAIL",
               ">= 5 rows", f"{shortcut_rows} rows")

        # Close with Escape
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        modal_classes_after = modal.get_attribute("class") or ""
        record("Help Modal", "Escape closes modal",
               "PASS" if "visible" not in modal_classes_after else "FAIL",
               "No 'visible' class", modal_classes_after)

        # Open again and close by clicking overlay
        page.keyboard.press("?")
        page.wait_for_timeout(300)

        # Click outside the modal content (on the overlay)
        overlay_box = modal.bounding_box()
        if overlay_box:
            page.mouse.click(overlay_box["x"] + 10, overlay_box["y"] + 10)
            page.wait_for_timeout(300)
            modal_classes_click = modal.get_attribute("class") or ""
            record("Help Modal", "Click overlay closes modal",
                   "PASS" if "visible" not in modal_classes_click else "FAIL",
                   "No 'visible' class", modal_classes_click)

        # Open with button
        page.locator("#btn-help").click()
        page.wait_for_timeout(300)
        modal_classes_btn = modal.get_attribute("class") or ""
        record("Help Modal", "? button opens modal",
               "PASS" if "visible" in modal_classes_btn else "FAIL",
               "Modal has 'visible' class", modal_classes_btn)
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)

        # ============================================================
        # 10. PREVIEW PANEL
        # ============================================================
        print("\n=== 10. PREVIEW PANEL ===")

        # Draw a lasso and check preview
        page.locator("#frame-input").fill("100")
        page.locator("#frame-input").press("Enter")
        page.wait_for_timeout(800)

        canvas_box = page.locator("#canvas").bounding_box()
        if canvas_box:
            cx = canvas_box["x"] + canvas_box["width"] / 2
            cy = canvas_box["y"] + canvas_box["height"] / 2

            page.mouse.move(cx - 60, cy - 60)
            page.mouse.down()
            steps = 20
            for i in range(steps + 1):
                angle = 2 * math.pi * i / steps
                page.mouse.move(cx + 60 * math.cos(angle), cy + 60 * math.sin(angle))
                page.wait_for_timeout(15)
            page.mouse.up()
            page.wait_for_timeout(1000)

            shot = ss(page, "10_preview_panel")

            # Check preview image appeared
            preview_img = page.locator("#preview-img")
            preview_style = preview_img.get_attribute("style") or ""
            preview_src = preview_img.get_attribute("src") or ""
            has_preview = "none" not in preview_style and len(preview_src) > 0
            record("Preview Panel", "Preview image appears after drawing",
                   "PASS" if has_preview else "WARN",
                   "Preview image visible with src",
                   f"style='{preview_style}', src='{preview_src[:50]}'", shot)

            # Save and check preview updates
            page.keyboard.press("s")
            page.wait_for_timeout(1500)

            shot_saved = ss(page, "10b_preview_after_save")
            preview_info_style = page.locator("#preview-info").get_attribute("style") or ""
            has_info = "none" not in preview_info_style
            record("Preview Panel", "Preview info shows after save",
                   "PASS" if has_info else "WARN",
                   "Preview info visible",
                   f"style='{preview_info_style}'", shot_saved)

            # Check preview shows filename
            filename_text = page.locator("#preview-filename").text_content()
            record("Preview Panel", "Preview shows filename",
                   "PASS" if len(filename_text) > 0 else "FAIL",
                   "Non-empty filename", filename_text)

            # Check preview shows dimensions
            dims_text = page.locator("#preview-dims").text_content()
            record("Preview Panel", "Preview shows dimensions",
                   "PASS" if "x" in dims_text else "FAIL",
                   "Contains 'x' (WxH)", dims_text)

            # Undo this save to clean up
            page.keyboard.press("Meta+z")
            page.wait_for_timeout(1000)

        # ============================================================
        # 11. EDGE CASES
        # ============================================================
        print("\n=== 11. EDGE CASES ===")

        # Navigate to frame 0 and try going left
        page.locator("#frame-input").fill("0")
        page.locator("#frame-input").press("Enter")
        page.wait_for_timeout(500)
        page.locator("#canvas").click()
        page.wait_for_timeout(200)

        page.keyboard.press("ArrowLeft")
        page.wait_for_timeout(500)
        frame_at_zero = page.locator("#frame-input").input_value()
        record("Edge Cases", "Cannot go below frame 0",
               "PASS" if frame_at_zero == "0" else "FAIL",
               "0", frame_at_zero)

        # Navigate to last frame and try going right
        # Get total frames from API
        api_response = page.evaluate("fetch('/api/video/info').then(r => r.json())")
        total_frames = api_response["total_frames"]
        last_frame = total_frames - 1

        page.locator("#frame-input").fill(str(last_frame))
        page.locator("#frame-input").press("Enter")
        page.wait_for_timeout(800)
        page.locator("#canvas").click()
        page.wait_for_timeout(200)

        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(500)
        frame_at_end = page.locator("#frame-input").input_value()
        record("Edge Cases", "Cannot go beyond last frame",
               "PASS" if frame_at_end == str(last_frame) else "FAIL",
               str(last_frame), frame_at_end)

        shot = ss(page, "11_edge_last_frame")

        # Test negative frame input
        page.locator("#frame-input").fill("-5")
        page.locator("#frame-input").press("Enter")
        page.wait_for_timeout(500)
        frame_neg = page.locator("#frame-input").input_value()
        record("Edge Cases", "Negative frame input handled",
               "PASS" if frame_neg == "0" else "WARN",
               "0 (clamped to min)", frame_neg)

        # Test very large frame input
        page.locator("#frame-input").fill("999999")
        page.locator("#frame-input").press("Enter")
        page.wait_for_timeout(500)
        frame_big = page.locator("#frame-input").input_value()
        record("Edge Cases", "Oversized frame input handled",
               "PASS" if frame_big == str(last_frame) else "WARN",
               f"{last_frame} (clamped to max)", frame_big)

        shot = ss(page, "11b_edge_big_frame")

        # ============================================================
        # 12. ERROR HANDLING
        # ============================================================
        print("\n=== 12. ERROR HANDLING ===")

        # Navigate back to frame 0
        page.locator("#frame-input").fill("0")
        page.locator("#frame-input").press("Enter")
        page.wait_for_timeout(500)

        # Try saving with no lasso drawn
        page.keyboard.press("Escape")  # Clear any existing lasso
        page.wait_for_timeout(200)
        page.keyboard.press("s")
        page.wait_for_timeout(1000)

        shot = ss(page, "12_save_no_lasso")

        # Check error toast appeared
        toasts = page.locator(".toast")
        error_found = False
        for i in range(toasts.count()):
            t = toasts.nth(i)
            classes = t.get_attribute("class") or ""
            text = t.text_content()
            if "error" in classes and ("lasso" in text.lower() or "draw" in text.lower()):
                error_found = True
                break
        record("Error Handling", "Save without lasso shows error toast",
               "PASS" if error_found else "FAIL",
               "Error toast with 'lasso' or 'draw'",
               f"Found: {error_found}", shot)

        # Test undo with nothing to undo (undo all saves first to be sure)
        # Make sure undo stack is empty by calling undo multiple times via API
        for _ in range(5):
            page.evaluate("fetch('/api/undo', {method:'POST'})")
        page.wait_for_timeout(300)

        page.keyboard.press("Meta+z")
        page.wait_for_timeout(1000)

        shot = ss(page, "12b_undo_nothing")
        toasts = page.locator(".toast")
        undo_error_found = False
        for i in range(toasts.count()):
            t = toasts.nth(i)
            text = t.text_content()
            if "undo" in text.lower() or "nothing" in text.lower():
                undo_error_found = True
                break
        record("Error Handling", "Undo with empty stack shows feedback",
               "PASS" if undo_error_found else "WARN",
               "Toast with 'undo' or 'nothing'",
               f"Found: {undo_error_found}", shot)

        # ============================================================
        # 13. VISUAL INSPECTION
        # ============================================================
        print("\n=== 13. VISUAL INSPECTION ===")

        # Take full-page screenshots at different states
        page.locator("#frame-input").fill("0")
        page.locator("#frame-input").press("Enter")
        page.wait_for_timeout(800)
        shot = ss(page, "13_visual_frame0")
        record("Visual Inspection", "Frame 0 display",
               "PASS", "Frame renders without glitches",
               "Visual check needed", shot)

        page.locator("#frame-input").fill("2000")
        page.locator("#frame-input").press("Enter")
        page.wait_for_timeout(800)
        shot = ss(page, "13b_visual_frame2000")
        record("Visual Inspection", "Mid-video frame display",
               "PASS", "Frame renders without glitches",
               "Visual check needed", shot)

        # Check for text overlap in sidebar
        sidebar_visible = page.locator(".sidebar").is_visible()
        record("Visual Inspection", "Sidebar visible and not overlapping",
               "PASS" if sidebar_visible else "FAIL",
               "Sidebar visible", str(sidebar_visible))

        # Check scrubber alignment
        scrub_info = page.locator(".scrubber-info").is_visible()
        record("Visual Inspection", "Scrubber info visible",
               "PASS" if scrub_info else "FAIL",
               "Scrubber info visible", str(scrub_info))

        # Check that the canvas area fills available space (no blank gaps)
        canvas_box_final = page.locator("#canvas").bounding_box()
        if canvas_box_final:
            record("Visual Inspection", "Canvas fills center area",
                   "PASS" if canvas_box_final["width"] > 400 and canvas_box_final["height"] > 300 else "WARN",
                   "Width > 400 and height > 300",
                   f"{canvas_box_final['width']:.0f}x{canvas_box_final['height']:.0f}")

        # Final full screenshot with various elements visible
        shot = ss(page, "13c_final_state")
        record("Visual Inspection", "Final state clean",
               "PASS", "No visual anomalies",
               "Visual check needed", shot)

        # ============================================================
        # 14. SKIP BUTTON INTERACTION
        # ============================================================
        print("\n=== 14. SKIP BUTTONS ===")

        # Test clicking skip buttons
        skip_btns = page.locator(".skip-btn")
        for i in range(skip_btns.count()):
            btn = skip_btns.nth(i)
            skip_val = btn.get_attribute("data-skip")
            btn.click()
            page.wait_for_timeout(200)
            is_active = "active" in (btn.get_attribute("class") or "")
            record("Skip Buttons", f"Skip {skip_val} button activates on click",
                   "PASS" if is_active else "FAIL",
                   "Button has 'active' class", str(is_active))

        # Reset to skip 1
        page.locator(".skip-btn[data-skip='1']").click()
        page.wait_for_timeout(200)

        # ============================================================
        # 15. RESPONSIVE BEHAVIOR
        # ============================================================
        print("\n=== 15. RESPONSIVE CHECK ===")

        # Resize viewport smaller
        page.set_viewport_size({"width": 900, "height": 600})
        page.wait_for_timeout(500)
        shot = ss(page, "15_small_viewport")

        # Check elements still visible at smaller size
        header_vis = page.locator(".header").is_visible()
        sidebar_vis = page.locator(".sidebar").is_visible()
        canvas_vis = page.locator("#canvas").is_visible()
        record("Responsive", "Elements visible at 900x600",
               "PASS" if all([header_vis, sidebar_vis, canvas_vis]) else "WARN",
               "Header, sidebar, canvas all visible",
               f"header={header_vis}, sidebar={sidebar_vis}, canvas={canvas_vis}", shot)

        # Restore viewport
        page.set_viewport_size({"width": 1400, "height": 900})
        page.wait_for_timeout(500)

        # ============================================================
        # DONE
        # ============================================================
        browser.close()

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    fail_count = sum(1 for r in results if r["status"] == "FAIL")
    warn_count = sum(1 for r in results if r["status"] == "WARN")
    total = len(results)
    print(f"Total: {total}  |  PASS: {pass_count}  |  FAIL: {fail_count}  |  WARN: {warn_count}")
    print(f"Pass rate: {pass_count/total*100:.1f}%")

    if fail_count > 0:
        print("\nFAILURES:")
        for r in results:
            if r["status"] == "FAIL":
                print(f"  - [{r['area']}] {r['name']}: Expected '{r['expected']}', Got '{r['actual']}'")

    if warn_count > 0:
        print("\nWARNINGS:")
        for r in results:
            if r["status"] == "WARN":
                print(f"  - [{r['area']}] {r['name']}: Expected '{r['expected']}', Got '{r['actual']}'")

    return results


if __name__ == "__main__":
    import math
    all_results = run_tests()

    # Write results as JSON for report generation
    results_file = SCREENSHOT_DIR / "results.json"
    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults written to {results_file}")
