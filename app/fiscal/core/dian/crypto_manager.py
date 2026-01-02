import hashlib
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)

class FiscalCryptoManager:
    """
    Gestor de Criptografía y Firma Digital (XAdES-BES) y cálculo de CUFE.
    Permite cargar un archivo .p12 (PKCS#12) y utilizar su llave privada para firmar.
    """
    def __init__(self, certificate_path=None, password=None, load_cert=True):
        self.certificate_path = certificate_path
        self.password = password.encode('utf-8') if isinstance(password, str) and password else password
        self.private_key = None
        self.cert = None
        self.additional_certs = []
        
        # Only load certificate if requested and path is provided
        if load_cert and certificate_path and password:
            try:
                self._load_certificate()
            except Exception as e:
                logger.warning(f"Could not load certificate: {e}. CUFE generation will still work.")

    def _load_certificate(self):
        """Carga el archivo .p12 y extrae la llave privada y el certificado."""
        if not self.certificate_path or not os.path.exists(self.certificate_path):
            raise FileNotFoundError(f"No se encontró el certificado en: {self.certificate_path}")
            
        with open(self.certificate_path, "rb") as f:
            p12_data = f.read()
        
        # Cargar PKCS12 usando cryptography
        self.private_key, self.cert, self.additional_certs = pkcs12.load_key_and_certificates(
            p12_data,
            self.password
        )

    def generar_cufe(
        self,
        numero_factura: str,
        fecha_emision: str,
        hora_emision: str,
        valor_total: float,
        cod_imp1: str,
        val_imp1: float,
        cod_imp2: str,
        val_imp2: float,
        cod_imp3: str,
        val_imp3: float,
        valor_pagar: float,
        nit_emisor: str,
        tipo_adquirente: str,
        num_adquirente: str,
        clave_tecnica: str,
        tipo_ambiente: str = '2'
    ) -> str:
        """
        Calcula el CUFE usando SHA-384 según Anexo Técnico 1.8 DIAN.
        
        Fórmula exacta de concatenación:
        NumFac + FecFac + HorFac + ValFac + CodImp1 + ValImp1 + CodImp2 + ValImp2 + 
        CodImp3 + ValImp3 + ValPag + NitOFE + TipAdq + NumAdq + ClTec + TipoAmb
        
        Args:
            numero_factura: Número de factura con prefijo (ej: "SETP990001")
            fecha_emision: Fecha en formato YYYY-MM-DD (ej: "2024-01-15")
            hora_emision: Hora en formato HH:MM:SS-05:00 (ej: "14:30:00-05:00")
            valor_total: Valor total de la factura CON impuestos
            cod_imp1: Código impuesto 1 (ej: "01" para IVA)
            val_imp1: Valor del impuesto 1 (formato XX.XX)
            cod_imp2: Código impuesto 2 (ej: "04" para Consumo)
            val_imp2: Valor del impuesto 2
            cod_imp3: Código impuesto 3 (ej: "03" para ICA)
            val_imp3: Valor del impuesto 3
            valor_pagar: Valor total a pagar (usualmente igual a valor_total)
            nit_emisor: NIT del emisor SIN dígito de verificación
            tipo_adquirente: Tipo de documento del adquirente ("31"=NIT, "13"=CC, etc.)
            num_adquirente: Número de identificación del adquirente
            clave_tecnica: Clave técnica del rango de numeración
            tipo_ambiente: "1"=Producción, "2"=Habilitación
            
        Returns:
            Hash SHA-384 en hexadecimal (96 caracteres)
            
        Raises:
            ValueError: Si algún campo requerido es inválido
            
        Ejemplo:
            >>> cufe = crypto.generar_cufe(
            ...     numero_factura="SETP990001",
            ...     fecha_emision="2024-01-15",
            ...     hora_emision="14:30:00-05:00",
            ...     valor_total=119000.00,
            ...     cod_imp1="01", val_imp1=19000.00,
            ...     cod_imp2="04", val_imp2=0.00,
            ...     cod_imp3="03", val_imp3=0.00,
            ...     valor_pagar=119000.00,
            ...     nit_emisor="900123456",
            ...     tipo_adquirente="31",
            ...     num_adquirente="860123456",
            ...     clave_tecnica="fc8eac422eba16e22ffd8c6f94b3f40a6e38162c",
            ...     tipo_ambiente="2"
            ... )
        """
        # Validaciones de entrada
        if not numero_factura or not numero_factura.strip():
            raise ValueError("numero_factura es requerido")
        
        if not fecha_emision or len(fecha_emision) != 10:
            raise ValueError("fecha_emision debe estar en formato YYYY-MM-DD")
        
        if not hora_emision:
            raise ValueError("hora_emision es requerida")
        
        # Formatear valores decimales a 2 decimales con punto
        def format_decimal(value: float) -> str:
            """Formatea un valor decimal según estándar DIAN (2 decimales, punto)."""
            return f"{float(value):.2f}"
        
        # Construir cadena de concatenación según especificación exacta DIAN
        cadena_cufe = "".join([
            str(numero_factura),                    # NumFac
            str(fecha_emision),                     # FecFac (YYYY-MM-DD)
            str(hora_emision),                      # HorFac (HH:MM:SS-05:00)
            format_decimal(valor_total),            # ValFac
            str(cod_imp1),                          # CodImp1
            format_decimal(val_imp1),               # ValImp1
            str(cod_imp2),                          # CodImp2
            format_decimal(val_imp2),               # ValImp2
            str(cod_imp3),                          # CodImp3
            format_decimal(val_imp3),               # ValImp3
            format_decimal(valor_pagar),            # ValPag
            str(nit_emisor),                        # NitOFE
            str(tipo_adquirente),                   # TipAdq
            str(num_adquirente),                    # NumAdq
            str(clave_tecnica),                     # ClTec
            str(tipo_ambiente)                      # TipoAmb
        ])
        
        # Calcular SHA-384
        cufe_hash = hashlib.sha384(cadena_cufe.encode('utf-8')).hexdigest()
        
        return cufe_hash

    def firmar_xml(self, xml_content):
        """
        Firma digitalmente el contenido XML usando XAdES-BES.
        (Implementación pendiente: Requiere lxml y construcción de Signature)
        """
        # Por ahora retornamos el XML sin firmar para validar el flujo
        return xml_content
