# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""OCR service for extracting data from receipt images."""

import re
from datetime import datetime
from io import BytesIO
from typing import Optional, TypedDict

from PIL import Image, ImageEnhance, ImageFilter

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# Tesseract config: PSM 6 = uniform block of text, OEM 3 = LSTM
TESSERACT_CONFIG = '--psm 6 --oem 3'


class ReceiptData(TypedDict):
    """Extracted data from a receipt."""
    title: Optional[str]
    amount: Optional[float]
    date: Optional[str]
    raw_text: str
    confidence: float


def _preprocess_image(image: Image.Image, binarize: bool = True) -> Image.Image:
    """
    Preprocess image for better OCR accuracy.

    Steps:
    1. Convert to grayscale
    2. Resize if too small (for better OCR)
    3. Increase contrast
    4. Sharpen
    5. Binarize (optional)
    """
    # Convert to grayscale
    if image.mode != 'L':
        image = image.convert('L')

    # Resize if too small (aim for ~300 DPI equivalent)
    min_width = 800
    if image.width < min_width:
        ratio = min_width / image.width
        new_size = (int(image.width * ratio), int(image.height * ratio))
        image = image.resize(new_size, Image.LANCZOS)

    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.8)

    # Sharpen
    image = image.filter(ImageFilter.SHARPEN)

    # Binarize (convert to pure black/white)
    if binarize:
        threshold = 140
        image = image.point(lambda x: 255 if x > threshold else 0, '1')

    return image


def _run_ocr(image: Image.Image) -> str:
    """Run Tesseract OCR on image with optimal config."""
    try:
        return pytesseract.image_to_string(image, lang='fra+eng', config=TESSERACT_CONFIG)
    except Exception:
        # Fallback to English only if French not available
        return pytesseract.image_to_string(image, lang='eng', config=TESSERACT_CONFIG)


def extract_from_receipt(image_bytes: bytes) -> ReceiptData:
    """
    Extract transaction data from a receipt image using OCR.

    Args:
        image_bytes: Raw bytes of the receipt image

    Returns:
        Extracted data including title, amount, date, raw OCR text, and confidence score
    """
    if not TESSERACT_AVAILABLE:
        raise RuntimeError("pytesseract is not installed. Please install it with: pip install pytesseract")

    image = Image.open(BytesIO(image_bytes))

    # Try with full preprocessing (binarization)
    processed = _preprocess_image(image.copy(), binarize=True)
    raw_text = _run_ocr(processed)

    amount = _extract_amount(raw_text)
    date = _extract_date(raw_text)
    title = _extract_title(raw_text)
    confidence = _calculate_confidence(amount, date, title)

    # If confidence is low, try without binarization (for colored receipts)
    if confidence < 0.5:
        processed_soft = _preprocess_image(image.copy(), binarize=False)
        raw_text_soft = _run_ocr(processed_soft)

        amount_soft = _extract_amount(raw_text_soft)
        date_soft = _extract_date(raw_text_soft)
        title_soft = _extract_title(raw_text_soft)
        confidence_soft = _calculate_confidence(amount_soft, date_soft, title_soft)

        if confidence_soft > confidence:
            amount, date, title, raw_text, confidence = (
                amount_soft, date_soft, title_soft, raw_text_soft, confidence_soft
            )

    return ReceiptData(
        title=title,
        amount=amount,
        date=date,
        raw_text=raw_text,
        confidence=confidence,
    )


