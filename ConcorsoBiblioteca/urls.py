"""ConcorsoLetterarioBiblioteca URL Configuration

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
from django.contrib import admin
from django.urls import path, include, re_path
from home.views import homepage, login

urlpatterns = [
    #path('admin/', admin.site.urls),
    path('', login, name="login"),

    #Schermata di login per le pagine autenticate
    path('accounts/login/', login),  # <--
    #re_path(r'^articles/(?P<year>[0-9]{4})/$),

    path('home/', homepage, name="home"),
    path('gestore/', include('gestore.urls')),
    path('valutatore/', include('valutatore.urls')),
    path('autore/', include('autore.urls')),
    path('segreteria/', include('segreteria.urls')),
    path('accounts/', include('allauth.urls')),

]
