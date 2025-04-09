import hashlib
import os
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )


def check_user_exists(username):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = f"""
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
        return jsonify({'All fields are required'}), 400

    if check_user_exists(username):
        return jsonify('Username already exists'), 400

    try:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        conn = get_db_connection()
        cursor = conn.cursor()

        query = f"""
        INSERT INTO 
            users (username, password)
        VALUES 
            (%s, %s)
        RETURNING user_id;
        """
        cursor.execute(query, (username, hashed_password))
        user_id = cursor.fetchone()[0]
        conn.commit()

        conn.close()
        return jsonify({'username': username, 'userId': user_id}), 200

    except Exception as e:
        return jsonify({str(e)}), 500


@app.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    if not data:
        return jsonify({'No data provided'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'All fields are required'}), 400

    try:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        conn = get_db_connection()
        cursor = conn.cursor()

        query = f"""
            SELECT
                user_id, username
            FROM
                users
            WHERE
                username = %s AND password = %s;
        """
        cursor.execute(query, (username, hashed_password))
        result = cursor.fetchone()

        conn.close()
        if result:
            user_id, username = result
            return jsonify({'userId': user_id, 'username': username}), 200
        else:
            return jsonify({'Invalid credentials'}), 401

    except Exception as e:
        return jsonify({str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=3100, host='0.0.0.0')
