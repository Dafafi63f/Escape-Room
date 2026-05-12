import csv
from pathlib import Path


CSV_PATH = Path(r"C:\Users\34681\Documents\UAB\Running\Treball Final de Grau 🔘\Data\Preguntas.csv")


FIXES = {
    "26": {
        "Pregunta": "¿Cuántas iteraciones realiza for i in range(5)?",
        "A": "4",
        "B": "5",
        "C": "6",
        "D": "0",
        "Correcta": "B",
    },
    "219": {
        "Pregunta": "Un coche pasa de 10 m/s a 25 m/s en 5 s. ¿Cuál es su aceleración media?",
        "A": "3 m/s²",
        "B": "5 m/s²",
        "C": "7.5 m/s²",
        "D": "15 m/s²",
        "Correcta": "A",
    },
    "268": {
        "Pregunta": "Si la precisión en validación sube de 0.82 a 0.88, ¿cuál es la mejora absoluta?",
        "A": "0.06",
        "B": "0.82",
        "C": "0.88",
        "D": "0.12",
        "Correcta": "A",
    },
    "300": {
        "Pregunta": "Con factor de descuento 0.9 y pago de 10 cada periodo para siempre, ¿valor presente?",
        "A": "90",
        "B": "10",
        "C": "100",
        "D": "110",
        "Correcta": "C",
    },
    "350": {
        "Pregunta": "Con coeficiente de reducción caballera 0.5 y profundidad real 20, ¿qué profundidad se dibuja?",
        "A": "5",
        "B": "10",
        "C": "20",
        "D": "40",
        "Correcta": "B",
    },
    "357": {
        "Pregunta": "Si una contraseña tiene 8 caracteres y cada uno puede ser una de 26 letras minúsculas, ¿cuántas combinaciones hay?",
        "A": "26^8",
        "B": "8^26",
        "C": "2^8",
        "D": "26*8",
        "Correcta": "A",
    },
    "383": {
        "Pregunta": "¿Qué protocolo de IoT está diseñado para dispositivos con recursos limitados y funciona sobre UDP?",
        "A": "HTTP",
        "B": "MQTT",
        "C": "CoAP",
        "D": "FTP",
        "Correcta": "C",
    },
    "387": {
        "Pregunta": "Un sensor envía 1 lectura por segundo durante 5 minutos. ¿Cuántas lecturas envía?",
        "A": "60",
        "B": "120",
        "C": "300",
        "D": "600",
        "Correcta": "C",
    },
    "389": {
        "Pregunta": "Si cada mensaje IoT ocupa 200 bytes y se envían 50 mensajes por segundo, ¿qué caudal se genera?",
        "A": "5 KB/s",
        "B": "10 KB/s",
        "C": "50 KB/s",
        "D": "100 KB/s",
        "Correcta": "B",
    },
    "397": {
        "Pregunta": "En una imagen de 640 por 480 píxeles, ¿cuántos píxeles hay en total?",
        "A": "307200",
        "B": "1120",
        "C": "640",
        "D": "480",
        "Correcta": "A",
    },
    "398": {
        "Pregunta": "Si una imagen RGB tiene 3 canales y cada canal usa 8 bits, ¿cuántos bits por píxel tiene?",
        "A": "8",
        "B": "16",
        "C": "24",
        "D": "32",
        "Correcta": "C",
    },
    "399": {
        "Pregunta": "Convolución 3x3 con stride 1 y padding 0 sobre entrada de 32x32: ¿salida?",
        "A": "30x30",
        "B": "32x32",
        "C": "29x29",
        "D": "34x34",
        "Correcta": "A",
    },
}


with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f, delimiter=";")
    rows = list(reader)
    fieldnames = reader.fieldnames

for row in rows:
    patch = FIXES.get(row["Id"])
    if patch:
        row.update(patch)

with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
    writer.writeheader()
    writer.writerows(rows)

print(f"Filas corregidas: {len(FIXES)}")
