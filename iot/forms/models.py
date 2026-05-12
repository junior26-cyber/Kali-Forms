from django.db import models
from django.contrib.auth.models import User

# --- Modèles Principaux KaliForms ---

class Sondage(models.Model):
    """Représente un formulaire/sondage créé par un utilisateur."""
    title = models.CharField(max_length=255, verbose_name="Titre")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sondages')
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    def __str__(self):
        return self.title

class Question(models.Model):
    """Une question spécifique au sein d'un sondage."""
    QUESTION_TYPES = (
        ('text', 'Texte court'),
        ('textarea', 'Texte long'),
        ('radio', 'Choix multiple'),
        ('checkbox', 'Cases à cocher'),
        ('select', 'Liste déroulante'),
        ('boolean', 'Oui/Non'),
    )
    sondage = models.ForeignKey(Sondage, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=500, verbose_name="Texte de la question")
    type = models.CharField(max_length=20, choices=QUESTION_TYPES, verbose_name="Type de question")
    is_required = models.BooleanField(default=False, verbose_name="Obligatoire")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.sondage.title} - {self.text}"

class Option(models.Model):
    """Option de réponse pour les questions de type choix multiple, cases à cocher, etc."""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255, verbose_name="Texte de l'option")

    def __str__(self):
        return self.text

class Response(models.Model):
    """Instance unique de soumission d'un sondage par un répondant."""
    sondage = models.ForeignKey(Sondage, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Réponse à {self.sondage.title} le {self.created_at}"

class Answer(models.Model):
    """Réponse individuelle à une question spécifique dans une soumission."""
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text_value = models.TextField(blank=True, null=True, verbose_name="Réponse textuelle")
    selected_options = models.ManyToManyField(Option, blank=True, verbose_name="Options sélectionnées")

    def __str__(self):
        return f"Réponse à {self.question.text}"
