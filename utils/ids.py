import datetime
import random

def generate_case_number():
    year = datetime.datetime.now().year
    random_part = random.randint(1, 999999)
    return f"LD-{year}-{random_part:06d}"
