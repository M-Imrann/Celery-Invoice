from celery import shared_task
from django.core.mail import send_mail, EmailMessage
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from PIL import Image
from django.conf import settings
import requests
import os
import random
from django.contrib.auth.models import User
from .models import Order


@shared_task(bind=True, max_retries=3)
def send_welcome_email(self, user_email):
    try:
        subject = "Welcome Email"
        message = "Hi there,\n\nThank you for\
            registering with us. We're excited to have you on board!"
        from_email = "admin@gmail.com"

        recipient_list = [user_email]

        send_mail(subject, message, from_email, recipient_list)
        print(f"Sending email to : {user_email}")
        return f"Email sent to {user_email}"

    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)


@shared_task
def generate_and_send_invoices(order_id, user_email):
    order = Order.objects.get(id=order_id)

    pdf_path = os.path.join(settings.MEDIA_ROOT, f'invoice_{order_id}.pdf')
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)

    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("INVOICE", styles['Title']))
    elements.append(Spacer(1, 12))

    # User info
    elements.append(
        Paragraph(f"Customer: {order.user.username}", styles['Normal'])
        )
    elements.append(Paragraph(f"Order ID: {order.id}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Table data
    data = [["Item", "Quantity", "Price", "Total"]]
    for item in order.items.all():
        data.append([
            item.item_name,
            str(item.quantity),
            f"${item.price}",
            f"${item.total_price()}"
        ])

    # Add total row
    data.append(["", "", "Total Amount", f"${order.total_amount()}"])

    table = Table(data, colWidths=[200, 100, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    # Thank you message
    elements.append(
        Paragraph("Thank you for your purchase!", styles['Normal'])
        )

    doc.build(elements)

    # Send email
    email = EmailMessage(
        'Order Invoice',
        'Please find your invoice attached.',
        'admin@gmail.com',
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


@shared_task(
        bind=True,
        autoretry_for=(Exception,),
        retry_backoff=True,
        max_retries=5
        )
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
