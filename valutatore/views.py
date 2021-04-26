from datetime import datetime
from allauth.account.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from ConcorsoBiblioteca.restserviceeese3 import dipendente_email, studente_email
from ConcorsoBiblioteca.settings import NUM_PAGE, CATEGORIE_ETA, RANKING_POINT
from ConcorsoBiblioteca.utils import render_to_pdf, id_active_event, is_selectable, is_classifiable, get_permission, \
    get_birthDateLimit, insert_log, is_only_readable
from autore.models import racconti
from gestore.models import events, gestore
from .forms import valutatoreModelForm
from .models import valutatore, valutazione, letturaracconto
from django.shortcuts import get_object_or_404


# Crea un valutatore per un determinato concorso
# Permesso solo per il ruolo Gestore
@login_required
def create_valutatore(request, pk_event):
    # Controllo che l'utente sia un gestore
    utente_gestore = gestore.objects.filter(username=request.user.email)[:1]
    if utente_gestore.count() == 0:  # Non è un gestore
        return redirect('home')
    # print(pk_event)
    # if this is a POST request we need to process the form data
    permissions = get_permission(request.user.email)
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = valutatoreModelForm(request.POST)

        # check whether it's valid:
        if form.is_valid():
            id_event = pk_event  # id_active_event()
            email = form.cleaned_data['idUser']

            # Controllo che non sia già stato inserito per questo evento
            # Se si invalido il form e lo restituisco
            count = valutatore.objects.filter(idUser=email, idEvent=id_event).count()
            # print(count)
            if count > 0:
                form.add_error("idUser", "Utente già inserito come valutatore per questo concorso")
                context = {'form': form, 'pk_event': pk_event, 'is_gestore': True}
                permissions = get_permission(request.user.email)
                context.update(permissions)
                return render(request, 'create_valutatore.html', context)

            # Controllo che sia un dipendente o uno studente e ne ricavo i dati
            res = dipendente_email(email)
            if res is None:
                res = studente_email(email)

            forename = res["nome"]
            surname = res["cognome"]
            utente_valutatore = valutatore.objects.create(idUser=email, forename=forename, surname=surname,
                                                          idEvent=events.objects.get(pk=id_event))

            # LOG operazione
            insert_log(username=request.user.email,
                       operationDate=datetime.now(),
                       roleUser="Gestore",
                       type="Inserimento valutatore",
                       description="Inserimento valutatore \"{utente_valutatore}\" per il concorso con id = {id}".format(
                           id=id_active_event(), utente_valutatore=utente_valutatore.idUser,
                       ))

            return HttpResponseRedirect(reverse('list_valutatore', kwargs={'pk_event': pk_event}))

    # if a GET (or any other method) we'll create a blank form
    else:
        form = valutatoreModelForm()
    context = {'form': form, 'pk_event': pk_event, 'is_gestore': True}
    context.update(permissions)
    return render(request, 'create_valutatore.html', context)


# Lista Valutatori per un determinato concorso
# Permesso solo per il ruolo Gestore
@login_required
def list_valutatore(request, pk_event):
    # Controllo che l'utente sia un gestore
    utente_gestore = gestore.objects.filter(username=request.user.email)[:1]
    if utente_gestore.count() == 0:  # Non è un gestore
        return redirect('home')

    permissions = get_permission(request.user.email)

    valutatori_evento = valutatore.objects.filter(idEvent=pk_event).order_by('idUser')
    context = {'valutatori': valutatori_evento, 'pk_event': pk_event, 'is_gestore': True}
    context.update(permissions)
    return render(request, 'list_valutatore.html', context)


