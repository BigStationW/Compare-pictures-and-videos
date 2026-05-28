# Version: stacked captions + exact last-caption baseline alignment
# === Adjustable Text Parameters ===
TITLE_FONT_SCALE_BASE = 0.2        # Adjusts title font size (default 1.0)
FILENAME_FONT_SCALE_BASE = 1.0     # Adjusts filename caption font size (default 1.0)

# === Layout Parameters ===
ROW_LAYOUT_THRESHOLD = 3          # Number of clips (or less) to use row layout. Above this, uses grid layout.

# === Font Customization Options ===
FONT_FACE = 'SIMPLEX'              # Choose from: SIMPLEX, PLAIN, DUPLEX, COMPLEX, TRIPLEX, COMPLEX_SMALL, SCRIPT_SIMPLEX, SCRIPT_COMPLEX
FONT_BOLD = True                   # Set to True for bold text, False for normal
# ==================================

# === Font Customization Options ===
FONT_PATH = "C:/Windows/Fonts/arial.ttf"  # Path to a TrueType font file
FONT_BOLD_PATH = "C:/Windows/Fonts/arialbd.ttf"  # Path to bold font
FONT_BOLD = True                   # Set to True for bold text, False for normal
# ==================================

import cv2
import numpy as np
from moviepy.editor import VideoFileClip, VideoClip
from PIL import Image, ImageDraw, ImageFont
import os
import glob
import math
import re

# Title text for the video (set to "" or " " to disable the title bar)
# Use \n to jump lines

title_text = 'Qwen-Image-Edit-2511 - Turn this image into a painting.'

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def get_stack_group_number(media_file):
    """
    Return the leading number for filenames like:
      1a.png, 1b.png, 1a My Caption.png, 1b_My_Caption.png

    Files with the same leading number AND a letter suffix are treated as one
    vertical stack. Plain "1.png" / "2.png" remain normal standalone cells.
    """
    basename = os.path.splitext(os.path.basename(media_file))[0]
    match = re.match(r'^\s*(\d+)([a-zA-Z])(?:[\s._-]+|$)', basename)
    return int(match.group(1)) if match else None

def group_media_indices_for_layout(loaded_media_files):
    """
    Converts loaded clips into layout cells.

    Example:
      1a.png, 1b.png, 2.png, 3.png
    becomes:
      [[0, 1], [2], [3]]

    The first layout cell is rendered as a vertical stack.
    """
    stack_buckets = {}
    for idx, media_file in enumerate(loaded_media_files):
        group_number = get_stack_group_number(media_file)
        if group_number is not None:
            stack_buckets.setdefault(group_number, []).append(idx)

    layout_items = []
    added_stack_groups = set()

    for idx, media_file in enumerate(loaded_media_files):
        group_number = get_stack_group_number(media_file)

        if group_number is not None and len(stack_buckets[group_number]) > 1:
            if group_number not in added_stack_groups:
                layout_items.append(stack_buckets[group_number])
                added_stack_groups.add(group_number)
        else:
            layout_items.append([idx])

    return layout_items

def make_layout_item_display_name(item_clip_indices, display_names):
    names = [
        display_names[clip_idx]
        for clip_idx in item_clip_indices
        if clip_idx < len(display_names) and display_names[clip_idx].strip()
    ]
    return "\n".join(names)

def find_media_files():
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
    media_files = []

    script_dir = os.path.dirname(os.path.abspath(__file__))

    for ext in video_extensions + image_extensions:
        media_files.extend(glob.glob(os.path.join(script_dir, f'*{ext}')))

    output_file = os.path.join(script_dir, "combined_video.mp4")
    output_image = os.path.join(script_dir, "combined_image.jpg")
    if output_file in media_files:
        media_files.remove(output_file)
    if output_image in media_files:
        media_files.remove(output_image)

    media_files.sort(key=natural_sort_key)
    return media_files

