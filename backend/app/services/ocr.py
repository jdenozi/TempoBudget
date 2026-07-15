# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""OCR service for extracting data from receipt images."""

import re
from datetime import datetime
from io import BytesIO
from typing import Optional, TypedDict

from PIL import Image

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


class ReceiptData(TypedDict):
    """Extracted data from a receipt."""
    title: Optional[str]
    amount: Optional[float]
    date: Optional[str]
    raw_text: str
    confidence: float


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

    # Convert to grayscale for better OCR
    if image.mode != 'L':
        image = image.convert('L')

    # Use French + English for better recognition
    try:
        raw_text = pytesseract.image_to_string(image, lang='fra+eng')
    except Exception:
        # Fallback to English only if French not available
        raw_text = pytesseract.image_to_string(image, lang='eng')

    amount = _extract_amount(raw_text)
    date = _extract_date(raw_text)
    title = _extract_title(raw_text)
    confidence = _calculate_confidence(amount, date, title)

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

    # Priority patterns for total amount
    total_patterns = [
        r'TOTAL\s*(?:TTC|À PAYER|A PAYER)?\s*[:\s]*(\d+[.,]\d{2})',
        r'(?:À PAYER|A PAYER)\s*[:\s]*(\d+[.,]\d{2})',
        r'MONTANT\s*(?:TOTAL|TTC)?\s*[:\s]*(\d+[.,]\d{2})',
        r'NET\s*(?:À PAYER|A PAYER)?\s*[:\s]*(\d+[.,]\d{2})',
        r'SOMME\s*(?:DUE|TOTALE)?\s*[:\s]*(\d+[.,]\d{2})',
    ]

    for pattern in total_patterns:
        for line in lines:
            match = re.search(pattern, line)
            if match:
                amount_str = match.group(1).replace(',', '.')
                try:
                    return float(amount_str)
                except ValueError:
                    continue

    # Fallback: find the largest amount on the receipt
    all_amounts = re.findall(r'(\d+[.,]\d{2})\s*(?:€|EUR)?', text_upper)
    if all_amounts:
        amounts = []
        for a in all_amounts:
            try:
                amounts.append(float(a.replace(',', '.')))
            except ValueError:
                continue
        if amounts:
            return max(amounts)

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
