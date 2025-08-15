import json
from typing import Any, Dict, Optional

import streamlit as st
from firebase_admin import credentials, firestore, initialize_app, auth
import firebase_admin


_admin_initialized = False


def _init_admin_if_needed() -> None:
    global _admin_initialized
    if _admin_initialized:
        return

    service_json_str = st.secrets.get("firebase", {}).get("service_account_json")
    if not service_json_str:
        raise RuntimeError("Firebase service_account_json eksik. .streamlit/secrets.toml dosyasını doldurun.")
    service_dict = json.loads(service_json_str)
    cred = credentials.Certificate(service_dict)
    if not firebase_admin._apps:
        initialize_app(cred)
    _admin_initialized = True


def get_firestore_client() -> Any:
    _init_admin_if_needed()
    return firestore.client()


class FirebaseAuthWrapper:
    """Wrapper to provide pyrebase-like API using firebase-admin"""
    
    def __init__(self):
        _init_admin_if_needed()
        self.auth = auth
    
    def create_user_with_email_and_password(self, email: str, password: str) -> Dict[str, Any]:
        try:
            user = self.auth.create_user(
                email=email,
                password=password
            )
            return {"localId": user.uid, "uid": user.uid}
        except Exception as e:
            raise Exception(str(e))
    
    def sign_in_with_email_and_password(self, email: str, password: str) -> Dict[str, Any]:
        try:
            # For demo purposes, we'll accept any email/password
            # In production, you'd need to implement proper authentication
            return {"localId": "demo_user", "uid": "demo_user"}
        except Exception as e:
            raise Exception(str(e))
    
    def send_password_reset_email(self, email: str) -> None:
        try:
            # For demo purposes
            pass
        except Exception as e:
            raise Exception(str(e))


def get_pyrebase_auth() -> FirebaseAuthWrapper:
    return FirebaseAuthWrapper()