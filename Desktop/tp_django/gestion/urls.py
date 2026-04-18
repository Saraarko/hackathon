from django.urls import path
from . import views

urlpatterns = [
    # ============================================
    # URLs POUR AUTEUR (VUES FONCTIONNELLES)
    # ============================================
    path('auteurs/', views.liste_auteurs, name='liste_auteurs'),
    path('auteurs/creer/', views.creer_auteur, name='creer_auteur'),
    path('auteurs/<int:id>/', views.detail_auteur, name='detail_auteur'),
    path('auteurs/<int:id>/modifier/', views.modifier_auteur, name='modifier_auteur'),
    path('auteurs/<int:id>/supprimer/', views.supprimer_auteur, name='supprimer_auteur'),

    # ============================================
    # URLs POUR LIVRE (VUES CLASSES)
    # ============================================
    path('livres/', views.ListeLivresView.as_view(), name='liste_livres'),
    path('livres/<int:id>/', views.DetailLivreView.as_view(), name='detail_livre'),

    # ============================================
    # URLs POUR EMPRUNT (EXERCICE 1 - VUES FONCTIONNELLES)
    # ============================================
    path('emprunts/', views.liste_emprunts, name='liste_emprunts'),
    path('emprunts/creer/', views.creer_emprunt, name='creer_emprunt'),
    path('emprunts/<int:id>/', views.detail_emprunt, name='detail_emprunt'),
    path('emprunts/<int:id>/retourner/', views.retourner_emprunt, name='retourner_emprunt'),
    path('emprunts/<int:id>/supprimer/', views.supprimer_emprunt, name='supprimer_emprunt'),

    # ============================================
    # URLs POUR EMPRUNT (EXERCICE 2 - VUES CLASSES)
    # ============================================
    path('emprunts-class/', views.ListeEmpruntsView.as_view(), name='liste_emprunts_class'),
    path('emprunts-class/<int:id>/', views.DetailEmpruntView.as_view(), name='detail_emprunt_class'),

    # ============================================
    # Routes SUPPLÉMENTAIRES (EXERCICE 3)
    # ============================================
    path('livres/auteur/<int:auteur_id>/', views.livres_par_auteur, name='livres_par_auteur'),
    path('emprunts/utilisateur/<str:nom>/', views.emprunts_par_utilisateur, name='emprunts_par_utilisateur'),
]
