import operator
from datetime import datetime

from ConcorsoBiblioteca.mailer import Gmail, emailsender, da_carattere_speciale_ad_entity
from valutatore.models import valutatore
from valutatore.views import get_classifiche_valutatore
from allauth.account.decorators import login_required
from django.http import HttpResponse
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView
from openpyxl import Workbook
from ConcorsoBiblioteca.restserviceeese3 import dipendente_email, studente_email
from ConcorsoBiblioteca.settings import CATEGORIE_ETA, RANKING_POINT
from ConcorsoBiblioteca.utils import get_permission, id_active_event, render_to_pdf, insert_log
from autore.models import racconti
from gestore.models import events
from segreteria.forms import segretarioModelForm
from segreteria.models import segretario
from .forms import MailForm


# Crea un segretario
# Permesso solo per il ruolo Gestore
@login_required
def create_segretario(request):
    # Controllo che l'utente sia un gestore
    permissions = get_permission(request.user.email)

    if not permissions["is_gestore"]:  # Non è un gestore
        return redirect('home')

    # if this is a POST request we need to process the form data

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = segretarioModelForm(request.POST)

        # check whether it's valid:
        if form.is_valid():
            email = form.cleaned_data['idUser']

            # Controllo che non sia già stato inserito
            # Se si invalido il form e lo restituisco
            count = segretario.objects.filter(idUser=email).count()
            # print(count)
            if count > 0:
                form.add_error("idUser", "Utente già inserito come segretario")
                context = {'form': form, }
                permissions = get_permission(request.user.email)
                context.update(permissions)
                return render(request, 'create_segretario.html', context)

            # Controllo che sia un dipendente o uno studente e ne ricavo i dati
            res = dipendente_email(email)
            if res is None:
                res = studente_email(email)

            forename = res["nome"]
            surname = res["cognome"]
            segretario.objects.create(idUser=email, forename=forename, surname=surname)

            # LOG operazione
            insert_log(username=request.user.email,
                       operationDate=datetime.now(),
                       roleUser="Gestore",
                       type="Creazione segretario",
                       description="Inserimento segretario {segretario}".format(segretario=email, )
                       )

            return HttpResponseRedirect(reverse('list_segretario', ))

    # if a GET (or any other method) we'll create a blank form
    else:
        form = segretarioModelForm()
    context = {'form': form}
    context.update(permissions)
    return render(request, 'create_segretario.html', context)


# Lista Segretari
# Permesso solo per il ruolo Gestore
@login_required
def list_segretario(request):
    # Controllo che l'utente sia un gestore
    permissions = get_permission(request.user.email)

    if not permissions["is_gestore"]:  # Non è un gestore
        return redirect('home')

    segretari_evento = segretario.objects.all().order_by('idUser')
    context = {'segretari': segretari_evento, }
    context.update(permissions)
    return render(request, 'list_segretario.html', context)


# Cancella Segretario
# Permesso solo per il ruolo Gestore
@login_required
def delete_segretario(request, pk_segretario):
    # Controllo che l'utente sia un gestore
    permissions = get_permission(request.user.email)

    if not permissions["is_gestore"]:  # Non è un gestore
        return redirect('home')

    # Cancellazione segretario
    _segretario = get_object_or_404(segretario, pk=pk_segretario)
    email = _segretario.idUser
    _segretario.delete()

    # LOG operazione
    insert_log(username=request.user.email,
               operationDate=datetime.now(),
               roleUser="Gestore",
               type="Eliminazione segretario",
               description="Eliminazione segretario {segretario}".format(segretario=email, )
               )

    return redirect('list_segretario')


# Lista Concorsi
# Permesso solo per il ruolo Segretario
@method_decorator(login_required, name='dispatch')
class list_event_segreteria(ListView):
    model = events
    template_name = "list_event_segreteria.html"

    def get_context_data(self, **kwargs):
        context = super(list_event_segreteria, self).get_context_data(**kwargs)
        context['id_evento_attivo'] = id_active_event()
        return context

    def get(self, request, *args, **kwargs):
        # Controllo che l'utente sia un segretario
        permissions = get_permission(request.user.email)

        if not permissions["is_segretario"]:  # Non è un segretario
            return redirect('home')

        self.object_list = events.objects.all().order_by('id')
        context = self.get_context_data(object_list=self.object_list)
        permissions = get_permission(request.user.email)
        context.update(permissions)
        return self.render_to_response(context)


