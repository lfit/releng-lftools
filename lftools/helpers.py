import random
import string


def generate_password(length=12):
    punctuation = "!#$%&()*+,-.:;<=>?@[]^_{|}~"
    password_characters = string.ascii_letters + string.digits + punctuation
    return ''.join(random.choice(password_characters) for _ in range(length))
