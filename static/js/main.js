console.log("Visor de simulaciones おｋ");

$(document).ready(function () {
    const $desde = $('#fechaDesde');
    const $hasta = $('#fechaHasta');
    const $transmision = $('#filtroTransmision');

    const tabla = $('#tablaSimulaciones').DataTable({
        "processing": true,
        "serverSide": true,
        "searchDelay": 400,
        "ajax": {
            "url": "/api/simulaciones",
            "data": function (d) {
                d.fecha_desde = $desde.val();
                d.fecha_hasta = $hasta.val();
                d.modo_transmision = $transmision.val();
            }
        },
        "columns": [
            { "data": "id" },
            { "data": "escenario" },
            { "data": "fecha" },
            { "data": "sexo" },
            { "data": "exposicion" },
            {
                "data": "vel_max",
                "render": function (data) {
                    return data + " km/h";
                }
            },
            {
                "data": "tiempo_sobre_limite",
                "render": function (data) {
                    return data + " s";
                }
            },
            {
                "data": null,
                "orderable": false,
                "render": function (data, type, row) {
                    return `<a href="/simulacion/${row.id}">Ver</a>`;
                }
            }
        ],
        "language": {
            "url": "/static/vendor/datatables/i18n/es-ES.json"
        }
    });

    fetch('/api/modos_transmision')
        .then(r => r.json())
        .then(modos => {
            if (!Array.isArray(modos)) return;
            modos.forEach(m => $transmision.append($('<option>').val(m).text(m)));
        })
        .catch(e => console.error('Error al cargar transmisiones:', e));

    $desde.add($hasta).add($transmision).on('change', function () {
        tabla.ajax.reload();
    });

    $('#btnLimpiarFechas').on('click', function () {
        $desde.val('');
        $hasta.val('');
        $transmision.val('');
        tabla.ajax.reload();
    });

    let ultimaClave = null;
    tabla.on('xhr.dt', function () {
        const p = tabla.ajax.params();
        const filtros = {
            search: (p.search && p.search.value) || '',
            fecha_desde: p.fecha_desde || '',
            fecha_hasta: p.fecha_hasta || '',
            modo_transmision: p.modo_transmision || ''
        };
        const clave = JSON.stringify(filtros);
        if (clave === ultimaClave) return;
        ultimaClave = clave;
        cargarPromedios(filtros);
    });
});


let controladorPromedios = null;

async function cargarPromedios(filtros) {
    if (controladorPromedios) controladorPromedios.abort();
    controladorPromedios = new AbortController();

    setTexto('promedioEstado', 'Calculando promedios...');

    try {
        const respuesta = await fetch('/api/promedios?' + new URLSearchParams(filtros), {
            signal: controladorPromedios.signal
        });
        const data = await respuesta.json();

        if (data.error) {
            setTexto('promedioEstado', 'Error al calcular los promedios: ' + data.error);
            return;
        }
        mostrarPromedios(data, filtros);
    } catch (error) {
        if (error.name === 'AbortError') return;
        console.error('Error al obtener los promedios:', error);
        setTexto('promedioEstado', 'No se pudieron calcular los promedios.');
    }
}

function setTexto(id, texto) {
    const el = document.getElementById(id);
    if (el) el.textContent = texto;
}

function fmt(valor) {
    return (valor === null || valor === undefined) ? 'N/A' : Number(valor).toFixed(2);
}

function mostrarPromedios(data, filtros) {
    const p = data.promedios;
    const set = setTexto;

    let rango = 'Todas las fechas';
    if (filtros.fecha_desde && filtros.fecha_hasta) rango = `${filtros.fecha_desde} → ${filtros.fecha_hasta}`;
    else if (filtros.fecha_desde) rango = `Desde ${filtros.fecha_desde}`;
    else if (filtros.fecha_hasta) rango = `Hasta ${filtros.fecha_hasta}`;

    set('promCantidad', data.cantidad);
    set('promRango', rango);
    set('promTransmision', filtros.modo_transmision || 'Todas');
    set('promEdad', fmt(p.edad));
    set('promVelMax', fmt(p.vel_max));
    set('promTiempoVelMax', fmt(p.tiempo_vel_max));
    set('promChoquesAutos', fmt(p.choques_autos));
    set('promChoquesPeatones', fmt(p.choques_peatones));
    set('promChoquesObjetos', fmt(p.choques_objetos));
    set('promChoquesTotales', fmt(p.choques_totales));
    set('promSemaforos', fmt(p.semaforos_rojo));

    setTexto('promedioEstado', data.cantidad === 0
        ? 'No hay simulaciones que cumplan el filtro.'
        : '');
}

function mostrarEstadoEnlace(texto, esError) {
    const el = document.getElementById('enlaceEstado');
    if (!el) return;
    el.textContent = texto;
    el.style.color = esError ? '#ff6b6b' : '#6bdc7a';
}

function dibujarEnlaceActual(enlace) {
    const contenedor = document.getElementById('enlaceActual');
    if (!contenedor) return;
    contenedor.textContent = '';

    if (!enlace) {
        contenedor.textContent = 'Todavía no hay un enlace guardado.';
        return;
    }

    const a = document.createElement('a');
    a.href = enlace.url;
    a.textContent = enlace.url;
    a.target = '_blank';
    a.rel = 'noopener noreferrer';

    const fecha = document.createElement('span');
    fecha.className = 'enlace-fecha';
    fecha.textContent = ' (guardado el ' + enlace.fecha_creacion + ')';

    contenedor.append(a, fecha);
}

async function cargarEnlace() {
    try {
        const respuesta = await fetch('/api/enlace');
        const enlace = await respuesta.json();
        if (enlace && enlace.error) throw new Error(enlace.error);

        dibujarEnlaceActual(enlace);
        const input = document.getElementById('inputEnlace');
        if (input && enlace) input.value = enlace.url;
    } catch (error) {
        console.error('Error al cargar el enlace:', error);
        mostrarEstadoEnlace('No se pudo cargar el enlace.', true);
    }
}

async function guardarEnlace(url) {
    try {
        const respuesta = await fetch('/api/enlace', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });
        const data = await respuesta.json();

        if (!respuesta.ok) {
            mostrarEstadoEnlace(data.error || 'No se pudo guardar el enlace.', true);
            return;
        }
        dibujarEnlaceActual(data);
        mostrarEstadoEnlace('Enlace guardado.', false);
    } catch (error) {
        console.error('Error al guardar el enlace:', error);
        mostrarEstadoEnlace('No se pudo guardar el enlace.', true);
    }
}

$(document).ready(function () {
    const form = document.getElementById('formEnlace');
    if (!form) return;

    form.addEventListener('submit', function (evento) {
        evento.preventDefault();
        guardarEnlace(document.getElementById('inputEnlace').value.trim());
    });

    cargarEnlace();
});