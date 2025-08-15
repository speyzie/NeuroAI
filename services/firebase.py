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


def get_firebase_auth() -> Any:
    _init_admin_if_needed()
    return auth


# For backward compatibility
def get_pyrebase_auth() -> Any:
    """Backward compatibility function - returns firebase-admin auth"""
    return get_firebase_auth()