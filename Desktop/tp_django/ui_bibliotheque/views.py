from django.shortcuts import render


def auteurs(request):
    return render(request, 'auteurs.html')


def livres(request):
    return render(request, 'livres.html')


def emprunts(request):
    return render(request, 'emprunts.html')
