"""
Modelos del módulo fiscal.
"""
# Fase A - Modelos Base DIAN
from app.fiscal.models.perfil_fiscal import PerfilFiscal
from app.fiscal.models.cuenta_contable import CuentaContable
from app.fiscal.models.impuesto import Impuesto
from app.fiscal.models.audit_log import FiscalAuditLog

# Fase B - Contabilidad Automática
from app.fiscal.models.asiento_contable import AsientoContable
from app.fiscal.models.detalle_asiento import DetalleAsiento
from app.fiscal.models.periodo_contable import PeriodoContable
from app.fiscal.models.log_auditoria_contable import LogAuditoriaContable

# Fase C - Facturación Electrónica
from app.fiscal.models.factura_electronica import FacturaElectronica
from app.fiscal.models.evento_dian import EventoDian
from app.fiscal.models.fiscal_config import FiscalConfig

__all__ = [
    # Fase A
    'PerfilFiscal',
    'CuentaContable',
    'Impuesto',
    'FiscalAuditLog',
    # Fase B
    'AsientoContable',
    'DetalleAsiento',
    'PeriodoContable',
    'LogAuditoriaContable',
    # Fase C - Facturación Electrónica
    'FacturaElectronica',
    'EventoDian',
    'FiscalConfig',
]
