from flask import Flask, jsonify, render_template, request
import random
import json
import mysql.connector
import os

ENV = os.getenv("FLASK_ENV", "development")

def get_db_connection():
    if ENV == "development":
        return mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password=os.getenv("MYSQL_PASSWORD"),
            database="ai_impostor_dev"
        )
    else:  # production on PythonAnywhere
        return mysql.connector.connect(
            host="ferraijv.mysql.pythonanywhere-services.com",
            user="ferraijv",
            password=os.getenv("MYSQL_PASSWORD"),
            database="ferraijv$data"
        )

with open("utils/game_rounds.json", "r") as f:
    rounds = json.load(f)

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/game")
def game():
    return jsonify(random.choice(rounds))


@app.route("/submit_guess", methods=["POST"])
def submit_guess():
    data = request.get_json()

    game_id = data["game_id"]
    guessed_index = data["guessed_index"]
    correct_index = data["correct_index"]
    model_used = data["model_used"]
    is_correct = guessed_index == correct_index

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO guesses (game_id, guessed_index, correct_index, is_correct, model_used)
            VALUES (%s, %s, %s, %s, %s)
        """, (game_id, guessed_index, correct_index, is_correct, model_used))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "success"}), 200

    except Exception as e:
        print("DB error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/leaderboard")
def leaderboard():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # so we get dicts instead of tuples

        cursor.execute("""
            SELECT 
                model_used,
                ROUND(AVG(is_correct) * 100, 2) AS accuracy_percent,
                COUNT(*) AS total_guesses
            FROM guesses
            GROUP BY model_used
            ORDER BY accuracy_percent
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template("leaderboard.html", leaderboard=rows)

    except Exception as e:
        return f"<p>Error loading leaderboard: {e}</p>", 500


if __name__ == "__main__":
    app.run(debug=True)
