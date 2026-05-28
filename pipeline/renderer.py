# pipeline/renderer.py
import os
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS_DIR = os.path.join(BASE_DIR, 'fonts')

def get_best_font(font_size, font_family="default"):
    """Loads specific .ttf/.otf files based on UI selection, scaling appropriately."""
    try:
        size = int(font_size)
    except (ValueError, TypeError):
        size = 40 # Safe fallback
        
    font_map = {
        "animeace": "animeace.otf",
        "mangatemple": "mangatemple.ttf",
        "komika": "komika.ttf",
        "arial": "arial.ttf",
        "times": "times.ttf"
    }
    
    if font_family == "default":
        font_filename = "arial.ttf"
    else:
        font_filename = font_map.get(font_family, "arial.ttf")
    
    font_path = os.path.join(FONTS_DIR, font_filename)
    try:
        return ImageFont.truetype(font_path, size)
    except IOError:
        try:
            return ImageFont.truetype(font_filename, size)
        except IOError:
            print(f"[Warning] {font_filename} not found locally or in OS. Falling back to unscalable Pillow bitmap.")
            return ImageFont.load_default()

def wrap_text(text, font, max_width, draw):
    """Wraps text so it doesn't spill outside the speech bubble."""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        line_string = " ".join(current_line)
        bbox = draw.textbbox((0, 0), line_string, font=font)
        line_width = bbox[2] - bbox[0]
        
        if line_width > max_width:
            if len(current_line) == 1:
                lines.append(current_line.pop())
            else:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
                
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def render_image(image_path, translated_data, output_path, style="white_fill", font_family="default", fixed_font_size="default"):
    """
    Paints the translated text back onto the image using the selected style and typography settings.
    Implements Dynamic Auto-Scaling if 'auto' is passed.
    """
    print(f"\nStarting Render Phase (Style: {style}, Font: {font_family}, Size: {fixed_font_size})...")
    
    img = Image.open(image_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    text_draw = ImageDraw.Draw(overlay) 
    
    for item in translated_data:
        x1, y1, x2, y2 = item['coordinates']
        text = item['english_text']
        
        orig_width = x2 - x1
        orig_height = y2 - y1
        
        # Shrink the box by 6% on each side to act as an inner margin
        pad_x = orig_width * 0.06
        pad_y = orig_height * 0.06
        ix1, iy1 = x1 + pad_x, y1 + pad_y
        ix2, iy2 = x2 - pad_x, y2 - pad_y
        
        box_width = ix2 - ix1
        box_height = iy2 - iy1
        target_width = box_width * 0.85
        target_height = box_height * 0.85
        
        # Draw Background Bubble
        if style == "white_fill":
            draw.ellipse([ix1, iy1, ix2, iy2], fill=(255, 255, 255, 255))
            text_color = (0, 0, 0, 255) 
            outline_kwargs = {}
        elif style == "black_fill":
            draw.ellipse([ix1, iy1, ix2, iy2], fill=(0, 0, 0, 255))
            text_color = (255, 255, 255, 255) 
            outline_kwargs = {}
        elif style == "transparent":
            draw.ellipse([ix1, iy1, ix2, iy2], fill=(255, 255, 255, 180)) 
            text_color = (0, 0, 0, 255)
            outline_kwargs = {}
        elif style == "outline":
            text_color = (255, 255, 255, 255) 
            outline_kwargs = {"stroke_width": 3, "stroke_fill": (0, 0, 0, 255)}

        # Optimization Route: Auto-Scale or Fixed
        if fixed_font_size == "auto":
            chosen_font = None
            chosen_lines = []
            
            # Descending validation loop (40px down to 15px)
            for test_size in range(40, 14, -1):
                test_font = get_best_font(test_size, font_family)
                test_lines = wrap_text(text, test_font, target_width, text_draw)
                
                line_heights = [text_draw.textbbox((0, 0), line, font=test_font)[3] - text_draw.textbbox((0, 0), line, font=test_font)[1] for line in test_lines]
                total_height = sum(line_heights) + (len(test_lines) * 4) 
                
                if total_height <= target_height:
                    chosen_font = test_font
                    chosen_lines = test_lines
                    break
            
            # Absolute floor catch (Force 15px even if it overflows)
            if chosen_font is None:
                chosen_font = get_best_font(15, font_family)
                chosen_lines = wrap_text(text, chosen_font, target_width, text_draw)
                
            font = chosen_font
            lines = chosen_lines
        else:
            try:
                base_font_size = int(fixed_font_size)
            except ValueError:
                base_font_size = 40
                
            font = get_best_font(base_font_size, font_family)
            lines = wrap_text(text, font, target_width, text_draw)

        # Execute final text painting
        line_heights = [text_draw.textbbox((0, 0), line, font=font)[3] - text_draw.textbbox((0, 0), line, font=font)[1] for line in lines]
        total_height = sum(line_heights) + (len(lines) * 4) 
        
        current_y = iy1 + (box_height - total_height) / 2
        
        for line in lines:
            bbox = text_draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            current_x = ix1 + (box_width - line_width) / 2
            
            text_draw.text((current_x, current_y), line, font=font, fill=text_color, **outline_kwargs)
            current_y += (bbox[3] - bbox[1]) + 4 
            
    final_img = Image.alpha_composite(img, overlay).convert("RGB") 
    final_img.save(output_path, "PNG")