def _extract_amount(text: str) -> Optional[float]:
    """
    Extract the total amount from receipt text.

    Looks for patterns like:
    - TOTAL: 12,50 €
    - TOTAL TTC 12.50
    - MONTANT: 12,50
    - A PAYER: 12.50 EUR
    """
    text_upper = text.upper()
    lines = text_upper.split('\n')

    # Keywords indicating total amount
    total_keywords = ['A PAYER', 'À PAYER', 'TOTAL', 'MONTANT', 'CB EMV', 'SOMME']

    # Method 1: Find line with keyword and extract amount from it or next line
    for i, line in enumerate(lines):
        line_clean = line.strip()
        for keyword in total_keywords:
            if keyword in line_clean:
                # Search in current line and next line combined
                search_text = line_clean
                if i + 1 < len(lines):
                    search_text += ' ' + lines[i + 1].strip()

                # Strict pattern: 1-3 digits, separator, 2 digits
                match = re.search(r'(\d{1,3})[.,](\d{2})(?:\s*€|\s*EUR|\s|$)', search_text)
                if match:
                    amount = float(f"{match.group(1)}.{match.group(2)}")
                    if 0.01 <= amount <= 999.99:
                        return amount

    # Method 2: Pattern matching with keyword prefix (stricter)
    strict_patterns = [
        r'(?:À PAYER|A PAYER)\s*[:\s]*(\d{1,3})[.,](\d{2})',
        r'TOTAL\s*(?:TTC)?\s*[:\s]*(\d{1,3})[.,](\d{2})',
        r'CB\s*EMV\s*[:\s]*(\d{1,3})[.,](\d{2})',
        r'MONTANT\s*[:\s]*(\d{1,3})[.,](\d{2})',
    ]

    for pattern in strict_patterns:
        for line in lines:
            match = re.search(pattern, line)
            if match:
                amount = float(f"{match.group(1)}.{match.group(2)}")
                if 0.01 <= amount <= 999.99:
                    return amount

    # Method 3: Look for amounts with € symbol (likely the total)
    euro_amounts = re.findall(r'(\d{1,3})[.,](\d{2})\s*€', text_upper)
    if euro_amounts:
        # Take the last one (usually the total at the bottom)
        last = euro_amounts[-1]
        return float(f"{last[0]}.{last[1]}")

    # Fallback: find the LAST reasonable amount
    all_amounts = re.findall(r'(\d{1,3})[.,](\d{2})', text_upper)
    if all_amounts:
        amounts = []
        for parts in all_amounts:
            val = float(f"{parts[0]}.{parts[1]}")
            if 0.01 <= val <= 999.99:
                amounts.append(val)
        if amounts:
            return amounts[-1]

    return None


def _extract_date(text: str) -> Optional[str]:
    """
    Extract date from receipt text.

    Recognizes formats:
    - DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
    - YYYY-MM-DD (ISO)
    - DD MMM YYYY (e.g., 15 Jan 2024)
    """
    # French month names
    month_map = {
        'JANVIER': '01', 'JAN': '01', 'JANV': '01',
        'FÉVRIER': '02', 'FEVRIER': '02', 'FEV': '02', 'FEVR': '02',
        'MARS': '03', 'MAR': '03',
        'AVRIL': '04', 'AVR': '04',
        'MAI': '05',
        'JUIN': '06', 'JUN': '06',
        'JUILLET': '07', 'JUIL': '07', 'JUL': '07',
        'AOÛT': '08', 'AOUT': '08', 'AOU': '08',
        'SEPTEMBRE': '09', 'SEPT': '09', 'SEP': '09',
        'OCTOBRE': '10', 'OCT': '10',
        'NOVEMBRE': '11', 'NOV': '11',
        'DÉCEMBRE': '12', 'DECEMBRE': '12', 'DEC': '12',
    }

    text_upper = text.upper()

    # Pattern: DD/MM/YYYY or DD-MM-YYYY or DD.MM.YYYY
    match = re.search(r'(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})', text)
    if match:
        day, month, year = match.groups()
        try:
            parsed = datetime(int(year), int(month), int(day))
            return parsed.strftime('%Y-%m-%d')
        except ValueError:
            pass

    # Pattern: YYYY-MM-DD (ISO format)
    match = re.search(r'(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})', text)
    if match:
        year, month, day = match.groups()
        try:
            parsed = datetime(int(year), int(month), int(day))
            return parsed.strftime('%Y-%m-%d')
        except ValueError:
            pass

    # Pattern: DD MONTH YYYY (French months)
    for month_name, month_num in month_map.items():
        pattern = rf'(\d{{1,2}})\s*{month_name}\s*(\d{{4}})'
        match = re.search(pattern, text_upper)
        if match:
            day, year = match.groups()
            try:
                parsed = datetime(int(year), int(month_num), int(day))
                return parsed.strftime('%Y-%m-%d')
            except ValueError:
                continue

    return None


def _extract_title(text: str) -> Optional[str]:
    """
    Extract a likely store/merchant name from the receipt.

    Typically the merchant name is on the first few non-empty lines.
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    # Skip very short lines (likely noise) and look for the first meaningful line
    for line in lines[:5]:
        # Skip lines that look like dates, amounts, or common receipt noise
        if re.match(r'^\d+[/\-.]', line):
            continue
        if re.match(r'^\d+[.,]\d{2}\s*€?$', line):
            continue
        if len(line) < 3:
            continue
        if line.upper() in ('TICKET', 'RECU', 'RECEIPT', 'FACTURE'):
            continue

        # Return the first meaningful line as the title
        return line[:100]  # Limit length

    return None


def _calculate_confidence(amount: Optional[float], date: Optional[str], title: Optional[str]) -> float:
    """
    Calculate a confidence score (0-1) based on extracted data quality.
    """
    score = 0.0

    if amount is not None:
        score += 0.5

    if date is not None:
        score += 0.3

    if title is not None and len(title) > 3:
        score += 0.2

    return score
