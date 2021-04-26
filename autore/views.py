from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import render
from allauth.account.decorators import login_required
from django.urls import reverse

from ConcorsoBiblioteca.mailer import emailsender
from .forms import raccontiModelForm
from ConcorsoBiblioteca.utils import id_active_event, is_active_event_submittible, get_counter, \
    is_submitted_in_active_event, get_permission
from gestore.models import events
from autore.models import racconti
from ConcorsoBiblioteca.restserviceeese3 import studente_email, dipendente_email
from datetime import datetime, date
from codicefiscale import codicefiscale
from ConcorsoBiblioteca.settings import MAX_NUM_CHAR
from ConcorsoBiblioteca.utils import insert_log


# Create your views here.

# Crea un evento
@login_required
def create_racconto(request):
    # Controllo se c'è un concorso attivo
    idEvent = id_active_event()
    permissions = get_permission(request.user.email)

    if idEvent is not None:
        # Calcolo informazioni del concorso da passare alla template
        is_submittable = is_active_event_submittible()  # Controllo se è possibile fare invio racconto
        titolo_concorso = events.objects.all().get(pk=idEvent).eventName

        # Controllo se l'autore ha già sottomesso il racconto
        # in questo caso mostrerà il form solo in lettura
        # CASO RACCONTO INVIATO
        if is_submitted_in_active_event(request.user.email):
            # print("RACCONTO INVIATO")
            racconto_inviato = racconti.objects.filter(idEvent=id_active_event(), idUser=request.user.email)[0]
            # Costruisco il form da inviare per mostrare i dati del racconto
            form = raccontiModelForm()
            form.fields["title"] = forms.CharField(label="Titolo del racconto", max_length=128,
                                                   initial=racconto_inviato.title, disabled=True)
            form.fields["content"] = forms.CharField(
                widget=forms.Textarea(attrs={'rows': 20, 'maxlength': MAX_NUM_CHAR}),
                label="Testo del racconto ANONIMO (massimo " + str(MAX_NUM_CHAR) + " caratteri)",
                initial=racconto_inviato.content, disabled=True)
            form.fields["coAuthors"] = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'maxlength': 8000}),
                                                       label="Coautori in caso di testo collettivo (nome, cognome"
                                                             " e indirizzo email istituzionale)",
                                                       required=False, initial=racconto_inviato.coAuthors,
                                                       disabled=True)
            form.fields["contacts"] = forms.CharField(label="Recapito telefonico", max_length=128,
                                                      initial=racconto_inviato.contacts, disabled=True)
            form.fields["publishingPermission"] = forms.ChoiceField(widget=forms.CheckboxInput(),  # .RadioSelect(),
                                                                    initial=racconto_inviato.publishingPermission,
                                                                    choices=[(True, 'Si'), (False, 'No')],
                                                                    label='Autorizzo la Biblioteca di Ateneo alla pubblicazione del mio racconto',
                                                                    required=False, disabled=True)
            # form.fields["visioneregolamento"] = forms.ChoiceField(widget=forms.RadioSelect(),
            #                                                       initial=True, choices=[(True, 'Si'), (False, 'No')],
            #                                                       label='Dichiaro di aver preso visione del regolamento del concorso e di accettare le condizioni <a href="https://www.biblio.unimib.it/it/terza-missione/concorso-letterario" target="_blank">LINK</a>',
            #                                                       required=False, disabled=True)
            # form.fields["visioneinformativa"] = forms.ChoiceField(widget=forms.RadioSelect(),
            #                                                       initial=True, choices=[(True, 'Si'), (False, 'No')],
            #                                                       label="Dichiaro di aver preso visione dell'informativa privacy all'indirizzo <a href = 'https://www.unimib.it/sites/default/files/allegati/informativa_eventi_e_iniziative.pdf' target = '_blank' >LINK</a>",
            #                                                       required=False, disabled=True)
            context = {'form': form, 'idEvent': idEvent, 'titolo_concorso': titolo_concorso,
                       'is_submitted_in_active_event': True, 'is_submittable': is_submittable,
                       'MAX_NUM_CHAR': None, 'is_not_valid_user': False}
            context.update(permissions)
            return render(request, 'create_racconto.html', context)

        # Controllo se il periodo delle sottomissioni è attivo
        # (l'autore non ha inviato nessun racconto)
        # CASO RACCONTO INVIABILE
        elif is_submittable:
            # print("RACCONTO INVIABILE")
            # if this is a POST request we need to process the form data
            if request.method == 'POST':
                # create a form instance and populate it with data from the request:
                form = raccontiModelForm(request.POST)
                # check whether it's valid:
                if form.is_valid():
                    # Estrazione dati da Esse3
                    user = studente_email(request.user.email)

                    if user is not None:  # l'utente è di tipo @campus.unimib.it
                        authorSurname = user["cognome"]
                        authorForename = user["nome"]
                        authorBirthDate = codicefiscale.decode(user["codFis"])["birthdate"]
                        authorStatus = "Studente"
                        authorDetail = user["tipoCorsoDes"] + " " + user["cdsDes"] + " " + user["cdsCod"]

                    else:  # l'utente è di tipo @unimib.it
                        user = dipendente_email(request.user.email)

                        if user is None:  # Si tratta ad esempio di una casella di struttura
                            print("is_not_valid_user")
                            return render(request, 'create_racconto.html',
                                          {'idEvent': idEvent, 'is_not_valid_user': True,
                                           'titolo_concorso': titolo_concorso, })

                        authorSurname = user["cognome"]
                        authorForename = user["nome"]
                        authorBirthDate = codicefiscale.decode(user["codFis"])["birthdate"]
                        # print(authorBirthDate, type(authorBirthDate))
                        authorStatus = user["dsTipoRuolo"]
                        authorDetail = user["dsTipoRuolo"]

                    # Racconto da salvare
                    racconto = racconti(
                        counter=get_counter(),
                        idUser=request.user.email,
                        idEvent=events.objects.get(pk=id_active_event()),
                        title=form.cleaned_data["title"],
                        content=form.cleaned_data["content"],
                        submissionDate=datetime.now(),
                        publishingPermission=eval(form.cleaned_data["publishingPermission"]),
                        contacts=form.cleaned_data["contacts"],
                        coAuthors=form.cleaned_data["coAuthors"],
                        authorSurname=authorSurname,
                        authorForename=authorForename,
                        authorBirthDate=authorBirthDate,
                        authorStatus=authorStatus,
                        authorDetail=authorDetail
                    )
                    racconto.save()

                    # LOG operazione
                    insert_log(username=request.user.email,
                               operationDate=datetime.now(),
                               roleUser="Autore",
                               type="Inserimento racconto",
                               description="Inserimento racconto con id = {idRacconto} per il concorso con id = {id}".format(
                                   id=id_active_event(), idRacconto=racconto.pk),
                               )

                    #Invio email di notifica all'utente
                    subject = "[Notifica invio racconto concorso - {concorso}]".format(concorso=events.objects.all().get(pk=idEvent).eventName)
                    body = "Il racconto da te inviato &egrave; stato memorizzato.<br><br><br><br>Questo messaggio &egrave; una notifica automatica, qualunque risposta verr&agrave; ignorata."
                    subject = subject.encode("utf8").decode()
                    body = body.encode("utf8").decode()
                    emailsender(subject, body, [request.user.email], [], [])

                    return HttpResponseRedirect(reverse('create_racconto'))
            # if a GET (or any other method) we'll create a blank form
            else:
                form = raccontiModelForm()

        # Controllo che il racconto non sia più inviabile
        # in questo caso mostro il form vuoto in sola lettura
        # (l'autore non ha inviato nessun racconto)
        # CASO RACCONTO NON INVIATO E NON INVIABILE        #
        elif not is_submittable:
            # print("RACCONTO NON INVIABILE")
            form = raccontiModelForm()
            form.fields["title"] = forms.CharField(label="Titolo del racconto", max_length=128,
                                                   disabled=True)
            form.fields["content"] = forms.CharField(
                widget=forms.Textarea(attrs={'rows': 20, 'maxlength': MAX_NUM_CHAR}),
                label="Testo del racconto ANONIMO (massimo " + str(MAX_NUM_CHAR) + " caratteri)",
                disabled=True)
            form.fields["coAuthors"] = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'maxlength': 8000}),
                                                       label="Coautori in caso di testo collettivo (nome, cognome"
                                                             " e indirizzo email istituzionale)",
                                                       required=False,
                                                       disabled=True)
            form.fields["contacts"] = forms.CharField(label="Recapito telefonico", max_length=128,
                                                      disabled=True)
            form.fields["publishingPermission"] = forms.ChoiceField(widget=forms.CheckboxInput(),  # .RadioSelect(),
                                                                    choices=[(True, 'Si'), (False, 'No')],
                                                                    label='Autorizzo la Biblioteca di Ateneo alla pubblicazione del mio racconto',
                                                                    required=False, disabled=True)
            # form.fields["visioneregolamento"] = forms.ChoiceField(widget=forms.RadioSelect(),
            #                                                       initial=True, choices=[(True, 'Si'), (False, 'No')],
            #                                                       label='Dichiaro di aver preso visione del regolamento del concorso e di accettare le condizioni <a href="https://www.biblio.unimib.it/it/terza-missione/concorso-letterario" target="_blank">LINK</a>',
            #                                                       required=False, disabled=True)
            # form.fields["visioneinformativa"] = forms.ChoiceField(widget=forms.RadioSelect(),
            #                                                       initial=True, choices=[(True, 'Si'), (False, 'No')],
            #                                                       label="Dichiaro di aver preso visione dell'informativa privacy all'indirizzo <a href = 'https://www.unimib.it/sites/default/files/allegati/informativa_eventi_e_iniziative.pdf' target = '_blank' >LINK</a>",
            #                                                       required=False, disabled=True)
            context = {'form': form, 'idEvent': idEvent, 'titolo_concorso': titolo_concorso,
                       'is_submitted_in_active_event': False, 'is_submittable': is_submittable,
                       'MAX_NUM_CHAR': None, 'is_not_valid_user': False}
            context.update(permissions)
            return render(request, 'create_racconto.html', context)

        else:
            form = raccontiModelForm()

        context = {'form': form, 'idEvent': idEvent, 'titolo_concorso': titolo_concorso,
                   'is_submitted_in_active_event': False, 'is_submittable': is_submittable,
                   'MAX_NUM_CHAR': MAX_NUM_CHAR, 'is_not_valid_user': False}
        context.update(permissions)
        return render(request, 'create_racconto.html', context)
    else:
        context = {'idEvent': idEvent, 'is_not_valid_user': False}
        context.update(permissions)
        return render(request, 'create_racconto.html', context)
