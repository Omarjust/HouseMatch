from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    Departamento,
    Empresa,
    Etiqueta,
    ImagenInmueble,
    Inmueble,
    InmuebleGuardado,
    PerfilAsesor,
    TipoPropiedad,
    TipoTransaccion,
    Usuario,
)


@admin.register(Usuario)
class UsuarioAdmin(DjangoUserAdmin):
    model = Usuario
    ordering = ("id",)
    list_display = ("id", "email", "username", "is_asesor", "fecha_vencimiento_plan", "plan_activo", "is_staff", "is_active")
    list_filter = ("is_asesor", "is_staff", "is_active", "is_superuser")
    search_fields = ("email", "username", "first_name", "last_name")

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Informacion personal", {"fields": ("first_name", "last_name")}),
        (
            "Permisos",
            {"fields": ("is_active", "is_staff", "is_superuser", "is_asesor", "groups", "user_permissions")},
        ),
        ("Plan", {"fields": ("fecha_vencimiento_plan",)}),
        ("Fechas", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "password1", "password2", "is_asesor", "is_staff", "is_active", "fecha_vencimiento_plan"),
            },
        ),
    )

    @admin.display(boolean=True, description="Plan activo")
    def plan_activo(self, obj):
        return obj.plan_activo


@admin.register(PerfilAsesor)
class PerfilAsesorAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "empresa", "id_asesor_externo")
    list_filter = ("empresa",)
    search_fields = ("user__email", "user__username", "id_asesor_externo", "empresa__nombre")


class ImagenInmuebleInline(admin.TabularInline):
    model = ImagenInmueble
    extra = 1
    fields = ("orden", "url")
    ordering = ("orden",)


@admin.register(Inmueble)
class InmuebleAdmin(admin.ModelAdmin):
    inlines = [ImagenInmuebleInline]
    list_display = (
        "id",
        "titulo",
        "nombre_captador",
        "tipo_propiedad",
        "tipo_transaccion",
        "departamento",
        "precio_usd",
        "precio_bs",
        "ciudad",
        "activo",
    )
    list_filter = ("activo", "tipo_propiedad", "tipo_transaccion", "departamento", "parqueo", "piscina")
    search_fields = ("titulo", "descripcion", "calle", "zona", "ciudad", "nombre_captador", "celular_captacion")
    autocomplete_fields = ("tipo_propiedad", "tipo_transaccion", "departamento")


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "codigo")
    search_fields = ("nombre", "codigo")


@admin.register(TipoPropiedad)
class TipoPropiedadAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)


@admin.register(TipoTransaccion)
class TipoTransaccionAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)


@admin.register(Etiqueta)
class EtiquetaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "usuario", "creada_en")
    list_filter = ("usuario",)
    search_fields = ("nombre", "usuario__email")


@admin.register(InmuebleGuardado)
class InmuebleGuardadoAdmin(admin.ModelAdmin):
    list_display = ("id", "etiqueta", "inmueble", "guardado_en")
    list_filter = ("etiqueta__usuario",)
    search_fields = ("etiqueta__nombre", "inmueble__titulo")
