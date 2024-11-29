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
        print("user logined in system")
        return jsonify({"message": "Login successful", "user_id": user['id']})
    else:
        print("error: Invalid User")
        return jsonify({"message": "Invalid credentials"}), 401

@app.route('/sensor-data', methods=['GET'])
def get_sensor_data():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 1")
    latest_data = cursor.fetchone()
    conn.close()
    
    if latest_data:
        print("data send : ",latest_data)
        return jsonify(latest_data)
    else:
        print("Error: No data available")
        return jsonify({"message": "No data available"}), 404


@app.route('/upload_data', methods=['POST'])
def upload_data():
    data = request.json

    print("Received data:", data)

    required_keys = ['temperature', 'gas_level', 'light_intensity', 'fire_detected', 'fan_status', 'led_status']
    for key in required_keys:
        if key not in data:
            print(f"error: '{key}' is required")
            return jsonify({"error": f"'{key}' is required"}), 400

    try:
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
        print("Data uploaded successfully")
        return jsonify({"message": "Data uploaded successfully"}), 201

    except Exception as e:
        print("Error:", e) 
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

def get_hourly_averages():
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT 
        DATE_TRUNC('hour', timestamp) AS hour,
        AVG(temperature) AS avg_temperature,
        AVG(gas_level) AS avg_gas,
        BOOL_OR(light_intensity) AS avg_light,
        BOOL_OR(fire_detected) AS avg_fire,
        BOOL_OR(fan_status::boolean) AS avg_fan,
        BOOL_OR(led_status::boolean) AS avg_led
    FROM sensor_data
    WHERE timestamp >= NOW() - INTERVAL '24 HOURS'
    GROUP BY hour
    ORDER BY hour;
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "hour": row[0].strftime("%H:00"),
            "avg_temperature": round(row[1], 2),
            "avg_gas": round(row[2], 2),
            "avg_light": "true" if row[3] else "false",
            "avg_fire": "true" if row[4] else "false",
            "avg_fan": "true" if row[5] else "false",
            "avg_led": "true" if row[6] else "false",
        })

    return results

@app.route("/api/hourly-averages", methods=["GET"])
def hourly_averages():
    data = get_hourly_averages()
    return jsonify(data)