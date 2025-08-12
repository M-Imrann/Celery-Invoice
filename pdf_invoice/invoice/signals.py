from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .tasks import (
    send_welcome_email,
    generate_and_send_invoices,
    resize_user_image
)
from .models import Order, UserProfile


@receiver(post_save, sender=User)
def send_email_on_user_creation(sender, instance, created, **kwargs):
    if created:
        send_welcome_email.delay(instance.email)


@receiver(post_save, sender=Order)
def invoice_signal(sender, instance, created, **kwargs):
    if created:
        generate_and_send_invoices.delay(instance.id, instance.user.email)


@receiver(post_save, sender=UserProfile)
def image_resize_signal(sender, instance, **kwargs):
    if instance.image:
        resize_user_image.delay(instance.image.path)
