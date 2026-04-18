from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.views import View
from django.utils.decorators import method_decorator
import json
from .models import Auteur, Livre, Emprunt


# ============================================
# VUES FONCTIONNELLES POUR AUTEUR
# ============================================

def liste_auteurs(request):
    """GET : Retourne la liste de tous les auteurs"""
    auteurs = Auteur.objects.all()
    data = [
        {
            'id': auteur.id,
            'nom': auteur.nom,
            'prenom': auteur.prenom,
            'date_naissance': auteur.date_naissance,
            'biographie': auteur.biographie
        }
        for auteur in auteurs
    ]
    return JsonResponse(data, safe=False)


def detail_auteur(request, id):
    """GET : Retourne les détails d'un auteur spécifique"""
    auteur = get_object_or_404(Auteur, id=id)
    data = {
        'id': auteur.id,
        'nom': auteur.nom,
        'prenom': auteur.prenom,
        'date_naissance': auteur.date_naissance,
        'biographie': auteur.biographie
    }
    return JsonResponse(data)


@csrf_exempt
def creer_auteur(request):
    """POST : Crée un nouvel auteur"""
    if request.method != 'POST':
        return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)

    try:
        data = json.loads(request.body)
        auteur = Auteur.objects.create(
            nom=data.get('nom'),
            prenom=data.get('prenom'),
            date_naissance=data.get('date_naissance'),
            biographie=data.get('biographie', '')
        )
        return JsonResponse({
            'id': auteur.id,
            'message': 'Auteur créé avec succès'
        }, status=201)
    except Exception as e:
        return JsonResponse({'erreur': str(e)}, status=400)


@csrf_exempt
def modifier_auteur(request, id):
    """PUT : Modifie un auteur existant"""
    if request.method != 'PUT':
        return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)

    auteur = get_object_or_404(Auteur, id=id)
    try:
        data = json.loads(request.body)
        auteur.nom = data.get('nom', auteur.nom)
        auteur.prenom = data.get('prenom', auteur.prenom)
        auteur.date_naissance = data.get('date_naissance', auteur.date_naissance)
        auteur.biographie = data.get('biographie', auteur.biographie)
        auteur.save()

        return JsonResponse({'message': 'Auteur modifié avec succès'})
    except Exception as e:
        return JsonResponse({'erreur': str(e)}, status=400)


@csrf_exempt
def supprimer_auteur(request, id):
    """DELETE : Supprime un auteur"""
    if request.method != 'DELETE':
        return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)

    auteur = get_object_or_404(Auteur, id=id)
    auteur.delete()
    return JsonResponse({'message': 'Auteur supprimé avec succès'}, status=204)


# ============================================
# VUES CLASSES POUR LIVRE
# ============================================

