from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import ProfilUtilisateur, GroupeEtendu, HistoriqueGroupes


# Configuration pour ProfilUtilisateur
class ProfilUtilisateurInline(admin.StackedInline):
    model = ProfilUtilisateur
    can_delete = False
    verbose_name = "Profil"
    verbose_name_plural = "Profils"
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('telephone', 'service', 'poste', 'date_embauche')
        }),
        ('Statut', {
            'fields': ('actif',)
        }),
    )


@admin.register(ProfilUtilisateur)
class ProfilUtilisateurAdmin(admin.ModelAdmin):
    list_display = ['nom_complet', 'user_username', 'service', 'poste', 'telephone', 'actif', 'date_creation']
    list_filter = ['actif', 'service', 'date_embauche', 'date_creation']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'service', 'poste', 'telephone']
    readonly_fields = ['date_creation', 'date_modification']
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Informations professionnelles', {
            'fields': ('service', 'poste', 'telephone', 'date_embauche')
        }),
        ('Statut et dates', {
            'fields': ('actif', 'date_creation', 'date_modification'),
        }),
    )
    
    def nom_complet(self, obj):
        return obj.nom_complet
    nom_complet.short_description = 'Nom complet'
    nom_complet.admin_order_field = 'user__last_name'
    
    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'Username'
    user_username.admin_order_field = 'user__username'


# Configuration pour GroupeEtendu
class GroupeEtenduInline(admin.StackedInline):
    model = GroupeEtendu
    can_delete = False
    verbose_name = "Informations étendues"
    verbose_name_plural = "Informations étendues"
    fieldsets = (
        (None, {
            'fields': ('description', 'couleur', 'niveau_acces', 'actif')
        }),
    )


@admin.register(GroupeEtendu)
class GroupeEtenduAdmin(admin.ModelAdmin):
    list_display = ['group_name', 'couleur_display', 'niveau_acces', 'nombre_utilisateurs', 'nombre_permissions', 'actif', 'date_creation']
    list_filter = ['niveau_acces', 'actif', 'date_creation']
    search_fields = ['group__name', 'description']
    readonly_fields = ['date_creation', 'date_modification', 'nombre_utilisateurs', 'nombre_permissions']
    
    fieldsets = (
        ('Groupe', {
            'fields': ('group',)
        }),
        ('Configuration', {
            'fields': ('description', 'couleur', 'niveau_acces', 'actif')
        }),
        ('Statistiques', {
            'fields': ('nombre_utilisateurs', 'nombre_permissions'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def group_name(self, obj):
        return obj.group.name
    group_name.short_description = 'Nom du groupe'
    group_name.admin_order_field = 'group__name'
    
    def couleur_display(self, obj):
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            obj.couleur,
            obj.couleur
        )
    couleur_display.short_description = 'Couleur'


@admin.register(HistoriqueGroupes)
class HistoriqueGroupesAdmin(admin.ModelAdmin):
    list_display = ['group_name', 'action_display', 'utilisateur_modifieur', 'utilisateur_cible', 'date_action']
    list_filter = ['action', 'date_action', 'group']
    search_fields = ['group__name', 'utilisateur_modifieur__username', 'utilisateur_cible__username', 'details']
    readonly_fields = ['group', 'action', 'utilisateur_modifieur', 'utilisateur_cible', 'permission_cible', 'details', 'date_action']
    date_hierarchy = 'date_action'
    
    fieldsets = (
        ('Action', {
            'fields': ('group', 'action', 'date_action')
        }),
        ('Utilisateurs concernés', {
            'fields': ('utilisateur_modifieur', 'utilisateur_cible')
        }),
        ('Permission concernée', {
            'fields': ('permission_cible',)
        }),
        ('Détails', {
            'fields': ('details',)
        }),
    )
    
    def group_name(self, obj):
        return obj.group.name
    group_name.short_description = 'Groupe'
    group_name.admin_order_field = 'group__name'
    
    def action_display(self, obj):
        colors = {
            'create': '#28a745',
            'update': '#17a2b8', 
            'delete': '#dc3545',
            'add_user': '#28a745',
            'remove_user': '#fd7e14',
            'add_permission': '#20c997',
            'remove_permission': '#ffc107',
        }
        color = colors.get(obj.action, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_action_display()
        )
    action_display.short_description = 'Action'
    
    def has_add_permission(self, request):
        return False  # Pas d'ajout manuel d'historique
    
    def has_change_permission(self, request, obj=None):
        return False  # Pas de modification d'historique
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Seul le superuser peut supprimer


# Personnalisation de l'admin User existant
class CustomUserAdmin(UserAdmin):
    inlines = (ProfilUtilisateurInline,)
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'groupes_display', 'date_joined')
    list_filter = UserAdmin.list_filter + ('groups', 'profil__service', 'profil__actif')
    
    def groupes_display(self, obj):
        if hasattr(obj, 'profil'):
            groupes = obj.groups.all()
            if groupes:
                badges = []
                for groupe in groupes:
                    try:
                        groupe_etendu = groupe.groupe_etendu
                        badges.append(
                            f'<span style="background-color: {groupe_etendu.couleur}; color: white; '
                            f'padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-right: 2px;">'
                            f'{groupe.name}</span>'
                        )
                    except:
                        badges.append(
                            f'<span style="background-color: #6c757d; color: white; '
                            f'padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-right: 2px;">'
                            f'{groupe.name}</span>'
                        )
                return mark_safe(''.join(badges))
        return '-'
    groupes_display.short_description = 'Groupes'


# Personnalisation de l'admin Group existant  
class CustomGroupAdmin(GroupAdmin):
    inlines = (GroupeEtenduInline,)
    
    list_display = ('name', 'niveau_acces_display', 'utilisateurs_count', 'permissions_count', 'couleur_display')
    list_filter = ('permissions', 'groupe_etendu__niveau_acces', 'groupe_etendu__actif')
    
    def niveau_acces_display(self, obj):
        try:
            return f"Niveau {obj.groupe_etendu.niveau_acces}"
        except:
            return "Non défini"
    niveau_acces_display.short_description = 'Niveau d\'accès'
    
    def utilisateurs_count(self, obj):
        count = obj.user_set.count()
        if count > 0:
            url = reverse('admin:auth_user_changelist') + f'?groups__id__exact={obj.id}'
            return format_html('<a href="{}">{} utilisateur{}</a>', 
                             url, count, 's' if count > 1 else '')
        return '0 utilisateur'
    utilisateurs_count.short_description = 'Utilisateurs'
    
    def permissions_count(self, obj):
        count = obj.permissions.count()
        if count > 0:
            return f"{count} permission{'s' if count > 1 else ''}"
        return '0 permission'
    permissions_count.short_description = 'Permissions'
    
    def couleur_display(self, obj):
        try:
            couleur = obj.groupe_etendu.couleur
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">●</span>',
                couleur
            )
        except:
            return '-'
    couleur_display.short_description = 'Couleur'


# Désinscrire les anciens admins et réinscrire les nouveaux
admin.site.unregister(User)
admin.site.unregister(Group)

admin.site.register(User, CustomUserAdmin)
admin.site.register(Group, CustomGroupAdmin)

# Configuration du site d'administration
admin.site.site_header = "Administration - Suivi des Conducteurs"
admin.site.site_title = "Suivi Conducteurs Admin"
admin.site.index_title = "Gestion des utilisateurs et groupes"
