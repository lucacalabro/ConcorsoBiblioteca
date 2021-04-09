from django.db import models
from django.urls import reverse


class events(models.Model):
    eventName = models.CharField("Titolo concorso", max_length=256, null=False)
    maxSubmissions = models.DecimalField("Numero massimo di racconti inviabili", decimal_places=0, max_digits=3,
                                         default=0, null=False)
    maxSelections = models.DecimalField("Numero massimo di racconti selezionabili", decimal_places=0, max_digits=3,
                                        default=0, null=False)
    submissionDateStart = models.DateTimeField("Data inizio invio racconti", null=False)
    submissionDateEnd = models.DateTimeField("Data fine invio racconti", null=False)
    selectionDateStart = models.DateTimeField("Data inizio selezioni racconti", null=False)
    selectionDateEnd = models.DateTimeField("Data fine selezioni racconti", null=False)
    classificationDateStart = models.DateTimeField("Data inizio classificazione racconti", null=False)
    classificationDateEnd = models.DateTimeField("Data fine classificazione racconti", null=False)
    birthDateLimit = models.DateTimeField(
        "Limite data di nascita (i racconti inviati da autori nati prima di questa data saranno classificati nella categoria Senior)",
        null=False)

    class Meta:
        # app_label = 'events'
        ordering = ["submissionDateStart"]

    def __str__(self):
        return self.eventName

    def get_absolute_url(self):
        return reverse('update_event', kwargs={'pk': self.pk})


class gestore(models.Model):
    username = models.CharField(max_length=256, null=False)

    def __str__(self):
        return self.username

    class Meta:
        # app_label = 'events'
        ordering = ["username"]


class log(models.Model):
    username = models.CharField(max_length=256, null=False)
    operationDate = models.DateTimeField(null=False)
    roleUser = models.CharField(max_length=256, null=True)
    type = models.CharField(max_length=256, null=True)
    description = models.CharField(max_length=1024, null=True)

