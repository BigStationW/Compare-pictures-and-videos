# === Adjustable Text Parameters ===
TITLE_FONT_SCALE_BASE = 0.3        # Adjusts title font size (default 1.0)
FILENAME_FONT_SCALE_BASE = 1.5     # Adjusts filename caption font size (default 1.0)

# === Font Customization Options ===
FONT_FACE = 'SIMPLEX'              # Choose from: SIMPLEX, PLAIN, DUPLEX, COMPLEX, TRIPLEX, COMPLEX_SMALL, SCRIPT_SIMPLEX, SCRIPT_COMPLEX
FONT_BOLD = True                  # Set to True for bold text, False for normal
# ==================================

import cv2
import numpy as np
from moviepy.editor import VideoFileClip, VideoClip
import os
import glob
import math
import re

def get_user_inputs():
    """Get user inputs for title, grid dimensions, and custom labels"""
    print("\n=== Media Collage Configuration ===")
    
    # Get title
    title = input("Enter a title for your collage (press Enter for no title): ").strip()
    if not title:
        title = ""
    
    # Get grid dimensions
    print("\nGrid Layout Options:")
    print("1. Auto-calculate based on number of files")
    print("2. Custom columns and rows")
    
    while True:
        choice = input("Choose option (1 or 2): ").strip()
        if choice in ['1', '2']:
            break
        print("Please enter 1 or 2")
    
    custom_grid = choice == '2'
    custom_cols = None
    custom_rows = None
    
    if custom_grid:
        while True:
            try:
                custom_cols = int(input("Enter number of columns: "))
                if custom_cols > 0:
                    break
                print("Columns must be greater than 0")
            except ValueError:
                print("Please enter a valid number")
        
        while True:
            try:
                custom_rows = int(input("Enter number of rows: "))
                if custom_rows > 0:
                    break
                print("Rows must be greater than 0")
            except ValueError:
                print("Please enter a valid number")
    
    return title, custom_grid, custom_cols, custom_rows

def get_custom_labels(media_files):
    """Get custom labels for each media file"""
    print(f"\n=== Custom Labels for {len(media_files)} files ===")
    print("You can set custom labels for each file. Press Enter to use the filename.")
    
    custom_labels = []
    for i, media_file in enumerate(media_files):
        basename = os.path.splitext(os.path.basename(media_file))[0]
        default_label = re.sub(r'^\s*\d+\.\s*', '', basename).replace('@', ':')
        
        print(f"\nFile {i+1}: {os.path.basename(media_file)}")
        print(f"Default label: '{default_label}'")
        custom_label = input("Enter custom label (or press Enter for default): ").strip()
        
        if custom_label:
            custom_labels.append(custom_label)
        else:
            custom_labels.append(default_label)
    
    return custom_labels

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
    if output_file in media_files:
        media_files.remove(output_file)
    if output_image in media_files:
        media_files.remove(output_image)

    media_files.sort(key=natural_sort_key)
    return media_files

font_map = {
    'SIMPLEX': cv2.FONT_HERSHEY_SIMPLEX,
    'PLAIN': cv2.FONT_HERSHEY_PLAIN,
    'DUPLEX': cv2.FONT_HERSHEY_DUPLEX,
    'COMPLEX': cv2.FONT_HERSHEY_COMPLEX,
    'TRIPLEX': cv2.FONT_HERSHEY_TRIPLEX,
    'COMPLEX_SMALL': cv2.FONT_HERSHEY_COMPLEX_SMALL,
    'SCRIPT_SIMPLEX': cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,
    'SCRIPT_COMPLEX': cv2.FONT_HERSHEY_SCRIPT_COMPLEX,
}
font = font_map.get(FONT_FACE.upper(), cv2.FONT_HERSHEY_SIMPLEX)

# Find media files
media_files = find_media_files()
if len(media_files) < 1:
    print("Error: No media files found.")
    exit(1)

print(f"Found {len(media_files)} media files:")
for i, file in enumerate(media_files):
    print(f"  {i+1}. {os.path.basename(file)}")

# Get user inputs
title_text, custom_grid, custom_cols, custom_rows = get_user_inputs()

# Ask for custom labels
print("\nLabel Options:")
print("1. Use default labels (based on filenames)")
print("2. Set custom labels for each file")

