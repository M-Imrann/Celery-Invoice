import os
import tempfile
import shutil
from unittest import mock
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from .models import Order, Items, UserProfile
from decimal import Decimal
from django.core import mail
from django.conf import settings
from .tasks import (
    send_welcome_email,
    generate_and_send_invoices,
    send_daily_summary,
    send_data_to_api,
    resize_user_image
)
from PIL import Image


class SignalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="john",
            email="john@example.com",
            password="pass"
            )

    @mock.patch("core.signals.send_welcome_email.delay")
    def test_welcome_email_signal_triggered(self, mock_task):
        User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="pass"
            )
        self.assertTrue(mock_task.called)
        mock_task.assert_called_with("alice@example.com")

    @mock.patch("core.signals.generate_and_send_invoice.delay")
    def test_invoice_signal_triggered(self, mock_task):
        Order.objects.create(user=self.user)
        self.assertTrue(mock_task.called)

    @mock.patch("core.signals.resize_user_image.delay")
    def test_image_resize_signal_triggered(self, mock_task):
        profile = UserProfile.objects.create(
            user=self.user,
            image="profiles/test.jpg"
            )
        self.assertTrue(mock_task.called)


TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(
            username="john",
            email="john@example.com",
            password="pass"
            )

    def test_send_welcome_email(self):
        send_welcome_email(self.user.email)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Welcome to Our Platform", mail.outbox[0].subject)

    def test_generate_and_send_invoice(self):
        order = Order.objects.create(user=self.user)
        Items.objects.create(
            order=order,
            item_name="Product A",
            quantity=2,
            price=Decimal('10.00')
            )
        generate_and_send_invoices(order.id, self.user.email)

        pdf_path = os.path.join(settings.MEDIA_ROOT, f"invoice_{order.id}.pdf")
        self.assertTrue(os.path.exists(pdf_path))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Your Invoice", mail.outbox[0].subject)

    def test_send_daily_summary(self):
        send_daily_summary()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Daily Summary", mail.outbox[0].subject)

    @mock.patch("core.tasks.requests.post")
    def test_send_data_to_api_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"success": True}
        result = send_data_to_api(data={"test": "data"})
        self.assertEqual(result, {"success": True})

    def test_resize_user_image(self):
        image_path = os.path.join(settings.MEDIA_ROOT, "test.jpg")
        img = Image.new("RGB", (500, 500), color="red")
        img.save(image_path)

        resize_user_image(image_path)

        resized_100 = os.path.join(settings.MEDIA_ROOT, "test_100x100.jpg")
        resized_300 = os.path.join(settings.MEDIA_ROOT, "test_300x300.jpg")

        self.assertTrue(os.path.exists(resized_100))
        self.assertTrue(os.path.exists(resized_300))


class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="john",
            email="john@example.com",
            password="pass"
            )

    def test_orderitem_total_price(self):
        order = Order.objects.create(user=self.user)
        item = Items.objects.create(
            order=order,
            item_name="Product A",
            quantity=2,
            price=Decimal('10.00')
            )
        self.assertEqual(item.total_price(), Decimal('20.00'))

    def test_order_total_amount(self):
        order = Order.objects.create(user=self.user)
        Items.objects.create(
            order=order,
            item_name="Product A",
            quantity=2,
            price=Decimal('10.00')
            )
        Items.objects.create(
            order=order,
            item_name="Product B",
            quantity=1,
            price=Decimal('5.00')
            )
        self.assertEqual(order.total_amount(), Decimal('25.00'))

    def test_userprofile_creation(self):
        profile = UserProfile.objects.create(
            user=self.user,
            image="profiles/test.jpg"
            )
        self.assertEqual(profile.user.username, "john")