# Cancella Valutatore di un determinato concorso
# Permesso solo per il ruolo Gestore
@login_required
def delete_valutatore(request, pk_valutatore):
    # Controllo che l'utente sia un gestore
    utente_gestore = gestore.objects.filter(username=request.user.email)[:1]
    if utente_gestore.count() == 0:  # Non è un gestore
        return redirect('home')
    # Cancellazione valutatore
    permissions = get_permission(request.user.email)
    _valutatore = valutatore.objects.get(pk=pk_valutatore)

    # Controllo che il valutatore non abbia nessuna selezione attiva e non abbia nessuna
    # classificazione per qualche racconto

    # Possibili selezioni del valutatore
    numero_selezioni_attive = valutazione.objects.filter(idValutatore=_valutatore, selected=True).count()

    # Possibili valutazioni del valutatore
    numero_valutazioni = valutazione.objects.filter(idValutatore=_valutatore,
                                                    ranking__in=[RANKING_POINT[0], RANKING_POINT[1],
                                                                 RANKING_POINT[2]]).count()

    if (numero_valutazioni + numero_selezioni_attive) > 0:
        # LOG operazione
        insert_log(username=request.user.email,
                   operationDate=datetime.now(),
                   roleUser="Gestore",
                   type="Eliminazione valutatore",
                   description="Eliminazione valutatore \"{utente_valutatore}\" per il concorso "
                               "con id = {id} non riuscita in quanto ha dati associati".format(
                       id=id_active_event(), utente_valutatore=_valutatore.idUser,
                   ))
    else:
        # LOG operazione
        insert_log(username=request.user.email,
                   operationDate=datetime.now(),
                   roleUser="Gestore",
                   type="Eliminazione valutatore",
                   description="Eliminazione valutatore \"{utente_valutatore}\" per il concorso con id = {id}".format(
                       id=id_active_event(), utente_valutatore=_valutatore.idUser,
                   ))

        _valutatore.delete()

    _id_evento = _valutatore.idEvent.pk

    # context = {'valutatori': valutatore.objects.filter(idEvent=_id_evento).order_by("idUser"), 'pk_event': _id_evento,
    #            'is_gestore': True}
    #
    # context.update(permissions)
    # return render(request, 'list_valutatore.html', context)
    return redirect('list_valutatore', _id_evento)


# Genera la vista per la selezione dei racconti di un dato concorso
# Vista accessibile SOLO AD utenti VALUTATORI
@login_required
def selezione_racconti(request, page_number=1, categoriaeta=CATEGORIE_ETA[0]):
    idEvent = id_active_event()
    permissions = get_permission(request.user.email)
    # Controllo che il parametro categoriaeta sia valido

    if categoriaeta not in CATEGORIE_ETA:
        return redirect('home')

    # Controlla se l'evento è attivo
    if idEvent is None:
        return render(request, "selezioni.html", context={'is_active': False})

    concorso = events.objects.all().get(pk=idEvent)

    valutatore_concorso = valutatore.objects.all().filter(idEvent=concorso, idUser=request.user.email)[:1]

    if valutatore_concorso.count() == 0:  # L'utente non ' un valutatore per questo concorso
        return redirect('home')

    # Se il periodo di selezione non è attivo più mostra il messaggio
    if not is_selectable():
        context = {'is_selectable': False, 'is_active': True, 'categoriaeta': categoriaeta}
        context.update(permissions)
        return render(request, "selezioni.html", context=context)

    # Ricavo la lista dei racconti per l'evento con relative selezioni da parte del valutatore.
    # e classificazione in categoria Junior o Senior

    if categoriaeta == CATEGORIE_ETA[0]:
        racconti_evento = racconti.objects.all().filter(idEvent=idEvent, authorBirthDate__gte=concorso.birthDateLimit)
    else:
        racconti_evento = racconti.objects.all().filter(idEvent=idEvent, authorBirthDate__lt=concorso.birthDateLimit)

    lista_record_racconto = []
    record_racconto = []

    for racconto in racconti_evento:
        # Cerco se il racconto sia già stato selezionato dall'autore
        valutazione_racconto = \
            valutazione.objects.all().filter(idRacconto=racconto, idValutatore=valutatore_concorso)[:1]

        # Il racconto non è mai stato selezionato da questo valutatore
        if valutazione_racconto.count() == 0:
            record_racconto.append(False)
        else:
            # print(valutazione_racconto[0].pk, valutazione_racconto[0].selected)
            record_racconto.append(valutazione_racconto[0].selected)

        record_racconto.append(racconto.counter)  # Counter racconto




        # Calcolo categoria età
        if racconto.authorBirthDate < concorso.birthDateLimit:
            record_racconto.append(CATEGORIE_ETA[1])  # Status età
        else:
            record_racconto.append(CATEGORIE_ETA[0])  # Status età

        record_racconto.append(racconto.title)  # Titolo racconto

        record_racconto.append(racconto.pk)  # Id racconto



        # Vedo se il racconto è stato marcato come letto dal valutatore loggato
        raccontoletto = letturaracconto.objects.all().filter(idRacconto=racconto, idValutatore=valutatore_concorso[0])[:1]

        # Il racconto non è stato letto da questo valutatore
        if raccontoletto.count() == 0:
            record_racconto.append(False)
        else:
            record_racconto.append(True)
        # print(raccontoletto)
        # print("racconto",racconto)
        # print("valutatore", valutatore_concorso)




        lista_record_racconto.append(record_racconto)
        record_racconto = []

    # Numero dei racconti selezionati dall'utente
    # numero_racconti_selezionati = valutazione.objects.all().filter(selected=True,
    #                                                                idValutatore=valutatore_concorso,
    #                                                                idValutatore__idEvent_id=concorso)

    numero_racconti_selezionati = valutatore_concorso[0].valutatorevalutazione.all().filter(selected=1).count()

    # print(numero_racconti_selezionati)

    # Paginazione risultati
    paginator = Paginator(lista_record_racconto, NUM_PAGE)

    # if request.GET.get('page') is None:
    #     page_number = 1
    # else:
    #     page_number = request.GET.get('page')

    # page_number = request.GET.get('page')
    # print('page_number:', page_number)

    page_obj = paginator.get_page(page_number)

    # Non si possonopiù selezionare racconti
    if numero_racconti_selezionati >= concorso.maxSelections:
        is_possible_select = False
    else:
        is_possible_select = True
    _is_only_readable = is_only_readable()

    context = {'record_set': page_obj, 'numero_racconti_selezionabili': concorso.maxSelections,
               'numero_racconti_selezionati': numero_racconti_selezionati, 'is_only_readable': _is_only_readable,
               'is_possible_select': is_possible_select, 'is_selectable': True, 'is_active': True,
               'page_number': page_number, 'categoriaeta': categoriaeta, }
    context.update(permissions)

    # return render(request, "selezioni.html", context={'record_set': lista_record_racconto})
    return render(request, "selezioni.html", context=context)


