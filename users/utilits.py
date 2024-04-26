import requests
from django.conf import settings
from django.core.cache import cache


def check_rate_limit(phone_number):
    attempts = cache.get(f"attempts_{phone_number}", 0)
    if attempts >= 5:  # Limit to 5 attempts
        return False
    cache.set(f"attempts_{phone_number}", attempts + 1, timeout=3600)  # Reset after 1 hour
    return True


class SmsOtp:
    token = None
    username = settings.SMS_OTP_USERNAME
    password = settings.SMS_OTP_PASSWORD
    base_url = settings.SMS_OTP_BASE_URL

    def __init__(self, phone_number, otp):
        self.phone_number = phone_number
        self.otp = otp

    def get_token(self):
        print(self.base_url + "/auth/login")
        if cache.get("sms_otp_token"):
            self.token = cache.get("sms_otp_token")
            return
        url = self.base_url + "/auth/login"
        data = {
            "email": self.username,
            "password": self.password
        }
        response = requests.post(url, data=data)
        if response.status_code == 200:
            self.token = response.json().get("data", {}).get("token")
            cache.set("sms_otp_token", self.token, timeout=2592000)
        elif response.status_code == 401:
            raise Exception("Invalid credentials")
        else:
            raise Exception("Failed to get token")

    def refresh_token(self):
        url = "https://notify.eskiz.uz/api/auth/refresh"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        response = requests.patch(url, headers=headers)
        print(response.text)
        if response.status_code == 200:
            self.token = response.json().get("data", {}).get("token")
            cache.set("sms_otp_token", self.token, timeout=2592000)
        else:
            raise Exception("Failed to refresh token")

    def send_otp(self):
        self.get_token()
        data = {
            'mobile_phone': self.phone_number[1:],
            'message': 'Bu Eskiz dan test',
            'from': '4546',
        }
        url = "https://" + self.base_url + "/message/sms/send"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            cache.set(f"otp_{self.phone_number}", self.otp, timeout=300)
            return response.json()
        else:
            self.refresh_token()
            response = requests.post(url, headers=headers, data=data)
            if response.status_code == 200:
                cache.set(f"otp_{self.phone_number}", self.otp, timeout=300)
                return response.json()
            else:
                raise Exception("Failed to send OTP, Problem with SMS service")


def verify_otp(phone_number, user_input_otp):
    cached_otp = cache.get(f"otp_{phone_number}")
    if cached_otp and int(cached_otp) == int(user_input_otp):
        cache.delete(f"otp_{phone_number}")
        cache.set(f"verified_{phone_number}", True, timeout=86400)
        return True
    return False
