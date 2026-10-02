import os
import pytesseract
from PIL import Image, ImageOps
import io

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


def extract_text_from_image(image_bytes: bytes) -> str:
    """Extract text from receipt image using Tesseract OCR with adaptive PSM."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        # Handle smartphone photo rotation from EXIF
        image = ImageOps.exif_transpose(image)
        # Preprocess: convert to grayscale for OCR
        gray = image.convert('L')

        # Try PSM 6 (uniform block), if output is minimal try PSM 4 / 3 (columns / automatic)
        text = pytesseract.image_to_string(gray, config='--psm 6').strip()
        if len(text) < 30:
            alt_text = pytesseract.image_to_string(gray, config='--psm 3').strip()
            if len(alt_text) > len(text):
                text = alt_text
        return text.strip()
    except Exception as e:
        print(f"OCR error: {e}")
        return ""


def extract_text_from_file(file_path: str) -> str:
    """Extract text from a saved image file."""
    try:
        image = Image.open(file_path)
        image = image.convert('L')
        text = pytesseract.image_to_string(image, config='--psm 6')
        return text.strip()
    except Exception as e:
        print(f"OCR file error: {e}")
        return ""
