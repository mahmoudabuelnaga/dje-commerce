from django.shortcuts import render , get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.contrib import messages
from .forms import CheckoutForm
from django.conf import settings
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
from .models import Item , Order, OrderItem, BillingAddress, Payment


# "sk_test_4eC39HqLyjWDarjtT1zdp7dc"
# `source` is obtained with Stripe.js; see https://stripe.com/docs/payments/accept-a-payment-charges#web-create-token


# Create your views here.
class HomeView(ListView):
    model = Item
    paginate_by = 10
    template_name = 'home.html'

class ItemDetailView(DetailView):
    model = Item
    template_name = 'product.html'


@login_required
def add_to_cart(request, pk, slug):
    item        = get_object_or_404(Item, pk=pk, slug=slug)
    order_item, create_item  = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False,
        )
    order_qs    = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
        else:
            order.items.add(order_item)
            messages.info(request, "This item add to your cart.")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item add to your cart.")
    return redirect("core:order-summary")


@login_required
def remove_from_cart(request,pk, slug):
    item = get_object_or_404(Item, pk=pk, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            messages.info(request, "This item was removed from your cart.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", pk=pk, slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", pk=pk, slug=slug)


@login_required
def remove_single_item_from_cart(request,pk, slug):
    item = get_object_or_404(Item, pk=pk, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item was removed from your cart.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:order-summary")
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:order-summary")


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self,*args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object':order,
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an active order")
            return redirect("/")



class checkoutView(View, LoginRequiredMixin):
    def get(self, *args, **kwargs):
        form = CheckoutForm()
        order = Order.objects.get(user=self.request.user, ordered=False)
        context = {
            'form':form,
            'order':order,
        }
        return render(self.request, 'checkout.html', context)
    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            
            if form.is_valid():
                street_address       = form.cleaned_data.get('street_address')
                apartment_address    = form.cleaned_data.get('apartment_address')
                country              = form.cleaned_data.get('country')
                zip                  = form.cleaned_data.get('zip')
                # some_shoping_address = form.cleaned_data.get('some_shoping_address')
                # save_info            = form.cleaned_data.get('save_info')
                payment_option       = form.cleaned_data.get('payment_option')

                billing_address      = BillingAddress(
                    user             = self.request.user,
                    street_address   = street_address,
                    apartment_address = apartment_address,
                    country          = country,
                    zip              = zip,
                )
                billing_address.save()
                order.billing_address = billing_address
                order.save()

                if payment_option == "S":
                    return redirect("core:payment", payment_option='stripe')
                elif payment_option == "P":
                    return redirect("core:payment", payment_option='paypal')
                else:
                    messages.warning(self.request, "Invalid payment option selected")
                    return redirect("core:checkout")
        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an active order")
            return redirect("core:order-summary")
        



class PaymentView(View, LoginRequiredMixin):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        context = {
            'order' : order,
        }
        return render(self.request, 'payment.html', context)
    
    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        token = self.request.POST.get('stripeToken')
        amount = int(order.get_total() * 100)  #cents

        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency="usd",
                source=token,
            )

            # create the payment
            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = order.get_total()
            payment.save()

            # assign the payment to the order
            order.ordered = True
            order.payment = payment
            order.save()

            messages.success(self.request, "Your order was seccessful!")
            return redirect("core:home")

        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught
            body = e.json_body
            err = body.get('error', {})
            messages.error(self.request, f"{err.get('message')}")
            return redirect("core:home")

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.error(self.request, "Rate limit error")
            return redirect("core:home")

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.error(self.request, "Invalid prameters")
            return redirect("core:home")

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.error(self.request, "Not authenticated")
            return redirect("core:home")

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.error(self.request, "Network Error")
            return redirect("core:home")

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.error(self.request, "Something went wrong. You were not charged. Please try again")
            return redirect("core:home")

        except Exception as e:
            # Sending an email to ourselves
            messages.error(self.request, "A Serious error occurred. We have been notifed.")
            return redirect("core:home")
