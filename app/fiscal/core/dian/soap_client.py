class DianSOAPClient:
    """
    Cliente SOAP para comunicación con los Web Services de la DIAN.
    """
    AMIENTE_HABILITACION = "https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc"
    AMBIENTE_PRODUCCION = "https://vpfe.dian.gov.co/WcfDianCustomerServices.svc"

    def __init__(self, ambiente='habilitacion'):
        self.url = self.AMIENTE_HABILITACION if ambiente == 'habilitacion' else self.AMBIENTE_PRODUCCION

    def enviar_factura(self, xml_firmado):
        """
        Envía una factura firmada (SendBill).
        """
        pass

    def consultar_estado(self, track_id):
        """
        Consulta el estado de un envío (GetStatus).
        """
        pass
