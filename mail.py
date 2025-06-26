import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_otp_email(email, otp):
    sender_email = "abc@gmail.com"
    sender_password = "XXXX XXXX XXXX XXXX"  # App Password

    message = MIMEMultipart()                                
    message["From"] = sender_email
    message["To"] = email
    message["Subject"] = "Your SecureGate OTP"

    body = f"Your OTP for SecureGate is: {otp}"
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, message.as_string())
        print("OTP email sent successfully.")
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False