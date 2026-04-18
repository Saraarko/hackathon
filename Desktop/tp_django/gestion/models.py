from django.db import models


class Auteur(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField(null=True, blank=True)
    biographie = models.TextField(blank=True)

    def __str__(self):
        return f"{self.prenom} {self.nom}"


class Livre(models.Model):
    titre = models.CharField(max_length=200)
    date_publication = models.DateField(null=True, blank=True)
    auteur = models.ForeignKey(Auteur, on_delete=models.CASCADE)
    resume = models.TextField(blank=True)

    def __str__(self):
        return self.titre


class Emprunt(models.Model):
    livre = models.ForeignKey(Livre, on_delete=models.CASCADE)
    utilisateur = models.CharField(max_length=100)
    date_emprunt = models.DateField(auto_now_add=True)
    date_retour_prevue = models.DateField(null=True, blank=True)
    date_retour_effective = models.DateField(null=True, blank=True)
    retourne = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.utilisateur} - {self.livre.titre}"