# Font mapping to TrueType equivalents
def get_font_path(font_face, bold=False):
    """Map OpenCV font names to Windows TrueType fonts"""
    
    font_map = {
        'SIMPLEX': 'C:/Windows/Fonts/arial.ttf' if not bold else 'C:/Windows/Fonts/arialbd.ttf',
        'PLAIN': 'C:/Windows/Fonts/cour.ttf' if not bold else 'C:/Windows/Fonts/courbd.ttf',
        'DUPLEX': 'C:/Windows/Fonts/arial.ttf' if not bold else 'C:/Windows/Fonts/arialbd.ttf',
        'COMPLEX': 'C:/Windows/Fonts/times.ttf' if not bold else 'C:/Windows/Fonts/timesbd.ttf',
        'TRIPLEX': 'C:/Windows/Fonts/times.ttf' if not bold else 'C:/Windows/Fonts/timesbd.ttf',
        'COMPLEX_SMALL': 'C:/Windows/Fonts/times.ttf' if not bold else 'C:/Windows/Fonts/timesbd.ttf',
        'SCRIPT_SIMPLEX': 'C:/Windows/Fonts/comic.ttf',
        'SCRIPT_COMPLEX': 'C:/Windows/Fonts/KUNSTLER.TTF',
    }
    
    return font_map.get(font_face.upper())

def get_pil_font(size, bold=False):
    try:
        font_path = get_font_path(FONT_FACE, bold and FONT_BOLD)
        if font_path and os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)
        else:
            print(f"Warning: Font '{FONT_FACE}' not found at {font_path}, using Arial as fallback")
            return ImageFont.truetype('C:/Windows/Fonts/arial.ttf', size)
    except Exception as e:
        print(f"Error loading font: {e}, using default")
        return ImageFont.load_default()

media_files = find_media_files()
if len(media_files) < 1:
    print("Error: No media files found.")
    exit(1)

print(f"Found {len(media_files)} media files to combine")

clips = []
display_names = []
clip_types = []
loaded_media_files = []
image_duration = 5
has_videos = False
max_video_duration = 0

for media_file in media_files:
    ext = os.path.splitext(media_file)[1].lower()
    if ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
        has_videos = True
        temp_clip = VideoFileClip(media_file)
        max_video_duration = max(max_video_duration, temp_clip.duration)
        temp_clip.close()

if has_videos:
    image_duration = max_video_duration
    print(f"Videos detected. Using max video duration: {max_video_duration:.2f}s")
else:
    print("Only images detected. Will output a single combined image.")

for media_file in media_files:
    ext = os.path.splitext(media_file)[1].lower()
    basename = os.path.splitext(os.path.basename(media_file))[0]
    display_name = re.sub(r'^\s*\d+[a-zA-Z]?(?:[\.\s_-]+|$)', '', basename).replace('@', ':')

    if ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
        print(f"Loading video: {media_file}")
        clip = VideoFileClip(media_file)
        clip_types.append('video')
    elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
        print(f"Loading image: {media_file}")
        img = cv2.imread(media_file)
        if img is None:
            print(f"Warning: Unable to load image {media_file}")
            continue

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        clip = VideoClip(lambda t, img=img: img, duration=image_duration)
        height, width = img.shape[:2]
        clip.size = (width, height)
        clip_types.append('image')
    else:
        continue

    clips.append(clip)
    display_names.append(display_name)
    loaded_media_files.append(media_file)

# Calculate actual dimensions for each clip
clip_dimensions = []
for i, clip in enumerate(clips):
    frame = clip.get_frame(0)
    h, w = frame.shape[:2]
    clip_dimensions.append((w, h))

# Build layout cells. A cell can contain one clip, or a vertical stack like 1a + 1b.
layout_items = group_media_indices_for_layout(loaded_media_files)
layout_item_names = [
    make_layout_item_display_name(item_clip_indices, display_names)
    for item_clip_indices in layout_items
]

