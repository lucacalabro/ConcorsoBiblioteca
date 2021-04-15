from django import forms
from ConcorsoBiblioteca.restserviceeese3 import dipendente_email, studente_email
from ConcorsoBiblioteca.settings import CATEGORIE_ETA
from .models import segretario


class segretarioModelForm(forms.ModelForm):
    """Classe segretario"""
    idUser = forms.CharField(label="Email segretario", required=True, min_length=1)

    # Validazione form
    def clean(self):
        cleaned_data = super().clean()
        _idUser = cleaned_data.get("idUser")

        # print("idUser", _idUser)

        # Controllo che sia un dipendente o uno studente valido in esse3
        res = dipendente_email(_idUser)

        if res is None:
            res = studente_email(_idUser)
            if res is None:
                self.add_error("idUser", "Utente non valido")

    class Meta:
        model = segretario
        fields = ["idUser"]

#aria-label="
class MailForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Campi aggiunti non appartenenti al model
        self.fields['destinatari'] = forms.ChoiceField(widget=forms.RadioSelect(),
                                                       initial=False,
                                                       choices=[("Tutti", 'Tutti i membri della commissione'), (
                                                           "Selezioni",
                                                           'Solo i membri della commissione che non hanno selezionato il numero massimo di racconti.'),
                                                                ("Valutazioni",
                                                                 'Solo i membri della commissione che non hanno effettuato tutte le valutazioni per i racconti della categoria {J} e/o {S}'.format(
                                                                     J=CATEGORIE_ETA[0], S=CATEGORIE_ETA[1]))],
                                                       label='Destinatari',
                                                       required=True)
        self.fields['subject'] = forms.CharField(label='Subject', max_length=256, required=True)
        self.fields['body'] = forms.CharField(
            widget=forms.Textarea(attrs={'rows': 10, 'id': "body", }),
            label="Testo email", required=True
        )
