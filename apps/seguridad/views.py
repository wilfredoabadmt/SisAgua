# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.core.services import registrar_auditoria
from apps.core.decorators import requiere_permiso
from .models import Usuario, Rol, Permiso
from .forms import LoginForm, CambiarClaveForm, UsuarioCrearForm, PerfilForm
from .services import sugerir_username, generar_clave_temporal

def login_view(request):
    """
    Vista de inicio de sesión con protección contra ataques de fuerza bruta (FR-004),
    auditoría inalterable y detección de claves temporales forzadas (FR-003).
    """
    if request.user.is_authenticated:
        if getattr(request.user, 'requiere_cambio_clave', False):
            return redirect('seguridad:cambiar_contrasena')
        return redirect('seguridad:dashboard')

    form = LoginForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        # Buscar usuario para control de intentos
        user_obj = Usuario.objects.filter(username__iexact=username).first()

        if user_obj and user_obj.esta_bloqueado():
            registrar_auditoria(
                modulo='AUTH',
                accion='LOGIN_BLOCKED',
                resultado='FALLO',
                request=request,
                detalle={'username_intentado': username, 'razon': 'Cuenta temporalmente bloqueada por 5 intentos fallidos'}
            )
            form.add_error(None, "Credenciales no válidas o cuenta temporalmente bloqueada. Por favor intente más tarde.")
            return render(request, 'auth/login.html', {'form': form})

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_active:
            user.reiniciar_fallos_login()
            login(request, user)

            registrar_auditoria(
                modulo='AUTH',
                accion='LOGIN',
                resultado='EXITO',
                usuario=user,
                request=request,
                detalle={'rol': user.rol.codigo if user.rol else 'SIN_ROL'}
            )

            if user.requiere_cambio_clave:
                messages.warning(request, "Bienvenido. Por seguridad, debe establecer su contraseña personal.")
                return redirect('seguridad:cambiar_contrasena')

            messages.success(request, f"Bienvenido al sistema, {user.nombres}.")
            return redirect('seguridad:dashboard')
        else:
            if user_obj:
                user_obj.registrar_fallo_login()

            registrar_auditoria(
                modulo='AUTH',
                accion='LOGIN_FAILED',
                resultado='FALLO',
                request=request,
                detalle={'username_intentado': username}
            )
            form.add_error(None, "Credenciales no válidas o cuenta temporalmente bloqueada. Por favor intente más tarde.")

    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    """Cierra la sesión activa y audita el evento."""
    if request.user.is_authenticated:
        registrar_auditoria(
            modulo='AUTH',
            accion='LOGOUT',
            resultado='EXITO',
            usuario=request.user,
            request=request
        )
    logout(request)
    messages.info(request, "Ha cerrado sesión correctamente.")
    return redirect('seguridad:login')


@login_required
def cambiar_contrasena_view(request):
    """
    Vista de cambio de contraseña (forzado en primer acceso o voluntario en perfil).
    """
    user = request.user
    es_forzado = getattr(user, 'requiere_cambio_clave', False)

    if request.method == 'POST':
        form = CambiarClaveForm(user=user, data=request.POST)
        if form.is_valid():
            nueva_clave = form.cleaned_data['password_nuevo']
            user.set_password(nueva_clave)
            user.requiere_cambio_clave = False
            user.save(update_fields=['password', 'requiere_cambio_clave'])

            update_session_auth_hash(request, user)

            registrar_auditoria(
                modulo='AUTH',
                accion='PASSWORD_CHANGED',
                resultado='EXITO',
                usuario=user,
                request=request,
                detalle={'tipo': 'FORZADO' if es_forzado else 'VOLUNTARIO'}
            )

            messages.success(request, "Su contraseña ha sido actualizada con éxito.")
            return redirect('seguridad:dashboard')
    else:
        form = CambiarClaveForm(user=user)

    return render(request, 'auth/cambiar_clave.html', {
        'form': form,
        'es_forzado': es_forzado,
    })


