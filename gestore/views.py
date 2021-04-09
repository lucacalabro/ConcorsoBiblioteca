from datetime import datetime

from allauth.account.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from django.views.generic import UpdateView
from ConcorsoBiblioteca.utils import id_active_event, get_permission, insert_log
from .forms import eventsModelForm
from .models import events, gestore


# Create your views here.

# Crea un evento
# Permesso solo per il ruolo Gestore
@login_required
def create_event(request):
    # Controllo che l'utente sia un gestore
    utente_gestore = gestore.objects.filter(username=request.user.email)[:1]
    if utente_gestore.count() == 0:  # Non è un gestore
        return redirect('home')

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = eventsModelForm(request.POST)

        # check whether it's valid:
        if form.is_valid():
            form.save()

            # LOG operazione
            insert_log(username=request.user.email,
                       operationDate=datetime.now(),
                       roleUser="Gestore",
                       type="Creazione concorso",
                       description="Creazione concorso \"{titolo}\"".format(titolo=form.cleaned_data['eventName'], )
                       )
            return HttpResponseRedirect(reverse('list_event'))

    # if a GET (or any other method) we'll create a blank form
    else:
        form = eventsModelForm()
    context = {'form': form}
    permissions = get_permission(request.user.email)
    context.update(permissions)
    return render(request, 'create_event.html', context)


# Aggiorna un evento
# Permesso solo per il ruolo Gestore
@method_decorator(login_required, name='dispatch')
class update_event(UpdateView):
    model = events
    # form_class = eventsModelForm
    fields = "__all__"
    template_name = "update_event.html"

    # success_url = '/gestore/list_event/'  # reverse('list_event')

    def get_success_url(self):
        pk = self.kwargs["pk"]
        return reverse("detail_event", kwargs={"pk": pk})

    def get_initial(self):
        pk = self.kwargs["pk"]
        _event = events.objects.get(pk=pk)
        # print(_event.birthDateLimit)
        return {'birthDateLimit': _event.birthDateLimit, }

    def get(self, request, *args, **kwargs):
        # Controllo che l'utente sia un gestore
        utente_gestore = gestore.objects.filter(username=request.user.email)[:1]
        if utente_gestore.count() == 0:  # Non è un gestore
            return redirect('home')
        pk = self.kwargs["pk"]
        self.object = events.objects.get(pk=pk)
        context = self.get_context_data(object=self.object)
        permissions = get_permission(request.user.email)
        context.update(permissions)
        return self.render_to_response(context)


# Lista eventi
# Permesso solo per il ruolo Gestore
@method_decorator(login_required, name='dispatch')
class list_event(ListView):
    model = events
    template_name = "list_event.html"

    def get_context_data(self, **kwargs):
        context = super(list_event, self).get_context_data(**kwargs)
        context['id_evento_attivo'] = id_active_event()
        return context

    def get(self, request, *args, **kwargs):
        # Controllo che l'utente sia un gestore
        utente_gestore = gestore.objects.filter(username=request.user.email)[:1]
        if utente_gestore.count() == 0:  # Non è un gestore
            return redirect('home')
        self.object_list = events.objects.all().order_by('id')
        context = self.get_context_data(object_list=self.object_list)
        permissions = get_permission(request.user.email)
        context.update(permissions)
        return self.render_to_response(context)


# Dettagli evento
# Permesso solo per il ruolo Gestore
@method_decorator(login_required, name='dispatch')
class detail_event(DetailView):
    model = events
    template_name = "detail_event.html"

    def get(self, request, *args, **kwargs):
        # Controllo che l'utente sia un gestore
        utente_gestore = gestore.objects.filter(username=request.user.email)[:1]
        if utente_gestore.count() == 0:  # Non è un gestore
            return redirect('home')
        pk = self.kwargs["pk"]
        self.object = events.objects.get(pk=pk)
        context = self.get_context_data(object=self.object)
        permissions = get_permission(request.user.email)
        context.update(permissions)
        return self.render_to_response(context)
