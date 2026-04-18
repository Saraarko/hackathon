from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required(login_url='login')
def auteurs(request):
    return render(request, 'auteurs.html')


@login_required(login_url='login')
def livres(request):
    return render(request, 'livres.html')


@login_required(login_url='login')
def emprunts(request):
    return render(request, 'emprunts.html')
