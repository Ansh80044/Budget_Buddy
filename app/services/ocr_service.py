import os
import pytesseract
from PIL import Image, ImageOps
import io
import re

# Set Tesseract path if provided or search common Windows install locations
tesseract_cmd = os.environ.get('TESSERACT_CMD')
if tesseract_cmd and os.path.exists(tesseract_cmd):
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
else:
    # Check standard Windows paths
    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    for p in common_paths:
        if os.path.exists(p):
            pytesseract.pytesseract.tesseract_cmd = p
            break


def _clean_line_currency_artifacts(text: str) -> str:
    """Normalize common OCR misreadings of the Indian Rupee symbol."""
    # '%659.03' -> '₹659.03', '~659.03' -> '₹659.03', '*659.03' -> '₹659.03'
    return re.sub(r'(?:^|(?<=\s))[%~*]\s*(\d+(?:\.\d{1,2})?)', r'₹\1', text)


def _is_garbled_line(line: str) -> bool:
    """Check if an OCR line is garbled noise from a cut-off slice."""
    words = re.findall(r'[a-zA-Z]{3,}', line)
    if not words and not re.search(r'\d', line):
        return True
    if len(re.findall(r'[^\w\s.,₹#&()+\-/%:]', line)) > 2:
        return True
    return False


def extract_text_from_image(image_bytes: bytes) -> str:
    """Extract text from receipt or order image using multi-pass and adaptive segmentation."""
    try:
        import re
        image = Image.open(io.BytesIO(image_bytes))
        # Handle smartphone photo rotation from EXIF
        image = ImageOps.exif_transpose(image)
        # Preprocess: convert to grayscale for OCR
        gray = image.convert('L')
        w, h = gray.size

        extracted_lines = []
        seen = set()

        def add_line(raw: str):
            line = _clean_line_currency_artifacts(raw.strip())
            if not line or len(line) < 2 or _is_garbled_line(line):
                return
            key = line.lower()
            if key not in seen:
                seen.add(key)
                extracted_lines.append(line)

        # Pass 1: Standard uniform block (PSM 6) on full image - highest structural quality
        text_psm6 = pytesseract.image_to_string(gray, config='--psm 6').strip()
        for l in text_psm6.splitlines():
            add_line(l)

        # Pass 2: Sparse text (PSM 11) - catches standalone prices, badges, and button labels
        text_psm11 = pytesseract.image_to_string(gray, config='--psm 11').strip()
        for l in text_psm11.splitlines():
            # If line is like '7659.03', check if it's an OCR artifact for ₹659.03
            m7 = re.match(r'^7(\d{2,4}\.\d{2})$', l.strip())
            if m7:
                add_line(f"₹{m7.group(1)}")
            else:
                add_line(l)

        # Pass 3: Overlapping horizontal band scanning
        # Receipts often place total amounts between divider lines next to buttons (e.g. '₹659.03 [Reorder]').
        # Standard whole-page segmentation often drops lines bounded by dividers or dark buttons.
        slice_height = int(h * 0.40)
        step = int(h * 0.25)
        for y_top in range(0, max(1, h - 60), step):
            y_bottom = min(y_top + slice_height, h)
            band = gray.crop((0, y_top, w, y_bottom))

            # Left 65% of band (amounts are typically on the left, avoids right-side CTA button noise)
            left_band = band.crop((0, 0, int(w * 0.65), band.height))
            left_txt = pytesseract.image_to_string(left_band, config='--psm 6').strip()
            for l in left_txt.splitlines():
                if re.search(r'\d', l):
                    add_line(l)

        return "\n".join(extracted_lines).strip()
    except Exception as e:
        print(f"OCR error: {e}")
        return ""


def extract_text_from_file(file_path: str) -> str:
    """Extract text from a saved image file using multi-pass OCR."""
    try:
        with open(file_path, "rb") as f:
            return extract_text_from_image(f.read())
    except Exception as e:
        print(f"OCR file error: {e}")
        return ""
