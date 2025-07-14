# chat_backend.py (producción con gestión de canales)

from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

load_dotenv()
uri = os.getenv("MONGO_URI")
client = MongoClient(uri)
db = client.chat_db
mensajes = db.mensajes
canales = db.canales  # nueva colección para los canales

@app.route("/")
def inicio():
    return "Servidor de producción activo. Usa /enviar, /mensajes, /canales y /crear_canal."

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

@app.route("/canales", methods=["GET"])
def listar_canales():
    lista = list(canales.find({}, {"_id": 0, "nombre": 1}))
    return jsonify([c["nombre"] for c in lista])

@app.route("/crear_canal", methods=["POST"])
def crear_canal():
    data = request.json
    nombre = data.get("nombre")
    if not nombre:
        return jsonify({"error": "Nombre del canal requerido"}), 400

    if canales.find_one({"nombre": nombre}):
        return jsonify({"error": "El canal ya existe"}), 409

    canales.insert_one({"nombre": nombre, "fecha_creado": datetime.utcnow()})
    return jsonify({"status": "canal creado", "nombre": nombre})

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