# Lista Racconti consegnati per un dato concorso
# Permesso solo per il ruolo Segretario
@login_required
def list_racconti_segreteria(request, pk_event):
    # Controllo che l'utente sia un segretario
    permissions = get_permission(request.user.email)

    if not permissions["is_segretario"]:  # Non è un segretario
        return redirect('home')

    # Controllo che il pk_event corrisponda all'id di un evento esistente
    concorso = get_object_or_404(events, pk=pk_event)

    racconti_consegnati = get_racconti_consegnati_concorso(concorso)

    context = {'racconti_consegnati': racconti_consegnati, 'titolo_concorso': concorso.eventName,
               'categorieeta': CATEGORIE_ETA, 'limite_data': concorso.birthDateLimit, 'pk_event': pk_event}

    context.update(permissions)

    return render(request, 'list_consegne_racconti_concorso.html', context)


# Restituisce il Queryset dei racconti consegnati per un dato concorso
def get_racconti_consegnati_concorso(concorso):
    # Controllo che il pk_event corrisponda all'id di un evento esistente
    racconti_consegnati = racconti.objects.filter(idEvent=concorso).order_by("counter")

    return racconti_consegnati



# Restituisce il Queryset dei racconti consegnati per un dato concorso
def get_racconti_consegnati_concorso_pubblicabili(concorso):
    # Controllo che il pk_event corrisponda all'id di un evento esistente
    racconti_consegnati = racconti.objects.filter(idEvent=concorso, publishingPermission=True).order_by("counter")

    return racconti_consegnati





# Lista Racconti selezionati per un dato concorso
# Permesso solo per il ruolo Segretario
@login_required
def list_selezioni_segreteria(request, pk_event):
    # Controllo che l'utente sia un segretario
    permissions = get_permission(request.user.email)

    if not permissions["is_segretario"]:  # Non è un segretario
        return redirect('home')

    # Controllo che il pk_event corrisponda all'id di un evento esistente
    concorso = get_object_or_404(events, pk=pk_event)

    racconti_selezionati = get_racconti_selezionati_concorso(concorso)

    context = {'racconti_selezionati': racconti_selezionati, 'titolo_concorso': concorso.eventName,
               'categorieeta': CATEGORIE_ETA, 'limite_data': concorso.birthDateLimit, 'pk_event': pk_event}

    context.update(permissions)

    return render(request, 'list_selezioni_racconti_concorso.html', context)


# Restituisce il Queryset dei racconti selezionati per un dato concorso
def get_racconti_selezionati_concorso(concorso):
    racconti_selezionati = racconti.objects.filter(idEvent=concorso, raccontovalutazione__selected=True).only("counter",
                                                                                                              "idUser",
                                                                                                              "authorForename",
                                                                                                              "authorSurname",
                                                                                                              "authorBirthDate",
                                                                                                              "title").distinct().order_by(
        "counter")
    return racconti_selezionati


# Lista classifiche junior per un dato concorso
# Permesso solo per il ruolo Segretario
@login_required
def list_racconti_junior(request, pk_event):
    # Controllo che l'utente sia un segretario
    permissions = get_permission(request.user.email)
    if not permissions["is_segretario"]:  # Non è un segretario
        return redirect('home')

    concorso = get_object_or_404(events, pk=pk_event)

    racconti_junior = get_racconti_junior_classificati_concorso(concorso)

    context = {'racconti_junior': racconti_junior, 'titolo_concorso': concorso.eventName,
               'categorieeta': CATEGORIE_ETA, 'limite_data': concorso.birthDateLimit, 'pk_event': pk_event}

    context.update(permissions)

    return render(request, 'list_classifica_junior_concorso.html', context)


# Restituisce il Queryset dei racconti Junior classificati per un dato concorso
# con relativo punteggio totalizzato in base alle votazioni date dalla commissione
def get_racconti_junior_classificati_concorso(concorso):
    racconti_junior = racconti.objects.filter(authorBirthDate__gte=concorso.birthDateLimit, idEvent=concorso,
                                              raccontovalutazione__ranking__in=[RANKING_POINT[0], RANKING_POINT[1],
                                                                                RANKING_POINT[2]]).only("counter",
                                                                                                        "idUser",
                                                                                                        "authorForename",
                                                                                                        "authorSurname",
                                                                                                        "authorBirthDate",
                                                                                                        "title", ).distinct().order_by(
        "counter")
    # Aggiunta valutazioni totali ad ogni racconto
    for racconto in racconti_junior:
        racconto.ranking = get_ranking_racconto(racconto)

    racconti_junior = sorted(racconti_junior, key=operator.attrgetter('ranking'), reverse=True)

    return racconti_junior


