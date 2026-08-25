from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets

from .models import House
from .serializers import HouseSerializer


class HouseViewSet(viewsets.ModelViewSet):

    queryset = House.objects.all()

    serializer_class = HouseSerializer