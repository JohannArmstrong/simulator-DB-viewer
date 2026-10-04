console.log("Página de simulación おｋ");

const MAX_PUNTOS_GRAFICA = 500;

const DATOS_PAGINA = document.querySelector("main").dataset;
const SIMULACION_ID = Number(DATOS_PAGINA.simulacionId);

// El límite de velocidad no se guarda en la base de datos.
// Completa aquí el límite (km/h) de cada nivel/escenario.
const LIMITES_POR_NIVEL = {
    // "Default": 50,
};
const LIMITE_VELOCIDAD = LIMITES_POR_NIVEL[DATOS_PAGINA.nivel] ?? null;

document.addEventListener("DOMContentLoaded", () => {
    cargarDatosYDibujarGraficas();
});

function cargarDatosYDibujarGraficas() {
    fetch(`/api/simulacion/${SIMULACION_ID}/datos`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error("Error del servidor:", data.error);
                return;
            }
            document.getElementById("datoMuestrasPorSegundo").textContent = data.muestrasPorSegundo;
            procesarDatos(data.muestras);
        })
        .catch(error => console.error("Error al obtener los datos:", error));
}

function procesarDatos(muestras) {
    const cantidadMuestras = muestras.length;
    
    let primerIndiceDesviacion = -1;
    let primerTiempoDesviacion = -1;
    let maxAbsDesviacion = 0;

    for (let i = 0; i < cantidadMuestras; i++) {
        const desv = muestras[i].desviacion;
        if (desv !== null && !isNaN(desv) && desv !== 0) {
            primerIndiceDesviacion = i;
            primerTiempoDesviacion = muestras[i].tiempo;
            break;
        }
    }

    if (primerIndiceDesviacion === -1) {
        for (let i = 0; i < cantidadMuestras; i++) {
            if (muestras[i].desviacion !== null && !isNaN(muestras[i].desviacion)) {
                primerIndiceDesviacion = i;
                primerTiempoDesviacion = muestras[i].tiempo;
                break;
            }
        }
    }

    let paso = 1;
    if (cantidadMuestras > MAX_PUNTOS_GRAFICA) {
        paso = Math.ceil(cantidadMuestras / MAX_PUNTOS_GRAFICA);
    }

    const tiemposVelocidad = [];
    const datosVelocidad = [];
    const datosEbriedad = [];
    const datosVelMaxima = [];

    const tiemposDesviacion = [];
    const datosDesviacion = [];

    for (let i = 0; i < cantidadMuestras; i += paso) {
        const m = muestras[i];
        
        tiemposVelocidad.push(m.tiempo.toFixed(2));
        datosVelocidad.push(m.velocidad);
        datosEbriedad.push(m.ebriedad);
        
        if (LIMITE_VELOCIDAD !== null && m.velocidad > LIMITE_VELOCIDAD) {
            datosVelMaxima.push(m.velocidad);
        } else {
            datosVelMaxima.push(null);
        }

        if (m.desviacion !== null && !isNaN(m.desviacion) && primerIndiceDesviacion >= 0 && i >= primerIndiceDesviacion) {
            tiemposDesviacion.push(m.tiempo.toFixed(2));
            datosDesviacion.push(m.desviacion);
            
            const absDesv = Math.abs(m.desviacion);
            if (absDesv > maxAbsDesviacion) {
                maxAbsDesviacion = absDesv;
            }
        }
    }

    dibujarGraficaVelocidad(tiemposVelocidad, datosVelocidad, datosEbriedad, datosVelMaxima);
    dibujarGraficaDesviacion(tiemposDesviacion, datosDesviacion, maxAbsDesviacion);
}

function dibujarGraficaVelocidad(labels, velocidad, ebriedad, velMaxima) {
    const ctx = document.getElementById('graficaVelocidad').getContext('2d');
    
    const limiteArray = new Array(labels.length).fill(LIMITE_VELOCIDAD); // null = sin línea

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Velocidad',
                    data: velocidad,
                    borderColor: 'blue',
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0
                },
                {
                    label: 'Ebriedad',
                    data: ebriedad,
                    borderColor: 'purple',
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0
                },
                {
                    label: 'Velocidad Maxima',
                    data: velMaxima,
                    borderColor: 'red',
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0
                },
                {
                    label: 'Limite de velocidad',
                    data: limiteArray,
                    borderColor: 'rgba(242, 92, 51, 1)',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    tension: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            plugins: {
                title: { display: true, text: 'Evolución velocidad alcanzada', font: { size: 16 } }
            },
            scales: {
                x: { title: { display: true, text: 'Tiempo (s)' } },
                y: { min: 0, max: 90 }
            }
        }
    });
}

function dibujarGraficaDesviacion(labels, desviacion, maxAbsDesviacion) {
    const ctx = document.getElementById('graficaDesviacion').getContext('2d');
    
    // Array para la línea del centro del carril
    const centroArray = new Array(labels.length).fill(0);
    
    const rangoY = Math.max(maxAbsDesviacion * 1.1, 1.0);

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Desviación',
                    data: desviacion,
                    borderColor: 'green',
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.4
                },
                {
                    label: 'Centro del carril',
                    data: centroArray,
                    borderColor: 'yellow',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    tension: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            plugins: {
                title: { display: true, text: 'Desviación lateral', font: { size: 16 } }
            },
            scales: {
                x: { title: { display: true, text: 'Tiempo (s)' } },
                y: {
                    min: -rangoY,
                    max: rangoY,
                    reverse: true
                }
            }
        }
    });
}