# Lista classifiche junior per un dato concorso
# Permesso solo per il ruolo Segretario
@login_required
def list_racconti_senior(request, pk_event):
    # Controllo che l'utente sia un segretario
    permissions = get_permission(request.user.email)
    if not permissions["is_segretario"]:  # Non è un segretario
        return redirect('home')

    concorso = get_object_or_404(events, pk=pk_event)

    racconti_senior = get_racconti_senior_classificati_concorso(concorso)

    context = {'racconti_senior': racconti_senior, 'titolo_concorso': concorso.eventName,
               'categorieeta': CATEGORIE_ETA, 'limite_data': concorso.birthDateLimit, 'pk_event': pk_event}

    context.update(permissions)

    return render(request, 'list_classifica_senior_concorso.html', context)


# Restituisce il Queryset dei racconti Senior classificati per un dato concorso
# con relativo punteggio totalizzato in base alle votazioni date dalla commissione
def get_racconti_senior_classificati_concorso(concorso):
    racconti_senior = racconti.objects.filter(authorBirthDate__lt=concorso.birthDateLimit, idEvent=concorso,
                                              raccontovalutazione__ranking__in=[RANKING_POINT[0], RANKING_POINT[1],
                                                                                RANKING_POINT[2]]).only("counter",
                                                                                                        "idUser",
                                                                                                        "authorForename",
                                                                                                        "authorSurname",
                                                                                                        "authorBirthDate",
                                                                                                        "title", ).distinct().order_by(
        "counter")
    # Aggiunta valutazioni totali ad ogni racconto
    for racconto in racconti_senior:
        racconto.ranking = get_ranking_racconto(racconto)

    racconti_senior = sorted(racconti_senior, key=operator.attrgetter('ranking'), reverse=True)

    return racconti_senior


# Lista classifiche junior e senior per un dato concorso
# Permesso solo per il ruolo Segretario
@login_required
def list_racconti_junior_senior(request, pk_event):
    # Controllo che l'utente sia un segretario
    permissions = get_permission(request.user.email)
    if not permissions["is_segretario"]:  # Non è un segretario
        return redirect('home')

    concorso = get_object_or_404(events, pk=pk_event)

    racconti_junior_senior = get_racconti_junior_senior_classificati_concorso(concorso)

    context = {'racconti_junior_senior': racconti_junior_senior, 'titolo_concorso': concorso.eventName,
               'categorieeta': CATEGORIE_ETA, 'limite_data': concorso.birthDateLimit, 'pk_event': pk_event}

    context.update(permissions)

    return render(request, 'list_classifica_junior_senior_concorso.html', context)


# Restituisce il Queryset dei racconti Junior e Senior classificati per un dato concorso
# con relativo punteggio totalizzato in base alle votazioni date dalla commissione
def get_racconti_junior_senior_classificati_concorso(concorso):
    racconti_junior_senior = racconti.objects.filter(idEvent=concorso,
                                                     raccontovalutazione__ranking__in=[RANKING_POINT[0],
                                                                                       RANKING_POINT[1],
                                                                                       RANKING_POINT[2]]).only(
        "counter",
        "idUser",
        "authorForename",
        "authorSurname",
        "authorBirthDate",
        "title", ).distinct().order_by(
        "counter")

    # Aggiunta valutazioni totali ad ogni racconto
    for racconto in racconti_junior_senior:
        racconto.ranking = get_ranking_racconto(racconto)

    racconti_junior_senior = sorted(racconti_junior_senior, key=operator.attrgetter('ranking'), reverse=True)

    return racconti_junior_senior


