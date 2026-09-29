import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "simulador-conduccion-vr-2026" / "Database" / "simulaciones.db" 


def get_connection():
    """
    Abre una conexión con la base de datos SQLite.
    """
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def obtener_simulaciones():
    """
    Obtiene todas las simulaciones almacenadas (Sin DataTables).
    """
    connection = get_connection()
    try:
        cursor = connection.execute("""
            SELECT *
            FROM simulacion
            ORDER BY fecha DESC
        """)
        return cursor.fetchall()
    finally:
        connection.close()


def obtener_simulaciones_datatables(start, length, search_value, order_column_index=0, order_dir='desc'):
    """
    Obtiene las simulaciones con paginación, filtros y ordenamiento dinámico para DataTables.
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()

        query = """
            SELECT 
                s.id, 
                s.nivel AS escenario, 
                s.fecha, 
                sx.nombre AS sexo, 
                ex.nombre AS exposicion, 
                s.vel_max, 
                s.tiempo_vel_max 
            FROM simulacion s
            LEFT JOIN sexo sx ON s.sexo_id = sx.id
            LEFT JOIN exposicion ex ON s.exposicion_id = ex.id
        """
        params = []

        if search_value:
            query += " WHERE s.nivel LIKE ? OR s.fecha LIKE ? OR sx.nombre LIKE ? OR ex.nombre LIKE ?"
            params.extend([f"%{search_value}%", f"%{search_value}%", f"%{search_value}%", f"%{search_value}%"])

        cursor.execute(f"SELECT COUNT(*) FROM ({query})", params)
        records_filtered = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM simulacion")
        records_total = cursor.fetchone()[0]

        columnas_orden = {
            0: "s.id",
            1: "s.nivel",
            2: "s.fecha",
            3: "sx.nombre",
            4: "ex.nombre",
            5: "s.vel_max",
            6: "s.tiempo_vel_max"
        }
        
        columna_sql = columnas_orden.get(order_column_index, "s.id")
        
        direccion_sql = "ASC" if order_dir.lower() == 'asc' else "DESC"

        query += f" ORDER BY {columna_sql} {direccion_sql} LIMIT ? OFFSET ?"
        params.extend([length, start])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        data = []
        for row in rows:
            data.append({
                "id": row["id"],
                "escenario": row["escenario"] or "",
                "fecha": row["fecha"] or "",
                "sexo": row["sexo"] or "N/A",
                "exposicion": row["exposicion"] or "N/A",
                "vel_max": round(row["vel_max"], 2) if row["vel_max"] else 0,
                "tiempo_sobre_limite": round(row["tiempo_vel_max"], 2) if row["tiempo_vel_max"] else 0
            })

        return records_total, records_filtered, data
    finally:
        connection.close()


def obtener_simulacion(simulacion_id):
    """
    Obtiene una simulación concreta mediante su ID.
    """
    connection = get_connection()
    try:
        cursor = connection.execute("""
            SELECT 
                s.*, 
                sx.nombre AS sexo_nombre, 
                ex.nombre AS exposicion_nombre
            FROM simulacion s
            LEFT JOIN sexo sx ON s.sexo_id = sx.id
            LEFT JOIN exposicion ex ON s.exposicion_id = ex.id
            WHERE s.id = ?
        """, (simulacion_id,))
        return cursor.fetchone()
    finally:
        connection.close()