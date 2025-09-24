import cv2
import numpy as np
from moviepy.editor import VideoFileClip, VideoClip
import os
import glob
import math
import re

# === Adjustable Text Parameters ===
TITLE_FONT_SCALE_BASE = 0.3      # Adjusts title font size
FILENAME_FONT_SCALE_BASE = 1.5   # Adjusts filename caption font size

# === Font Customization Options ===
FONT_FACE = 'SIMPLEX'            # Choose from: SIMPLEX, PLAIN, DUPLEX, COMPLEX, etc.
FONT_BOLD = True                 # Set to True for bold text, False for normal
# ==================================

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def find_media_files():
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
    media_files = []
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for ext in video_extensions + image_extensions:
        media_files.extend(glob.glob(os.path.join(script_dir, f'*{ext}')))
    output_file = os.path.join(script_dir, "combined_video.mp4")
    output_image = os.path.join(script_dir, "combined_image.jpg")
    if output_file in media_files: media_files.remove(output_file)
    if output_image in media_files: media_files.remove(output_image)
    media_files.sort(key=natural_sort_key)
    return media_files

font_map = {'SIMPLEX': cv2.FONT_HERSHEY_SIMPLEX, 'PLAIN': cv2.FONT_HERSHEY_PLAIN, 'DUPLEX': cv2.FONT_HERSHEY_DUPLEX, 'COMPLEX': cv2.FONT_HERSHEY_COMPLEX, 'TRIPLEX': cv2.FONT_HERSHEY_TRIPLEX, 'COMPLEX_SMALL': cv2.FONT_HERSHEY_COMPLEX_SMALL, 'SCRIPT_SIMPLEX': cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 'SCRIPT_COMPLEX': cv2.FONT_HERSHEY_SCRIPT_COMPLEX}
font = font_map.get(FONT_FACE.upper(), cv2.FONT_HERSHEY_SIMPLEX)

media_files = find_media_files()
if not media_files:
    print("Error: No media files found.")
    exit(1)

num_clips = len(media_files)
print(f"Found {num_clips} media files to combine")

# === COMMAND-LINE DIALOGUE FOR SETUP ===
cols_input = input(f"Enter the number of COLUMNS (press Enter for auto): ")
rows_input = input(f"Enter the number of ROWS (press Enter for auto): ")
# New prompt for the title
title_text = input("Enter the title for the final output (press Enter for no title): ")

try:
    GRID_COLS = int(cols_input) if cols_input else 'auto'
except ValueError:
    print("Invalid column input. Defaulting to 'auto'.")
    GRID_COLS = 'auto'

try:
    GRID_ROWS = int(rows_input) if rows_input else 'auto'
except ValueError:
    print("Invalid row input. Defaulting to 'auto'.")
    GRID_ROWS = 'auto'
# =======================================

clips, display_names, clip_types = [], [], []
image_duration, has_videos, max_video_duration = 5, False, 0

for media_file in media_files:
    ext = os.path.splitext(media_file)[1].lower()
    if ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
        has_videos = True
        with VideoFileClip(media_file) as temp_clip:
            max_video_duration = max(max_video_duration, temp_clip.duration)

if has_videos:
    image_duration = max_video_duration
    print(f"Videos detected. Using max video duration: {max_video_duration:.2f}s")
else:
    print("Only images detected. Will output a single combined image.")

for media_file in media_files:
    ext = os.path.splitext(media_file)[1].lower()
    
    # Label logic is now simplified to only use the filename
    basename = os.path.splitext(os.path.basename(media_file))[0]
    display_name = re.sub(r'^\s*\d+\.\s*', '', basename).replace('@', ':')

    if ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
        print(f"Loading video: {media_file}")
        clip = VideoFileClip(media_file)
        clip_types.append('video')
    elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
        print(f"Loading image: {media_file}")
        img = cv2.imread(media_file)
        if img is None:
            print(f"Warning: Unable to load image {media_file}"); continue
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        clip = VideoClip(lambda t, img=img: img, duration=image_duration)
        clip.size = (img.shape[1], img.shape[0])
        clip_types.append('image')
    else:
        continue

    clips.append(clip)
    display_names.append(display_name)

