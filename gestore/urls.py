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

from segreteria.views import create_segretario, list_segretario, delete_segretario
from .views import create_event, update_event, list_event, detail_event

urlpatterns = [
    path('create_event/', create_event, name='create_event'),
    path('update_event/<int:pk>', update_event.as_view(), name='update_event'),
    path('list_event/', list_event.as_view(), name='list_event'),
    path('detail_event/<int:pk>', detail_event.as_view(), name='detail_event'),

    path('create_segretario/', create_segretario, name='create_segretario'),
    path('list_segretario/', list_segretario, name='list_segretario'),
    path('delete_segretario/<int:pk_segretario>', delete_segretario, name='delete_segretario'),
]
