import random
import string
import stripe
from django.contrib import messages
from django.contrib.auth.models import User, auth
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import ListView, DetailView, View

from .forms import CheckoutForm, CouponForm, RefundForm
from .models import Item, Order, OrderItem, Address, Payment, Coupon, Refund

stripe.api_key = "sk_test_4eC39HqLyjWDarjtT1zdp7dc"


def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


def products(request):
    context = {'Items': Item.objects.all()}
    return render(request, 'store/product-page.html', context)


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


class HomeView(ListView):
    model = Item
    paginate_by = 4
    template_name = 'store/home-page.html'


class ItemDetailsView(DetailView):
    model = Item
    template_name = 'store/product-page.html'


class OrderSummaryView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('store:login')
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {'object': order}
            return render(self.request, 'store/summary_view.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You don't have an active order.")
            return redirect('/')


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            forms = CheckoutForm()
            context = {'forms': forms, 'order': order, 'coupon_form': CouponForm(),
                       'DISPLAY_COUPON_FORM': True}

            shipping_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='S',
                default=True
            )
            if shipping_address_qs.exists():
                context.update({'default_shipping_address': shipping_address_qs[0]})

            billing_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='B',
                default=True
            )
            if billing_address_qs.exists():
                context.update({'default_billing_address': billing_address_qs[0]})

            return render(self.request, 'store/checkout-page.html', context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You don't have an active order")
            return redirect('store:checkout')

    def post(self, *args, **kwargs):
        forms = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if forms.is_valid():

                use_default_shipping = forms.cleaned_data.get('use_default_shipping')
                if use_default_shipping:
                    print('Using default shipping address')

                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(self.request, "No default shipping address available")
                        return redirect('store:checkout')
                else:
                    print('User has entered new shipping address')

                    shipping_address = forms.cleaned_data.get('shipping_address')
                    shipping_address2 = forms.cleaned_data.get('shipping_address2')
                    shipping_country = forms.cleaned_data.get('shipping_country')
                    shipping_zip_code = forms.cleaned_data.get('shipping_zip_code')

                    if is_valid_form([shipping_address, shipping_country, shipping_zip_code]):
                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address,
                            country=shipping_country,
                            apartment_address=shipping_address2,
                            zip_code=shipping_zip_code,
                            address_type='S'
                        )
                        shipping_address.save()

                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = forms.cleaned_data.get('set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()
                    else:
                        messages.info(self.request, 'Please fill in the required shipping address fields.')

                    use_default_billing = forms.cleaned_data.get('use_default_billing')
                    same_billing_address = forms.cleaned_data.get('same_billing_address')
                    if same_billing_address:
                        billing_address = shipping_address
                        billing_address.pk = None
                        billing_address.save()
                        billing_address.address_type = 'B'
                        billing_address.save()
                        order.billing_address = billing_address
                        order.save()

                    elif use_default_billing:
                        print('Using default billing address')

                        address_qs = Address.objects.filter(
                            user=self.request.user,
                            address_type='B',
                            default=True
                        )
                        if address_qs.exists():
                            billing_address = address_qs[0]
                            order.billing_address = billing_address
                            order.save()
                        else:
                            messages.info(self.request, "No default billing address available")
                            return redirect('store:checkout')
                    else:
                        print('User has entered new billing address')
                        billing_address = forms.cleaned_data.get('billing_address')
                        billing_address2 = forms.cleaned_data.get('billing_address2')
                        billing_country = forms.cleaned_data.get('billing_country')
                        billing_zip_code = forms.cleaned_data.get('billing_zip_code')
                        if is_valid_form([billing_address, billing_country, billing_zip_code]):
                            billing_address = Address(
                                user=self.request.user,
                                street_address=billing_address,
                                country=billing_country,
                                apartment_address=billing_address2,
                                zip_code=billing_zip_code,
                                address_type='B'
                            )
                            billing_address.save()

                            order.billing_address = billing_address
                            order.save()

                            set_default_billing = forms.cleaned_data.get('set_default_billing')
                            if set_default_billing:
                                billing_address.default = True
                                billing_address.save()
                        else:
                            messages.info(self.request, 'Please fill in the required shipping address fields.')

                    payment_option = forms.cleaned_data.get('payment_option')

                    if payment_option == 'C':
                        return redirect('store:payment', payment_option='credit_card')
                    elif payment_option == 'P':
                        return redirect('store:payment', payment_option='paypal')
                    else:
                        messages.warning(self.request, 'Invalid payment option selected')
                        return redirect('store:checkout')

            # return render(self.request, 'store/summary_view.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You don't have an active order.")
            return redirect('store:order_summary')


class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {'order': order, 'DISPLAY_COUPON_FORM': False}
            return render(self.request, 'payment_page.html', context)
        else:
            messages.warning(self.request, "You have not added a billing address.")
            return redirect('store:checkout')

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        token = self.request.POST.get('stripeToken')
        amount = int(order.get_total())

        try:
            charge = stripe.Charge.create(
                currency="usd",
                source=token,
                amount=amount
            )

            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = order.get_total()
            payment.save()

            order_items = OrderItem.objects.all()
            order_items.update(ordered=True)
            for item in order_items:
                item.save()

            order.ordered = True
            order.payment = payment
            order.ref_code = create_ref_code()
            order.save()

            messages.info(self.request, 'Your order has successful')
            return redirect('/')
        except stripe.error.CardError as e:
            body = e.json_body
            err = body.get('error', {})
            messages.warning(self.request, f"{err.get('message')}")
            return redirect('/')
        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.warning(self.request, f"Rate limit errors")
            return redirect('/')
        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.warning(self.request, f"Invalid Parameters")
            return redirect('/')
        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.warning(self.request, f"Not Authenticated")
            return redirect('/')
        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.warning(self.request, f"Network Error")
            return redirect('/')
        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.warning(self.request, f"Something went wong, You were not charge. Please try again.")
            return redirect('/')
        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            messages.warning(self.request, f"a serious error occurred. We have been noticed")
            return redirect('/')


def add_cart(request, slug):
    if not request.user.is_authenticated:
        return redirect('store:login')
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # CHECK IF THE ORDER ITEM IS IN THE ORDER
        if order.item.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, 'This item quantity was updated.')
            return redirect('store:order_summary')
        else:
            order.item.add(order_item)
            messages.info(request, 'This item was added in your cart.')
            return redirect('store:product', slug=slug)

    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.item.add(order_item)
        messages.info(request, 'This item was added in your cart.')
    return redirect('store:product', slug=slug)