clip_dimensions = [(clip.size[0], clip.size[1]) for clip in clips]

if GRID_ROWS == 'auto' and GRID_COLS == 'auto':
    grid_cols = math.ceil(math.sqrt(num_clips))
    grid_rows = math.ceil(num_clips / grid_cols)
elif GRID_ROWS != 'auto' and GRID_COLS != 'auto':
    grid_rows, grid_cols = int(GRID_ROWS), int(GRID_COLS)
elif GRID_COLS != 'auto':
    grid_cols = int(GRID_COLS)
    grid_rows = math.ceil(num_clips / grid_cols)
elif GRID_ROWS != 'auto':
    grid_rows = int(GRID_ROWS)
    grid_cols = math.ceil(num_clips / grid_rows)

if grid_rows * grid_cols < num_clips:
    print(f"Warning: Your grid settings ({grid_rows} rows x {grid_cols} columns) are too small for {num_clips} files.")
    print(f"Only the first {grid_rows * grid_cols} files will be shown.")

print(f"Using grid layout: {grid_rows} rows x {grid_cols} columns")

def wrap_text(text, max_width, font_scale, thickness):
    words = text.split()
    if not words: return []
    lines, current_line = [], words[0]
    for word in words[1:]:
        test_line = current_line + ' ' + word
        (line_width, _), _ = cv2.getTextSize(test_line, font, font_scale, thickness)
        if line_width <= max_width - 20: current_line = test_line
        else: lines.append(current_line); current_line = word
    lines.append(current_line)
    return lines

def calculate_max_caption_height_for_row(row_idx, display_names, row_height, cell_widths_in_row):
    start_idx = row_idx * grid_cols
    end_idx = min((row_idx + 1) * grid_cols, len(display_names))
    has_any_text_in_row = any(display_names[i].strip() for i in range(start_idx, end_idx))
    if not has_any_text_in_row: return 0
    
    caption_font_scale = FILENAME_FONT_SCALE_BASE * (row_height / 800) if row_height > 0 else FILENAME_FONT_SCALE_BASE
    caption_thickness = 2 if FONT_BOLD else 1
    line_height = int(35 * caption_font_scale)
    max_lines = 0
    for i, image_width in enumerate(cell_widths_in_row):
        clip_idx = start_idx + i
        if clip_idx < len(display_names):
            wrapped_lines = wrap_text(display_names[clip_idx], image_width, caption_font_scale, caption_thickness)
            max_lines = max(max_lines, len(wrapped_lines))
    return max_lines * line_height + 60 if max_lines > 0 else 0

def add_text_to_frame(frame, text, position, font_scale=1, color=(255, 255, 255), thickness=2):
    cv2.putText(frame, text, position, font, font_scale, color, thickness, lineType=cv2.LINE_AA)

