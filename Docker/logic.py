import os, base64, requests
from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageEnhance, ImageChops
from io import BytesIO

FONT_DIR = '/app/fonts'

def apply_transforms(img, apply_default_size=True, invert=False, make_white=False, contrast=1.0, zoom=1.0, monochrome=False, tint=None):
    img = img.convert("RGBA")
    bbox = img.getbbox()
    if bbox: img = img.crop(bbox)
    if make_white:
        alpha = img.getchannel('A')
        img = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img.putalpha(alpha)
    if monochrome: img = img.convert("L").convert("RGBA")
    if invert:
        r, g, b, a = img.split()
        img = Image.merge('RGBA', (*ImageOps.invert(Image.merge('RGB', (r, g, b))).split(), a))
    if float(contrast) != 1.0:
        img = ImageEnhance.Contrast(img).enhance(float(contrast))
    
    canvas_side = 1000  

    if apply_default_size:
        # Fit into 80% of canvas, ignore zoom value from slider
        target_size = int(canvas_side * 0.8)
        ratio = min(target_size / img.width, target_size / img.height) if img.width > 0 and img.height > 0 else 0
        new_size = (int(img.width * ratio), int(img.height * ratio))
    else:
        # Apply zoom first, then fit to canvas if needed
        zoomed_size = (int(img.width * float(zoom)), int(img.height * float(zoom)))
        
        # Now, ensure the zoomed image still fits within the canvas, downscaling if necessary
        if zoomed_size[0] > canvas_side or zoomed_size[1] > canvas_side:
            ratio = min(canvas_side / zoomed_size[0], canvas_side / zoomed_size[1])
            new_size = (int(zoomed_size[0] * ratio), int(zoomed_size[1] * ratio))
        else:
            new_size = zoomed_size

    if new_size[0] > 0 and new_size[1] > 0:
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    final = Image.new('RGB', (canvas_side, canvas_side), (0, 0, 0))
    final.paste(img, ((canvas_side - img.width) // 2, (canvas_side - img.height) // 2), img)

    # Apply server-side tinting if requested. `tint` expected as a hex string like '#RRGGBB'.
    if tint:
        try:
            h = str(tint).lstrip('#')
            if len(h) == 3:
                h = ''.join([c*2 for c in h])
            if len(h) == 6:
                r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
                tint_img = Image.new('RGB', final.size, (r, g, b))
                # Multiply and blend to approximate the frontend multiply overlay
                multiplied = ImageChops.multiply(final, tint_img)
                final = Image.blend(final, multiplied, alpha=0.6)
        except Exception:
            # If parsing fails, silently ignore tint
            pass

    return final

def generate_text_logo(text, font_path, rows=1, color="white", case="none"):
    if case == "upper": text = text.upper()
    elif case == "lower": text = text.lower()
    words = text.split()
    n = len(words)
    wpl = (n + int(rows) - 1) // int(rows)
    lines = [" ".join(words[i : i + wpl]) for i in range(0, n, wpl)]
    
    try: font = ImageFont.truetype(font_path, 400)
    except: font = ImageFont.load_default()
    
    line_imgs = []
    d = ImageDraw.Draw(Image.new('RGBA', (1,1)))
    for line in lines:
        b = d.textbbox((0, 0), line, font=font)
        li = Image.new('RGBA', (int(b[2]-b[0]), int(b[3]-b[1])), (0,0,0,0))
        ImageDraw.Draw(li).text((-b[0], -b[1]), line, font=font, fill=color)
        line_imgs.append(li)

    max_w = max(l.width for l in line_imgs)
    total_h = sum(l.height for l in line_imgs) + (50 * (len(lines)-1))
    combined = Image.new('RGBA', (max_w, total_h), (0,0,0,0))
    curr_y = 0
    for l in line_imgs:
        combined.paste(l, ((max_w - l.width)//2, curr_y), l)
        curr_y += l.height + 50
    return apply_transforms(combined)