# Vista per la SELEZIONE di un racconto
# Vista accessibile SOLO AD utenti VALUTATORI
@login_required
def seleziona_racconto(request, pk_racconto, page_number, categoriaeta):
    idEvent = id_active_event()

    # Controlla se l'evento è attivo
    if idEvent is None:
        return redirect('home')

    concorso = events.objects.all().get(pk=idEvent)
    valutatore_concorso = valutatore.objects.all().filter(idEvent=concorso, idUser=request.user.email)[:1]

    if valutatore_concorso.count() == 0:  # L'utente non ' un valutatore per questo concorso
        return redirect('home')

    # Se il periodo di selezione non è ancora attivo o non lo è l'operazione non è valida
    if not is_selectable():
        return redirect('home')

    racconto_da_valutare = racconti.objects.all().get(pk=pk_racconto)
    racconti_concorso_attivo = racconti.objects.all().filter(idEvent=id_active_event())

    if racconto_da_valutare not in racconti_concorso_attivo:  # Il racconto non può essere valutato in questo concorso
        return redirect('home')

    numero_racconti_selezionati = valutatore_concorso[0].valutatorevalutazione.all().filter(selected=1).count()

    if numero_racconti_selezionati >= concorso.maxSelections:  # Non si possono più selezionare racconti(controllo di sicurezza)
        return redirect('home')

    # permissions = get_permission(request.user.email)

    valutazione_racconto = valutazione.objects.all().filter(idValutatore=valutatore_concorso[0],
                                                            idRacconto=racconto_da_valutare)[:1]

    if valutazione_racconto.count() == 0:  # Non esiste nessuna valutazione, si crea quindi il record
        valutazione_racconto = valutazione(
            idRacconto=racconto_da_valutare,
            idValutatore=valutatore_concorso[0],
            ranking=0,
            selected=1
        )

    else:  # La valutazione esiste, si modifica quindi il record esistente
        valutazione_racconto = valutazione.objects.all().get(pk=valutazione_racconto[0].pk)
        valutazione_racconto.selected = 1
        valutazione_racconto.ranking = 0

    valutazione_racconto.save()

    # LOG operazione
    insert_log(username=request.user.email,
               operationDate=datetime.now(),
               roleUser="Valutatore",
               type="Selezione racconto",
               description="Selezione racconto con id = {idRacconto} per il concorso con id = {id}".format(
                   id=id_active_event(), idRacconto=pk_racconto),
               )

    return redirect('selezione_racconti', page_number=page_number, categoriaeta=categoriaeta)


