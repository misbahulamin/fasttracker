from django.apps import AppConfig
import firebase_admin
from firebase_admin import credentials
import os
from django.conf import settings

class MaintenanceConfig(AppConfig):
    name = 'maintenance'

    def ready(self):
        # Initialize Firebase Admin if not already initialized
        if not firebase_admin._apps:
            firebase_credentials_path = getattr(settings, 'FIREBASE_CREDENTIALS', None)
            if firebase_credentials_path and os.path.exists(firebase_credentials_path):
                cred = credentials.Certificate(firebase_credentials_path)
                firebase_admin.initialize_app(cred)
            else:
                raise FileNotFoundError("Firebase credentials file not found.")
        from . import signals
