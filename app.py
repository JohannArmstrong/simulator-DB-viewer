from flask import Flask, render_template, abort

from database import (
    obtener_simulaciones,
    obtener_simulacion
)


app = Flask(__name__)


@app.route("/")
def index():
    simulaciones = obtener_simulaciones()

    return render_template(
        "index.html",
        simulaciones=simulaciones
    )


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