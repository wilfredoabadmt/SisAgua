# Modelo de Datos y Vistas Analíticas: Fase 6 - Reportes Administrativos (006-reportes-administrativos-financieros)

## 1. Arquitectura Analítica (Mermaid)

```mermaid
graph TD
    subgraph Fuentes de Datos Transaccionales
        Socio[apps.socios.Socio]
        Zona[apps.socios.Zona]
        Medidor[apps.medidores.Medidor]
        Obligacion[apps.servicios.Obligacion]
        Lectura[apps.consumo.Lectura]
        Recibo[apps.caja.Recibo]
        Pago[apps.caja.Pago]
    end

    subgraph Capa de Agregación Analítica (apps.reportes.services)
        RepDeudores[obtener_reporte_deudores]
        RepRecaudacion[obtener_reporte_recaudacion]
        RepConsumo[obtener_reporte_consumo]
        RepZonas[obtener_reporte_zonas]
        RepMembresias[obtener_reporte_membresias]
        RepSocio360[obtener_estado_cuenta_socio]
    end

    subgraph Salidas y Presentación
        HTML[Plantillas Web Responsivas]
        PRINT[Vistas de Impresión con Membrete]
        CSV[Exportador CSV Streaming]
    end

    Socio --> RepDeudores
    Obligacion --> RepDeudores
    Zona --> RepDeudores

    Recibo --> RepRecaudacion
    Pago --> RepRecaudacion

    Lectura --> RepConsumo
    Medidor --> RepConsumo

    Socio --> RepZonas
    Obligacion --> RepZonas
    Pago --> RepZonas

    Obligacion --> RepMembresias
    Socio --> RepMembresias

    RepDeudores --> HTML
    RepRecaudacion --> HTML
    RepConsumo --> HTML
    RepZonas --> HTML
    RepMembresias --> HTML
    RepSocio360 --> HTML

    HTML --> PRINT
    HTML --> CSV
```

---

## 2. Estructuras de Datos Analíticas (Data Transfer Objects)

### 2.1. Fila de Deudor (`DeudorItem`)
- `socio_id`: int
- `codigo`: str (ej. `SOC-0001`)
- `ci_completo`: str
- `nombre_completo`: str
- `zona_nombre`: str
- `cantidad_medidores`: int
- `deuda_agua`: Decimal
- `deuda_membresia`: Decimal
- `deuda_otros`: Decimal
- `total_pendiente`: Decimal
- `importe_vencido`: Decimal
- `periodos_adeudados`: int
- `periodos_str`: str (ej. "2026-01, 2026-02")

### 2.2. Resumen de Recaudación (`RecaudacionResumen`)
- `total_recaudado_neto`: Decimal
- `total_efectivo`: Decimal
- `total_qr`: Decimal
- `total_transferencia`: Decimal
- `cantidad_recibos_emitidos`: int
- `cantidad_recibos_anulados`: int
- `monto_anulado`: Decimal
- `recaudacion_por_servicio`: dict[str, Decimal]

### 2.3. Resumen de Consumo (`ConsumoResumen`)
- `periodo`: str
- `total_consumo_m3`: Decimal
- `promedio_consumo_m3`: Decimal
- `total_medidores_leidos`: int
- `total_medidores_sin_lectura`: int
- `total_lecturas_observadas`: int
- `medidores_observados`: list[dict]

### 2.4. Resumen por Zona (`ZonaResumen`)
- `zona_id`: int
- `zona_codigo`: str
- `zona_nombre`: str
- `socios_activos`: int
- `socios_inactivos`: int
- `total_medidores`: int
- `total_facturado`: Decimal
- `total_recaudado`: Decimal
- `total_mora`: Decimal
- `eficacia_cobranza_pct`: float

