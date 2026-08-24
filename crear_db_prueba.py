import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "Database"
DATABASE_PATH = DATABASE_DIR / "simulador.db"


DATABASE_DIR.mkdir(exist_ok=True)


connection = sqlite3.connect(DATABASE_PATH)


connection.execute("""
CREATE TABLE IF NOT EXISTS Simulaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    fecha TEXT NOT NULL,
    nivel TEXT NOT NULL,

    muestras_por_segundo INTEGER NOT NULL,

    limite_velocidad REAL,

    velocidad_maxima REAL,
    tiempo_sobre_velocidad REAL,

    choques_total INTEGER,
    choques_auto INTEGER,
    choques_peaton INTEGER,
    pases_rojo INTEGER,

    datos_muestras BLOB
)
""")


connection.execute("""
INSERT INTO Simulaciones (
    fecha,
    nivel,
    muestras_por_segundo,
    limite_velocidad,
    velocidad_maxima,
    tiempo_sobre_velocidad,
    choques_total,
    choques_auto,
    choques_peaton,
    pases_rojo
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    "2026-08-20 02:00:00",
    "Paysandú",
    10,
    45.0,
    52.3,
    14.7,
    2,
    1,
    1,
    3
))


connection.commit()
connection.close()

print(f"Base creada en: {DATABASE_PATH}")