def wrap_text_pil(text, max_width, font):
    # Split by newlines first to respect manual line breaks
    manual_lines = text.split('\n')
    all_lines = []
    
    draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    
    for manual_line in manual_lines:
        words = manual_line.split()
        if not words:
            all_lines.append('')  # Preserve empty lines
            continue
            
        current_line = words[0]
        for word in words[1:]:
            test_line = current_line + ' ' + word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]
            if line_width <= max_width - 20:
                current_line = test_line
            else:
                all_lines.append(current_line)
                current_line = word
        all_lines.append(current_line)
    
    return all_lines


def get_caption_font_for_height(media_height):
    caption_font_size = int(FILENAME_FONT_SCALE_BASE * (media_height / 800) * 35) if media_height > 0 else int(FILENAME_FONT_SCALE_BASE * 35)
    caption_font_size = max(1, caption_font_size)
    return get_pil_font(caption_font_size, FONT_BOLD)

def get_font_line_height(font):
    draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    bbox = draw.textbbox((0, 0), "Ay", font=font)
    return max(1, int((bbox[3] - bbox[1]) * 1.4))

def calculate_caption_block_height(display_name, media_height, cell_width, top_padding=30, bottom_padding=30):
    """Caption height for one image/video, placed directly below that image/video."""
    if not (display_name and display_name.strip()):
        return 0

    caption_font = get_caption_font_for_height(media_height)
    line_height = get_font_line_height(caption_font)
    wrapped_lines = wrap_text_pil(display_name, cell_width, caption_font)

    return len(wrapped_lines) * line_height + top_padding + bottom_padding if wrapped_lines else 0

def draw_caption_on_cell(
    cell,
    display_name,
    y_start,
    caption_height,
    cell_width,
    media_height,
    vertical_align="center",
    bottom_padding=30
):
    """Draw one caption block directly under one image/video."""
    if caption_height <= 0 or not (display_name and display_name.strip()):
        return cell

    caption_font = get_caption_font_for_height(media_height)
    line_height = get_font_line_height(caption_font)
    wrapped_lines = wrap_text_pil(display_name, cell_width, caption_font)
    total_text_height = len(wrapped_lines) * line_height

    if vertical_align == "bottom":
        text_start_y = y_start + caption_height - total_text_height - bottom_padding
    else:
        text_start_y = y_start + (caption_height - total_text_height) // 2

    draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    for j, line in enumerate(wrapped_lines):
        bbox = draw.textbbox((0, 0), line, font=caption_font)
        line_width = bbox[2] - bbox[0]
        text_x = (cell_width - line_width) // 2
        text_y = text_start_y + j * line_height
        cell = add_text_to_frame_pil(cell, line, (text_x, text_y), caption_font)

    return cell

def calculate_clip_with_caption_dimension(clip_idx, target_width=None, stack_last=False):
    """Natural dimensions for one image/video plus its own caption below it."""
    w, h = clip_dimensions[clip_idx]
    if target_width is None:
        media_width = max(1, w)
        media_height = max(1, h)
    else:
        media_width = max(1, int(target_width))
        media_height = max(1, int(round(h * (media_width / w)))) if w > 0 else max(1, h)

    # In stacked cells, the final child's caption is drawn tight to the bottom
    # so the bottom of that filename text can align with neighboring image bottoms.
    bottom_padding = 0 if stack_last else 30
    caption_height = calculate_caption_block_height(
        display_names[clip_idx],
        media_height,
        media_width,
        bottom_padding=bottom_padding
    )
    return media_width, media_height + caption_height

def calculate_layout_item_dimension(item_clip_indices):
    """
    Returns the natural dimensions of a layout cell.

    Stacked cells are now built as:
      1a image
      1a caption
      1b image
      1b caption

    This keeps each filename/caption directly under its matching image/video.
    """
    if len(item_clip_indices) == 1:
        return calculate_clip_with_caption_dimension(item_clip_indices[0])

    stack_width = max((clip_dimensions[idx][0] for idx in item_clip_indices), default=1)
    total_height = 0

    last_stack_idx = item_clip_indices[-1]
    for idx in item_clip_indices:
        _, clip_total_height = calculate_clip_with_caption_dimension(
            idx,
            stack_width,
            stack_last=(idx == last_stack_idx)
        )
        total_height += clip_total_height

    return max(stack_width, 1), max(total_height, 1)

