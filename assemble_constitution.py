# -*- coding: utf-8 -*-
"""
Ensamblador de la Constitución SDD v1.0
"""
import os
import sys

# Agregar ruta de partes
sys.path.append(r'f:\Documentos\GitHub\SisAgua\sdd_parts')

from part_a import get_part_a
from part_b import get_part_b
from part_c import get_part_c
from part_d import get_part_d
from part_e import get_part_e
from part_f import get_part_f

def main():
    header = """# SISTEMA DE ADMINISTRACIÓN, CONSUMO Y COBRO DE AGUA POTABLE (SisAgua)
## CONSTITUCIÓN NORMATIVA DEL PROYECTO (SDD - Spec-Driven Development)
### Versión 1.0 — Documento Rector de Arquitectura, Dominio y Gobernanza

| Metadato | Detalle Normativo |
| :--- | :--- |
| **Proyecto** | SisAgua — Sistema de Administración, Consumo y Cobro de Agua Potable |
| **Documento** | Constitución Normativa SDD (Fase 1: Normativa y Principios) |
| **Versión** | 1.0 (Borrador Arquitectónico Oficial para Ratificación Institucional) |
| **Fecha de Emisión** | Octubre 2026 |
| **Estado Normativo** | **PROPUESTA ARQUITECTÓNICA EN REVISIÓN** (Requiere ratificación de Directorio/Asamblea) |
| **Fuente Primaria** | Documento *“SISTEMA DE ADMINISTRACIÓN.docx”* (40 págs., 18 secciones, 882 párrafos) |
| **Contexto Jurisdiccional** | Estado Plurinacional de Bolivia (Marco normativo Ley 2066 / AAPS) |
| **Moneda Base** | Bolivianos (Bs) |
| **Zona Horaria y Convención** | UTC-4 (BOT - Bolivia Time) / Formato de Fechas: `DD/MM/AAAA` |
| **Clasificación de Requisitos** | **[A]** Requisito Explícito | **[B]** Principio Derivado | **[C]** Mejora Propuesta | **[D]** Decisión Pendiente |

---

> ### NOTA DE ADVERTENCIA Y CONDICIÓN DE BLOQUEO PREVIO A PRODUCCIÓN
> Esta Constitución establece los fundamentos innegociables de arquitectura, reglas de negocio e integridad financiera. **NO AUTORIZA LA IMPLEMENTACIÓN DE CÓDIGO PRODUCTIVO NI LA EMISIÓN DE OBLIGACIONES ECONÓMICAS REALES** hasta que la organización resuelva formalmente las Decisiones Pendientes Bloqueantes (especialmente **D-01: Tarifa definitiva y anomalía > 15 m³** y **D-02: Importe de membresía**).

---
"""
    full_doc = "\n\n".join([
        header,
        get_part_a(),
        get_part_b(),
        get_part_c(),
        get_part_d(),
        get_part_e(),
        get_part_f()
    ])
    
    # Escribir en workspace
    ws_path = r'f:\Documentos\GitHub\SisAgua\CONSTITUCION_SDD_v1.0.md'
    with open(ws_path, 'w', encoding='utf-8') as f:
        f.write(full_doc)
    print(f"Escrito en workspace: {ws_path} ({len(full_doc)} caracteres)")
    
    # Escribir en artifact directory
    art_dir = r'C:\Users\Wilfredo Abad\.gemini\antigravity\brain\cadd33b7-fc6c-47a7-94e1-b9e41321562c'
    os.makedirs(art_dir, exist_ok=True)
    art_path = os.path.join(art_dir, 'CONSTITUCION_SDD_v1.0.md')
    with open(art_path, 'w', encoding='utf-8') as f:
        f.write(full_doc)
    print(f"Escrito en artifact dir: {art_path}")

if __name__ == '__main__':
    main()