@login_required
def dashboard_view(request):
    """Panel principal dinámico según el rol del usuario."""
    return render(request, 'core/dashboard.html', {
        'usuario': request.user,
    })


@login_required
def perfil_view(request):
    """Autoservicio de perfil del usuario (US6)."""
    user = request.user
    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            registrar_auditoria(
                modulo='PERFIL',
                accion='MODIFICAR',
                resultado='EXITO',
                usuario=user,
                request=request
            )
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect('seguridad:perfil')
    else:
        form = PerfilForm(instance=user)

    return render(request, 'seguridad/perfil.html', {
        'usuario': user,
        'form': form
    })


@login_required
@requiere_permiso(modulo='roles', accion='ver')
def roles_list_view(request):
    """Listado y matriz de roles y permisos (US3)."""
    roles = Rol.objects.all().prefetch_related('permisos')
    return render(request, 'seguridad/roles_list.html', {'roles': roles})


@login_required
@requiere_permiso(modulo='usuarios', accion='ver')
def usuarios_list_view(request):
    """Directorio y creación de usuarios con clave temporal (US5)."""
    usuarios = Usuario.objects.all().select_related('rol').order_by('apellido_paterno')
    
    if request.method == 'POST':
        form = UsuarioCrearForm(request.POST)
        if form.is_valid():
            nuevo_user = form.save(commit=False)
            
            if not nuevo_user.username:
                nuevo_user.username = sugerir_username(nuevo_user.nombres, nuevo_user.apellido_paterno)
                
            clave_temporal = generar_clave_temporal(10)
            nuevo_user.set_password(clave_temporal)
            nuevo_user.requiere_cambio_clave = True
            nuevo_user.save()

            registrar_auditoria(
                modulo='USUARIOS',
                accion='CREAR',
                resultado='EXITO',
                usuario=request.user,
                entidad_afectada='Usuario',
                registro_id=nuevo_user.id,
                detalle={'username_creado': nuevo_user.username, 'rol': nuevo_user.rol.codigo if nuevo_user.rol else 'SIN_ROL'},
                request=request
            )

            request.session['ultimo_enrolamiento'] = {
                'id': nuevo_user.id,
                'nombre_completo': nuevo_user.nombre_completo,
                'username': nuevo_user.username,
                'ci': f"{nuevo_user.ci_numero} {nuevo_user.ci_expedido}".strip(),
                'rol': nuevo_user.rol.nombre if nuevo_user.rol else "Sin Rol",
                'clave_temporal': clave_temporal,
            }
            messages.success(request, f"Usuario '{nuevo_user.username}' creado con éxito.")
            return redirect('seguridad:ficha_enrolamiento')
    else:
        form = UsuarioCrearForm()

    return render(request, 'seguridad/usuarios_list.html', {
        'usuarios': usuarios,
        'form': form,
    })


@login_required
@requiere_permiso(modulo='usuarios', accion='ver')
def ficha_enrolamiento_view(request):
    """Ficha imprimible confidencial de entrega de credenciales iniciales (US5)."""
    datos = request.session.get('ultimo_enrolamiento')
    if not datos:
        messages.warning(request, "No hay credenciales pendientes de entrega.")
        return redirect('seguridad:usuarios_list')
        
    return render(request, 'seguridad/ficha_enrolamiento.html', {'datos': datos})


@login_required
@requiere_permiso(modulo='usuarios', accion='crear')
def sugerir_username_view(request):
    """Endpoint utilitario para sugerencia de username (US5)."""
    from django.http import JsonResponse
    nombres = request.GET.get('nombres', '').strip()
    apellido = request.GET.get('apellido', '').strip()
    sugerencia = ""
    if nombres and apellido:
        sugerencia = sugerir_username(nombres, apellido)
    return JsonResponse({'sugerencia': sugerencia, 'disponible': True})
