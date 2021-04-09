from typing import io

from django import forms

from ConcorsoBiblioteca.utils import id_active_event
from gestore.models import events
from .models import valutatore
from ConcorsoBiblioteca.restserviceeese3 import dipendente_email, studente_email


class valutatoreModelForm(forms.ModelForm):
    """Classe valutatore"""
    idUser = forms.CharField(label="Email valutatore", required=True, min_length=1)

    # def __init__(self, *args, **kwargs):
    #     super(valutatoreModelForm, self).__init__(*args, **kwargs)
    #     self.fields["idUser"].validators = [MinLengthValidator(1)]



    # Validazione form
    def clean(self):
        cleaned_data = super().clean()
        _idUser = cleaned_data.get("idUser")

        # print("idUser", _idUser)

        if _idUser == "":
            self.add_error("idUser", "Utente vuoto non valido")

        # Controllo che sia un dipendente o uno studente valido in esse3
        res = dipendente_email(_idUser)

        if res is None:
            res = studente_email(_idUser)
            if res is None:
                self.add_error("idUser", "Utente non valido")

        # # Controllo che non sia già stato inserito per questo evento
        # id_event = id_active_event()
        # count = valutatore.objects.filter(idUser=_idUser, idEvent=id_event).count()
        # #print(count)
        # if count > 0:
        #     self.add_error("idUser", "Utente già inserito come valutatore per questo concorso")

    class Meta:
        model = valutatore
        fields = ["idUser"]


