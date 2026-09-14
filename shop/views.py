from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Order

class ProductListView(View):
    
    def get(self, request, *args, **kwargs):
        products = Product.objects.filter(is_available=True)
        context = {
            'products': products
        }
        return render(request=request, template_name='shop/product_list.html', context=context)

    def post(self, request, *args, **kwargs):
        pass


class ProductDetailView(View):
    
    def get(self, request, slug, *args, **kwargs):
        product = get_object_or_404(Product, slug=slug)
        context = {
            'product': product
        }
        return render(request=request, template_name='shop/product_detail.html', context=context)

    def post(self, request, *args, **kwargs):
        pass


class OrderCreateView(View):
    def get(self, request, *args, **kwargs):
        pass

    def post(self, request, *args, **kwargs):
        customer_name = request.POST.get('customer_name')
        phone_number = request.POST.get('phone_number')
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))

        product = get_object_or_404(Product, id=product_id)
        Order.objects.create(
            customer_name=customer_name,
            phone_number=phone_number,
            product=product,
            quantity=quantity
        )

        return redirect('product_list')
