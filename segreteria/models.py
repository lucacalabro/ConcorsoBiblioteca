from django.db import models


class segretario(models.Model):
    idUser = models.EmailField(null=False, max_length=64, blank=False)
    surname = models.CharField(max_length=64, null=False)
    forename = models.CharField(max_length=64, null=False)

    class Meta:
        #app_label = 'segreteria'
        ordering = ["-idUser"]

    def __str__(self):
        return self.idUser

    # def get_absolute_url(self):
    #     return reverse('update_event', kwargs={'pk': self.pk})

