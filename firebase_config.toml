import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore


def init_firebase():
    try:
        if not firebase_admin._apps:
            firebase_config = dict(st.secrets["firebase"])
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred)

        return firestore.client()

    except Exception as e:
        st.warning(f"Erro ao conectar ao Firebase: {e}")
        return None
