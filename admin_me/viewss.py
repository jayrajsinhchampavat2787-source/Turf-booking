from django.shortcuts import render
from .models import Product
# Create your views here.
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from datetime import date

def login_view(request):
    if request.method == 'POST':
        uname = request.POST['username']
        pwd = request.POST['password']
        user = authenticate(request, username=uname, password=pwd)
        if user is not None:
            login(request, user)
            return redirect('index2')  # use your actual dashboard URL name
        else:
            return render(request, 'login2.html', {'form': {'errors': True}})
    return render(request, 'login2.html', {})

def index(request):
    return render(request, 'index2.html')

def accounts(request):
    return render(request, 'accounts.html')