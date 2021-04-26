from django import forms
from .models import racconti
from ConcorsoBiblioteca.settings import MAX_NUM_CHAR


class raccontiModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'] = forms.CharField(label="Titolo del racconto", max_length=128)
        self.fields['content'] = forms.CharField(
            widget=forms.Textarea(attrs={'rows': 20, 'maxlength': MAX_NUM_CHAR, 'id': "content", 'onkeyup': "foo()"}),
            label="Testo del racconto ANONIMO (massimo " + str(MAX_NUM_CHAR) + " caratteri)",
        )
        self.fields['contacts'] = forms.CharField(label="Recapito telefonico", max_length=128)
        self.fields['coAuthors'] = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'maxlength': 8000}),
                                                   label="Coautori in caso di testo collettivo (nome, cognome"
                                                         " e indirizzo email istituzionale)",
                                                   required=False)
        self.fields['publishingPermission'] = forms.ChoiceField(widget=forms.CheckboxInput(),  # .RadioSelect(),
                                                                initial=False, choices=[(True, 'Si'), (False, 'No')],
                                                                label='Autorizzo la Biblioteca di Ateneo alla pubblicazione del mio racconto',
                                                                required=False)

        # Campi aggiunti non appartenenti al model
        self.fields['visioneregolamento'] = forms.ChoiceField(widget=forms.CheckboxInput(),  # .RadioSelect(),
                                                              initial=False, choices=[(True, 'Si'), (False, 'No')],
                                                              label="Dichiaro di aver preso visione del regolamento del concorso e di accettare le condizioni <a aria-labelledby='Sito web esterno - informativa regolamento concorso'  href='https://www.biblio.unimib.it/it/terza-missione/concorso-letterario' target='_blank'>LINK</a>",
                                                              required=True)
        self.fields['visioneinformativa'] = forms.ChoiceField(widget=forms.CheckboxInput(),  # .RadioSelect(),
                                                              initial=False, choices=[(True, 'Si'), (False, 'No')],
                                                              label="Dichiaro di aver preso visione dell'informativa privacy all'indirizzo <a aria-labelledby='Sito web esterno - informativa privacy' href = 'https://www.unimib.it/sites/default/files/allegati/informativa_eventi_e_iniziative.pdf' target = '_blank' >LINK</a>",
                                                              required=True)

    # title = forms.CharField(label="Titolo del racconto", max_length=128)
    # content = forms.CharField(widget=forms.Textarea(attrs={'rows': 20, 'maxlength': 8000}),
    #                           label="Testo del racconto ANONIMO (massimo 8000 caratteri)")
    # contacts = forms.CharField(label="Recapito telefonico", max_length=128)
    # coAuthors = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'maxlength': 8000}),
    #                             label="Coautori in caso di testo collettivo (nome, cognome"
    #                                   " e indirizzo email istituzionale)",
    #                             required=False)
    #
    # publishingPermission = forms.ChoiceField(widget=forms.RadioSelect,
    #                                          initial=False, choices=[(True, 'Si'), (False, 'No')],
    #                                          label='Autorizzo la pubblicazione dei racconti '
    #                                                'sul sito della Biblioteca di Ateneo',
    #                                          required=False)

    # Validazione form
    def clean(self):
        cleaned_data = super().clean()
        _visioneregolamento = eval(cleaned_data.get("visioneregolamento"))
        _visioneinformativa = eval(cleaned_data.get("visioneinformativa"))
        _numero_caratteri_inserito = cleaned_data.get("content")

        if _numero_caratteri_inserito is not None:
            _numero_caratteri_inserito = cleaned_data.get("content").replace("\r\n", "").replace("\r", "").replace("\n","")

        # if _numero_caratteri_inserito is not None:
        #     print("Numero caratteri inserito", len(_numero_caratteri_inserito))
        #     print(_numero_caratteri_inserito)
        # else:
        #     print("None")

        # Validazione data inizio selezioni
        if not _visioneregolamento:
            self.add_error("visioneregolamento", "Visione regolamento non dichiarata")

        if not _visioneinformativa:
            self.add_error("visioneinformativa", "Visione informativa non dichiarata")

        if _numero_caratteri_inserito is not None and len(_numero_caratteri_inserito) > MAX_NUM_CHAR:
            self.add_error("content", "Superato il numero di " + str(MAX_NUM_CHAR) + " caratteri.")

    class Meta:
        model = racconti
        fields = ['title', 'content', 'contacts', 'coAuthors', 'publishingPermission']
