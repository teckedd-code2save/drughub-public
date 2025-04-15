from app.models import EmailSchema, Message, VerifyOTPRequest
from fastapi import  HTTPException
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.utils.config import settings
from app.utils.redis_db import delete_redis_key, set_redis_key,get_redis_key
import pyotp
import smtplib
from email.mime.text import MIMEText


email_sender = settings.SMTP_USER
email_password = settings.SMTP_PASSWORD

secret = pyotp.random_base32()

async def send_otp_mail(data: EmailSchema, subject: str = "DrugHub - Verify Your Email", message: str = None):
    totp = pyotp.TOTP(secret)
    otp = totp.now()

    redis_key = f"otp-secret:{data.email}"
    await set_redis_key(redis_key, secret, 300)  # 5-minute expiration
    print(f"OTP: {otp}")
    print(f"Secret: {secret}")
    print(f"Verify OTP: {totp.verify(otp)}")

    msg = MIMEText(f"Your otp code is {otp}", "html")
    msg['From'] = email_sender
    msg['To'] = data.email
    msg['Subject'] = subject

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(email_sender, email_password)
            smtp.sendmail(email_sender, data.email, msg.as_string())
        print("Message sent!")
    except Exception as e:
        print(f"Email sending failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to send OTP email")

def verify_otp(data: VerifyOTPRequest):
    redis_key = f"otp-secret:{data.email}"
    stored_secret = get_redis_key(redis_key)
    print(f"Secret from Redis: {secret}")

    if not stored_secret:
        raise HTTPException(status_code=400, detail="OTP expired or not found")

    totp = pyotp.TOTP(secret)
    verify = totp.verify(data.otp, valid_window=1)  # Allow 30-second drift
    print(f"OTP verification result: {verify}")

    if verify:
        delete_redis_key(redis_key)
        return Message(message="OTP verified successfully")

    raise HTTPException(status_code=400, detail="Invalid OTP")
# Redis setup
# ----------- SEND WITH FASTAPIMAIL --------
# Mail config
conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.EMAILS_FROM_EMAIL,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_FROM_NAME=settings.PROJECT_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True

)



async def send_otp(data: EmailSchema):
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    otp = totp.now()

    # Store secret in Redis with 5 min expiration
    redis_key = f"otp-secret:{data.email}"
    set_redis_key(redis_key,secret,300)

    # Send email
    message = MessageSchema(
        subject="Your OTP Code",
        recipients=[data.email],
        body=f"Your OTP code is: {otp}",
        subtype="plain"
    )
    fm = FastMail(conf)
    await fm.send_message(message)

    return {"detail": "OTP sent successfully"}

