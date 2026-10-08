from flask import Flask, render_template, abort, request, jsonify

from database import (
    get_connection,
    obtener_simulaciones,
    obtener_simulacion,
    obtener_simulaciones_datatables
)

import struct
import math
import io

app = Flask(__name__)

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

        order_column_index = request.args.get('order[0][column]', type=int, default=0)
        order_dir = request.args.get('order[0][dir]', type=str, default='desc')

        records_total, records_filtered, data = obtener_simulaciones_datatables(
            start, length, search_value, order_column_index, order_dir
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
        print("======== ERROR AL DECODIFICAR BLOB ========")
        print(e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)