def remove_cart(request, slug):
    if not request.user.is_authenticated:
        return redirect('store:login')
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # CHECK IF THE ORDER ITEM IS IN THE ORDER
        if order.item.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.item.remove(order_item)
            messages.info(request, 'This item was removed in your cart.')
            return redirect('store:order_summary')
        else:
            messages.info(request, 'This item was not in your cart.')
            return redirect('store:product', slug=slug)
    else:
        messages.info(request, "You don't have an active order.")
        return redirect('store:product', slug=slug)


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['pass']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Invalid Username or Password !')
            return redirect('store:login')
    else:
        return render(request, 'store/login.html')


def logout(request):
    auth.logout(request)
    return redirect('store:login')


def signup(request):
    if request.method == 'POST':
        name = request.POST['name']
        username = request.POST['username']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        if password1 == password2:
            if User.objects.filter(username=username).exists():
                messages.info(request, 'Username exists !')
                return redirect('store:signup')
            else:
                user = User.objects.create_user(first_name=name, username=username, password=password1)
                user.save()
                return redirect('store:login')
        else:
            messages.info(request, 'Password not Matching !')
        return redirect('store:signup')

    else:
        return render(request, 'store/signup.html')


def remove_single_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # CHECK IF THE ORDER ITEM IS IN THE ORDER
        if order.item.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.item.remove(order_item)
            messages.info(request, 'This item quantity was updated.')
            return redirect('store:order_summary')
        else:
            messages.info(request, 'This item was not in your cart.')
            return redirect('store:product', slug=slug)
    else:
        messages.info(request, "You don't have an active order.")
        return redirect('store:product', slug=slug)


def admin(request):
    return redirect('admin')


def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.warning(request, "This coupon doesn't exist")
        return redirect('store:checkout')


class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "The coupon successfully added")
                return redirect('store:checkout')
            except ObjectDoesNotExist:
                messages.info(self.request, "You don't have an active order")
                return redirect('store:checkout')


class RequestRefundView(View):

    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {'form': form}
        return render(self.request, 'store/request_refund.html', context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()
                messages.info(self.request, 'Your request was received.')
                return redirect('store:request-refund')

            except ObjectDoesNotExist:
                messages.warning(self.request, 'This order does not exist.')
                return redirect('store:request-refund')
