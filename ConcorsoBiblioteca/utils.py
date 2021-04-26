# deriva il concorso attivo se esiste
import threading

from django.utils import timezone
from gestore.models import events, gestore
from autore.models import racconti
from django.utils import timezone
from gestore.models import events
from ConcorsoBiblioteca.settings import COUNTER

# Restituisce l'id dell'evento attivo se esistente
# None altrimenti
from segreteria.models import segretario
from valutatore.models import valutatore


# Restituisce l'id del concorso attivo se c'è
# altrimenti None
def id_active_event():
    now = timezone.now()

    for e in events.objects.all():
        if now >= e.submissionDateStart and now <= e.classificationDateEnd:
            return e.pk
    return None


# Controlla se il perioro di selezione racconti è attivo
# per il concorso in atto
# restituisce True o False
def is_selectable():
    idEvent = id_active_event()

    if idEvent is not None:
        evento_attivo = events.objects.all().get(pk=idEvent)
        now = timezone.now()
        # Controllo se si è nell'intervallo valido per l'invio dei racocnti
        #if now >= evento_attivo.selectionDateStart and now <= evento_attivo.selectionDateEnd:
        if now <= evento_attivo.selectionDateEnd:
            return True
        else:
            return False
    else:
        return False



# Controlla se il perioro di selezione racconti è attivo
# per il concorso in atto, se non è ancora iniziato
#i valutatori potranno solamente leggere i racconti inviati
# restituisce True o False
def is_only_readable():
    idEvent = id_active_event()

    if idEvent is not None:
        evento_attivo = events.objects.all().get(pk=idEvent)
        now = timezone.now()
        # Controllo se si è nell'intervallo valido per l'invio dei racocnti
        #if now >= evento_attivo.selectionDateStart and now <= evento_attivo.selectionDateEnd:
        if now < evento_attivo.selectionDateStart:
            #print("w")
            return True
        else:
            #print("q")
            return False
    else:
        return False


# Controlla se il perioro di votazione  racconti è attivo
# per il concorso in atto
# restituisce True o False
def is_classifiable():
    idEvent = id_active_event()

    if idEvent is not None:
        evento_attivo = events.objects.all().get(pk=idEvent)
        now = timezone.now()
        # Controllo se si è nell'intervallo valido per l'invio dei racocnti
        if now >= evento_attivo.classificationDateStart and now <= evento_attivo.classificationDateEnd:
            return True
        else:
            return False
    else:
        return False


# se c'è un evento attivo restituisce True se
# l'utente è nel periodo in cui sono consentite le sottomissioni dei racconti
# e non è stata superata la soglia dei racconti inviabili
# false se non lo sono
# se non c'è un evento attivo restituisce None
def is_active_event_submittible():
    idEvent = id_active_event()

    if idEvent is not None:
        evento_attivo = events.objects.all().get(pk=idEvent)
        now = timezone.now()

        # Controllo se si è nell'intervallo valido per l'invio dei racocnti
        if now >= evento_attivo.submissionDateStart and now <= evento_attivo.submissionDateEnd:
            # Controllo che la soglia dei racconti inviabili non sia stata raggiunta
            numero_racconti_inviati = racconti.objects.filter(idEvent=evento_attivo).count()
            numero_racconti_inviabili = evento_attivo.maxSubmissions
            if (numero_racconti_inviati >= numero_racconti_inviabili):
                return False
            else:
                return True
        else:
            return False
    else:
        return None


# restituisce True se l'utente è un valutatore per un dato Concorso altrimenti False
def is_valutatore(user, pk_event):
    from valutatore.models import valutatore

    if valutatore.objects.all().filter(idUser=user, idEvent=pk_event).count() > 0:
        return True
    else:
        return False


# calcola il valore del counter per un dato racconto
def get_counter():
    # Ultimo counter assegnato, se non c'è il valore sarà uguale a COUNTER(settings.py)
    ultimo_racconto_set = racconti.objects.filter(idEvent=id_active_event()).order_by('-id')[:1]
    if ultimo_racconto_set.count() == 0:
        return COUNTER
    else:
        return ultimo_racconto_set[0].counter + 1


# controlla se l'utente ha inviato il racconto per il concorso in atto
def is_submitted_in_active_event(useremail):
    # Eventuale racconto inviato dall'utente
    ultimo_racconto_set = racconti.objects.filter(idEvent=id_active_event(), idUser=useremail).order_by('-id')[:1]
    if ultimo_racconto_set.count() == 0:
        return False
    else:
        return True


