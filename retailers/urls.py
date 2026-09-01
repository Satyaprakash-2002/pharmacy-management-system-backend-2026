
from django.urls import path

from .views import RetailerCreateView


urlpatterns = [

    path(

        "",

        RetailerCreateView.as_view(),

        name="create-retailer",

    ),

]