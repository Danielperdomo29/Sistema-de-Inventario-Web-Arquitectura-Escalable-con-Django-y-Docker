"""
Configuración centralizada para servicios DIAN de Facturación Electrónica.
Define endpoints, timeouts y configuraciones específicas por ambiente.
"""
from typing import Dict, Any
from enum import IntEnum


class AmbienteDIAN(IntEnum):
    """Tipos de ambiente DIAN para facturación electrónica."""
    PRODUCCION = 1
    HABILITACION = 2  # Ambiente de pruebas


class DIANConfig:
    """
    Configuración de endpoints y parámetros DIAN por ambiente.
    
    Referencias:
    - Documentación técnica DIAN v1.8
    - https://www.dian.gov.co/facturae
    """
    
    # Endpoints SOAP para envío de documentos electrónicos
    ENDPOINTS = {
        AmbienteDIAN.PRODUCCION: {
            'webservice': 'https://vpfe.dian.gov.co/WcfDianCustomerServices.svc',
            'validacion': 'https://catalogo-vpfe.dian.gov.co/User/SearchDocument',
            'consulta': 'https://vpfe.dian.gov.co/WcfDianCustomerServices.svc/GetStatus',
        },
        AmbienteDIAN.HABILITACION: {
            'webservice': 'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc',
            'validacion': 'https://catalogo-vpfe-hab.dian.gov.co/User/SearchDocument',
            'consulta': 'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc/GetStatus',
        }
    }
    
    # Namespaces UBL 2.1 y extensiones DIAN
    UBL_NAMESPACES = {
        'xmlns': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
        'xmlns:cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
        'xmlns:cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
        'xmlns:ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
        'xmlns:sts': 'dian:gov:co:facturaelectronica:Structures-2-1',
        'xmlns:xades': 'http://uri.etsi.org/01903/v1.3.2#',
        'xmlns:xades141': 'http://uri.etsi.org/01903/v1.4.1#',
        'xmlns:ds': 'http://www.w3.org/2000/09/xmldsig#',
    }
    
    # Códigos de tipo de documento DIAN
    TIPO_DOCUMENTO = {
        'FACTURA_VENTA': '01',
        'FACTURA_EXPORTACION': '02',
        'FACTURA_CONTINGENCIA': '03',
        'FACTURA_AIU': '04',
        'NOTA_DEBITO': '91',
        'NOTA_CREDITO': '92',
    }
    
    # Códigos de impuestos DIAN
    CODIGOS_IMPUESTO = {
        'IVA': '01',
        'INC': '02',  # Impuesto Nacional al Consumo
        'ICA': '03',  # Impuesto de Industria y Comercio
        'CONSUMO': '04',
    }
    
    # Tarifas de IVA válidas en Colombia
    TARIFAS_IVA = [0, 5, 19]  # Porcentajes válidos
    
    # Configuración de conexión
    CONNECTION_CONFIG = {
        'timeout': 30,  # segundos
        'retry_attempts': 3,
        'retry_delay': 2,  # segundos entre reintentos
    }
    
    # Validaciones
    MAX_FILE_SIZE_MB = 5  # Tamaño máximo XML
    
    @classmethod
    def get_endpoint(cls, ambiente: int, tipo: str = 'webservice') -> str:
        """
        Obtiene el endpoint DIAN según ambiente y tipo de servicio.
        
        Args:
            ambiente: 1=Producción, 2=Habilitación
            tipo: 'webservice', 'validacion', 'consulta'
            
        Returns:
            URL del endpoint
            
        Raises:
            ValueError: Si el ambiente o tipo no es válido
        """
        if ambiente not in cls.ENDPOINTS:
            raise ValueError(f"Ambiente inválido: {ambiente}. Use 1 (Producción) o 2 (Habilitación)")
        
        if tipo not in cls.ENDPOINTS[ambiente]:
            raise ValueError(f"Tipo de servicio inválido: {tipo}")
        
        return cls.ENDPOINTS[ambiente][tipo]
    
    @classmethod
    def get_connection_config(cls) -> Dict[str, Any]:
        """Retorna configuración de conexión para requests HTTP."""
        return cls.CONNECTION_CONFIG.copy()
    
    @classmethod
    def validar_tarifa_iva(cls, tarifa: float) -> bool:
        """
        Valida si una tarifa de IVA es válida según normativa colombiana.
        
        Args:
            tarifa: Porcentaje de IVA (ej: 19, 5, 0)
            
        Returns:
            True si la tarifa es válida
        """
        return tarifa in cls.TARIFAS_IVA