while True:
    label_choice = input("Choose option (1 or 2): ").strip()
    if label_choice in ['1', '2']:
        break
    print("Please enter 1 or 2")

if label_choice == '2':
    custom_labels = get_custom_labels(media_files)
else:
    # Generate default labels
    custom_labels = []
    for media_file in media_files:
        basename = os.path.splitext(os.path.basename(media_file))[0]
        default_label = re.sub(r'^\s*\d+\.\s*', '', basename).replace('@', ':')
        custom_labels.append(default_label)

print(f"\nProcessing {len(media_files)} media files...")

clips = []
display_names = custom_labels
clip_types = []
image_duration = 5
has_videos = False
max_video_duration = 0

# Check for videos and determine duration
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

# Load media files
for media_file in media_files:
    ext = os.path.splitext(media_file)[1].lower()

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

# Calculate grid dimensions
num_clips = len(clips)
if custom_grid:
    grid_cols = custom_cols
    grid_rows = custom_rows
    
    # Check if grid can accommodate all clips
    total_cells = grid_cols * grid_rows
    if total_cells < num_clips:
        print(f"Warning: Grid ({grid_cols}x{grid_rows} = {total_cells} cells) is smaller than number of clips ({num_clips})")
        print(f"Only the first {total_cells} clips will be used.")
        clips = clips[:total_cells]
        display_names = display_names[:total_cells]
        clip_types = clip_types[:total_cells]
        num_clips = len(clips)
    elif total_cells > num_clips:
        print(f"Grid ({grid_cols}x{grid_rows} = {total_cells} cells) is larger than number of clips ({num_clips})")
        print("Some cells will be empty.")
else:
    # Auto-calculate grid dimensions
    if num_clips <= 3:
        grid_cols = num_clips
        grid_rows = 1
    else:
        grid_cols = math.ceil(math.sqrt(num_clips))
        grid_rows = math.ceil(num_clips / grid_cols)

print(f"Using grid layout: {grid_cols} columns x {grid_rows} rows")

# Calculate actual dimensions for each clip
clip_dimensions = []
for i, clip in enumerate(clips):
    frame = clip.get_frame(0)
    h, w = frame.shape[:2]
    clip_dimensions.append((w, h))

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
    has_any_text_in_row = False
    start_clip_idx = row_idx * grid_cols
    end_clip_idx = min(start_clip_idx + grid_cols, len(display_names))
    for i in range(start_clip_idx, end_clip_idx):
        if i < len(display_names) and display_names[i] and display_names[i].strip():
            has_any_text_in_row = True
            break 

    if not has_any_text_in_row:
        return 0 

    caption_font_scale = FILENAME_FONT_SCALE_BASE * (row_height / 800) if row_height > 0 else FILENAME_FONT_SCALE_BASE
    caption_thickness = 2 if FONT_BOLD else 1
    caption_padding = 30
    line_height = int(35 * caption_font_scale)
    max_lines = 0
    for i, image_width in enumerate(cell_widths_in_row):
        clip_idx = row_idx * grid_cols + i
        if clip_idx < len(display_names):
            display_name = display_names[clip_idx]
            wrapped_lines = wrap_text(display_name, image_width, caption_font_scale, caption_thickness)
            max_lines = max(max_lines, len(wrapped_lines))
    
    return max_lines * line_height + caption_padding * 2 if max_lines > 0 else 0

def add_text_to_frame(frame, text, position, font_scale=1, color=(255, 255, 255), thickness=2):
    cv2.putText(frame, text, position, font, font_scale, color, thickness, lineType=cv2.LINE_AA)
    return frame

