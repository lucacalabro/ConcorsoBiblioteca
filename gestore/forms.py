from django import forms
from .models import events


class eventsModelForm(forms.ModelForm):
    """Classe eventi"""
    eventName = forms.CharField(label="Titolo concorso", max_length=256)

    maxSubmissions = forms.DecimalField(min_value=0, label="Numero massimo di racconti inviabili", )

    maxSelections = forms.DecimalField(min_value=0, label="Numero massimo di racconti selezionabili", )

    submissionDateStart = forms.DateTimeField(widget=forms.widgets.DateInput(attrs={'type': 'date'}),
                                              label="Data inizio invio racconti")
    submissionDateEnd = forms.DateTimeField(widget=forms.widgets.DateInput(attrs={'type': 'date'}),
                                            label="Data fine invio racconti")

    selectionDateStart = forms.DateTimeField(widget=forms.widgets.DateInput(attrs={'type': 'date'}),
                                             label="Data inizio selezioni racconti")
    selectionDateEnd = forms.DateTimeField(widget=forms.widgets.DateInput(attrs={'type': 'date'}),
                                           label="Data fine selezioni racconti")

    classificationDateStart = forms.DateTimeField(widget=forms.widgets.DateInput(attrs={'type': 'date'}),
                                                  label="Data inizio classificazione racconti")
    classificationDateEnd = forms.DateTimeField(widget=forms.widgets.DateInput(attrs={'type': 'date'}),
                                                label="Data fine classificazione racconti")

    birthDateLimit = forms.DateTimeField(widget=forms.widgets.DateInput(attrs={'type': 'date'}),
                                         label="Limite data di nascita (i racconti inviati da autori nati prima di questa data saranno classificati nella categoria Senior)")

    # Validazione form
    def clean(self):
        cleaned_data = super().clean()
        _maxSubmissions = cleaned_data.get("maxSubmissions")
        _maxSelections = cleaned_data.get("maxSelections")
        _submissionDateStart = cleaned_data.get("submissionDateStart")
        _submissionDateEnd = cleaned_data.get("submissionDateEnd")
        _selectionDateStart = cleaned_data.get("selectionDateStart")
        _selectionDateEnd = cleaned_data.get("selectionDateEnd")
        _classificationDateStart = cleaned_data.get("classificationDateStart")
        _classificationDateEnd = cleaned_data.get("classificationDateEnd")
        _birthDateLimit = cleaned_data.get("birthDateLimit")

        # Validazione numero racconti selezionabili
        if _maxSubmissions is not None and _maxSelections is not None and (
                _maxSubmissions <= _maxSelections):
            self.add_error("maxSelections",
                           "Il numero di racconti selezionabili non può essere maggiore del massimo numero di inviabili.")

        # Validazione data inizio selezioni
        if _selectionDateStart is not None and _submissionDateStart is not None and (
                _selectionDateStart <= _submissionDateStart):
            self.add_error("selectionDateStart",
                           "La data di inizio selezione racconti non può essere precedente o uguale alla data di inizio invio.")

        # Validazione data inizio classificazioni
        if _classificationDateStart is not None and _submissionDateStart is not None and (
                _classificationDateStart <= _submissionDateStart):
            self.add_error("classificationDateStart",
                           "La data di inizio classificazione racconti non può essere precedente o uguale alla data di inizio invio.")

        # Validazione data fine sottomissioni
        if _submissionDateEnd is not None and _submissionDateStart is not None and (
                _submissionDateEnd <= _submissionDateStart):
            self.add_error("submissionDateEnd",
                           "La data di fine invio racconti non può essere precedente o uguale alla data di inizio invio.")

        # Validazione data fine selezioni
        if _selectionDateEnd is not None and _selectionDateStart is not None and (
                _selectionDateEnd <= _selectionDateStart):
            self.add_error("selectionDateEnd",
                           "La data di fine selezioni racconti non può essere precedente o uguale alla data di inizio selezione.")

        # Validazione data fine classificazioni
        if _classificationDateEnd is not None and _classificationDateStart is not None and (
                _classificationDateEnd <= _classificationDateStart):
            self.add_error("classificationDateEnd",
                           "La data di fine classificazion racconti non può essere precedente o uguale alla data di inizio classificazione.")

        # Controllo che il nuovo evento non si sovrapponga ad uno precedentemente creato
        data_inizio = _submissionDateStart
        data_fine = _classificationDateEnd

        # for e in events.objects.all():
        #     print(e.submissionDateStart)
        #     print(e.selectionDateEnd)

        for e in events.objects.all():
            if data_inizio is not None and (
                    data_inizio >= e.submissionDateStart and data_inizio <= e.classificationDateEnd):
                self.add_error("submissionDateStart",
                               "La data di inizio concorso ricade dentro l'intervallo di un concorso precedentemente creato.")

        for e in events.objects.all():
            if data_fine is not None and (data_fine >= e.submissionDateStart and data_fine <= e.classificationDateEnd):
                self.add_error("classificationDateEnd",
                               "La data di fine concorso ricade dentro l'intervallo di un concorso precedentemente creato.")

    class Meta:
        model = events
        fields = "__all__"
