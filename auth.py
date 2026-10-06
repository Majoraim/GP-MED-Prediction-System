import hashlib
import sqlite3
import os

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_PATH, "prediction_records.db")

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
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            '''
            INSERT INTO users (
                full_name,
                email,
                user_type,
                organisation_name,
                username,
                password_hash
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (
                full_name,
                email,
                user_type,
                organisation_name,
                username,
                password_hash
            )
        )

        conn.commit()
        conn.close()

        return True, "Account created successfully!"

    except sqlite3.IntegrityError:
        return False, "Username already exists."

    except Exception as e:
        return False, f"Error creating account: {e}"


def login_user(username, password):

    username = username.strip()
    password_hash = hash_password(password)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        '''
        SELECT id, username, full_name, email,
               user_type, organisation_name
        FROM users
        WHERE username = ? AND password_hash = ?
        ''',
        (username, password_hash)
    )

    user = cursor.fetchone()

    conn.close()

    if user:
        return {
            "id": user[0],
            "username": user[1],
            "full_name": user[2],
            "email": user[3],
            "user_type": user[4],
            "organisation_name": user[5]
        }

    return None