@method_decorator(csrf_exempt, name='dispatch')
class ListeLivresView(View):
    """GET : Liste tous les livres"""
    def get(self, request):
        livres = Livre.objects.all()
        data = [
            {
                'id': livre.id,
                'titre': livre.titre,
                'date_publication': livre.date_publication,
                'auteur_id': livre.auteur_id,
                'resume': livre.resume
            }
            for livre in livres
        ]
        return JsonResponse(data, safe=False)

    """POST : Crée un nouveau livre"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            livre = Livre.objects.create(
                titre=data.get('titre'),
                date_publication=data.get('date_publication'),
                auteur_id=data.get('auteur_id'),
                resume=data.get('resume', '')
            )
            return JsonResponse({
                'id': livre.id,
                'message': 'Livre créé avec succès'
            }, status=201)
        except Exception as e:
            return JsonResponse({'erreur': str(e)}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class DetailLivreView(View):
    """GET : Récupère un livre spécifique"""
    def get(self, request, id):
        livre = get_object_or_404(Livre, id=id)
        data = {
            'id': livre.id,
            'titre': livre.titre,
            'date_publication': livre.date_publication,
            'auteur_id': livre.auteur_id,
            'auteur_nom': f"{livre.auteur.prenom} {livre.auteur.nom}",
            'resume': livre.resume
        }
        return JsonResponse(data)

    """PUT : Modifie un livre"""
    def put(self, request, id):
        livre = get_object_or_404(Livre, id=id)
        try:
            data = json.loads(request.body)
            livre.titre = data.get('titre', livre.titre)
            livre.date_publication = data.get('date_publication', livre.date_publication)
            livre.auteur_id = data.get('auteur_id', livre.auteur_id)
            livre.resume = data.get('resume', livre.resume)
            livre.save()

            return JsonResponse({'message': 'Livre modifié avec succès'})
        except Exception as e:
            return JsonResponse({'erreur': str(e)}, status=400)

    """DELETE : Supprime un livre"""
    def delete(self, request, id):
        livre = get_object_or_404(Livre, id=id)
        livre.delete()
        return JsonResponse({'message': 'Livre supprimé avec succès'}, status=204)


# ============================================
# VUES FONCTIONNELLES POUR EMPRUNT (Exercice 1)
# ============================================

def liste_emprunts(request):
    """GET : Retourne tous les emprunts"""
    emprunts = Emprunt.objects.all()
    data = [
        {
            'id': emprunt.id,
            'livre_id': emprunt.livre_id,
            'livre_titre': emprunt.livre.titre,
            'utilisateur': emprunt.utilisateur,
            'date_emprunt': emprunt.date_emprunt,
            'date_retour_prevue': emprunt.date_retour_prevue,
            'date_retour_effective': emprunt.date_retour_effective,
            'retourne': emprunt.retourne
        }
        for emprunt in emprunts
    ]
    return JsonResponse(data, safe=False)


def detail_emprunt(request, id):
    """GET : Retourne un emprunt spécifique"""
    emprunt = get_object_or_404(Emprunt, id=id)
    data = {
        'id': emprunt.id,
        'livre_id': emprunt.livre_id,
        'livre_titre': emprunt.livre.titre,
        'utilisateur': emprunt.utilisateur,
        'date_emprunt': emprunt.date_emprunt,
        'date_retour_prevue': emprunt.date_retour_prevue,
        'date_retour_effective': emprunt.date_retour_effective,
        'retourne': emprunt.retourne
    }
    return JsonResponse(data)


@csrf_exempt
def creer_emprunt(request):
    """POST : Crée un nouvel emprunt"""
    if request.method != 'POST':
        return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)

    try:
        data = json.loads(request.body)
        emprunt = Emprunt.objects.create(
            livre_id=data.get('livre_id'),
            utilisateur=data.get('utilisateur'),
            date_retour_prevue=data.get('date_retour_prevue')
        )
        return JsonResponse({
            'id': emprunt.id,
            'message': 'Emprunt créé avec succès'
        }, status=201)
    except Exception as e:
        return JsonResponse({'erreur': str(e)}, status=400)


@csrf_exempt
def retourner_emprunt(request, id):
    """PUT : Marque un emprunt comme retourné"""
    if request.method != 'PUT':
        return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)

    emprunt = get_object_or_404(Emprunt, id=id)
    try:
        data = json.loads(request.body)
        emprunt.date_retour_effective = data.get('date_retour_effective')
        emprunt.retourne = True
        emprunt.save()

        return JsonResponse({'message': 'Emprunt marqué comme retourné'})
    except Exception as e:
        return JsonResponse({'erreur': str(e)}, status=400)


@csrf_exempt
def supprimer_emprunt(request, id):
    """DELETE : Supprime un emprunt"""
    if request.method != 'DELETE':
        return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)

    emprunt = get_object_or_404(Emprunt, id=id)
    emprunt.delete()
    return JsonResponse({'message': 'Emprunt supprimé avec succès'}, status=204)


# ============================================
# VUES CLASSES POUR EMPRUNT (Exercice 2)
# ============================================

@method_decorator(csrf_exempt, name='dispatch')
class ListeEmpruntsView(View):
    """GET : Liste tous les emprunts"""
    def get(self, request):
        emprunts = Emprunt.objects.all()
        data = [
            {
                'id': emprunt.id,
                'livre_id': emprunt.livre_id,
                'livre_titre': emprunt.livre.titre,
                'utilisateur': emprunt.utilisateur,
                'date_emprunt': emprunt.date_emprunt,
                'date_retour_prevue': emprunt.date_retour_prevue,
                'date_retour_effective': emprunt.date_retour_effective,
                'retourne': emprunt.retourne
            }
            for emprunt in emprunts
        ]
        return JsonResponse(data, safe=False)

    """POST : Crée un nouvel emprunt"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            emprunt = Emprunt.objects.create(
                livre_id=data.get('livre_id'),
                utilisateur=data.get('utilisateur'),
                date_retour_prevue=data.get('date_retour_prevue')
            )
            return JsonResponse({
                'id': emprunt.id,
                'message': 'Emprunt créé avec succès'
            }, status=201)
        except Exception as e:
            return JsonResponse({'erreur': str(e)}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class DetailEmpruntView(View):
    """GET : Récupère un emprunt spécifique"""
    def get(self, request, id):
        emprunt = get_object_or_404(Emprunt, id=id)
        data = {
            'id': emprunt.id,
            'livre_id': emprunt.livre_id,
            'livre_titre': emprunt.livre.titre,
            'utilisateur': emprunt.utilisateur,
            'date_emprunt': emprunt.date_emprunt,
            'date_retour_prevue': emprunt.date_retour_prevue,
            'date_retour_effective': emprunt.date_retour_effective,
            'retourne': emprunt.retourne
        }
        return JsonResponse(data)

    """PUT : Marque un emprunt comme retourné"""
    def put(self, request, id):
        emprunt = get_object_or_404(Emprunt, id=id)
        try:
            data = json.loads(request.body)
            emprunt.date_retour_effective = data.get('date_retour_effective', emprunt.date_retour_effective)
            emprunt.retourne = True
            emprunt.save()

            return JsonResponse({'message': 'Emprunt marqué comme retourné'})
        except Exception as e:
            return JsonResponse({'erreur': str(e)}, status=400)

    """DELETE : Supprime un emprunt"""
    def delete(self, request, id):
        emprunt = get_object_or_404(Emprunt, id=id)
        emprunt.delete()
        return JsonResponse({'message': 'Emprunt supprimé avec succès'}, status=204)


# ============================================
# ROUTES SUPPLÉMENTAIRES (Exercice 3)
# ============================================

def livres_par_auteur(request, auteur_id):
    """GET : Tous les livres d'un auteur"""
    livres = Livre.objects.filter(auteur_id=auteur_id)
    data = [
        {
            'id': livre.id,
            'titre': livre.titre,
            'date_publication': livre.date_publication,
            'auteur_id': livre.auteur_id,
            'resume': livre.resume
        }
        for livre in livres
    ]
    return JsonResponse(data, safe=False)


def emprunts_par_utilisateur(request, nom):
    """GET : Tous les emprunts d'un utilisateur"""
    emprunts = Emprunt.objects.filter(utilisateur__icontains=nom)
    data = [
        {
            'id': emprunt.id,
            'livre_id': emprunt.livre_id,
            'livre_titre': emprunt.livre.titre,
            'utilisateur': emprunt.utilisateur,
            'date_emprunt': emprunt.date_emprunt,
            'date_retour_prevue': emprunt.date_retour_prevue,
            'date_retour_effective': emprunt.date_retour_effective,
            'retourne': emprunt.retourne
        }
        for emprunt in emprunts
    ]
    return JsonResponse(data, safe=False)


# ============================================
# VIEWSETS AVEC DJANGO REST FRAMEWORK (TP4)
# ============================================

from rest_framework import viewsets
from .serializers import AuteurSerializer, LivreSerializer, EmpruntSerializer


class AuteurViewSet(viewsets.ModelViewSet):
    queryset = Auteur.objects.all()
    serializer_class = AuteurSerializer


class LivreViewSet(viewsets.ModelViewSet):
    queryset = Livre.objects.all()
    serializer_class = LivreSerializer


class EmpruntViewSet(viewsets.ModelViewSet):
    queryset = Emprunt.objects.all()
    serializer_class = EmpruntSerializer
