import json
from typing import Any, Dict, Optional

import streamlit as st
from firebase_admin import credentials, firestore, initialize_app
import firebase_admin
import pyrebase


_admin_initialized = False
_pyrebase_app: Optional[Any] = None


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


def get_pyrebase_auth() -> Any:
    global _pyrebase_app
    if _pyrebase_app is None:
        cfg = st.secrets.get("firebase", {})
        config: Dict[str, Any] = {
            "apiKey": cfg.get("api_key"),
            "authDomain": cfg.get("auth_domain"),
            "databaseURL": cfg.get("database_url"),
            "projectId": cfg.get("project_id"),
            "storageBucket": cfg.get("storage_bucket"),
            "messagingSenderId": cfg.get("messaging_sender_id"),
            "appId": cfg.get("app_id"),
        }
        _pyrebase_app = pyrebase.initialize_app(config)
    return _pyrebase_app.auth()