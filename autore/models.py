from django.db import models

from gestore.models import events


class racconti(models.Model):
    counter = models.IntegerField()
    idUser = models.EmailField(null=False, max_length=64)
    idEvent = models.ForeignKey(events, on_delete=models.DO_NOTHING)
    title = models.CharField(max_length=128)
    content = models.TextField(max_length=8000)
    submissionDate = models.DateTimeField(null=False)
    publishingPermission = models.BooleanField(default=True, null=False)
    contacts = models.CharField(max_length=128, null=False)
    coAuthors = models.TextField(max_length=8000, null=True)
    authorSurname = models.CharField(max_length=64, null=False)
    authorForename = models.CharField(max_length=64, null=False)
    authorBirthDate = models.DateTimeField(null=False)
    authorStatus = models.CharField(max_length=64, null=False)
    authorDetail = models.CharField(max_length=64, null=False)

    class Meta:
        #app_label = 'racconti'
        ordering = ["-counter"]

    def __str__(self):
        return self.title