# Lista dei valutatori di un concorso con relative valutazioni
# Permesso solo per il ruolo Segretario
def list_valutatori_selezioni(request, pk_event):
    # Controllo che l'utente sia un segretario
    permissions = get_permission(request.user.email)
    if not permissions["is_segretario"]:  # Non è un segretario
        return redirect('home')
    concorso = get_object_or_404(events, pk=pk_event)

    valutatori_concorso = concorso.valutatoriconcorso.all()

    for valutatore in valutatori_concorso:
        #Numero totale di racconti selezionati
        valutatore.numero_racconti_selezionati = get_numero_racconti_selezionati(valutatore)
        # Numero totale di racconti selezionati Junior
        valutatore.numero_racconti_selezionati_junior = get_numero_racconti_selezionati_junior(valutatore)
        # Numero totale di racconti selezionati Senior
        valutatore.numero_racconti_selezionati_senior = get_numero_racconti_selezionati_senior(valutatore)


    valutatori_concorso = sorted(valutatori_concorso, key=operator.attrgetter('idUser'), reverse=False)

    # print(valutatori_concorso)
    context = {'valutatori_concorso': valutatori_concorso, 'titolo_concorso': concorso.eventName,
               'pk_event': pk_event, 'inizio_periodo_selezioni': concorso.selectionDateStart,
               'scadenza_periodo_selezioni': concorso.selectionDateEnd, 'categorieeta': CATEGORIE_ETA, }
    context.update(permissions)
    context['max_num_racconti_selezionabili'] = concorso.maxSelections
    return render(request, 'list_valutatori_selezioni.html', context)


# Restituisce il numero di racconti selezionati da un valutatore
def get_numero_racconti_selezionati(valutatore):
    count = 0
    for valutazione in valutatore.valutatorevalutazione.all():
        if valutazione.selected:
            count += 1
    return count


# Restituisce il numero di racconti Junior selezionati da un valutatore
def get_numero_racconti_selezionati_junior(valutatore):
    count = 0
    for valutazione in valutatore.valutatorevalutazione.all():
        if valutazione.selected and valutazione.idRacconto.authorBirthDate >= valutatore.idEvent.birthDateLimit:
            count += 1
    return count

# Restituisce il numero di racconti Senior selezionati da un valutatore
def get_numero_racconti_selezionati_senior(valutatore):
    count = 0
    for valutazione in valutatore.valutatorevalutazione.all():
        if valutazione.selected and valutazione.idRacconto.authorBirthDate < valutatore.idEvent.birthDateLimit:
            count += 1
    return count

# Lista dei valutatori di un concorso con relative classificazioni
# Permesso solo per il ruolo Segretario
def list_valutatori_classificazioni(request, pk_event):
    # Controllo che l'utente sia un segretario
    permissions = get_permission(request.user.email)
    if not permissions["is_segretario"]:  # Non è un segretario
        return redirect('home')
    concorso = get_object_or_404(events, pk=pk_event)

    # Valutatori del concorso
    valutatori_concorso = concorso.valutatoriconcorso.all().order_by("idUser")

    # valutatori_concorso = sorted(valutatori_concorso, key=operator.attrgetter('idUser'), reverse=False)

    for valutatore in valutatori_concorso:
        valutatore.valutazioni = get_classifiche_valutatore(valutatore)

    valutatori_concorso = sorted(valutatori_concorso, key=operator.attrgetter('idUser'), reverse=False)

    #print(type(valutatori_concorso))

    # print(valutatori_concorso)
    context = {'valutatori_concorso': valutatori_concorso, 'titolo_concorso': concorso.eventName,
               'pk_event': pk_event, 'categorieeta': CATEGORIE_ETA,
               'inizio_periodo_classificazioni': concorso.classificationDateStart,
               'scadenza_periodo_classificazioni': concorso.classificationDateEnd}
    context.update(permissions)

    return render(request, 'list_valutatori_classificazioni.html', context)


# Restituisce il punteggio totale di un racconto
def get_ranking_racconto(racconto):
    ranking = 0

    for valutazione in racconto.raccontovalutazione.all():
        ranking += valutazione.ranking

    return ranking


