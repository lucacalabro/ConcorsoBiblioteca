from django.http import HttpResponse
from django.shortcuts import render
from allauth.account.decorators import login_required
from ConcorsoBiblioteca.utils import id_active_event, is_active_event_submittible, is_submitted_in_active_event, \
    get_permission
from autore.models import racconti
from gestore.models import events
from django.utils import timezone






def login(request):
    context = {}
    if hasattr(request.user, 'email'):
        permissions = get_permission(request.user.email)
        context.update(permissions)

    return render(request, "home_not_logged.html", context)

# Homepage
@login_required
def homepage(request):
    idEvent = id_active_event()
    permissions = get_permission(request.user.email)

    if idEvent is not None:
        evento_attivo = events.objects.all().get(pk=idEvent)

        # Numero di giorni rimasti alla scadenza del periodo valido per l'invio dei racconti
        delta = evento_attivo.submissionDateEnd - timezone.now()

        context = {
            'idEvent': idEvent,
            'titolo_concorso': evento_attivo.eventName,
            'is_submittable': is_active_event_submittible(),
            'numero_racconti_inviati': racconti.objects.filter(idEvent=evento_attivo).count(),
            'numero_racconti_inviabili': evento_attivo.maxSubmissions,
            'posti_disponibili': evento_attivo.maxSubmissions - racconti.objects.filter(idEvent=evento_attivo).count(),
            'delta': delta.days,
        }
        context.update(permissions)
        return render(request, "home.html", context=context)

    return render(request, "home.html",  context=permissions)
