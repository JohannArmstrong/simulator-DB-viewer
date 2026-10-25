import os
import shutil
import tempfile
from datetime import datetime
from urllib.parse import urlparse

from flask import Flask, render_template, abort, request, jsonify, Response

from database import (
    get_connection,
    obtener_simulaciones,
    obtener_simulacion,
    obtener_simulaciones_datatables,
    obtener_promedios,
    obtener_modos_transmision,
    obtener_enlace,
    guardar_enlace,
    exportar_base_datos,
    DATABASE_PATH
)

import struct
import math
import io

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 1024  # 1 GB: las bases con datos binarios pueden ser grandes

def limpiar(valor):
    return None if math.isnan(valor) else valor

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/simulaciones")
def api_simulaciones():
    try:
        draw = request.args.get('draw', type=int)
        start = request.args.get('start', type=int)
        length = request.args.get('length', type=int)
        search_value = request.args.get('search[value]', type=str)
        fecha_desde = request.args.get('fecha_desde', type=str) or None
        fecha_hasta = request.args.get('fecha_hasta', type=str) or None
        modo_transmision = request.args.get('modo_transmision', type=str) or None

        order_column_index = request.args.get('order[0][column]', type=int, default=0)
        order_dir = request.args.get('order[0][dir]', type=str, default='desc')

        records_total, records_filtered, data = obtener_simulaciones_datatables(
            start, length, search_value, order_column_index, order_dir,
            fecha_desde, fecha_hasta, modo_transmision
        )

        return jsonify({
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,
            "data": data
        })
    except Exception as e:
        print("Error en Datatables")
        print(e)
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@app.route("/api/modos_transmision")
def api_modos_transmision():
    try:
        return jsonify(obtener_modos_transmision())
    except Exception as e:
        print("Error al obtener modos de transmisión")
        print(e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/promedios")
def api_promedios():
    """Promedios de las simulaciones que cumplen el mismo filtro que la tabla."""
    try:
        search_value = request.args.get('search', type=str) or None
        fecha_desde = request.args.get('fecha_desde', type=str) or None
        fecha_hasta = request.args.get('fecha_hasta', type=str) or None
        modo_transmision = request.args.get('modo_transmision', type=str) or None

        promedios = obtener_promedios(search_value, fecha_desde, fecha_hasta, modo_transmision)

        return jsonify({
            "cantidad": promedios.pop("cantidad"),
            "promedios": promedios
        })
    except Exception as e:
        print("Error al calcular promedios")
        print(e)
        return jsonify({"error": str(e)}), 500


def _url_valida(url):
    """Solo se aceptan enlaces http/https."""
    if not url or len(url) > 2048:
        return False
    try:
        partes = urlparse(url)
    except ValueError:
        return False
    return partes.scheme in ("http", "https") and bool(partes.netloc)


@app.route("/api/enlace", methods=["GET"])
def api_enlace_obtener():
    try:
        return jsonify(obtener_enlace())
    except Exception as e:
        print("Error al obtener el enlace")
        print(e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/enlace", methods=["PUT"])
def api_enlace_guardar():
    datos = request.get_json(silent=True) or {}
    url = (datos.get("url") or "").strip()

    if not _url_valida(url):
        return jsonify({"error": "Ingresá un enlace válido que empiece con http:// o https://"}), 400

    try:
        return jsonify(guardar_enlace(url))
    except Exception as e:
        print("Error al guardar el enlace")
        print(e)
        return jsonify({"error": str(e)}), 500


def _enviar_y_borrar(ruta, carpeta):
    """Envía el archivo por partes y borra la carpeta temporal al terminar."""
    try:
        with open(ruta, "rb") as f:
            while True:
                bloque = f.read(64 * 1024)
                if not bloque:
                    break
                yield bloque
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


@app.route("/api/base_datos/exportar")
def api_base_datos_exportar():
    """Descarga una copia de la base de datos."""
    carpeta = tempfile.mkdtemp(prefix="export_simulaciones_")
    try:
        destino = os.path.join(carpeta, "simulaciones.db")
        exportar_base_datos(destino)
        nombre = f"simulaciones_{datetime.now():%Y%m%d_%H%M%S}.db"
        tamano = os.path.getsize(destino)
    except Exception as e:
        shutil.rmtree(carpeta, ignore_errors=True)
        print("Error al exportar la base de datos")
        print(e)
        return jsonify({"error": str(e)}), 500

    return Response(
        _enviar_y_borrar(destino, carpeta),
        mimetype="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{nombre}"',
            "Content-Length": str(tamano)
        }
    )


@app.route("/api/base_datos/importar", methods=["POST"])
def api_base_datos_importar():
    """Reemplaza la base de datos por el archivo subido."""
    archivo = request.files.get("archivo")
    if archivo is None or not archivo.filename:
        return jsonify({"error": "Seleccioná un archivo de base de datos."}), 400

    try:
        temporal = str(DATABASE_PATH) + ".nueva"
        archivo.save(temporal)
        os.replace(temporal, DATABASE_PATH)
        return jsonify({"ok": True})
    except Exception as e:
        print("Error al importar la base de datos")
        print(e)
        return jsonify({"error": f"No se pudo importar: {e}"}), 500


@app.route("/simulacion/<int:simulacion_id>")
def ver_simulacion(simulacion_id):
    simulacion = obtener_simulacion(simulacion_id)

    if simulacion is None:
        abort(404)

    return render_template("simulacion.html", simulacion=simulacion)


def read_csharp_string(f):
    count = 0
    shift = 0
    while True:
        b_read = f.read(1)
        if not b_read:
            break
        b = b_read[0]
        count |= (b & 0x7F) << shift
        shift += 7
        if not (b & 0x80):
            break
    if count == 0:
        return ""
    return f.read(count).decode('utf-8')


@app.route("/api/simulacion/<int:simulacion_id>/datos")
def api_simulacion_datos(simulacion_id):
    try:
        connection = get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT datos_muestras FROM simulacion WHERE id = ?",
                (simulacion_id,)
            )
            row = cursor.fetchone()
        finally:
            connection.close()

        if not row or not row["datos_muestras"]:
            return jsonify({"error": "No hay datos binarios"}), 404

        stream = io.BytesIO(row["datos_muestras"])

        version, muestras_por_segundo, cantidad_muestras, cantidad_variables = \
            struct.unpack('<iiii', stream.read(16))

        nombres_variables = [read_csharp_string(stream) for _ in range(cantidad_variables)]

        total_floats = cantidad_muestras * cantidad_variables
        datos_crudos = struct.unpack(f'<{total_floats}f', stream.read(4 * total_floats))

        muestras = []
        idx = 0
        for _ in range(cantidad_muestras):
            muestras.append({
                "ebriedad": limpiar(datos_crudos[idx]),
                "velocidad": limpiar(datos_crudos[idx + 1]),
                "tiempo": limpiar(datos_crudos[idx + 2]),
                "desviacion": limpiar(datos_crudos[idx + 3])
            })
            idx += cantidad_variables

        return jsonify({
            "muestrasPorSegundo": muestras_por_segundo,
            "cantidadMuestras": cantidad_muestras,
            "muestras": muestras
        })

    except Exception as e:
        print("Error al decodificar blob")
        print(e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)