# Vista per la DESELEZIONE di un racconto
# Vista accessibile SOLO AD utenti VALUTATORI
@login_required
def deseleziona_racconto(request, pk_racconto, page_number, categoriaeta):
    idEvent = id_active_event()

    # Controlla se l'evento è attivo
    if idEvent is None:
        return redirect('home')

    concorso = events.objects.all().get(pk=idEvent)
    valutatore_concorso = valutatore.objects.all().filter(idEvent=concorso, idUser=request.user.email)[:1]

    if valutatore_concorso.count() == 0:  # L'utente non ' un valutatore per questo concorso
        return redirect('home')

    # Se il periodo di selezione non è ancora attivo o non lo è l'operazione non è valida
    if not is_selectable():
        return redirect('home')

    racconto_da_valutare = racconti.objects.all().get(pk=pk_racconto)
    racconti_concorso_attivo = racconti.objects.all().filter(idEvent=id_active_event())

    if racconto_da_valutare not in racconti_concorso_attivo:  # Il racconto non può essere valutato in questo concorso
        return redirect('home')

    valutazione_racconto = valutazione.objects.all().filter(idValutatore=valutatore_concorso[0],
                                                            idRacconto=racconto_da_valutare)[:1]

    if valutazione_racconto.count() == 0:  # Non esiste nessuna valutazione, si crea quindi il record
        valutazione_racconto = valutazione(
            idRacconto=racconto_da_valutare,
            idValutatore=valutatore_concorso[0],
            ranking=0,
            selected=0
        )
    else:  # La valutazione esiste, si modifica quindi il record esistente
        valutazione_racconto = valutazione.objects.all().get(pk=valutazione_racconto[0].pk)
        valutazione_racconto.selected = 0
        # valutazione_racconto.ranking = 0

    valutazione_racconto.save()

    # LOG operazione
    insert_log(username=request.user.email,
               operationDate=datetime.now(),
               roleUser="Valutatore",
               type="Deselezione racconto",
               description="Deselezione racconto con id = {idRacconto} per il concorso con id = {id}".format(
                   id=id_active_event(), idRacconto=pk_racconto),
               )

    return redirect('selezione_racconti', page_number=page_number, categoriaeta=categoriaeta)


# Vista per marcare un racconto come letto
@login_required
def lettura_racconto(request, pk_racconto, page_number, categoriaeta):
    # Vedo se il racconto è stato marcato come letto dal valutatore loggato
    idEvent = id_active_event()
    concorso = events.objects.all().get(pk=idEvent)
    racconto = racconti.objects.all().get(pk=pk_racconto)

    valutatore_concorso = valutatore.objects.all().filter(idEvent=concorso, idUser=request.user.email)[:1]

    #Creo un record di lettura
    raccontoletto = letturaracconto.objects.all().filter(idRacconto=racconto, idValutatore=valutatore_concorso[0])[:1]

    # Il racconto non è stato letto da questo valutatore
    # Controllo di sicurezza per stabilire
    # che il valutatore non abbia effettivamente letto il racconto
    if raccontoletto.count() == 0:
        letturaracconto.objects.all().create(idRacconto=racconto, idValutatore=valutatore_concorso[0])


    return redirect('selezione_racconti', page_number=page_number, categoriaeta=categoriaeta)


# Vista per marcare un racconto come non letto
@login_required
def nonlettura_racconto(request, pk_racconto, page_number, categoriaeta):
    # Vedo se il racconto è stato marcato come letto dal valutatore loggato
    idEvent = id_active_event()
    concorso = events.objects.all().get(pk=idEvent)
    racconto = racconti.objects.all().get(pk=pk_racconto)

    valutatore_concorso = valutatore.objects.all().filter(idEvent=concorso, idUser=request.user.email)[:1]

    # Creo un record di lettura
    raccontoletto = letturaracconto.objects.all().filter(idRacconto=racconto, idValutatore=valutatore_concorso[0])[:1]

    # Il racconto non è stato letto da questo valutatore
    # Controllo di sicurezza per stabilire
    # che il valutatore non abbia effettivamente letto il racconto
    if raccontoletto.count() >= 1:
        print("Cancellazione")
        l = letturaracconto.objects.all().filter(idRacconto=racconto, idValutatore=valutatore_concorso[0])
        l.delete()

    return redirect('selezione_racconti', page_number=page_number, categoriaeta=categoriaeta)