# Restituisce dizionario dei permessi
# per le voci di menù
def get_permission(user):
    if id_active_event() is None:
        concorso = None
    else:
        concorso = events.objects.all().get(pk=id_active_event())

    res = {}
    # print(type(concorso))

    # Controllo che l'utente sia un gestore
    is_gestore = False
    utente_gestore = gestore.objects.filter(username=user)[:1]
    if utente_gestore.count() != 0:  # Non è un gestore
        is_gestore = True
    res["is_gestore"] = is_gestore

    # Controllo che l'utente sia un valutatore
    is_valutatore = False
    if concorso is not None:
        utente_valutatore = valutatore.objects.filter(idUser=user, idEvent=concorso)[:1]
        if utente_valutatore.count() != 0:  # Non è un gestore
            is_valutatore = True
    res["is_valutatore"] = is_valutatore

    # Controllo che l'utente sia un segretario
    is_segretario = False
    utente_segretario = segretario.objects.filter(idUser=user)[:1]
    if utente_segretario.count() != 0:  # Non è un gestore
        is_segretario = True
    res["is_segretario"] = is_segretario

    # Controllo che l'utente abbia già inviato un racconto per il concorso corrente
    res["is_inviato"] = is_submitted_in_active_event(user)

    return res


# Restituisce la data per cui stabilire se un autore è di categoria Junior o senior
def get_birthDateLimit():
    return events.objects.all().get(pk=id_active_event()).birthDateLimit


# Serve a generare i PDF
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


from gestore.models import log


# Inserisce un entry nella tabella dei log
def insert_log(username, operationDate, roleUser, type, description):
    import pytz
    from datetime import datetime
    tz = pytz.timezone('Europe/Rome')
    entry_log = log(
        username=username,
        operationDate=datetime.utcnow().replace(tzinfo=tz),
        roleUser=roleUser,
        type=type,
        description=description
    )
    entry_log.save()


# Inserisce racconti di test per il concorso attivo
# age = 0 Categoria Junior
# a <> 0 Categoria Senior
def insert_racconti(age):
    import random, string
    import datetime
    publishingPermission = True

    if age == 0:
        _authorBirthDate = timezone.now()
    else:
        _authorBirthDate = datetime.datetime(1967, 5, 17)

    for i in range(0, 20):
        if i % 2 == 0:
            publishingPermission = True
        else:
            publishingPermission = False

        letters = string.ascii_lowercase
        nome = ''.join(random.choice(letters) for i in range(10))
        cognome = ''.join(random.choice(letters) for i in range(10))

        racconto = racconti(
            counter=get_counter(),
            idUser=nome + "." + cognome + "@unimib.it",
            idEvent=events.objects.all().get(pk=id_active_event()),
            title="Titolo racconto " + str(get_counter()),
            content=content_test,
            submissionDate=timezone.now(),
            publishingPermission=publishingPermission,
            contacts="contacts di " + nome + "." + cognome + "@unimib.it",
            coAuthors="coAuthors di " +nome + "." + cognome + "@unimib.it",
            authorSurname=cognome,
            authorForename=nome,
            authorBirthDate=_authorBirthDate,
            authorStatus="authorStatus di " + nome + "." + cognome + "@unimib.it",
            authorDetail="authorDetail di " + nome + "." + cognome + "@unimib.it",
        )

        racconto.save()


content_test = "At vero eos et accusamus et iusto odio dignissimos ducimus " \
               "qui blanditiis praesentium voluptatum deleniti atque corrupti " \
               "quos dolores et quas molestias excepturi sint occaecati cupiditate " \
               "non provident, similique sunt in culpa qui officia deserunt mollitia animi," \
               " id est laborum et dolorum fuga. Et harum quidem rerum facilis est et expedita " \
               "distinctio. Nam libero tempore, cum soluta nobis est eligendi optio cumque nihil " \
               "impedit quo minus id quod maxime placeat facere possimus, omnis voluptas assumenda est," \
               " omnis dolor repellendus. Temporibus autem quibusdam et aut officiis debitis aut rerum" \
               " necessitatibus saepe eveniet ut et voluptates repudiandae sint et molestiae non recusandae." \
               " Itaque earum rerum hic tenetur a sapiente delectus, ut aut reiciendis voluptatibus maiores alias" \
               " consequatur aut perferendis doloribus asperiores repellat."
