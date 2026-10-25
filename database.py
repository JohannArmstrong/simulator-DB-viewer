import sqlite3
from pathlib import Path

#BASE_DIR = Path(__file__).resolve().parent.parent
#DATABASE_PATH = BASE_DIR / "simulador-conduccion-vr-2026" / "Database" / "simulaciones.db" 

DATABASE_PATH = (Path.home() / "AppData" / "LocalLow" / "DefaultCompany" / "Simulador" / "simulaciones.db")

def get_connection():
    """
    Abre una conexión con la base de datos SQLite.
    """
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _asegurar_tabla_enlaces(connection):
    """
    Crea la tabla `enlaces` si todavía no existe. No toca ninguna tabla existente.
    """
    connection.execute("""
        CREATE TABLE IF NOT EXISTS enlaces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            fecha_creacion TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)


def obtener_enlace():
    """
    Devuelve el enlace guardado ({url, fecha_creacion}) o None si todavía no hay.
    """
    connection = get_connection()
    try:
        _asegurar_tabla_enlaces(connection)
        row = connection.execute("""
            SELECT url, fecha_creacion
            FROM enlaces
            ORDER BY fecha_creacion DESC, id DESC
            LIMIT 1
        """).fetchone()
        return dict(row) if row else None
    finally:
        connection.close()


def guardar_enlace(url):
    """
    Guarda el enlace reemplazando el anterior: la tabla siempre queda con una sola fila.
    """
    connection = get_connection()
    try:
        _asegurar_tabla_enlaces(connection)
        connection.execute("DELETE FROM enlaces")
        connection.execute("INSERT INTO enlaces (id, url) VALUES (1, ?)", (url,))
        connection.commit()
        row = connection.execute("SELECT url, fecha_creacion FROM enlaces WHERE id = 1").fetchone()
        return dict(row)
    finally:
        connection.close()


def _copiar_base(origen, destino):
    """
    Copia una base SQLite a otra usando la API de backup de SQLite
    (consistente aunque haya otras conexiones abiertas).
    """
    try:
        origen.backup(destino)
    finally:
        destino.close()
        origen.close()


def exportar_base_datos(ruta_destino):
    """
    Genera una copia consistente de la base actual en `ruta_destino`.
    """
    _copiar_base(get_connection(), sqlite3.connect(ruta_destino))


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


_FROM_SIMULACIONES = """
    FROM simulacion s
    LEFT JOIN sexo sx ON s.sexo_id = sx.id
    LEFT JOIN exposicion ex ON s.exposicion_id = ex.id
"""


def _construir_filtros(search_value=None, fecha_desde=None, fecha_hasta=None, modo_transmision=None):
    """
    Construye el WHERE compartido por la tabla y por los promedios.
    """
    condiciones = []
    params = []

    if search_value:
        like = f"%{search_value}%"
        condiciones.append("(s.nivel LIKE ? OR s.fecha LIKE ? OR sx.nombre LIKE ? OR ex.nombre LIKE ?)")
        params.extend([like, like, like, like])

    if fecha_desde:
        condiciones.append("substr(s.fecha, 1, 10) >= ?")
        params.append(fecha_desde)

    if fecha_hasta:
        condiciones.append("substr(s.fecha, 1, 10) <= ?")
        params.append(fecha_hasta)

    if modo_transmision:
        condiciones.append("s.modo_transmision = ?")
        params.append(modo_transmision)

    where = (" WHERE " + " AND ".join(condiciones)) if condiciones else ""
    return where, params


def obtener_simulaciones_datatables(start, length, search_value, order_column_index=0,
                                    order_dir='desc', fecha_desde=None, fecha_hasta=None,
                                    modo_transmision=None):
    """
    Obtiene las simulaciones con paginación, filtros y ordenamiento dinámico para DataTables.
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()

        where, params = _construir_filtros(search_value, fecha_desde, fecha_hasta, modo_transmision)

        cursor.execute(f"SELECT COUNT(*) {_FROM_SIMULACIONES} {where}", params)
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

        query = f"""
            SELECT
                s.id,
                s.nivel AS escenario,
                s.fecha,
                sx.nombre AS sexo,
                ex.nombre AS exposicion,
                s.vel_max,
                s.tiempo_vel_max
            {_FROM_SIMULACIONES}
            {where}
            ORDER BY {columna_sql} {direccion_sql} LIMIT ? OFFSET ?
        """
        cursor.execute(query, params + [length, start])
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


def obtener_promedios(search_value=None, fecha_desde=None, fecha_hasta=None, modo_transmision=None):
    """
    Promedio de los datos numéricos de las simulaciones que cumplen el filtro.
    """
    where, params = _construir_filtros(search_value, fecha_desde, fecha_hasta, modo_transmision)
    connection = get_connection()
    try:
        row = connection.execute(f"""
            SELECT
                COUNT(*) AS cantidad,
                AVG(COALESCE(s.vel_max, 0)) AS vel_max,
                AVG(COALESCE(s.tiempo_vel_max, 0)) AS tiempo_vel_max,
                AVG(s.edad) AS edad,
                AVG(COALESCE(s.choques_autos, 0)) AS choques_autos,
                AVG(COALESCE(s.choques_peatones, 0)) AS choques_peatones,
                AVG(COALESCE(s.choques_objetos, 0)) AS choques_objetos,
                AVG(COALESCE(s.choques_autos, 0)
                    + COALESCE(s.choques_peatones, 0)
                    + COALESCE(s.choques_objetos, 0)) AS choques_totales,
                AVG(COALESCE(s.semaforos_rojo, 0)) AS semaforos_rojo
            {_FROM_SIMULACIONES}
            {where}
        """, params).fetchone()
        return {k: (round(row[k], 2) if k != "cantidad" and row[k] is not None else row[k])
                for k in row.keys()}
    finally:
        connection.close()


def obtener_modos_transmision():
    """
    Valores distintos de modo_transmision presentes en la base (para el desplegable).
    """
    connection = get_connection()
    try:
        cursor = connection.execute("""
            SELECT DISTINCT modo_transmision
            FROM simulacion
            WHERE modo_transmision IS NOT NULL AND modo_transmision != ''
            ORDER BY modo_transmision
        """)
        return [row["modo_transmision"] for row in cursor.fetchall()]
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