def process_frame_row_layout(t):
    row_layout_info = []
    max_overall_width = 0

    for row_idx in range(grid_rows):
        if row_idx * grid_cols >= num_clips: continue
        max_h = 0
        for col_idx in range(grid_cols):
            clip_idx = row_idx * grid_cols + col_idx
            if clip_idx < num_clips:
                _, h = clip_dimensions[clip_idx]
                max_h = max(max_h, h)
        
        uniform_height = max_h if max_h > 0 else 1
        scaled_widths = []

        for col_idx in range(grid_cols):
            clip_idx = row_idx * grid_cols + col_idx
            if clip_idx < num_clips:
                w, h = clip_dimensions[clip_idx]
                new_w = int(w * (uniform_height / h)) if h > 0 else 0
                scaled_widths.append(new_w)
        
        natural_width = sum(scaled_widths)
        max_overall_width = max(max_overall_width, natural_width)
        
        row_layout_info.append({
            "row_idx": row_idx,
            "scaled_widths": scaled_widths,
            "natural_width": natural_width,
            "uniform_height": uniform_height,
        })

    all_final_rows = []
    
    for layout_info in row_layout_info:
        row_idx = layout_info["row_idx"]
        uniform_height = layout_info["uniform_height"]
        scaled_widths = layout_info["scaled_widths"]
        natural_width = layout_info["natural_width"]
        
        row_caption_height = calculate_max_caption_height_for_row(row_idx, display_names, uniform_height, scaled_widths)
        
        cells_in_row = []
        for i, image_width in enumerate(scaled_widths):
            col_idx = i
            clip_idx = row_idx * grid_cols + col_idx
            
            clip = clips[clip_idx]
            frame = clip.get_frame(min(t, clip.duration - 0.001)) if clip_types[clip_idx] == 'video' else clip.get_frame(0)
            resized_frame = cv2.resize(frame, (image_width, uniform_height), interpolation=cv2.INTER_LANCZOS4)
            
            cell = np.zeros((uniform_height + row_caption_height, image_width, 3), dtype=np.uint8)
            cell[:uniform_height, :] = resized_frame

            if row_caption_height > 0:
                display_name = display_names[clip_idx]
                caption_font_scale = FILENAME_FONT_SCALE_BASE * (uniform_height / 800)
                caption_thickness = 2 if FONT_BOLD else 1
                line_height = int(35 * caption_font_scale)
                wrapped_lines = wrap_text(display_name, image_width, caption_font_scale, caption_thickness)
                total_text_height = len(wrapped_lines) * line_height
                text_start_y = uniform_height + (row_caption_height - total_text_height) // 2
                for j, line in enumerate(wrapped_lines):
                    (line_width, _), _ = cv2.getTextSize(line, font, caption_font_scale, caption_thickness)
                    text_x = (image_width - line_width) // 2
                    text_y = text_start_y + j * line_height + int(line_height * 0.8)
                    add_text_to_frame(cell, line, (text_x, text_y), font_scale=caption_font_scale, thickness=caption_thickness)
            
            cells_in_row.append(cell)
            
        row_with_captions = np.hstack(cells_in_row)
        
        final_row_canvas = np.zeros((row_with_captions.shape[0], max_overall_width, 3), dtype=np.uint8)
        x_offset = (max_overall_width - natural_width) // 2
        final_row_canvas[:, x_offset : x_offset + natural_width] = row_with_captions
        
        all_final_rows.append(final_row_canvas)

    return np.vstack(all_final_rows) if all_final_rows else None

