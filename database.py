import sqlite3
from pathlib import Path


# VisorDB/
#     database.py
#
# La base está un nivel por encima:
#     Simulador/
#         Database/
#             simulador.db

# arreglar despue's la ubicaci'on
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = BASE_DIR / "simulador-conduccion-vr-2026" / "Database" / "simulador.db"


def get_connection():
    """
    Abre una conexión con la base de datos SQLite.
    """
    connection = sqlite3.connect(DATABASE_PATH)

    # Permite acceder a las columnas por nombre.
    connection.row_factory = sqlite3.Row

    return connection


def obtener_simulaciones():
    """
    Obtiene todas las simulaciones almacenadas.
    """
    connection = get_connection()

    try:
        cursor = connection.execute("""
            SELECT *
            FROM Simulaciones
            ORDER BY fecha DESC
        """)

        return cursor.fetchall()

    finally:
        connection.close()


def obtener_simulacion(simulacion_id):
    """
    Obtiene una simulación concreta mediante su ID.
    """
    connection = get_connection()

    try:
        cursor = connection.execute("""
            SELECT *
            FROM Simulaciones
            WHERE id = ?
        """, (simulacion_id,))

        return cursor.fetchone()

    finally:
        connection.close()