from flask import Flask, jsonify, render_template
import random
import json

with open("utils/game_rounds.json", "r") as f:
    rounds = json.load(f)

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/game")
def game():
    return jsonify(random.choice(rounds))

if __name__ == "__main__":
    app.run(debug=True)
