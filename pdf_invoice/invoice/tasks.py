from celery import shared_task
from django.core.mail import send_mail, EmailMessage
from reportlab.pdfgen import canvas
from PIL import Image
from django.conf import settings
import requests
import os
import random
from django.contrib.auth.models import User


@shared_task(bind=True, max_retries=3)
def send_welcome_email(self, user_email):
    try:
        subject = "Welcome Email"
        message = "Hi there,\n\nThank you for registering with us. We're excited to have you on board!"
        from_email = "admin@gmail.com"

        recipient_list = [user_email]

        send_mail(subject, message, from_email, recipient_list)
        print(f"Sending email to : {user_email}")
        return f"Email sent to {user_email}"

    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)
    

@shared_task
def generate_and_send_invoices(order_id, user_email):
    pdf_path = os.path.join(settings.MEDIA_ROOT, f'invoice_{order_id}.pdf')
    c = canvas.Canvas(pdf_path)
    c.drawString(100, 750, f"Invoice for Order # {order_id}")
    c.drawString(100, 730, "Thank you for your Purchase!")
    c.save()

    email = EmailMessage(
        "Purchase Invoice",
        "Please find your invoice attached.",
        "admin@gmail.com",
        [user_email]
    )
    email.attach_file(pdf_path)
    email.send()


@shared_task
def send_daily_summary():
    for user in User.objects.all():
        send_mail(
            "Daily Summary",
            "Here is your daily summary.",
            "admin@gmail.com",
            [user.email],
            fail_silently=True
        )


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def send_data_to_api(self, data):
    if random.choice([True, False]):
        raise Exception("Simulated API Failure")
    

    response = requests.post('https://httpbin.org/post', json=data)
    response.raise_for_status()
    return response.json()


@shared_task
def resize_user_image(image_path):
    sizes = [(100, 100), (300, 300)]
    for size in sizes:
        img = Image.open(image_path)
        img.thumbnail(size)
        base, ext = os.path.splitext(image_path)
        new_path = f"{base}_{size[0]}x{size[1]}{ext}"
        img.save(new_path)
