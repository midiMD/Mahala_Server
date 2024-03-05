from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework import views, status
from rest_framework.response import Response
from .models import Profile
from .serializers import ProfileSerializer

class ProfileView(views.APIView):
    def get(self, request, pk, format=None):
        profile = get_object_or_404(Profile, pk=pk)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        profile = get_object_or_404(Profile, pk=pk)
        serializer = ProfileSerializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