# Genera la vista per la votazione dei racconti
# selezionati dal valutatore
# Vista accessibile SOLO AD utenti VALUTATORI
@login_required
def votazione_racconti(request, categoriaeta):
    idEvent = id_active_event()
    permissions = get_permission(request.user.email)

    # Controlla se l'evento è attivo
    if idEvent is None:
        context = {'is_active': False}
        context.update(permissions)
        return render(request, "votazioni.html", context=context)

    # Controllo che il parametro categoriaeta sia valido
    if categoriaeta not in CATEGORIE_ETA:
        return redirect('home')

    # Controllo che l'utente sia un valutatore
    if not permissions['is_valutatore']:
        return redirect('home')

    # Se il periodo di classificazione non è ancora attivo o non lo è più mostra il messaggio
    if not is_classifiable():
        context = {'is_classifiable': False, 'is_active': True}
        context.update(permissions)
        return render(request, "votazioni.html", context=context)

    concorso = events.objects.all().get(pk=idEvent)

    if categoriaeta == CATEGORIE_ETA[0]:
        # racconti categoria senior scelti dai valutatori del concorso
        racconti_evento = racconti.objects.all().filter(  # raccontovalutazione__idValutatore=valutatore_concorso[0],
            raccontovalutazione__selected=True,
            authorBirthDate__gte=concorso.birthDateLimit,
            idEvent=concorso).only('counter', 'title', 'authorBirthDate', 'pk').distinct().order_by("counter")
    else:
        # racconti categoria junior scelti dai valutatori del concorso
        racconti_evento = racconti.objects.all().filter(  # raccontovalutazione__idValutatore=valutatore_concorso[0],
            raccontovalutazione__selected=True,
            authorBirthDate__lt=concorso.birthDateLimit,
            idEvent=concorso).only('counter', 'title', 'authorBirthDate', 'pk').distinct().order_by("counter")

    # print("racconti_evento", racconti_evento)

    lista_record_racconto = []
    record_racconto = []

    for racconto in racconti_evento:

        record_racconto.append(racconto.counter)  # Counter racconto

        # Calcolo categoria età
        if racconto.authorBirthDate < concorso.birthDateLimit:
            record_racconto.append(CATEGORIE_ETA[1])  # Status età
        else:
            record_racconto.append(CATEGORIE_ETA[0])  # Status età

        record_racconto.append(racconto.title)  # Titolo racconto

        record_racconto.append(racconto.pk)  # Id racconto

        lista_record_racconto.append(record_racconto)
        record_racconto = []

    valutatore_concorso = valutatore.objects.all().filter(idUser=request.user.email, idEvent=concorso)

    classifica = get_classifiche_valutatore(valutatore_concorso[0])

    context = {'record_set': lista_record_racconto, 'numero_racconti_selezionabili': concorso.maxSelections,
               'is_classifiable': True, 'is_active': True}
    context.update(permissions)
    context.update(classifica)
    return render(request, "votazioni.html", context)


