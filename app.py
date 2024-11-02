from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

DATABASE_CONFIG = {
    'dbname': os.getenv('DB_DATABASE'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

def get_db_connection():
    conn = psycopg2.connect(
        dbname=DATABASE_CONFIG['dbname'],
        user=DATABASE_CONFIG['user'],
        password=DATABASE_CONFIG['password'],
        host=DATABASE_CONFIG['host'],
        port=DATABASE_CONFIG['port']
    )
    return conn


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user = cursor.fetchone()
    
    conn.close()
    
    if user:
        return jsonify({"message": "Login successful", "user_id": user['id']})
    else:
        return jsonify({"message": "Invalid credentials"}), 401

@app.route('/sensor-data', methods=['GET'])
def get_sensor_data():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 1")
    latest_data = cursor.fetchone()
    
    conn.close()
    
    if latest_data:
        return jsonify(latest_data)
    else:
        return jsonify({"message": "No data available"}), 404


@app.route('/upload_data', methods=['POST'])
def upload_data():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO sensor_data (temperature, gas_level, light_intensity, fire_detected, fan_status, led_status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (
        data['temperature'],
        data['gas_level'],
        data['light_intensity'],
        data['fire_detected'],
        data['fan_status'],
        data['led_status']
    ))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Data uploaded successfully"}), 201
