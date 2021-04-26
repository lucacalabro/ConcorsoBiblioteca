"""ConcorsoBiblioteca URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path

from .views import create_valutatore, list_valutatore, delete_valutatore, selezione_racconti, seleziona_racconto, \
    deseleziona_racconto, GeneratePDFMULTIPLORaccontiSelezionati, GeneraPDF_SINGOLO, votazione_racconti, \
    votazione_racconto, GeneratePDFMULTIPLORaccontiSelezionabili, lettura_racconto, nonlettura_racconto

urlpatterns = [
    path('create_valutatore/<int:pk_event>', create_valutatore, name='create_valutatore'),
    path('list_valutatore/<int:pk_event>', list_valutatore, name='list_valutatore'),
    path('delete_valutatore/<int:pk_valutatore>', delete_valutatore, name='delete_valutatore'),

    path('selezione_racconti/<int:page_number>/<str:categoriaeta>', selezione_racconti, name='selezione_racconti'),
    path('seleziona_racconto/<int:pk_racconto>/<int:page_number>/<str:categoriaeta>', seleziona_racconto,
         name='seleziona_racconto'),
    path('deseleziona_racconto/<int:pk_racconto>/<int:page_number>/<str:categoriaeta>', deseleziona_racconto,
         name='deseleziona_racconto'),

    path('votazione_racconti/<str:categoriaeta>', votazione_racconti, name='votazione_racconti'),

    path('votazione_racconto/<int:counter_id_racconto>/<str:categoriaeta>/<int:classifica>', votazione_racconto,
         name='votazione_racconto'),

    path('lettura_racconto/<int:pk_racconto>/<int:page_number>/<str:categoriaeta>', lettura_racconto,
         name='lettura_racconto'),

    path('nonlettura_racconto/<int:pk_racconto>/<int:page_number>/<str:categoriaeta>', nonlettura_racconto,
         name='nonlettura_racconto'),

    path('singolo/<int:pk>', GeneraPDF_SINGOLO.as_view(), name='singolo'),
    path('multiploselezionati/', GeneratePDFMULTIPLORaccontiSelezionati.as_view(), name='multiploselezionati'),
    path('multiploselezionabili/', GeneratePDFMULTIPLORaccontiSelezionabili.as_view(), name='multiploselezionabili'),

]
