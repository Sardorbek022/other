# from django.contrib import admin
# from .models import Category, Product, Order

# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ['name', 'slug']
#     prepopulated_fields = {'slug': ('name',)}


# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ['name', 'category', 'price', 'is_available', 'stock']
#     list_filter = ['is_available', 'category']
#     search_fields = ['name', 'description']
#     prepopulated_fields = {'slug': ('name',)}


# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ['id', 'customer_name', 'phone_number', 'product', 'quantity', 'order_price', 'status', 'created_at']
#     list_filter = ['status', 'created_at']
#     search_fields = ['customer_name', 'phone_number']

from django.contrib import admin
from .models import Category, Product, Order


admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Order)
