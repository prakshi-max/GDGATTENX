import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st

# Initialize Firebase app only once
if not firebase_admin._apps:
    service_account_info = st.secrets["firebase"]
    cred = credentials.Certificate(dict(service_account_info))
    firebase_admin.initialize_app(cred)

db = firestore.client() 