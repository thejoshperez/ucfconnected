"""
Email delivery helpers for verification and calendar invites.
"""
from __future__ import annotations

import logging
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailDeliveryError(RuntimeError):
    """Raised when an outbound email cannot be delivered."""


def _smtp_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_FROM_EMAIL)


def _build_sender() -> str:
    if settings.SMTP_FROM_NAME:
        return f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    return settings.SMTP_FROM_EMAIL


def _send_email(message: EmailMessage) -> None:
    if not _smtp_configured():
        raise EmailDeliveryError(
            "SMTP is not configured. Set SMTP_HOST and SMTP_FROM_EMAIL before sending email."
        )

    try:
        if settings.SMTP_USE_SSL:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
                if settings.SMTP_USERNAME:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(message)
            return

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
            server.ehlo()
            if settings.SMTP_USE_TLS:
                server.starttls()
                server.ehlo()
            if settings.SMTP_USERNAME:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(message)
    except (smtplib.SMTPException, OSError) as exc:
        logger.error(
            "SMTP failure (host=%s port=%s tls=%s ssl=%s user=%s): %s",
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            settings.SMTP_USE_TLS,
            settings.SMTP_USE_SSL,
            settings.SMTP_USERNAME,
            exc,
        )
        raise EmailDeliveryError(f"Email delivery failed: {exc}") from exc


def send_verification_email(user_email: str, username: str, code: str) -> None:
    """Send the 6-digit account verification code."""
    message = EmailMessage()
    message["Subject"] = "Verify your KnightLife account"
    message["From"] = _build_sender()
    message["To"] = user_email

    text_body = (
        f"Hi {username},\n\n"
        "Thanks for signing up for KnightLife.\n"
        "Use this 6-digit code to verify your email address:\n\n"
        f"{code}\n\n"
        "If you did not create this account, you can ignore this email.\n"
    )
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #111827;">
        <p>Hi {username},</p>
        <p>Thanks for signing up for <strong>KnightLife</strong>.</p>
        <p>Use this 6-digit code to verify your email address:</p>
        <p style="font-size: 28px; font-weight: 700; letter-spacing: 0.2em; margin: 24px 0;">{code}</p>
        <p>If you did not create this account, you can ignore this email.</p>
      </body>
    </html>
    """
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")
    _send_email(message)


def _generate_ics(
    event_id: int,
    title: str,
    description: str | None,
    location: str | None,
    start_at: datetime | None,
    end_at: datetime | None,
) -> str:
    """Return a minimal RFC 5545 VCALENDAR string."""
    now_utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    uid = f"event-{event_id}@knightlife.ucf"

    if start_at is not None:
        tzid = str(getattr(start_at.tzinfo, "key", "America/New_York"))
        dtstart = start_at.strftime("%Y%m%dT%H%M%S")
        
        if end_at is not None:
            dtend = end_at.strftime("%Y%m%dT%H%M%S")
        else:
            dtend = (start_at + timedelta(hours=1)).strftime("%Y%m%dT%H%M%S")
            
        dtstart_line = f"DTSTART;TZID={tzid}:{dtstart}"
        dtend_line = f"DTEND;TZID={tzid}:{dtend}"
    else:
        dtstart_line = f"DTSTART:{now_utc}"
        dtend_line = f"DTEND:{now_utc}"

    desc_escaped = (description or "").replace("\n", "\\n").replace(",", "\\,")
    loc_escaped = (location or "").replace(",", "\\,")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//KnightLife//UCF Events//EN",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{now_utc}",
        dtstart_line,
        dtend_line,
        f"SUMMARY:{title or 'UCF Event'}",
        f"DESCRIPTION:{desc_escaped}",
        f"LOCATION:{loc_escaped}",
        "END:VEVENT",
        "END:VCALENDAR",
        "",
    ]
    return "\r\n".join(lines)


def send_calendar_invite(user_email: str, event, message_body: str | None = None) -> None:  # noqa: ANN001
    """
    Send an ICS calendar invite if SMTP is configured, otherwise log a mock payload.
    """
    ics = _generate_ics(
        event_id=event.id,
        title=event.title,
        description=event.description,
        location=event.location,
        start_at=event.start_at,
        end_at=event.end_at,
    )

    if not _smtp_configured():
        logger.info(
            "[MOCK EMAIL] To: %s | Subject: You're going to %r\n--- event.ics ---\n%s",
            user_email,
            event.title,
            ics,
        )
        return

    message = EmailMessage()
    message["Subject"] = f"You're going to {event.title}" if not message_body else f"Calendar Invite: {event.title}"
    message["From"] = _build_sender()
    message["To"] = user_email
    
    body = message_body if message_body else f"You RSVPed to {event.title} on KnightLife. A calendar invite is attached."
    message.set_content(body)
    message.add_attachment(
        ics.encode("utf-8"),
        maintype="text",
        subtype="calendar",
        filename="event.ics",
    )
    _send_email(message)