def process_frame_grid_layout(t):
    max_col_widths = [0] * grid_cols
    for i, (w, h) in enumerate(clip_dimensions):
        if i >= grid_cols * grid_rows:  # Handle custom grid case
            break
        col_idx = i % grid_cols
        max_col_widths[col_idx] = max(max_col_widths[col_idx], w)

    scaled_clip_dimensions = []
    for i, (w, h) in enumerate(clip_dimensions):
        if i >= grid_cols * grid_rows:  # Handle custom grid case
            break
        col_idx = i % grid_cols
        target_width = max_col_widths[col_idx]
        if w > 0:
            scale_factor = target_width / w
            scaled_h = int(h * scale_factor)
            scaled_clip_dimensions.append((target_width, scaled_h))
        else:
            scaled_clip_dimensions.append((target_width, h))

    total_grid_width = sum(max_col_widths)
    all_final_rows = []

    for row_idx in range(grid_rows):
        start_clip_idx = row_idx * grid_cols
        if start_clip_idx >= num_clips: 
            # Create empty row if we have more rows than clips
            empty_row = np.zeros((100, total_grid_width, 3), dtype=np.uint8)
            all_final_rows.append(empty_row)
            continue

        max_row_height = 0
        col_widths_in_row = []
        for col_idx in range(grid_cols):
            clip_idx = start_clip_idx + col_idx
            if clip_idx < num_clips:
                _, scaled_h = scaled_clip_dimensions[clip_idx]
                max_row_height = max(max_row_height, scaled_h)
            col_widths_in_row.append(max_col_widths[col_idx])
        
        if max_row_height == 0:
            max_row_height = 100  # Default height for empty rows
        
        row_caption_height = calculate_max_caption_height_for_row(row_idx, display_names, max_row_height, col_widths_in_row)
        row_canvas = np.zeros((max_row_height + row_caption_height, total_grid_width, 3), dtype=np.uint8)
        current_x = 0
        
        for col_idx in range(grid_cols):
            clip_idx = start_clip_idx + col_idx
            col_width = max_col_widths[col_idx]
            
            if clip_idx < num_clips:
                clip = clips[clip_idx]
                scaled_w, scaled_h = scaled_clip_dimensions[clip_idx]
                frame = clip.get_frame(min(t, clip.duration - 0.001)) if clip_types[clip_idx] == 'video' else clip.get_frame(0)
                resized_frame = cv2.resize(frame, (scaled_w, scaled_h), interpolation=cv2.INTER_LANCZOS4)
                y_offset = (max_row_height - scaled_h) // 2
                row_canvas[y_offset:y_offset + scaled_h, current_x:current_x + scaled_w] = resized_frame

                if row_caption_height > 0:
                    display_name = display_names[clip_idx]
                    caption_font_scale = FILENAME_FONT_SCALE_BASE * (max_row_height / 800) if max_row_height > 0 else FILENAME_FONT_SCALE_BASE
                    caption_thickness = 2 if FONT_BOLD else 1
                    line_height = int(35 * caption_font_scale)
                    wrapped_lines = wrap_text(display_name, scaled_w, caption_font_scale, caption_thickness)
                    total_text_height = len(wrapped_lines) * line_height
                    text_start_y_base = max_row_height + (row_caption_height - total_text_height) // 2
                    for j, line in enumerate(wrapped_lines):
                        (line_width, _), _ = cv2.getTextSize(line, font, caption_font_scale, caption_thickness)
                        text_x = current_x + (scaled_w - line_width) // 2
                        text_y = text_start_y_base + j * line_height + int(line_height * 0.8)
                        add_text_to_frame(row_canvas, line, (text_x, text_y), font_scale=caption_font_scale, thickness=caption_thickness)
            
            current_x += col_width
        all_final_rows.append(row_canvas)
    
    return np.vstack(all_final_rows) if all_final_rows else None

def process_frame(t):
    # Use row layout for 3 or fewer clips, grid layout otherwise
    if num_clips <= 3 and not custom_grid:
        grid = process_frame_row_layout(t)
    else:
        grid = process_frame_grid_layout(t)

    # Title bar logic
    if not (title_text and title_text.strip()):
        if grid is None: return np.zeros((100, 100, 3), dtype=np.uint8)
        return grid.astype(np.uint8)

    combined_width = grid.shape[1] if grid is not None else 800
    if combined_width == 0: combined_width = 800

    title_font_scale = TITLE_FONT_SCALE_BASE * (combined_width / 700)
    title_thickness = 2 if FONT_BOLD else 1
    title_padding = 40
    (text_width, text_height), _ = cv2.getTextSize(title_text, font, title_font_scale, title_thickness)

    lines = wrap_text(title_text, combined_width - 40, title_font_scale, title_thickness)
    line_spacing = int(text_height * 1.4)
    title_height = line_spacing * len(lines) + title_padding * 2
    title_bar = np.zeros((title_height, combined_width, 3), dtype=np.uint8)

    for i, line in enumerate(lines):
        (line_width, _), _ = cv2.getTextSize(line, font, title_font_scale, title_thickness)
        line_x = (combined_width - line_width) // 2
        line_y = title_padding + i * line_spacing + text_height
        add_text_to_frame(title_bar, line, (line_x, line_y), font_scale=title_font_scale, thickness=title_thickness)

    if grid is not None:
        combined = np.vstack([title_bar, grid])
    else:
        combined = title_bar
    
    return combined.astype(np.uint8)

# Generate output
print(f"\nGenerating collage with title: '{title_text}'")
print(f"Grid: {grid_cols}x{grid_rows}")
print(f"Labels: {display_names}")

if has_videos:
    output_file = "combined_video.mp4"
    max_duration = max((clip.duration for clip in clips if clip.duration is not None), default=image_duration)
    final_clip = VideoClip(make_frame=process_frame, duration=max_duration)
    final_clip.write_videofile(output_file, fps=24, codec='libx264', audio=False)
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

print("Process completed!")
