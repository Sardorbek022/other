from django.urls import path
from .views import ProductListView, ProductDetailView, OrderCreateView

urlpatterns = [
    path('', ProductListView.as_view(), name='product_list'),
    path('product/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('order/create/', OrderCreateView.as_view(), name='order_create'),
]