def calculate_layout_item_core_dimension(item_clip_indices):
    """
    Dimensions used for row/column alignment.

    - A stacked cell's core includes every child image/video plus each child's
      own caption, because that whole stack is the visual block to align against.
    - A normal single-item cell's core is only the image/video. Its caption is
      drawn in an extra row below, so the bottom of the image/video can align
      with the bottom of a stacked cell's final caption.
    """
    if len(item_clip_indices) == 1:
        w, h = clip_dimensions[item_clip_indices[0]]
        return max(w, 1), max(h, 1)

    return calculate_layout_item_dimension(item_clip_indices)

layout_item_core_dimensions = [
    calculate_layout_item_core_dimension(item_clip_indices)
    for item_clip_indices in layout_items
]

# Backwards-compatible alias for any older helper code that expects this name.
layout_item_dimensions = layout_item_core_dimensions

# Calculate grid dimensions using layout cells, not raw clip count.
num_layout_items = len(layout_items)
if num_layout_items <= ROW_LAYOUT_THRESHOLD:
    grid_cols = num_layout_items
    grid_rows = 1
else:
    grid_cols = math.ceil(math.sqrt(num_layout_items))
    grid_rows = math.ceil(num_layout_items / grid_cols)

def calculate_max_caption_height_for_row(row_idx, display_names, row_height, cell_widths_in_row):
    has_any_text_in_row = False
    start_clip_idx = row_idx * grid_cols
    end_clip_idx = min(start_clip_idx + grid_cols, len(display_names))
    for i in range(start_clip_idx, end_clip_idx):
        if i < len(display_names) and display_names[i] and display_names[i].strip():
            has_any_text_in_row = True
            break 

    if not has_any_text_in_row:
        return 0 

    caption_font_size = int(FILENAME_FONT_SCALE_BASE * (row_height / 800) * 35) if row_height > 0 else int(FILENAME_FONT_SCALE_BASE * 35)
    caption_font = get_pil_font(caption_font_size, FONT_BOLD)
    caption_padding = 30
    
    # Get line height from font
    draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    bbox = draw.textbbox((0, 0), "Ay", font=caption_font)
    line_height = int((bbox[3] - bbox[1]) * 1.4)
    
    max_lines = 0
    for i, image_width in enumerate(cell_widths_in_row):
        clip_idx = row_idx * grid_cols + i
        if clip_idx < len(display_names):
            display_name = display_names[clip_idx]
            wrapped_lines = wrap_text_pil(display_name, image_width, caption_font)
            max_lines = max(max_lines, len(wrapped_lines))
    
    return max_lines * line_height + caption_padding * 2 if max_lines > 0 else 0

def add_text_to_frame_pil(frame, text, position, font, color=(255, 255, 255)):
    """Add text to frame using PIL for Unicode support"""
    img_pil = Image.fromarray(frame)
    draw = ImageDraw.Draw(img_pil)
    draw.text(position, text, font=font, fill=color)
    return np.array(img_pil)


def get_clip_frame_for_layout(clip_idx, t):
    clip = clips[clip_idx]
    if clip_types[clip_idx] == 'video':
        safe_t = min(t, max(clip.duration - 0.001, 0))
        return clip.get_frame(safe_t)
    return clip.get_frame(0)

