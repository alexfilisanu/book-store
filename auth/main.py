import datetime
import hashlib
import os
import jwt
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "my-secret-key")


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )


def generate_tokens(user_id, username, role):
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    }
    access_token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

    refresh_payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    refresh_token = jwt.encode(refresh_payload, app.config['SECRET_KEY'], algorithm='HS256')

    return access_token, refresh_token


def check_user_exists(username):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT
            username
        FROM
            users
        WHERE
            username = %s;
        """
        cursor.execute(query, (username,))
        result = cursor.fetchone()

        conn.close()
        return result is not None

    except Exception as e:
        return jsonify({str(e)}), 500


@app.route('/auth/register', methods=['POST'])
def register():
    data = request.json
    if not data:
        return jsonify({'No data provided'}), 400

    username = data.get('username')
    password = data.get('password')

    if not all([username, password]):
        return jsonify({'error': 'All fields are required'}), 400

    if check_user_exists(username):
        return jsonify({'error': 'Username already exists'}), 400

    try:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        INSERT INTO 
            users (username, password)
        VALUES 
            (%s, %s)
        RETURNING user_id;
        """
        cursor.execute(query, (username, hashed_password))
        user_id = cursor.fetchone()[0]
        conn.commit()

        access_token, refresh_token = generate_tokens(user_id, username, 'user')
        return jsonify({'access_token': access_token, 'refresh_token': refresh_token}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    if not data:
        return jsonify({'No data provided'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'All fields are required'}), 400

    try:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                user_id, username, role
            FROM
                users
            WHERE
                username = %s AND password = %s;
        """
        cursor.execute(query, (username, hashed_password))
        result = cursor.fetchone()

        conn.close()
        if result:
            user_id, username, role = result
            access_token, refresh_token = generate_tokens(user_id, username, role)
            return jsonify({'access_token': access_token, 'refresh_token': refresh_token}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/auth/refresh', methods=['POST'])
def refresh_token():
    data = request.json
    refresh_token = data.get('refresh_token')

    if not refresh_token:
        return jsonify({'error': 'Refresh token required'}), 400

    try:
        decoded = jwt.decode(refresh_token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = decoded['user_id']

        payload = {
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
        }
        new_access_token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({'access_token': new_access_token}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Refresh token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid refresh token'}), 401


if __name__ == "__main__":
    app.run(debug=True, port=3100, host='0.0.0.0')
