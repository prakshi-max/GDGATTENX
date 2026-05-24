import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st

# Initialize Firebase app only once
if not firebase_admin._apps:
    service_account_info = None
    if st.secrets and "firebase" in st.secrets:
        service_account_info = st.secrets["firebase"]
        if not isinstance(service_account_info, dict):
            service_account_info = dict(service_account_info)
    elif os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON"):
        raw_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        try:
            service_account_info = json.loads(raw_json)
        except json.JSONDecodeError:
            raise RuntimeError(
                "FIREBASE_SERVICE_ACCOUNT_JSON must contain valid JSON for the Firebase service account."
            )

    if not service_account_info and os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        cred = credentials.ApplicationDefault()
    elif service_account_info:
        cred = credentials.Certificate(service_account_info)
    else:
        raise RuntimeError(
            "Firebase credentials are missing. Add a `firebase` secret in .streamlit/secrets.toml "
            "or set the environment variable FIREBASE_SERVICE_ACCOUNT_JSON."
        )

    firebase_admin.initialize_app(cred)

db = firestore.client() 