"""
Modelo CuentaContable - Plan Único de Cuentas (PUC) colombiano.

Implementa jerarquía de 5 niveles para contabilidad colombiana.
"""
from django.db import models
from django.core.exceptions import ValidationError


class CuentaContable(models.Model):
    """
    Cuenta contable del Plan Único de Cuentas (PUC) colombiano.
    
    Jerarquía de 5 niveles:
    - Nivel 1: Clase (1 dígito) - Ej: 1 ACTIVO
    - Nivel 2: Grupo (2 dígitos) - Ej: 11 DISPONIBLE
    - Nivel 3: Cuenta (4 dígitos) - Ej: 1105 CAJA
    - Nivel 4: Subcuenta (6 dígitos) - Ej: 110505 CAJA GENERAL
    - Nivel 5: Auxiliar (8 dígitos) - Ej: 11050501 CAJA PRINCIPAL
    
    Solo las cuentas auxiliares (nivel 5) pueden tener movimientos contables.
    
    Attributes:
        codigo: Código único de la cuenta
        nombre: Nombre descriptivo
        nivel: Nivel jerárquico (1-5)
        padre: Cuenta padre en la jerarquía
        naturaleza: Débito (D) o Crédito (C)
        tipo: Clasificación (ACTIVO, PASIVO, etc.)
        acepta_movimiento: Si puede tener movimientos contables
        activa: Si la cuenta está activa
    
    Examples:
        >>> clase = CuentaContable.objects.create(
        ...     codigo='1',
        ...     nombre='ACTIVO',
        ...     nivel=1,
        ...     naturaleza='D',
        ...     tipo='ACTIVO'
        ... )
        >>> grupo = CuentaContable.objects.create(
        ...     codigo='11',
        ...     nombre='DISPONIBLE',
        ...     nivel=2,
        ...     padre=clase,
        ...     naturaleza='D',
        ...     tipo='ACTIVO'
        ... )
    """
    
    # Choices
    NATURALEZA_CHOICES = [
        ('D', 'Débito'),
        ('C', 'Crédito'),
    ]
    
    TIPO_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('PASIVO', 'Pasivo'),
        ('PATRIMONIO', 'Patrimonio'),
        ('INGRESO', 'Ingreso'),
        ('GASTO', 'Gasto'),
        ('COSTO', 'Costo'),
    ]
    
    # Campos
    codigo = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        help_text='Código único de la cuenta'
    )
    
    nombre = models.CharField(
        max_length=200,
        help_text='Nombre descriptivo de la cuenta'
    )
    
    nivel = models.IntegerField(
        help_text='Nivel jerárquico (1-5)'
    )
    
    padre = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='hijos',
        help_text='Cuenta padre en la jerarquía'
    )
    
    naturaleza = models.CharField(
        max_length=1,
        choices=NATURALEZA_CHOICES,
        help_text='Naturaleza de la cuenta (Débito o Crédito)'
    )
    
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        help_text='Tipo de cuenta'
    )
    
    acepta_movimiento = models.BooleanField(
        default=False,
        help_text='Indica si la cuenta puede tener movimientos contables'
    )
    
    activa = models.BooleanField(
        default=True,
        help_text='Indica si la cuenta está activa'
    )
    
    descripcion = models.TextField(
        blank=True,
        help_text='Descripción adicional de la cuenta'
    )
    
    # Metadata
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text='Fecha de creación'
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        help_text='Fecha de última actualización'
    )
    
    class Meta:
        db_table = 'cuenta_contable'
        verbose_name = 'Cuenta Contable'
        verbose_name_plural = 'Cuentas Contables'
        ordering = ['codigo']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['nivel']),
            models.Index(fields=['tipo']),
        ]
    
    def clean(self):
        """
        Validaciones personalizadas del modelo.
        
        Valida:
        - Nivel coherente con longitud del código
        - Padre debe ser del nivel inmediatamente anterior
        - Naturaleza debe coincidir con el padre
        
        Raises:
            ValidationError: Si alguna validación falla
        """
        errors = {}
        
        # Validar nivel coherente con código
        nivel_esperado = self._calcular_nivel_from_codigo(self.codigo)
        if self.nivel != nivel_esperado:
            errors['nivel'] = f'Nivel {self.nivel} no coherente con código {self.codigo}. Esperado: {nivel_esperado}'
        
        # Validar que el padre sea del nivel anterior
        if self.padre:
            if self.padre.nivel != self.nivel - 1:
                errors['padre'] = f'Padre debe ser nivel {self.nivel - 1}, pero es nivel {self.padre.nivel}'
            
            # Validar que la naturaleza coincida con el padre
            if self.naturaleza != self.padre.naturaleza:
                errors['naturaleza'] = f'Naturaleza debe ser {self.padre.naturaleza} (igual al padre)'
        
        # Validar que nivel 1 no tenga padre
        if self.nivel == 1 and self.padre:
            errors['padre'] = 'Cuentas de nivel 1 (Clase) no pueden tener padre'
        
        # Validar que niveles > 1 tengan padre
        if self.nivel > 1 and not self.padre:
            errors['padre'] = f'Cuentas de nivel {self.nivel} deben tener padre'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """
        Override save para auto-calcular nivel y ejecutar validaciones.
        """
        # Auto-calcular nivel si no está definido
        if not self.nivel:
            self.nivel = self._calcular_nivel_from_codigo(self.codigo)
        
        # Ejecutar validaciones
        self.full_clean()
        
        super().save(*args, **kwargs)
    
    @staticmethod
    def _calcular_nivel_from_codigo(codigo):
        """
        Calcula el nivel basado en la longitud del código (método estático).
        
        Args:
            codigo: Código de la cuenta
        
        Returns:
            int: Nivel calculado (1-5)
        """
        longitud = len(codigo)
        
        if longitud == 1:
            return 1  # Clase
        elif longitud == 2:
            return 2  # Grupo
        elif longitud == 4:
            return 3  # Cuenta
        elif longitud == 6:
            return 4  # Subcuenta
        elif longitud == 8:
            return 5  # Auxiliar
        else:
            return 0  # Inválido
    
    def get_nivel_from_codigo(self):
        """
        Calcula el nivel basado en la longitud del código.
        
        Returns:
            int: Nivel calculado (1-5)
        
        Examples:
            >>> cuenta = CuentaContable(codigo='1')
            >>> cuenta.get_nivel_from_codigo()
            1
            >>> cuenta = CuentaContable(codigo='110505')
            >>> cuenta.get_nivel_from_codigo()
            4
        """
        return self._calcular_nivel_from_codigo(self.codigo)
    
    def get_ruta_jerarquica(self):
        """
        Retorna la ruta jerárquica completa desde la clase hasta esta cuenta.
        
        Returns:
            list: Lista de cuentas desde la raíz hasta esta cuenta
        
        Examples:
            >>> cuenta.get_ruta_jerarquica()
            [<CuentaContable: 1 ACTIVO>, <CuentaContable: 11 DISPONIBLE>, <CuentaContable: 1105 CAJA>]
        """
        ruta = [self]
        actual = self.padre
        
        while actual:
            ruta.insert(0, actual)
            actual = actual.padre
        
        return ruta
    
    def get_subcuentas(self):
        """
        Retorna todas las subcuentas hijas directas.
        
        Returns:
            QuerySet: Subcuentas hijas
        """
        return self.hijos.filter(activa=True)
    
    def puede_tener_movimientos(self):
        """
        Verifica si la cuenta puede tener movimientos contables.
        
        Returns:
            bool: True si puede tener movimientos
        """
        return self.acepta_movimiento
    
    def __str__(self):
        """Representación en string de la cuenta"""
        return f"{self.codigo} - {self.nombre}"