# Restituisce un dizionario con le classifiche del valutatore
# sia per i racconti Junior sia per quelli Senior
def get_classifiche_valutatore(valutatore_concorso):
    concorso = valutatore_concorso.idEvent

    classifica = {}
    # Ricavo la classifica dei racconti Junior
    primo_junior = valutazione.objects.filter(idRacconto__authorBirthDate__gte=concorso.birthDateLimit,
                                              idValutatore=valutatore_concorso,
                                              ranking=RANKING_POINT[0])[:1]

    if primo_junior.count() == 0:
        classifica["primo_junior"] = None
    else:
        classifica["primo_junior"] = primo_junior[0].idRacconto.title + " (" + str(
            primo_junior[0].idRacconto.counter) + ")"

    secondo_junior = valutazione.objects.filter(idRacconto__authorBirthDate__gte=concorso.birthDateLimit,
                                                idValutatore=valutatore_concorso,
                                                ranking=RANKING_POINT[1])[:1]

    if secondo_junior.count() == 0:
        classifica["secondo_junior"] = None
    else:
        classifica["secondo_junior"] = secondo_junior[0].idRacconto.title + " (" + str(
            secondo_junior[0].idRacconto.counter) + ")"

    terzo_junior = valutazione.objects.filter(idRacconto__authorBirthDate__gte=concorso.birthDateLimit,
                                              idValutatore=valutatore_concorso,
                                              ranking=RANKING_POINT[2])[:1]

    if terzo_junior.count() == 0:
        classifica["terzo_junior"] = None
    else:
        classifica["terzo_junior"] = terzo_junior[0].idRacconto.title + " (" + str(
            terzo_junior[0].idRacconto.counter) + ")"

    primo_senior = valutazione.objects.filter(idRacconto__authorBirthDate__lt=concorso.birthDateLimit,
                                              idValutatore=valutatore_concorso,
                                              ranking=RANKING_POINT[0])[:1]

    if primo_senior.count() == 0:
        classifica["primo_senior"] = None
    else:
        classifica["primo_senior"] = primo_senior[0].idRacconto.title + " (" + str(
            primo_senior[0].idRacconto.counter) + ")"

    secondo_senior = valutazione.objects.filter(idRacconto__authorBirthDate__lt=concorso.birthDateLimit,
                                                idValutatore=valutatore_concorso,
                                                ranking=RANKING_POINT[1])[:1]

    if secondo_senior.count() == 0:
        classifica["secondo_senior"] = None
    else:
        classifica["secondo_senior"] = secondo_senior[0].idRacconto.title + " (" + str(
            secondo_senior[0].idRacconto.counter) + ")"

    terzo_senior = valutazione.objects.filter(idRacconto__authorBirthDate__lt=concorso.birthDateLimit,
                                              idValutatore=valutatore_concorso,
                                              ranking=RANKING_POINT[2])[:1]

    if terzo_senior.count() == 0:
        classifica["terzo_senior"] = None
    else:
        classifica["terzo_senior"] = terzo_senior[0].idRacconto.title + " (" + str(
            terzo_senior[0].idRacconto.counter) + ")"

    return classifica


@login_required
def votazione_racconto(request, counter_id_racconto, categoriaeta, classifica):
    permission = get_permission(request.user.email)

    # Controllo che l'utente sia un valutatore
    if not permission['is_valutatore']:
        return redirect('home')

    # Controllo che il parametro classifica sia valido
    try:
        RANKING_POINT[classifica]
    except:
        return redirect('home')

    # Controllo che il parametro categoriaeta sia valido
    if categoriaeta not in CATEGORIE_ETA:
        return redirect('home')

    # Estraggo l'entry, se esiste, che associa la valutazione del racconto al valutatore
    concorso = events.objects.all().get(pk=id_active_event())
    valutatore_concorso = valutatore.objects.all().filter(idEvent=concorso, idUser=request.user.email)[:1]

    racconto = racconti.objects.all().filter(counter=counter_id_racconto, idEvent=concorso)[:1]

    # Controllo che il racconto esista
    if racconto.count() == 0:
        return redirect('home')

    valutazione_racconto = valutazione.objects.all().filter(idRacconto=racconto[0], idValutatore=valutatore_concorso[0])

    if valutazione_racconto.count() == 0:  # Non esiste entry, quindi la creo
        valutazione_racconto = valutazione(idRacconto=racconto[0], idValutatore=valutatore_concorso[0], selected=0,
                                           ranking=RANKING_POINT[classifica])

    else:  # L'entry esiste quindi la modifico
        valutazione_racconto = valutazione.objects.get(pk=valutazione_racconto[0].pk)
        valutazione_racconto.ranking = RANKING_POINT[classifica]

    valutazione_racconto.save()
    # LOG operazione
    insert_log(username=request.user.email,
               operationDate=datetime.now(),
               roleUser="Valutatore",
               type="Valutazione racconto",
               description="Valutazione racconto con id = {id_racconto} con punteggio assegnato {ranking} per il concorso con id = {id}".format(
                   id_racconto=valutazione_racconto.idRacconto.pk, ranking=valutazione_racconto.ranking,
                   id=id_active_event()),
               )

    # Bisogna porre a 0 il ranking di tutte le valutazioni del valutatore che avevano
    # valutazione_racconto.ranking = RANKING_POINT[classifica]

    if categoriaeta == CATEGORIE_ETA[0]:  # Valutazione per racconto Junior
        valutazioni_da_aggiornare = valutazione.objects.filter(idValutatore=valutatore_concorso,
                                                               idRacconto__authorBirthDate__gte=concorso.birthDateLimit,
                                                               ranking=RANKING_POINT[classifica]).exclude(
            idRacconto=racconto[0], idValutatore=valutatore_concorso[0]).update(ranking=0)
    else:  # Categoria senior
        valutazioni_da_aggiornare = valutazione.objects.filter(idValutatore=valutatore_concorso,
                                                               idRacconto__authorBirthDate__lt=concorso.birthDateLimit,
                                                               ranking=RANKING_POINT[classifica]).exclude(
            idRacconto=racconto[0], idValutatore=valutatore_concorso[0]).update(ranking=0)

    print(valutazioni_da_aggiornare)

    return redirect('votazione_racconti', categoriaeta=categoriaeta)


