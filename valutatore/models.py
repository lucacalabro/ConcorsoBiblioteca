from django.db import models
from autore.models import racconti
from gestore.models import events
from django.urls import reverse


class valutatore(models.Model):
    idUser = models.EmailField(null=False, max_length=64, blank=False)
    surname = models.CharField(max_length=64, null=False)
    forename = models.CharField(max_length=64, null=False)
    idEvent = models.ForeignKey(events, related_name='valutatoriconcorso', on_delete=models.CASCADE)

    class Meta:
        # app_label = 'valutatore'
        ordering = ["-idUser"]

    def __str__(self):
        return self.idUser

    # def get_absolute_url(self):
    #     return reverse('update_event', kwargs={'pk': self.pk})


class valutazione(models.Model):
    idRacconto = models.ForeignKey(racconti, related_name='raccontovalutazione', on_delete=models.CASCADE)
    idValutatore = models.ForeignKey(valutatore, related_name='valutatorevalutazione', on_delete=models.CASCADE)
    selected = models.BooleanField(default=True)
    ranking = models.IntegerField()

    class Meta:
        app_label = 'valutatore'
        ordering = ["-idRacconto"]