def render_clip_with_caption(clip_idx, target_width, t, stack_last=False):
    """Render one image/video plus its own caption directly below it."""
    target_width = max(int(target_width), 1)
    w, h = clip_dimensions[clip_idx]
    media_height = max(1, int(round(h * (target_width / w)))) if w > 0 else max(1, h)

    frame = get_clip_frame_for_layout(clip_idx, t)
    resized_frame = cv2.resize(frame, (target_width, media_height), interpolation=cv2.INTER_LANCZOS4)

    bottom_padding = 0 if stack_last else 30
    caption_height = calculate_caption_block_height(
        display_names[clip_idx],
        media_height,
        target_width,
        bottom_padding=bottom_padding
    )
    cell = np.zeros((media_height + caption_height, target_width, 3), dtype=np.uint8)
    cell[:media_height, :] = resized_frame

    if caption_height > 0:
        cell = draw_caption_on_cell(
            cell,
            display_names[clip_idx],
            media_height,
            caption_height,
            target_width,
            media_height,
            vertical_align=("bottom" if stack_last else "center"),
            bottom_padding=bottom_padding
        )

    return cell

def render_layout_item(item_clip_indices, target_width, target_height, t):
    """
    Render one complete stacked layout cell.

    If the cell is a stack, each child is rendered as its own image/video plus
    its own caption before the next child begins.
    """
    target_width = max(int(target_width), 1)
    target_height = max(int(target_height), 1)

    last_stack_idx = item_clip_indices[-1] if item_clip_indices else None
    child_cells = [
        render_clip_with_caption(idx, target_width, t, stack_last=(idx == last_stack_idx))
        for idx in item_clip_indices
    ]
    if child_cells:
        cell = np.vstack(child_cells)
    else:
        cell = np.zeros((target_height, target_width, 3), dtype=np.uint8)

    if cell.shape[0] != target_height or cell.shape[1] != target_width:
        cell = cv2.resize(cell, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)

    return cell


def render_clip_media_only(clip_idx, target_width, target_height, t):
    """Render only the image/video, with no caption underneath."""
    target_width = max(int(target_width), 1)
    target_height = max(int(target_height), 1)

    frame = get_clip_frame_for_layout(clip_idx, t)
    return cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)


def get_row_item_indices(row_idx):
    start_item_idx = row_idx * grid_cols
    end_item_idx = min(start_item_idx + grid_cols, num_layout_items)
    return list(range(start_item_idx, end_item_idx))


def get_single_item_caption_height(item_clip_indices, media_height, cell_width):
    """Caption height for normal, non-stacked cells only."""
    if len(item_clip_indices) != 1:
        return 0

    clip_idx = item_clip_indices[0]
    return calculate_caption_block_height(display_names[clip_idx], media_height, cell_width)


