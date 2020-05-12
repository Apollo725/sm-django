from __future__ import absolute_import
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from sm.new_frontend.profile.views.serializer import UserProfileSerializer
from sm.new_frontend.authenticate import HasProfile

import logging

logger = logging.getLogger(__name__)


class ProfileView(generics.RetrieveAPIView, generics.UpdateAPIView):
    permission_classes = (IsAuthenticated, HasProfile)
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user.sm.customer