# Invio messaggie email
def send_email(request, pk_event):
    # Controllo che l'utente sia un segretario
    permissions = get_permission(request.user.email)
    if not permissions["is_segretario"]:  # Non è un segretario
        return redirect('home')
    concorso = get_object_or_404(events, pk=pk_event)

    messaggio_inviato = {'messaggio_inviato': False}

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = MailForm(request.POST)

        # check whether it's valid:
        if form.is_valid():
            from html import unescape, escape

            subject = form.cleaned_data["subject"]
            body = form.cleaned_data["body"]
            destinatari = form.cleaned_data["destinatari"]

            # Modifica testo sostituendo i caratteri speciali in entities html
            body = da_carattere_speciale_ad_entity(body)
            body = body.replace('\n', '<br>')

            # Ricavo la lista dei destinatari
            if destinatari == "Tutti":  # Tutti i valutatori per il concorso
                lista_destinatari = valutatore.objects.filter(idEvent=concorso).values_list('idUser', flat=True)
                descrizione_destinatari = "Tutti i membri della commissione"

            elif destinatari == "Selezioni":  # Tutti i valutatori per il concorso che non hanno selezionato tutti i racconti consentiti
                destinatari = valutatore.objects.filter(idEvent=concorso)  # .values_list('idUser', flat=True)
                descrizione_destinatari = "Solo i membri della commissione che non hanno selezionato il numero massimo di racconti."
                lista_destinatari = []

                # Ricavo i valutatori che non hanno selezionato il numero massimo di racconti
                for dest in destinatari:
                    if (get_numero_racconti_selezionati(dest) < concorso.maxSelections):
                        lista_destinatari.append(dest.idUser)


            elif destinatari == "Valutazioni":
                destinatari = valutatore.objects.filter(idEvent=concorso)
                descrizione_destinatari = "Solo i membri della commissione che non hanno effettuato tutte le valutazioni per i racconti della categoria Junior e/o Senior"
                lista_destinatari = []
                # Ricavo i valutatori che non hanno valutazioni complete
                for dest in destinatari:
                    classifiche = get_classifiche_valutatore(dest)

                    if None in list(classifiche.values()):
                        lista_destinatari.append(dest.idUser)

            else:  # Opzione non valida
                return redirect('send_email', pk_event)

            # for i in lista_destinatari:
            #     print(i)

            # gmail = Gmail()
            # message = gmail.send_message(sender="noreply@unimib.it", to="luca.calabro@unimib.it",
            #                              subject='Test', message="<p>Test messaggio</p>")

            # Invio email
            for i in lista_destinatari:
                emailsender(subject, body, [i], [], [])

            # LOG operazione
            insert_log(username=request.user.email,
                       operationDate=datetime.now(),
                       roleUser="Segretario",
                       type="Invio comunicazione",
                       description="Invio comunicazione a \"{descrizione_destinatari}\" per il concorso con id = {id}".format(
                           descrizione_destinatari=descrizione_destinatari, id=id_active_event()),
                       )

            messaggio_inviato = {'messaggio_inviato': True}

            # return redirect('send_email', pk_event)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = MailForm()

    context = {'form': form, 'titolo_concorso': concorso.eventName,
               'pk_event': pk_event, 'categorieeta': CATEGORIE_ETA, 'id_event': id_active_event(), }
    context.update(permissions)

    context.update(messaggio_inviato)

    return render(request, 'send_email.html', context)


# Vista per racconto singolo con anagrafica(per segreteria)
@method_decorator(login_required, name='dispatch')
class GeneraPDF_SINGOLO_Con_Anagrafica(View):
    def get(self, request, pk, pk_event):
        template = get_template('pdf_template_singolo_con_anagrafica.html')
        concorso = get_object_or_404(events, pk=pk_event)
        racconto = get_object_or_404(racconti, pk=pk, idEvent=concorso)
        titolo_concorso = concorso.eventName
        anno = concorso.submissionDateStart.year

        context = {
            "racconto": racconto,
            "titolo_concorso": titolo_concorso,
            "anno": anno,
        }

        html = template.render(context)
        pdf = render_to_pdf('pdf_template_singolo_con_anagrafica.html', context)
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