def process_frame_row_layout(t):
    """
    Row layout with correct stack alignment.

    For rows containing a stacked cell like 1a+1b, the stack's full height
    includes the captions under 1a and 1b. Normal cells like 2 and 3 scale their
    image/video to that same height. Their own captions, if present, are placed
    in a separate row below. This makes the bottom of the 1b caption line up
    with the bottom of the 2/3 image/video.
    """
    row_layout_info = []
    max_overall_width = 0

    for row_idx in range(grid_rows):
        item_indices = get_row_item_indices(row_idx)
        if not item_indices:
            continue

        max_core_h = 0
        for item_idx in item_indices:
            _, h = layout_item_core_dimensions[item_idx]
            max_core_h = max(max_core_h, h)

        uniform_core_height = max_core_h if max_core_h > 0 else 1
        scaled_widths = []
        row_extra_caption_height = 0

        for item_idx in item_indices:
            w, h = layout_item_core_dimensions[item_idx]
            new_w = int(w * (uniform_core_height / h)) if h > 0 else 1
            new_w = max(new_w, 1)
            scaled_widths.append(new_w)

            item_clip_indices = layout_items[item_idx]
            row_extra_caption_height = max(
                row_extra_caption_height,
                get_single_item_caption_height(item_clip_indices, uniform_core_height, new_w)
            )

        natural_width = sum(scaled_widths)
        max_overall_width = max(max_overall_width, natural_width)

        row_layout_info.append({
            "row_idx": row_idx,
            "item_indices": item_indices,
            "scaled_widths": scaled_widths,
            "natural_width": natural_width,
            "uniform_core_height": uniform_core_height,
            "row_extra_caption_height": row_extra_caption_height,
        })

    all_final_rows = []

    for layout_info in row_layout_info:
        uniform_core_height = layout_info["uniform_core_height"]
        row_extra_caption_height = layout_info["row_extra_caption_height"]
        total_row_height = uniform_core_height + row_extra_caption_height
        scaled_widths = layout_info["scaled_widths"]
        natural_width = layout_info["natural_width"]

        cells_in_row = []
        for item_idx, cell_width in zip(layout_info["item_indices"], scaled_widths):
            item_clip_indices = layout_items[item_idx]
            cell = np.zeros((total_row_height, cell_width, 3), dtype=np.uint8)

            if len(item_clip_indices) > 1:
                rendered_core = render_layout_item(item_clip_indices, cell_width, uniform_core_height, t)
                cell[:uniform_core_height, :] = rendered_core
            else:
                clip_idx = item_clip_indices[0]
                rendered_media = render_clip_media_only(clip_idx, cell_width, uniform_core_height, t)
                cell[:uniform_core_height, :] = rendered_media

                if row_extra_caption_height > 0:
                    cell = draw_caption_on_cell(
                        cell,
                        display_names[clip_idx],
                        uniform_core_height,
                        row_extra_caption_height,
                        cell_width,
                        uniform_core_height
                    )

            cells_in_row.append(cell)

        row_with_captions = np.hstack(cells_in_row)

        final_row_canvas = np.zeros((row_with_captions.shape[0], max_overall_width, 3), dtype=np.uint8)
        x_offset = (max_overall_width - natural_width) // 2
        final_row_canvas[:, x_offset : x_offset + natural_width] = row_with_captions

        all_final_rows.append(final_row_canvas)

    return np.vstack(all_final_rows) if all_final_rows else None


def process_frame_grid_layout(t):
    """
    Grid layout with the same alignment rule as row layout.

    Stacked cells are treated as the row's core block. Single-item captions are
    drawn in a separate caption band below the row core, so a stack's final
    caption aligns with neighboring image/video bottoms.
    """
    max_col_widths = [0] * grid_cols
    for i, (w, h) in enumerate(layout_item_core_dimensions):
        col_idx = i % grid_cols
        max_col_widths[col_idx] = max(max_col_widths[col_idx], w)

    scaled_core_dimensions = []
    for i, (w, h) in enumerate(layout_item_core_dimensions):
        col_idx = i % grid_cols
        target_width = max(max_col_widths[col_idx], 1)
        if w > 0:
            scale_factor = target_width / w
            scaled_h = max(1, int(h * scale_factor))
            scaled_core_dimensions.append((target_width, scaled_h))
        else:
            scaled_core_dimensions.append((target_width, max(h, 1)))

    total_grid_width = sum(max_col_widths)
    all_final_rows = []

    for row_idx in range(grid_rows):
        item_indices = get_row_item_indices(row_idx)
        if not item_indices:
            continue

        max_row_core_height = 0
        for item_idx in item_indices:
            _, scaled_h = scaled_core_dimensions[item_idx]
            max_row_core_height = max(max_row_core_height, scaled_h)

        row_extra_caption_height = 0
        for item_idx in item_indices:
            scaled_w, scaled_h = scaled_core_dimensions[item_idx]
            item_clip_indices = layout_items[item_idx]
            row_extra_caption_height = max(
                row_extra_caption_height,
                get_single_item_caption_height(item_clip_indices, scaled_h, scaled_w)
            )

        total_row_height = max_row_core_height + row_extra_caption_height
        row_canvas = np.zeros((total_row_height, total_grid_width, 3), dtype=np.uint8)
        current_x = 0

        for col_idx in range(grid_cols):
            item_idx = row_idx * grid_cols + col_idx
            if item_idx >= num_layout_items:
                break

            scaled_w, scaled_h = scaled_core_dimensions[item_idx]
            item_clip_indices = layout_items[item_idx]
            cell = np.zeros((total_row_height, scaled_w, 3), dtype=np.uint8)
            y_offset = max_row_core_height - scaled_h  # bottom-align row cores

            if len(item_clip_indices) > 1:
                rendered_core = render_layout_item(item_clip_indices, scaled_w, scaled_h, t)
                cell[y_offset:y_offset + scaled_h, :] = rendered_core
            else:
                clip_idx = item_clip_indices[0]
                rendered_media = render_clip_media_only(clip_idx, scaled_w, scaled_h, t)
                cell[y_offset:y_offset + scaled_h, :] = rendered_media

                if row_extra_caption_height > 0:
                    cell = draw_caption_on_cell(
                        cell,
                        display_names[clip_idx],
                        max_row_core_height,
                        row_extra_caption_height,
                        scaled_w,
                        scaled_h
                    )

            row_canvas[:, current_x:current_x + scaled_w] = cell
            current_x += scaled_w

        all_final_rows.append(row_canvas)

    return np.vstack(all_final_rows) if all_final_rows else None

