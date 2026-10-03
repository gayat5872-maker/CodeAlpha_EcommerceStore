from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from .forms import CheckoutForm, RegisterForm
from .models import Order, OrderItem, Product

def product_list(request):
    products = Product.objects.all().order_by("-created_at")
    return render(request, "store/product_list.html", {"products": products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "store/product_detail.html", {"product": product})

def _cart(request):
    return request.session.setdefault("cart", {})

def _cart_items(request):
    cart = _cart(request)
    products = Product.objects.filter(id__in=cart.keys())
    result, total = [], Decimal("0")
    for product in products:
        qty = max(1, min(int(cart.get(str(product.id), 1)), product.stock))
        subtotal = product.price * qty
        result.append({"product": product, "quantity": qty, "subtotal": subtotal})
        total += subtotal
    return result, total

def cart(request):
    items, total = _cart_items(request)
    return render(request, "store/cart.html", {"items": items, "total": total})

def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if product.stock < 1:
        messages.error(request, "This product is out of stock.")
        return redirect("product_detail", pk=pk)
    cart = _cart(request)
    key = str(pk)
    cart[key] = min(int(cart.get(key, 0)) + 1, product.stock)
    request.session.modified = True
    messages.success(request, f"{product.name} added to cart.")
    return redirect("cart")

def update_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    qty = max(0, min(int(request.POST.get("quantity", 1)), product.stock))
    cart = _cart(request)
    key = str(pk)
    if qty == 0:
        cart.pop(key, None)
    else:
        cart[key] = qty
    request.session.modified = True
    return redirect("cart")

def remove_from_cart(request, pk):
    cart = _cart(request)
    cart.pop(str(pk), None)
    request.session.modified = True
    return redirect("cart")

@login_required
def checkout(request):
    items, total = _cart_items(request)
    if not items:
        return redirect("product_list")
    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                for item in items:
                    product = Product.objects.select_for_update().get(pk=item["product"].pk)
                    if item["quantity"] > product.stock:
                        messages.error(request, f"Not enough stock for {product.name}.")
                        return redirect("cart")
                order = Order.objects.create(
                    user=request.user, total=total,
                    shipping_address=form.cleaned_data["shipping_address"]
                )
                for item in items:
                    product = Product.objects.select_for_update().get(pk=item["product"].pk)
                    OrderItem.objects.create(order=order, product=product,
                                             quantity=item["quantity"], price=product.price)
                    product.stock -= item["quantity"]
                    product.save(update_fields=["stock"])
            request.session["cart"] = {}
            request.session.modified = True
            messages.success(request, f"Order #{order.id} placed successfully.")
            return redirect("orders")
    else:
        form = CheckoutForm()
    return render(request, "store/checkout.html", {"items": items, "total": total, "form": form})

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("product_list")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})

@login_required
def orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related("items__product")
    return render(request, "store/orders.html", {"orders": orders})
