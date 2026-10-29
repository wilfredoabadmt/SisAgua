# Investigación y Decisiones Técnicas: Fase 7 - Portal Individual de Socios (007-portal-individual-socios)

## 1. Vinculación entre Usuario y Socio
- **Decisión:** Agregar `usuario = models.OneToOneField('seguridad.Usuario', null=True, blank=True, on_delete=models.SET_NULL, related_name='perfil_socio')` en el modelo `Socio` (`apps/socios/models.py`).
- **Justificación:** Cumple con el Principio P2 (Fuente Única de Verdad). Permite que una persona física sea socio sin tener obligatoriamente acceso digital inmediato, pero una vez creada su cuenta institucional con rol `SOCIO`, se asocia unívocamente a su ficha.
- **Creación de Credenciales:** Función de servicio `habilitar_acceso_portal(socio_id, username=None)` que crea el usuario con rol `SOCIO`, contraseña temporal segura (generada con la función criptográfica existente) y flag `requiere_cambio_clave=True`.

## 2. Aislamiento y Seguridad Multitenant a Nivel Fila (Principio P7)
- Todas las consultas del portal se originan de `request.user.perfil_socio`.
- Si un usuario tiene el rol `SOCIO` pero no tiene `perfil_socio`, la vista muestra una pantalla clara de aviso o 403.
- Al consultar comprobantes (`/portal/recibo/<id>/`), se ejecuta `get_object_or_404(Recibo, pk=id, socio=request.user.perfil_socio)` evitando cualquier fuga IDOR (*Insecure Direct Object References*).

## 3. Experiencia de Usuario y Mobile-First
- Los socios frecuentemente acceden desde teléfonos móviles. La interfaz del portal debe utilizar tarjetas responsivas de Bootstrap 5 con tipografía clara y contrastes aprobados por accesibilidad.
- Botones de acción directa: "Ver Recibo", "Descargar Proforma Informativa", "Actualizar Teléfono".

