import hashlib
import streamlit as st
from supabase import create_client

def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def _extract_data(res):
    """Helper untuk mengekstrak data dari Supabase versi berapapun"""
    if res is None:
        return None
    if hasattr(res, 'data'):
        return res.data
    if isinstance(res, tuple) and len(res) > 0:
        return res[0]
    return res

def login_user(username, password):
    try:
        supabase = init_supabase()
        hashed_pw = hash_password(password)
        res = supabase.table('users').select('*').eq('username', username).eq('password', hashed_pw).execute()
        
        data = _extract_data(res)
        
        if data and isinstance(data, list) and len(data) > 0:
            user_item = data[0]
            if isinstance(user_item, dict):
                return user_item
        return None
    except Exception as e:
        print(f"Error login_user: {e}")
        return None

def register_user(username, password, nama_lengkap, email=None):
    try:
        supabase = init_supabase()
        hashed_pw = hash_password(password)
        payload = {
            "username": username,
            "password": hashed_pw,
            "nama_lengkap": nama_lengkap,
            "email": email,
            "role": "peserta",
            "sudah_mengerjakan": False
        }
        res = supabase.table('users').insert(payload).execute()
        data = _extract_data(res)
        return data
    except Exception as e:
        print(f"Error register_user: {e}")
        return None

def save_survey_response(user_id, username, response_dict):
    try:
        supabase = init_supabase()
        payload = {
            "user_id": user_id,
            "username": username,
            "data": response_dict
        }
        supabase.table('responses').insert(payload).execute()
        
        # Update status user
        supabase.table('users').update({"sudah_mengerjakan": True}).eq('id', user_id).execute()
        return True
    except Exception as e:
        print(f"Error save_survey_response: {e}")
        return False

def check_user_already_submitted(user_id):
    try:
        supabase = init_supabase()
        res = supabase.table('responses').select('id').eq('user_id', user_id).execute()
        data = _extract_data(res)
        return bool(data and len(data) > 0)
    except Exception as e:
        print(f"Error check_user_already_submitted: {e}")
        return False

def get_all_responses():
    try:
        supabase = init_supabase()
        res = supabase.table('responses').select('*').order('submitted_at', desc=True).execute()
        data = _extract_data(res)
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error get_all_responses: {e}")
        return []

def get_all_users():
    try:
        supabase = init_supabase()
        res = supabase.table('users').select('*').order('created_at', desc=True).execute()
        data = _extract_data(res)
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error get_all_users: {e}")
        return []