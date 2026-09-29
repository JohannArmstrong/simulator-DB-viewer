console.log("Visor de simulaciones おｋ");

console.log("Visor de simulaciones おｋ");

$(document).ready(function() {$('#tablaSimulaciones').DataTable({
        "processing": true,
        "serverSide": true,
        "ajax": "/api/simulaciones",
        "columns": [
            { "data": "id" },
            { "data": "escenario" },
            { "data": "fecha" },
            { "data": "sexo" },
            { "data": "exposicion" },
            { 
                "data": "vel_max",
                "render": function(data) {
                    return data + " km/h";
                }
            },
            { 
                "data": "tiempo_sobre_limite",
                "render": function(data) {
                    return data + " s";
                }
            },
            { 
                "data": null,
                "orderable": false,
                "render": function(data, type, row) {
                    return `<a href="/simulacion/${row.id}">Ver</a>`;
                }
            }
        ],
        "language": {
            "url": "//cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json"
        }
    });
});