# Vista per racconto singolo anonimo(per commissione)
@method_decorator(login_required, name='dispatch')
class GeneraPDF_SINGOLO(View):
    def get(self, request, pk):
        template = get_template('pdf_template_singolo.html')
        racconto = get_object_or_404(racconti, pk=pk)
        counter = racconto.counter
        birthDateLimit = get_birthDateLimit()
        context = {
            "counter": counter,
            "racconto": racconto,
            "birthDateLimit": birthDateLimit,
            "categorieeta": CATEGORIE_ETA,
            "titolo_concorso": events.objects.all().get(pk=id_active_event()).eventName,
            "anno": datetime.now().year,
        }

        html = template.render(context)
        pdf = render_to_pdf('pdf_template_singolo.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = str(racconto.counter) + "-" + racconto.title + ".pdf"
            content = "inline; filename=%s" % (filename)
            download = request.GET.get("download")
            if download:
                content = "attachment; filename='%s'" % (filename)
            response['Content-Disposition'] = content
            return response
        return HttpResponse("Not found")


# Vista per raccolta racconti anonimi CLASSIFICABILI (Selezionati)(per commissione)
@method_decorator(login_required, name='dispatch')
class GeneratePDFMULTIPLORaccontiSelezionati(View):
    def get(self, request, anonimo=True):
        template = get_template('pdf_template_multiplo.html')
        birthDateLimit = get_birthDateLimit()
        context = {
            "title": "Racconti selezionati",

            "racconti": racconti.objects.all().filter(raccontovalutazione__selected=True).only("title", "content",
                                                                                               "counter",
                                                                                               "authorBirthDate").distinct().order_by(
                "counter"),

            "titolo_concorso": events.objects.all().get(pk=id_active_event()).eventName,
            "anno": datetime.now().year,
            "birthDateLimit": birthDateLimit,
            "categorieeta": CATEGORIE_ETA,
        }
        html = template.render(context)
        pdf = render_to_pdf('pdf_template_multiplo.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = "Racconti selezionati.pdf"
            content = "inline; filename=%s" % (filename)
            download = request.GET.get("download")
            if download:
                content = "attachment; filename='%s'" % (filename)
            response['Content-Disposition'] = content
            return response
        return HttpResponse("Not found")


# Vista per raccolta racconti anonimi SELEZIONABILI(per commissione)
# E' la lista di tutti i racconti inviati senza informazioni anagrafiche
@method_decorator(login_required, name='dispatch')
class GeneratePDFMULTIPLORaccontiSelezionabili(View):
    def get(self, request, anonimo=True):
        template = get_template('pdf_template_multiplo.html')
        birthDateLimit = get_birthDateLimit()
        context = {
            "title": "Racconti selezionati",
            "racconti": racconti.objects.all().only("title", "content",
                                                    "counter",
                                                    "authorBirthDate").distinct().order_by("counter"),
            "titolo_concorso": events.objects.all().get(pk=id_active_event()).eventName,
            "anno": datetime.now().year,
            "birthDateLimit": birthDateLimit,
            "categorieeta": CATEGORIE_ETA,
        }
        html = template.render(context)
        pdf = render_to_pdf('pdf_template_multiplo.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = "Racconti inviati.pdf"
            content = "inline; filename=%s" % (filename)
            download = request.GET.get("download")
            if download:
                content = "attachment; filename='%s'" % (filename)
            response['Content-Disposition'] = content
            return response
        return HttpResponse("Not found")
