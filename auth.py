import hashlib
import re

import streamlit as st
from supabase import create_client


def _clean_url(raw):
    """Keep only https://PROJECT-ID.supabase.co (drops spaces, quotes, slashes, extra paths)."""
    raw = str(raw).strip().strip('"').strip("'").strip()
    match = re.match(r"(https://[A-Za-z0-9\-]+\.supabase\.co)", raw)
    if not match:
        raise ValueError(
            "SUPABASE_URL in Streamlit Secrets is not a valid Supabase URL. "
            "It should look like https://your-project-id.supabase.co"
        )
    return match.group(1)


@st.cache_resource
def get_supabase():
    url = _clean_url(st.secrets["SUPABASE_URL"])
    key = str(st.secrets["SUPABASE_KEY"]).strip().strip('"').strip("'").strip()
    return create_client(url, key)


def hash_password(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def create_user(
    full_name,
    email,
    user_type,
    organisation_name,
    username,
    password
):
    full_name = full_name.strip()
    email = email.strip()
    username = username.strip()

    if not full_name:
        return False, "Full name is required."

    if not email:
        return False, "Email is required."

    if not username:
        return False, "Username is required."

    if not password:
        return False, "Password is required."

    if user_type not in ["Personal", "Organisation"]:
        return False, "Invalid user type."

    if user_type == "Organisation":
        if not organisation_name.strip():
            return False, "Organisation name is required."
    else:
        organisation_name = None

    password_hash = hash_password(password)

    try:
        get_supabase().table("users").insert({
            "full_name": full_name,
            "email": email,
            "user_type": user_type,
            "organisation_name": organisation_name,
            "username": username,
            "password_hash": password_hash,
        }).execute()

        return True, "Account created successfully!"

    except Exception as e:
        error_text = str(e).lower()

        if "duplicate" in error_text or "23505" in error_text or "unique" in error_text:
            return False, "Username already exists."

        return False, f"Error creating account: {e}"


def login_user(username, password):

    username = username.strip()
    password_hash = hash_password(password)

    res = (
        get_supabase()
        .table("users")
        .select(
            "id,username,full_name,email,user_type,organisation_name"
        )
        .eq("username", username)
        .eq("password_hash", password_hash)
        .limit(1)
        .execute()
    )

    if res.data:
        user = res.data[0]
        return {
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "email": user["email"],
            "user_type": user["user_type"],
            "organisation_name": user["organisation_name"]
        }

    return None
