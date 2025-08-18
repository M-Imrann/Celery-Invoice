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
from PIL import Image

from celery import current_app as celery_app
celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = True

import invoice.signals
from .tasks import (
    send_welcome_email,
    generate_and_send_invoices,
    send_daily_summary,
    send_data_to_api,
    resize_user_image,
)

# ✅ Temporary media root for tests
TEMP_MEDIA_ROOT = tempfile.mkdtemp()


# ------------------- MODEL TESTS -------------------
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ModelTests(TestCase):
    """
    class for testing the models.
    """
    def setUp(self):
        # ensure directory exists
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        self.user = User.objects.create_user(
            username="imran",
            email="imran@example.com",
            password="imran",
        )

    def tearDown(self):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_order_creation(self):
        """
        Test case for testing the Order Model.
        """
        order = Order.objects.create(user=self.user)
        self.assertEqual(
            str(order),
            f"Order #{order.id} - {self.user.username}"
            )

    def test_items_creation_and_total(self):
        """
        Test case for testing the Items Model.
        """
        order = Order.objects.create(user=self.user)
        item1 = Items.objects.create(
            order=order,
            item_name="Product A",
            quantity=2,
            price=Decimal("10.00")
        )
        item2 = Items.objects.create(
            order=order,
            item_name="Product B",
            quantity=1,
            price=Decimal("20.00")
        )

        self.assertEqual(str(item1), "Product A  2")
        self.assertEqual(item1.total_price(), Decimal("20.00"))
        self.assertEqual(item2.total_price(), Decimal("20.00"))
        self.assertEqual(
            sum(i.total_price() for i in order.items.all()), Decimal("40.00")
        )

    def test_userprofile_creation(self):
        """
        Testcase for testing the UserProfile Model.
        """
        image_path = os.path.join(settings.MEDIA_ROOT, "profile.jpg")
        img = Image.new("RGB", (100, 100), color="green")
        img.save(image_path)

        profile = UserProfile.objects.create(
            user=self.user,
            image="profile.jpg"
            )
        # ✅ requires __str__ fix in UserProfile model
        self.assertEqual(str(profile), f"Profile of {self.user.username}")
        self.assertTrue(profile.image.name.endswith("profile.jpg"))


# ------------------- SIGNAL TESTS -------------------
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class SignalTests(TestCase):
    """
    Class for testing the Signals file.
    """
    def setUp(self):
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        self.user = User.objects.create_user(
            username="imran",
            email="imran@example.com",
            password="imran",
        )
        mail.outbox = []

    @mock.patch("invoice.signals.send_welcome_email")
    def test_welcome_email_signal_triggered(self, mock_task):
        """
        Test case for testing the send emai on user creation function.
        """
        User.objects.create_user(
            username="ali", email="ali@example.com", password="ali"
        )
        mock_task.delay.assert_called_with("ali@example.com")

    @mock.patch("invoice.signals.generate_and_send_invoices")
    def test_invoice_signal_triggered(self, mock_task):
        """
        Test case for testing the invoice signal function.
        """
        order = Order.objects.create(user=self.user)
        Items.objects.create(
            order=order,
            item_name="Product A",
            quantity=1,
            price=Decimal("10.00")
        )
        mock_task.delay.assert_called_with(order.id, self.user.email)

    @mock.patch("invoice.signals.resize_user_image")
    def test_image_resize_signal_triggered(self, mock_task):
        """
        Test case for testing the image_resize function.
        """
        image_path = os.path.join(settings.MEDIA_ROOT, "test.jpg")
        img = Image.new("RGB", (100, 100), color="blue")
        img.save(image_path)

        UserProfile.objects.create(user=self.user, image="test.jpg")
        mock_task.delay.assert_called()


# ------------------- TASK TESTS -------------------
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskTests(TestCase):
    """
    Class for testing the Tasks file.
    """
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        self.user = User.objects.create_user(
            username="imran",
            email="imran@example.com",
            password="imran",
        )
        mail.outbox = []

    def test_send_welcome_email(self):
        """
        Test case for testing the send welcome email function.
        """
        send_welcome_email(self.user.email)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Welcome Email", mail.outbox[0].subject)

    @mock.patch("invoice.signals.send_welcome_email.delay")
    def test_generate_and_send_invoice(self, mock_welcome):
        """
        Test case for testing the generate and send invoices function.
        Ensure invoice generation sends exactly one invoice email
        """
        order = Order.objects.create(user=self.user)
        Items.objects.create(
            order=order,
            item_name="Product A",
            quantity=2,
            price=Decimal("10.00")
            )

        # clear any emails from signals
        mail.outbox = []

        generate_and_send_invoices(order.id, self.user.email)

        pdf_path = os.path.join(settings.MEDIA_ROOT, f"invoice_{order.id}.pdf")
        self.assertTrue(os.path.exists(pdf_path))

        # ✅ Only invoice email should exist
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Order Invoice", mail.outbox[0].subject)

    def test_send_daily_summary(self):
        """
        Test case for testing the send daily summary function.
        """
        send_daily_summary()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Daily Summary", mail.outbox[0].subject)

    @mock.patch("invoice.tasks.send_data_to_api.run")
    def test_send_data_to_api_success(self, mock_run):
        """
        Test case for testing the send data to api function.
        """
        mock_run.return_value = {"success": True}
        result = send_data_to_api(data={"test": "data"})
        self.assertEqual(result, {"success": True})

    def test_resize_user_image(self):
        """
        Test case for testing the resize user image function.
        """
        image_path = os.path.join(settings.MEDIA_ROOT, "test.jpg")
        img = Image.new("RGB", (500, 500), color="red")
        img.save(image_path)

        resize_user_image(image_path)
        resized_100 = os.path.join(settings.MEDIA_ROOT, "test_100x100.jpg")
        resized_300 = os.path.join(settings.MEDIA_ROOT, "test_300x300.jpg")
        self.assertTrue(os.path.exists(resized_100))
        self.assertTrue(os.path.exists(resized_300))
