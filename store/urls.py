from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('product/<slug>/', views.ItemDetailsView.as_view(), name='product'),
    path('checkout_page/', views.CheckoutView.as_view(), name='checkout'),
    path('order_summary/', views.OrderSummaryView.as_view(), name='order_summary'),
    path('add_cart/<slug>/', views.add_cart, name='add_cart'),
    path('remove_cart/<slug>/', views.remove_cart, name='remove_cart'),
    path('remove_single_cart/<slug>/', views.remove_single_cart, name='remove_single_cart'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('signup/', views.signup, name='signup'),
    path('admin/', views.admin, name='admin'),
    path('payment/<payment_option>/', views.PaymentView.as_view(), name='payment'),
    path('add_coupon/', views.AddCouponView.as_view(), name='add_coupon'),
    path('request-refund/', views.RequestRefundView.as_view(), name='request-refund'),
]
