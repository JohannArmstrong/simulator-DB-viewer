from flask import Flask, render_template, abort, request, jsonify

from database import (
    obtener_simulaciones,
    obtener_simulacion,
    obtener_simulaciones_datatables
)

app = Flask(__name__)

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

    return render_template(
        "simulacion.html",
        simulacion=simulacion
    )

if __name__ == "__main__":
    app.run(debug=True)