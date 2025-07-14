# chat_backend.py (producción actualizado para Render)

from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import logging
import os

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

# URI real para la base principal en MongoDB Atlas
client = MongoClient("mongodb+srv://Jhonss:6GvuUcYUFNBFbX7C@cluster0.hxlprze.mongodb.net/chat_db?retryWrites=true&w=majority&appName=Cluster0")
db = client.chat_db
mensajes = db.mensajes

@app.route("/")
def inicio():
    return "Servidor de producción activo. Usa /enviar y /mensajes."

@app.route("/enviar", methods=["POST"])
def enviar():
    data = request.json
    if not all(k in data for k in ("usuario", "mensaje", "canal")):
        return jsonify({"error": "Faltan datos obligatorios"}), 400
    data["fecha"] = datetime.utcnow()
    mensajes.insert_one(data)
    return jsonify({"status": "ok"})

@app.route("/mensajes", methods=["GET"])
def obtener():
    canal = request.args.get("canal")
    if not canal:
        return jsonify({"error": "Falta el canal"}), 400
    resultado = list(mensajes.find({"canal": canal}).sort("fecha"))
    for m in resultado:
        m["_id"] = str(m.get("_id", ""))
    return jsonify(resultado)

@app.route("/verificar", methods=["GET"])
def verificar_estado():
    try:
        db.command("ping")
        return jsonify({"status": "ok", "mongo": "conectado"}), 200
    except Exception as e:
        return jsonify({"status": "error", "mongo": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
