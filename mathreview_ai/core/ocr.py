
"""Local OCR for MathReview AI using EasyOCR."""

from functools import lru_cache
from io import BytesIO

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


@lru_cache(maxsize=1)
def get_reader():
    import easyocr
    return easyocr.Reader(["en"], gpu=False, verbose=False)


def read_handwritten_solution(image_bytes, mime_type="image/png"):
    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")

        # Image preprocessing
        image = ImageOps.grayscale(image)
        image = ImageOps.autocontrast(image)
        image = ImageEnhance.Contrast(image).enhance(1.5)
        image = image.filter(ImageFilter.SHARPEN)

        # Local OCR - no OpenAI API required
        reader = get_reader()
        results = reader.readtext(
            image,
            detail=1,
            paragraph=False
        )

        if not results:
            return None, "No readable text detected. Upload a clearer image."

        lines = [
            str(item[1]).strip()
            for item in results
            if len(item) > 1 and str(item[1]).strip()
        ]

        extracted_text = "\n".join(lines)

        if not extracted_text:
            return None, "No text extracted. Please try another image."

        return extracted_text, (
            "OCR completed successfully using local EasyOCR. "
            "Please verify mathematical symbols and numbers."
        )

    except ImportError:
        return None, (
            "EasyOCR is missing. Run: "
            "python -m pip install easyocr"
        )

    except Exception as error:
        return None, f"OCR failed: {error}"
