# Copyright (c) 2024 Tempo Budget
# SPDX-License-Identifier: MIT
"""Notification service for n8n webhook integration."""

import hashlib
import hmac
import os
from datetime import datetime, timezone
from typing import Literal

import httpx

N8N_WEBHOOK_PAYMENT_CONFIRMATION = os.getenv("N8N_WEBHOOK_PAYMENT_CONFIRMATION", "")
N8N_WEBHOOK_PAYMENT_REMINDER = os.getenv("N8N_WEBHOOK_PAYMENT_REMINDER", "")
N8N_WEBHOOK_INVOICE = os.getenv("N8N_WEBHOOK_INVOICE", "")
N8N_WEBHOOK_PRO_INVOICE = os.getenv("N8N_WEBHOOK_PRO_INVOICE", "")
N8N_WEBHOOK_SECRET = os.getenv("N8N_WEBHOOK_SECRET", "")


def _sign_payload(payload: dict) -> str:
    """Sign payload with HMAC-SHA256."""
    if not N8N_WEBHOOK_SECRET:
        return ""
    import json
    body = json.dumps(payload, sort_keys=True)
    return hmac.new(
        N8N_WEBHOOK_SECRET.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()


async def _send_webhook(url: str, payload: dict) -> bool:
    """Send a webhook to n8n."""
    if not url:
        return False

    signature = _sign_payload(payload)
    headers = {"Content-Type": "application/json"}
    if signature:
        headers["X-Webhook-Signature"] = signature

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            return response.status_code in (200, 201, 202, 204)
    except Exception as e:
        print(f"Failed to send webhook to {url}: {e}")
        return False


async def send_payment_confirmation(
    user_email: str,
    user_name: str,
    plan_type: Literal["monthly", "annual"],
    amount: float,
    currency: str = "EUR",
    subscription_id: str | None = None,
    period_end: str | None = None,
) -> bool:
    """Send payment confirmation email via n8n.

    Triggered after successful checkout or invoice payment.
    """
    payload = {
        "event": "payment_confirmation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user": {
            "email": user_email,
            "name": user_name,
        },
        "subscription": {
            "plan_type": plan_type,
            "amount": amount,
            "currency": currency,
            "subscription_id": subscription_id,
            "period_end": period_end,
        },
    }
    return await _send_webhook(N8N_WEBHOOK_PAYMENT_CONFIRMATION, payload)


async def send_payment_reminder(
    user_email: str,
    user_name: str,
    plan_type: Literal["monthly", "annual"],
    amount_due: float,
    currency: str = "EUR",
    due_date: str | None = None,
    days_until_due: int = 0,
    reminder_type: Literal["upcoming_renewal", "payment_failed", "expiring_soon"] = "upcoming_renewal",
) -> bool:
    """Send payment reminder email via n8n.

    Types:
    - upcoming_renewal: Sent X days before automatic renewal
    - payment_failed: Sent after a failed payment attempt
    - expiring_soon: Sent when subscription is about to expire (cancel_at_period_end=true)
    """
    payload = {
        "event": "payment_reminder",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "reminder_type": reminder_type,
        "user": {
            "email": user_email,
            "name": user_name,
        },
        "subscription": {
            "plan_type": plan_type,
            "amount_due": amount_due,
            "currency": currency,
            "due_date": due_date,
            "days_until_due": days_until_due,
        },
    }
    return await _send_webhook(N8N_WEBHOOK_PAYMENT_REMINDER, payload)


async def send_invoice(
    user_email: str,
    user_name: str,
    plan_type: Literal["monthly", "annual"],
    invoice_number: str,
    amount: float,
    currency: str = "EUR",
    invoice_date: str | None = None,
    period_start: str | None = None,
    period_end: str | None = None,
    invoice_pdf_url: str | None = None,
    stripe_invoice_id: str | None = None,
) -> bool:
    """Send invoice email via n8n.

    Triggered after successful payment. Includes link to Stripe-hosted invoice PDF.
    """
    payload = {
        "event": "invoice",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user": {
            "email": user_email,
            "name": user_name,
        },
        "invoice": {
            "number": invoice_number,
            "amount": amount,
            "currency": currency,
            "date": invoice_date or datetime.now(timezone.utc).date().isoformat(),
            "period_start": period_start,
            "period_end": period_end,
            "pdf_url": invoice_pdf_url,
            "stripe_invoice_id": stripe_invoice_id,
        },
        "subscription": {
            "plan_type": plan_type,
        },
    }
    return await _send_webhook(N8N_WEBHOOK_INVOICE, payload)


async def send_pro_invoice_to_client(
    seller_email: str,
    seller_name: str,
    seller_company: str | None,
    seller_phone: str | None,
    client_email: str,
    client_name: str,
    invoice_number: str,
    invoice_date: str,
    due_date: str,
    total: float,
    currency: str = "EUR",
    pdf_base64: str | None = None,
    items_summary: list[dict] | None = None,
    notes: str | None = None,
    bank_iban: str | None = None,
    bank_bic: str | None = None,
) -> bool:
    """Send Pro invoice to client via n8n.

    This sends the invoice PDF and details to the Pro user's client.
    The n8n workflow should:
    1. Receive the payload
    2. Decode the PDF from base64
    3. Send email to client_email with PDF attached
    """
    payload = {
        "event": "pro_invoice",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seller": {
            "email": seller_email,
            "name": seller_name,
            "company": seller_company,
            "phone": seller_phone,
        },
        "client": {
            "email": client_email,
            "name": client_name,
        },
        "invoice": {
            "number": invoice_number,
            "date": invoice_date,
            "due_date": due_date,
            "total": total,
            "currency": currency,
            "items": items_summary or [],
            "notes": notes,
        },
        "payment": {
            "bank_iban": bank_iban,
            "bank_bic": bank_bic,
        },
        "pdf_base64": pdf_base64,
    }
    return await _send_webhook(N8N_WEBHOOK_PRO_INVOICE, payload)
