from django.shortcuts import render


def accueil(request):
    nb_visites = request.session.get('visites', 0) + 1
    request.session['visites'] = nb_visites

    context = {
        'visites': nb_visites
    }
    return render(request, 'accueil.html', context)