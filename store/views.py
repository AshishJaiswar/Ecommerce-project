from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.contrib.auth import login, logout, authenticate
from django.http import JsonResponse
from .models import *
import json
import datetime
from .utils import cookieCart, cartData, guestOrder
def store(request):
    data = cartData(request)
    cartItems = data['cartItems']
  

    products = Product.objects.all()
    context = {'products':products, 'cartItems':cartItems}
    return render(request, 'store/store.html', context)


def cart(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
        
    context = {'items':items, 'order':order, 'cartItems':cartItems }
    return render(request, 'store/cart.html', context)


def checkout(request):

    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items':items, 'order':order, 'cartItems':cartItems}
    return render(request, 'store/checkout.html', context)

def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    print('productId:', productId)
    print('action:', action)

    customer = request.user.customer
    product = Product.objects.get(id=productId)

    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)
    print(orderItem)
    if action == 'add':
        orderItem.quantity= (orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)
    
    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse("Item was added", safe=False)


def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer, complete=False)
        

    else:
        customer, order = guestOrder(request, data)

    total = float(data['form']['total'])
    order.transaction_id = transaction_id

    if total == order.get_cart_total:
        order.complete = True
    order.save()

    if order.shipping == True:
        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address= data['shipping']['address'],
            city = data['shipping']['city'], 
            state = data['shipping']['state'], 
            zipcode = data['shipping']['zipcode'],
        )
    return JsonResponse("Payment completed", safe=False)


def signupuser(request):
    if request.method == 'GET':
        return render(request, 'store/signup.html', {'form':UserCreationForm})
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                user = User.objects.create_user(request.POST['username'], 
                password=request.POST['password1'])
                user.save()
                login(request,user)
                return redirect('store')
            except IntegrityError:
                return render(request, 'store/signup.html', {'form':UserCreationForm, 
                'error':'Username Already taken please choose another username'})
        else:
            return render(request, 'todo/signup.html', {'form':UserCreationForm, 
            'error':'Password do not match'})

def logoutuser(request):
    if request.method == 'POST':
        logout(request)
        return redirect('store')



def loginuser(request):
    if request.method == 'GET':
        return render(request, 'store/login.html', {'form':AuthenticationForm})
    else:
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            return render(request, 'store/login.html', {'form':AuthenticationForm, 'error':'Invalid username and password'})
        else:
            login(request, user)
            return redirect('store')
