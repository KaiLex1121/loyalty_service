import random

def generate_otp(length: int = 6) -> str:
    return "".join([str(random.randint(0, 9)) for _ in range(length)])

async def send_sms_otp(phone_number: str, otp_code: str):
    print(f"DEBUG: Sending OTP {otp_code} to {phone_number}")
    return True
