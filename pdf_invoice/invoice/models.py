from django.db import models
from django.contrib.auth.models import User


class Order(models.Model):
    """
    Order model with user and date of creation fields.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def total_amount(self):
        """
        Calculates the total amount for all items in this order.

        Returns:
        Decimal: Total price of all items.
        """
        return sum(item.total_price() for item in self.items.all())

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


class Items(models.Model):
    """
    Items Model with order, item_name, quantity and price fields.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
        )
    item_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def total_price(self):
        """
        Calculates the total price for this item.

        Returns:
        Decimal: Quantity multiplied by price.
        """
        return self.quantity*self.price

    def __str__(self):
        return f"{self.item_name}  {self.quantity}"


class UserProfile(models.Model):
    """
    UserProfile model with user and image fields.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='profiles/')

    def __str__(self):
        return f"Profile of {self.user.username}"
