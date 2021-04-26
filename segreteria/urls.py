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

from .views import list_event_segreteria, list_racconti_segreteria, list_selezioni_segreteria, list_racconti_junior, \
    list_racconti_senior, GeneraPDF_SINGOLO_Con_Anagrafica, GeneratePDFMULTIPLO_Con_Anagrafica, \
    GenerateXLSX_Con_Anagrafica, list_racconti_junior_senior, list_valutatori_selezioni, \
    list_valutatori_classificazioni, send_email, delete_racconto

urlpatterns = [
    path('list_event_segreteria/', list_event_segreteria.as_view(), name='list_event_segreteria'),
    path('list_racconti_segreteria/<int:pk_event>', list_racconti_segreteria, name='list_racconti_segreteria'),
    path('list_selezioni_segreteria/<int:pk_event>', list_selezioni_segreteria, name='list_selezioni_segreteria'),
    path('list_racconti_junior/<int:pk_event>', list_racconti_junior, name='list_racconti_junior'),
    path('list_racconti_senior/<int:pk_event>', list_racconti_senior, name='list_racconti_senior'),
    path('list_racconti_junior_senior/<int:pk_event>', list_racconti_junior_senior, name='list_racconti_junior_senior'),
    path('list_valutatori_selezioni/<int:pk_event>', list_valutatori_selezioni, name='list_valutatori_selezioni'),
    path('list_valutatori_classificazioni/<int:pk_event>', list_valutatori_classificazioni,
         name='list_valutatori_classificazioni'),
    path('send_email/<int:pk_event>', send_email, name='send_email'),

    path('GeneraPDF_SINGOLO_Con_Anagrafica/<int:pk>/<int:pk_event>', GeneraPDF_SINGOLO_Con_Anagrafica.as_view(),
         name='GeneraPDF_SINGOLO_Con_Anagrafica'),

    path('GeneratePDFMULTIPLO_Con_Anagrafica/<int:pk_type>/<int:pk_event>',
         GeneratePDFMULTIPLO_Con_Anagrafica.as_view(),
         name='GeneratePDFMULTIPLO_Con_Anagrafica'),

    path('GeneratePDFMULTIPLO_Con_Anagrafica_Solo_Pubblicabili/<int:pk_type>/<int:pk_event>',
         GeneratePDFMULTIPLO_Con_Anagrafica.as_view(),
         name='GeneratePDFMULTIPLO_Con_Anagrafica_Solo_Pubblicabili'),

    path('GenerateXLSX_Con_Anagrafica/<int:pk_type>/<int:pk_event>',
         GenerateXLSX_Con_Anagrafica.as_view(),
         name='GenerateXLSX_Con_Anagrafica'),

    path('delete_racconto/<int:pk_racconto>', delete_racconto, name="delete_racconto"),



]
