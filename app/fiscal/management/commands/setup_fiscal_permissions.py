"""
Management command para configurar permisos fiscales.

Crea grupos y permisos necesarios para el módulo fiscal.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from app.fiscal.models import PerfilFiscal, CuentaContable, Impuesto, FiscalAuditLog


class Command(BaseCommand):
    help = 'Configura grupos y permisos para el módulo fiscal'
    
    def handle(self, *args, **options):
        self.stdout.write('Configurando permisos fiscales...')
        
        # Crear permisos personalizados
        self.create_custom_permissions()
        
        # Crear grupos
        self.create_groups()
        
        self.stdout.write(self.style.SUCCESS('✅ Permisos fiscales configurados'))
    
    def create_custom_permissions(self):
        """Crea permisos personalizados para datos fiscales"""
        self.stdout.write('Creando permisos personalizados...')
        
        # Obtener content type para PerfilFiscal
        content_type = ContentType.objects.get_for_model(PerfilFiscal)
        
        # Definir permisos personalizados
        custom_permissions = [
            ('view_fiscal_data', 'Puede ver datos fiscales'),
            ('add_fiscal_data', 'Puede crear datos fiscales'),
            ('change_fiscal_data', 'Puede modificar datos fiscales'),
            ('delete_fiscal_data', 'Puede eliminar datos fiscales'),
            ('audit_fiscal_data', 'Puede ver logs de auditoría fiscal'),
            ('export_fiscal_data', 'Puede exportar datos fiscales'),
        ]
        
        for codename, name in custom_permissions:
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={'name': name}
            )
            
            if created:
                self.stdout.write(f'  ✓ Creado: {name}')
            else:
                self.stdout.write(f'  - Ya existe: {name}')
    
    def create_groups(self):
        """Crea grupos con permisos predefinidos"""
        self.stdout.write('\nCreando grupos...')
        
        # Grupo: Contador
        contador_group, created = Group.objects.get_or_create(name='Contador')
        if created:
            self.stdout.write('  ✓ Creado grupo: Contador')
        
        contador_permissions = [
            'view_fiscal_data',
            'add_fiscal_data',
            'change_fiscal_data',
            'audit_fiscal_data',
            'export_fiscal_data',
        ]
        
        for perm_code in contador_permissions:
            try:
                perm = Permission.objects.get(codename=perm_code)
                contador_group.permissions.add(perm)
            except Permission.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠ Permiso no encontrado: {perm_code}')
                )
        
        self.stdout.write('  ✓ Permisos asignados a Contador')
        
        # Grupo: Auditor Fiscal
        auditor_group, created = Group.objects.get_or_create(name='Auditor Fiscal')
        if created:
            self.stdout.write('  ✓ Creado grupo: Auditor Fiscal')
        
        auditor_permissions = [
            'view_fiscal_data',
            'audit_fiscal_data',
            'export_fiscal_data',
        ]
        
        for perm_code in auditor_permissions:
            try:
                perm = Permission.objects.get(codename=perm_code)
                auditor_group.permissions.add(perm)
            except Permission.DoesNotExist:
                pass
        
        self.stdout.write('  ✓ Permisos asignados a Auditor Fiscal')
        
        # Grupo: Operador Fiscal
        operador_group, created = Group.objects.get_or_create(name='Operador Fiscal')
        if created:
            self.stdout.write('  ✓ Creado grupo: Operador Fiscal')
        
        operador_permissions = [
            'view_fiscal_data',
            'add_fiscal_data',
            'change_fiscal_data',
        ]
        
        for perm_code in operador_permissions:
            try:
                perm = Permission.objects.get(codename=perm_code)
                operador_group.permissions.add(perm)
            except Permission.DoesNotExist:
                pass
        
        self.stdout.write('  ✓ Permisos asignados a Operador Fiscal')
        
        # Resumen
        self.stdout.write('\n📊 Resumen de grupos:')
        self.stdout.write(f'  • Contador: {contador_group.permissions.count()} permisos')
        self.stdout.write(f'  • Auditor Fiscal: {auditor_group.permissions.count()} permisos')
        self.stdout.write(f'  • Operador Fiscal: {operador_group.permissions.count()} permisos')
