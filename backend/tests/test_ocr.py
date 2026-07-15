# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Unit tests for OCR service."""

import pytest
from app.services.ocr import (
    _extract_amount,
    _extract_date,
    _extract_title,
    _calculate_confidence,
)


class TestExtractAmount:
    """Tests for amount extraction from receipt text."""

    def test_total_with_euro_symbol(self):
        text = "TOTAL: 12,50 €"
        assert _extract_amount(text) == 12.50

    def test_total_ttc(self):
        text = "TOTAL TTC 45.99"
        assert _extract_amount(text) == 45.99

    def test_a_payer(self):
        text = "A PAYER: 123,45"
        assert _extract_amount(text) == 123.45

    def test_montant(self):
        text = "MONTANT TOTAL: 99,99"
        assert _extract_amount(text) == 99.99

    def test_net_a_payer(self):
        text = "NET A PAYER 50,00 EUR"
        assert _extract_amount(text) == 50.00

    def test_fallback_last_amount(self):
        text = """
        Article 1: 5,00 €
        Article 2: 10,00 €
        Article 3: 25,00 €
        """
        # Now returns last amount (typically total at bottom), not largest
        assert _extract_amount(text) == 25.00

    def test_ocr_space_in_number(self):
        text = "TOTAL: 23, 01 €"
        assert _extract_amount(text) == 23.01

    def test_cb_emv_pattern(self):
        text = "CB EMV 45,99"
        assert _extract_amount(text) == 45.99

    def test_a_payer_strict(self):
        # Should find 23.01 not 223.01
        text = """
        ARTICLE 223
        A PAYER 23,01 EUR
        """
        assert _extract_amount(text) == 23.01

    def test_a_payer_with_noise(self):
        text = "A PAYER : 15,50 €"
        assert _extract_amount(text) == 15.50

    def test_no_amount_found(self):
        text = "No amounts here"
        assert _extract_amount(text) is None

    def test_comma_decimal_separator(self):
        text = "TOTAL: 1234,56"
        assert _extract_amount(text) == 1234.56

    def test_dot_decimal_separator(self):
        text = "TOTAL: 1234.56"
        assert _extract_amount(text) == 1234.56


class TestExtractDate:
    """Tests for date extraction from receipt text."""

    def test_french_format_slash(self):
        text = "Date: 15/07/2024"
        assert _extract_date(text) == "2024-07-15"

    def test_french_format_dash(self):
        text = "Date: 15-07-2024"
        assert _extract_date(text) == "2024-07-15"

    def test_french_format_dot(self):
        text = "Date: 15.07.2024"
        assert _extract_date(text) == "2024-07-15"

    def test_iso_format(self):
        text = "Date: 2024-07-15"
        assert _extract_date(text) == "2024-07-15"

    def test_french_month_name(self):
        text = "15 JUILLET 2024"
        assert _extract_date(text) == "2024-07-15"

    def test_french_month_abbreviation(self):
        text = "15 JUIL 2024"
        assert _extract_date(text) == "2024-07-15"

    def test_january(self):
        text = "01 JANVIER 2024"
        assert _extract_date(text) == "2024-01-01"

    def test_december(self):
        text = "25 DEC 2024"
        assert _extract_date(text) == "2024-12-25"

    def test_no_date_found(self):
        text = "No date here"
        assert _extract_date(text) is None

    def test_invalid_date_ignored(self):
        text = "Date: 32/13/2024"
        # Should return None for invalid date
        assert _extract_date(text) is None


class TestExtractTitle:
    """Tests for title extraction from receipt text."""

    def test_first_meaningful_line(self):
        text = """
        CARREFOUR MARKET
        123 Rue Example
        15/07/2024
        """
        assert _extract_title(text) == "CARREFOUR MARKET"

    def test_skip_date_line(self):
        text = """15/07/2024
        SUPERMARCHE
        """
        assert _extract_title(text) == "SUPERMARCHE"

    def test_skip_amount_line(self):
        text = """12,50 €
        BOULANGERIE
        """
        assert _extract_title(text) == "BOULANGERIE"

    def test_skip_ticket_keyword(self):
        text = """TICKET
        MON MAGASIN
        """
        assert _extract_title(text) == "MON MAGASIN"

    def test_truncate_long_title(self):
        text = "A" * 150
        result = _extract_title(text)
        assert len(result) <= 100

    def test_empty_text(self):
        text = ""
        assert _extract_title(text) is None

    def test_only_noise(self):
        text = """
        12,50 €
        15/07/2024
        """
        assert _extract_title(text) is None


class TestCalculateConfidence:
    """Tests for confidence score calculation."""

    def test_all_fields_present(self):
        # amount=0.4 + date=0.2 + title=0.1 + ocr_confidence*0.3 = 0.7 + 0.3 = 1.0
        score = _calculate_confidence(amount=12.50, date="2024-07-15", title="Store", ocr_confidence=1.0)
        assert score == 1.0

    def test_all_fields_no_ocr_confidence(self):
        # amount=0.4 + date=0.2 + title=0.1 = 0.7
        score = _calculate_confidence(amount=12.50, date="2024-07-15", title="Store")
        assert score == 0.7

    def test_only_amount(self):
        score = _calculate_confidence(amount=12.50, date=None, title=None)
        assert score == 0.4

    def test_only_date(self):
        score = _calculate_confidence(amount=None, date="2024-07-15", title=None)
        assert score == 0.2

    def test_only_title(self):
        score = _calculate_confidence(amount=None, date=None, title="Store Name")
        assert score == 0.1

    def test_amount_and_date(self):
        score = _calculate_confidence(amount=12.50, date="2024-07-15", title=None)
        assert score == 0.6

    def test_nothing_extracted(self):
        score = _calculate_confidence(amount=None, date=None, title=None)
        assert score == 0.0

    def test_short_title_ignored(self):
        score = _calculate_confidence(amount=None, date=None, title="AB")
        assert score == 0.0

    def test_with_ocr_confidence(self):
        # OCR confidence adds up to 0.3 to the score
        score = _calculate_confidence(amount=12.50, date=None, title=None, ocr_confidence=0.9)
        assert score == 0.4 + 0.9 * 0.3  # 0.67
