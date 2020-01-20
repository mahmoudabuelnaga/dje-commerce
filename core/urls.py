from django.urls import path
from .views import (
    ItemDetailView, 
    HomeView,
    add_to_cart, 
    remove_from_cart,
    OrderSummaryView,
    remove_single_item_from_cart,
    checkoutView,
    PaymentView,
)

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),

    path('product/<pk>/<slug>/', ItemDetailView.as_view(), name='product'),

    path('checkout/', checkoutView.as_view(), name='checkout'),

    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    
    path('add-item-to-cart/<pk>/<slug>/', add_to_cart, name='add_to_cart'),
    
    path('remove-from-cart/<pk>/<slug>/', remove_from_cart, name='remove_from_cart'),
    
    path('remove-single-item-from-cart/<pk>/<slug>/', remove_single_item_from_cart, name='remove_single_item_from_cart'),

    path('payment/<payment_option>/', PaymentView.as_view(), name='payment'),


]