# Vista per raccolta racconti con anagrafica per un dato concorso(per segreteria)
# A seconda del parametro pk_type fornira:
# pk_type = 1 -> Racconti consegnati
# pk_type = 2 -> Racconti selezionati
# pk_type = 3 -> Racconti classifica Junior
# pk_type = 4 -> Racconti classifica Senior
@method_decorator(login_required, name='dispatch')
class GeneratePDFMULTIPLO_Con_Anagrafica(View):
    def get(self, request, pk_type, pk_event):
        template = get_template('pdf_template_multiplo_con_anagrafica.html')
        concorso = get_object_or_404(events, pk=pk_event)

        if pk_type == 1:  # Queryset racconti consegnati per il concorso
            racconti = get_racconti_consegnati_concorso(concorso)
            filename = "Consegne " + concorso.eventName + ".pdf"
            title = "Consegne " + concorso.eventName
        elif pk_type == 2:  # Queryset racconti selezionati per il concorso
            racconti = get_racconti_selezionati_concorso(concorso)
            filename = "Selezioni " + concorso.eventName + ".pdf"
            title = "Selezioni " + concorso.eventName
        elif pk_type == 3:  # Queryset classifica Junior per il concorso
            racconti = get_racconti_junior_classificati_concorso(concorso)
            filename = "Classificati " + CATEGORIE_ETA[0] + " " + concorso.eventName + ".pdf"
            title = "Classificati " + CATEGORIE_ETA[0] + " " + concorso.eventName
        elif pk_type == 4:  # Queryset classifica Senior per il concorso
            racconti = get_racconti_senior_classificati_concorso(concorso)
            filename = "Classificati " + CATEGORIE_ETA[1] + " " + concorso.eventName + ".pdf"
            title = "Classificati " + CATEGORIE_ETA[1] + " " + concorso.eventName
        elif pk_type == 5:  # Queryset classifica Junior e Senior per il concorso
            racconti = get_racconti_junior_senior_classificati_concorso(concorso)
            filename = "Classificati " + concorso.eventName + ".pdf"
            title = "Classificati " + concorso.eventName
        elif pk_type == 6:  # Queryset solo racconti consegnati per il concorso pubblicabili
            racconti = get_racconti_consegnati_concorso_pubblicabili(concorso)
            filename = "Consegne " + concorso.eventName + ".pdf"
            title = "Consegne " + concorso.eventName


        else:
            return HttpResponseNotFound()

        context = {
            "racconti": racconti,
            "titolo_concorso": concorso.eventName,
            "anno": concorso.submissionDateStart.year,
        }
        html = template.render(context)
        pdf = render_to_pdf('pdf_template_multiplo_con_anagrafica.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = filename
            content = "inline; filename=%s" % (filename)
            download = request.GET.get("download")
            if download:
                content = "attachment; filename='%s'" % (filename)
            response['Content-Disposition'] = content
            return response
        return HttpResponse("Not found")


# Vista per generazione XLSX(per segreteria)
# https://www.dangtrinh.com/2016/01/generate-excel-file-with-openpyxl-in.html
# A seconda del parametro pk_type fornira:
# pk_type = 1 -> Racconti consegnati
# pk_type = 2 -> Racconti selezionati
# pk_type = 3 -> Racconti classifica Junior
# pk_type = 4 -> Racconti classifica Senior
@method_decorator(login_required, name='dispatch')
class GenerateXLSX_Con_Anagrafica(View):
    def get(self, request, pk_type, pk_event):
        concorso = get_object_or_404(events, pk=pk_event)

        # funzione che restituisce la posizione di un racconto
        # il ranking assegnato dal valutatore
        def get_posizione(ranking):
            if ranking == 3:
                return 1
            elif ranking == 2:
                return 2
            elif ranking == 1:
                return 3

        if pk_type == 1:  # Dati racconti consegnati per il concorso
            racconti = get_racconti_consegnati_concorso(concorso)
            filename = "Consegne " + concorso.eventName + ".xlsx"

            import datetime
            import pytz

            # Differenza di orario tra il timezone del database e quello locale
            # calculate time difference from utcnow and the local system time reported by OS
            offset = datetime.datetime.now() - datetime.datetime.utcnow()
            # offset = datetime.datetime.now(pytz.timezone('Europe/Rome')) - datetime.datetime.now(pytz.timezone('UTC'))

            print(datetime.datetime.now(), datetime.datetime.utcnow())
            print(datetime.datetime.now(pytz.timezone('Europe/Rome')), datetime.datetime.now(pytz.timezone('UTC')))
            print(offset)

            # Creazione lista dati per generare l'excel
            excel_data = [
                ['numero racconto', 'account', 'cognome', 'nome', 'data di nascita', 'tipologia autore', 'status età',
                 'consegnato il', 'titolo', 'contenuto', 'permessi di pubblicazione', 'contatti', 'coautori', ]]
            from datetime import datetime, timedelta
            for racconto in racconti:
                excel_data.append(
                    [
                        racconto.counter, racconto.idUser, racconto.authorSurname, racconto.authorForename,
                        (racconto.authorBirthDate + offset).strftime("%d/%m/%Y"), racconto.authorStatus,
                        [CATEGORIE_ETA[0] if racconto.authorBirthDate >= concorso.birthDateLimit else CATEGORIE_ETA[1]][
                            0],
                        (racconto.submissionDate + offset).strftime("%d/%m/%Y"), racconto.title,
                        racconto.content, racconto.publishingPermission, racconto.contacts, racconto.coAuthors,
                    ]
                )
        elif pk_type == 2:  # Dati racconti selezionati per il concorso
            racconti = get_racconti_selezionati_concorso(concorso)
            filename = "Selezioni " + concorso.eventName + ".xlsx"

            # Creazione lista dati per generare l'excel
            excel_data = [
                ['numero racconto', 'account', 'cognome', 'nome', 'status età', 'titolo', 'selezioni', ]]

            for racconto in racconti:
                excel_data.append(
                    [
                        racconto.counter, racconto.idUser, racconto.authorSurname, racconto.authorForename,
                        [CATEGORIE_ETA[0] if racconto.authorBirthDate >= concorso.birthDateLimit else CATEGORIE_ETA[1]][
                            0],
                        racconto.title,
                        ', '.join(
                            [valutazione.idValutatore.idUser for valutazione in racconto.raccontovalutazione.all() if
                             valutazione.selected]),
                    ]
                )

        elif pk_type == 3:  # Dati classifica Junior per il concorso
            racconti = get_racconti_junior_classificati_concorso(concorso)
            filename = "Classificati " + CATEGORIE_ETA[0] + " " + concorso.eventName + ".xlsx"

            # Creazione lista dati per generare l'excel
            excel_data = [
                ['numero racconto', 'account', 'cognome', 'nome', 'status età', 'titolo', 'punteggio totale',
                 'posizionamenti']]

            for racconto in racconti:
                excel_data.append(
                    [
                        racconto.counter, racconto.idUser, racconto.authorSurname, racconto.authorForename,
                        [CATEGORIE_ETA[0] if racconto.authorBirthDate >= concorso.birthDateLimit else CATEGORIE_ETA[1]][
                            0],
                        racconto.title,
                        racconto.ranking,
                        ', '.join(
                            [valutazione.idValutatore.idUser + " " + str(get_posizione(valutazione.ranking)) for
                             valutazione in racconto.raccontovalutazione.all() if
                             valutazione.ranking > 0]),

                    ]
                )


        elif pk_type == 4:  # Dati classifica Senior per il concorso
            racconti = get_racconti_senior_classificati_concorso(concorso)
            filename = "Classificati " + CATEGORIE_ETA[1] + " " + concorso.eventName + ".xlsx"
            # Creazione lista dati per generare l'excel
            excel_data = [
                ['numero racconto', 'account', 'cognome', 'nome', 'status età', 'titolo', 'punteggio totale',
                 'posizionamenti']]

            for racconto in racconti:
                excel_data.append(
                    [
                        racconto.counter, racconto.idUser, racconto.authorSurname, racconto.authorForename,
                        [CATEGORIE_ETA[0] if racconto.authorBirthDate >= concorso.birthDateLimit else CATEGORIE_ETA[1]][
                            0],
                        racconto.title,
                        racconto.ranking,
                        ', '.join(
                            [valutazione.idValutatore.idUser + " " + str(get_posizione(valutazione.ranking)) for
                             valutazione in racconto.raccontovalutazione.all() if
                             valutazione.ranking > 0]),

                    ]
                )
        elif pk_type == 5:  # Dati classifica Junior e Senior per il concorso
            racconti = get_racconti_junior_senior_classificati_concorso(concorso)
            filename = "Classificati " + concorso.eventName + ".xlsx"
            # Creazione lista dati per generare l'excel
            excel_data = [
                ['numero racconto', 'account', 'cognome', 'nome', 'status età', 'titolo', 'punteggio totale',
                 'posizionamenti']]

            for racconto in racconti:
                excel_data.append(
                    [
                        racconto.counter, racconto.idUser, racconto.authorSurname, racconto.authorForename,
                        [CATEGORIE_ETA[0] if racconto.authorBirthDate >= concorso.birthDateLimit else CATEGORIE_ETA[1]][
                            0],
                        racconto.title,
                        racconto.ranking,
                        ', '.join(
                            [valutazione.idValutatore.idUser + " " + str(get_posizione(valutazione.ranking)) for
                             valutazione in racconto.raccontovalutazione.all() if
                             valutazione.ranking > 0]),

                    ]
                )
        else:
            return HttpResponseNotFound()

        if excel_data:
            wb = Workbook(write_only=True)
            ws = wb.create_sheet()
            for line in excel_data:
                ws.append(line)

            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename=' + filename

            wb.save(response)

            return response
        else:

            return HttpResponse("Not found")
