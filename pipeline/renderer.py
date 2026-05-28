# pipeline/renderer.py
import os
from PIL import Image, ImageDraw, ImageFont

def get_best_font(font_size):
    """Attempts to load a standard Windows font, falls back to default."""
    try:
        # Arial is natively available on Windows
        return ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        return ImageFont.load_default()

def wrap_text(text, font, max_width, draw):
    """Wraps text so it doesn't spill outside the speech bubble."""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        # Check the width of the line with the new word
        line_string = " ".join(current_line)
        bbox = draw.textbbox((0, 0), line_string, font=font)
        line_width = bbox[2] - bbox[0]
        
        if line_width > max_width:
            if len(current_line) == 1:
                # Word is too long by itself, force it
                lines.append(current_line.pop())
            else:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
                
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def render_image(image_path, translated_data, output_path, style="white_fill", font_family="default", fixed_font_size="20"):
    """
    Paints the translated text back onto the image using the selected style.
    Styles: 'white_fill', 'black_fill', 'transparent', 'outline'
    """
    print(f"\nStarting Render Phase (Style: {style})...")
    
    # Open image and convert to RGBA to support transparency
    img = Image.open(image_path).convert("RGBA")
    
    # Create an overlay layer for transparent styles
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    text_draw = ImageDraw.Draw(overlay) # Text drawn on overlay
    
    for item in translated_data:
        x1, y1, x2, y2 = item['coordinates']
        text = item['english_text']
        
        orig_width = x2 - x1
        orig_height = y2 - y1
        
        # --- THE BORDER PRESERVATION FIX ---
        # Shrink the box by 6% on each side to act as an inner margin
        pad_x = orig_width * 0.06
        pad_y = orig_height * 0.06
        
        ix1 = x1 + pad_x
        iy1 = y1 + pad_y
        ix2 = x2 - pad_x
        iy2 = y2 - pad_y
        
        # Update working dimensions for font scaling and wrapping
        box_width = ix2 - ix1
        box_height = iy2 - iy1
        
        # 1. DRAW THE BACKGROUND BUBBLE (using inset coordinates)
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
        
        # 2. DYNAMIC FONT SCALING
        font_size = 40
        font = get_best_font(font_size)
        
        while font_size > 10:
            lines = wrap_text(text, font, box_width * 0.85, text_draw)
            
            line_heights = [text_draw.textbbox((0, 0), line, font=font)[3] - text_draw.textbbox((0, 0), line, font=font)[1] for line in lines]
            total_height = sum(line_heights) + (len(lines) * 4) 
            
            if total_height <= box_height * 0.75:
                break 
            
            font_size -= 2
            font = get_best_font(font_size)

        # 3. DRAW THE TEXT
        current_y = iy1 + (box_height - total_height) / 2
        
        for line in lines:
            bbox = text_draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            current_x = ix1 + (box_width - line_width) / 2
            
            text_draw.text((current_x, current_y), line, font=font, fill=text_color, **outline_kwargs)
            current_y += (bbox[3] - bbox[1]) + 4 
            
    # Merge the transparency overlay with the original image
    final_img = Image.alpha_composite(img, overlay)
    
    final_img = final_img.convert("RGB") 
    final_img.save(output_path, "PNG")
    print(f"Final image saved successfully to: {output_path}")