def process_frame(t):
    # This function now acts as a dispatcher
    if num_layout_items <= ROW_LAYOUT_THRESHOLD:
        grid = process_frame_row_layout(t)
    else:
        grid = process_frame_grid_layout(t)

    # Title bar logic (common for both layouts)
    if not (title_text and title_text.strip()):
        if grid is None: return np.zeros((100, 100, 3), dtype=np.uint8)
        return grid.astype(np.uint8)

    combined_width = grid.shape[1] if grid is not None else 800
    if combined_width == 0: combined_width = 800

    title_font_size = int(TITLE_FONT_SCALE_BASE * (combined_width / 700) * 50)
    title_font = get_pil_font(title_font_size, FONT_BOLD)
    title_padding = 40

    lines = wrap_text_pil(title_text, combined_width - 40, title_font)
    
    # Calculate line height
    draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    bbox = draw.textbbox((0, 0), "Ay", font=title_font)
    line_spacing = int((bbox[3] - bbox[1]) * 1.4)
    
    title_height = line_spacing * len(lines) + title_padding * 2
    title_bar = np.zeros((title_height, combined_width, 3), dtype=np.uint8)

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=title_font)
        line_width = bbox[2] - bbox[0]
        line_x = (combined_width - line_width) // 2
        line_y = title_padding + i * line_spacing
        title_bar = add_text_to_frame_pil(title_bar, line, (line_x, line_y), title_font)

    if grid is not None:
        combined = np.vstack([title_bar, grid])
    else:
        combined = title_bar
    
    return combined.astype(np.uint8)


# Generate output
if has_videos:
    output_file = "combined_video.mp4"
    max_duration = max((clip.duration for clip in clips if clip.duration is not None), default=image_duration)
    
    # Create visual clip
    final_clip = VideoClip(make_frame=process_frame, duration=max_duration)
    
    # Extract and combine audio from video clips
    audio_clips = [clip.audio for i, clip in enumerate(clips) if clip_types[i] == 'video' and clip.audio is not None]
    
    if audio_clips:
        from moviepy.editor import CompositeAudioClip
        # Mix all audio tracks together
        combined_audio = CompositeAudioClip(audio_clips)
        final_clip = final_clip.set_audio(combined_audio)
    
    final_clip.write_videofile(output_file, fps=24, codec='libx264')
    print(f"Video saved as: {output_file}")
else:
    output_file = "combined_image.jpg"
    combined_frame = process_frame(0)
    combined_frame_bgr = cv2.cvtColor(combined_frame, cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_file, combined_frame_bgr)
    print(f"Image saved as: {output_file}")

# Clean up
for clip in clips:
    if isinstance(clip, VideoFileClip):
        clip.close()