def process_frame_grid_layout(t):
    if not clips: return None
    max_col_widths = [0] * grid_cols
    for i, (w, _) in enumerate(clip_dimensions):
        col_idx = i % grid_cols
        if col_idx < len(max_col_widths): max_col_widths[col_idx] = max(max_col_widths[col_idx], w)
    
    scaled_clip_dimensions = []
    for i, (w, h) in enumerate(clip_dimensions):
        target_width = max_col_widths[i % grid_cols]
        scaled_h = int(h * (target_width / w)) if w > 0 else h
        scaled_clip_dimensions.append((target_width, scaled_h))
        
    total_grid_width = sum(max_col_widths)
    all_final_rows = []

    for row_idx in range(grid_rows):
        start_clip_idx = row_idx * grid_cols
        if start_clip_idx >= num_clips: continue
        row_indices = range(start_clip_idx, min(start_clip_idx + grid_cols, num_clips))
        
        max_row_height = max((scaled_clip_dimensions[i][1] for i in row_indices), default=1)
        col_widths_in_row = [max_col_widths[i % grid_cols] for i in row_indices]
        
        row_caption_height = calculate_max_caption_height_for_row(row_idx, display_names, max_row_height, col_widths_in_row)
        row_canvas = np.zeros((max_row_height + row_caption_height, total_grid_width, 3), dtype=np.uint8)
        current_x = 0

        for clip_idx in row_indices:
            clip, (scaled_w, scaled_h) = clips[clip_idx], scaled_clip_dimensions[clip_idx]
            frame = clip.get_frame(min(t, clip.duration - 0.001) if clip_types[clip_idx] == 'video' else t)
            resized_frame = cv2.resize(frame, (scaled_w, scaled_h), interpolation=cv2.INTER_LANCZOS4)
            y_offset = (max_row_height - scaled_h) // 2
            row_canvas[y_offset:y_offset + scaled_h, current_x:current_x + scaled_w] = resized_frame
            
            if row_caption_height > 0:
                caption_font_scale = FILENAME_FONT_SCALE_BASE * (max_row_height / 800) if max_row_height > 0 else FILENAME_FONT_SCALE_BASE
                thickness = 2 if FONT_BOLD else 1
                line_height = int(35 * caption_font_scale)
                wrapped_lines = wrap_text(display_names[clip_idx], scaled_w, caption_font_scale, thickness)
                total_text_h = len(wrapped_lines) * line_height
                text_start_y = max_row_height + (row_caption_height - total_text_h) // 2
                for j, line in enumerate(wrapped_lines):
                    (line_w, _), _ = cv2.getTextSize(line, font, caption_font_scale, thickness)
                    text_x = current_x + (scaled_w - line_w) // 2
                    text_y = text_start_y + j * line_height + int(line_height * 0.8)
                    add_text_to_frame(row_canvas, line, (text_x, text_y), font_scale=caption_font_scale, thickness=thickness)
            
            current_x += scaled_w
        all_final_rows.append(row_canvas)
        
    return np.vstack(all_final_rows) if all_final_rows else None

def process_frame(t):
    grid = process_frame_grid_layout(t)
    if not (title_text and title_text.strip()):
        return grid.astype(np.uint8) if grid is not None else np.zeros((100, 100, 3), dtype=np.uint8)
    
    combined_width = grid.shape[1] if grid is not None else 800
    title_font_scale = TITLE_FONT_SCALE_BASE * (combined_width / 700)
    thickness = 2 if FONT_BOLD else 1
    (_, text_h), _ = cv2.getTextSize(title_text, font, title_font_scale, thickness)
    lines = wrap_text(title_text, combined_width - 40, title_font_scale, thickness)
    line_spacing = int(text_h * 1.4)
    title_height = line_spacing * len(lines) + 80
    title_bar = np.zeros((title_height, combined_width, 3), dtype=np.uint8)
    
    for i, line in enumerate(lines):
        (line_w, _), _ = cv2.getTextSize(line, font, title_font_scale, thickness)
        line_x = (combined_width - line_w) // 2
        line_y = 40 + i * line_spacing + text_h
        add_text_to_frame(title_bar, line, (line_x, line_y), font_scale=title_font_scale, thickness=thickness)
        
    return np.vstack([title_bar, grid]) if grid is not None else title_bar

if has_videos:
    output_file = "combined_video.mp4"
    max_duration = max((c.duration for c in clips if c.duration), default=image_duration)
    final_clip = VideoClip(make_frame=process_frame, duration=max_duration)
    final_clip.write_videofile(output_file, fps=24, codec='libx264', audio=False)
    print(f"Video saved as: {output_file}")
else:
    output_file = "combined_image.jpg"
    combined_frame = process_frame(0)
    combined_frame_bgr = cv2.cvtColor(combined_frame, cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_file, combined_frame_bgr)
    print(f"Image saved as: {output_file}")

for clip in clips:
    if isinstance(clip, VideoFileClip): clip.close()
