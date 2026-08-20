import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

logger = logging.getLogger("email_service")


def send_verification_otp_email(to_email: str, otp_code: str) -> bool:
    """
    Sends a 6-digit email verification code (OTP) directly to the target user inbox using SMTP.
    Uses smtplib and MIME for robust production email delivery.
    """
    subject = f"Your Decisio Verification Code: {otp_code}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Decisio Email Verification</title>
      <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8fafc; color: #1e293b; margin: 0; padding: 20px; }}
        .email-container {{ max-width: 520px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 32px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
        .header {{ text-align: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 20px; margin-bottom: 24px; }}
        .brand {{ font-size: 24px; font-weight: 800; color: #0f172a; letter-spacing: -0.5px; }}
        .code-box {{ background-color: #f1f5f9; border: 1px dashed #cbd5e1; border-radius: 10px; padding: 20px; text-align: center; margin: 28px 0; }}
        .otp-number {{ font-size: 36px; font-weight: 800; color: #1e40af; letter-spacing: 8px; font-family: monospace; }}
        .footer {{ font-size: 12px; color: #64748b; text-align: center; margin-top: 32px; border-top: 1px solid #f1f5f9; padding-top: 16px; }}
      </style>
    </head>
    <body>
      <div class="email-container">
        <div class="header">
          <div class="brand">Decisio</div>
        </div>
        <h2 style="font-size: 20px; margin-top: 0;">Verify your email address</h2>
        <p style="color: #475569; font-size: 14px; line-height: 1.6;">
          Thank you for creating an account with <strong>Decisio</strong>. Please use the 6-digit verification code below to complete your registration:
        </p>
        <div class="code-box">
          <div class="otp-number">{otp_code}</div>
        </div>
        <p style="color: #64748b; font-size: 13px;">
          This code is valid for <strong>10 minutes</strong>. If you did not request this email, you can safely ignore it.
        </p>
        <div class="footer">
          &copy; 2026 Decisio Platform. All rights reserved.
        </div>
      </div>
    </body>
    </html>
    """

    text_content = f"Your Decisio Verification Code is: {otp_code}\nValid for 10 minutes."

    # If no SMTP credentials configured, log and return fallback
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(
            f"SMTP_USER/SMTP_PASSWORD not configured in backend/.env. "
            f"Logged OTP for [{to_email}]: [{otp_code}]."
        )
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
        msg["To"] = to_email

        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        if settings.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
            if settings.SMTP_TLS:
                server.starttls()

        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(msg["From"], [to_email], msg.as_string())
        server.quit()

        logger.info(f"Verification email successfully delivered to {to_email} via SMTP.")
        return True

    except Exception as err:
        logger.error(f"Failed to send SMTP email to {to_email}: {err}")
        return False
