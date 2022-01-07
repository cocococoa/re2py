from django.urls import path

from . import views

app_name = "reviz"
urlpatterns = [
    path('', views.index, name='index'),
]
