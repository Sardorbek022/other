from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nomi")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Slag")

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="Kategoriya")
    name = models.CharField(max_length=200, verbose_name="Nomi")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="Slag")
    description = models.TextField(blank=True, verbose_name="Tavsif")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Narxi")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Rasm")
    stock = models.PositiveIntegerField(default=10, verbose_name="Qoldiq")
    is_available = models.BooleanField(default=True, verbose_name="Holati")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Kutilmoqda'),
        ('processing', 'Jarayonda'),
        ('completed', 'Yakunlandi'),
        ('canceled', 'Bekor qilindi'),
    )

    customer_name = models.CharField(max_length=100, verbose_name="Mijoz")
    phone_number = models.CharField(max_length=20, verbose_name="Telefon")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name="Mahsulot")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Soni")
    order_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False, blank=True, null=True, verbose_name="Narxi")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Status")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"

    def __str__(self):
        return f"Buyurtma #{self.id} - {self.customer_name}"

    def save(self, *args, **kwargs):
        if self.product and not self.order_price:
            self.order_price = self.product.price
        super().save(*args, **kwargs)
