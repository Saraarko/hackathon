from django.urls import path
from . import views

urlpatterns = [
    path('auteurs/', views.auteurs, name='auteurs'),
    path('livres/', views.livres, name='livres'),
    path('emprunts/', views.emprunts, name='emprunts'),
]
