"""
Locust Load Testing - Sistema de Inventario
Ejecutar: locust -f locustfile.py --host=http://127.0.0.1:8000
"""
from locust import HttpUser, task, between
import random

class InventarioUser(HttpUser):
    """Simula un usuario real del sistema de inventario"""
    
    wait_time = between(1, 3)  # Pausa entre 1-3 segundos entre requests
    
    def on_start(self):
        """Login antes de comenzar las tareas"""
        self.client.post("/login/", {
            "username": "admin",
            "password": "1003811758"
        }, name="Login")
    
    @task(5)
    def view_products(self):
        """Vista de productos (más frecuente, cacheable)"""
        self.client.get("/productos/", name="Productos - List")
    
    @task(3)
    def view_sales(self):
        """Vista de ventas"""
        self.client.get("/ventas/", name="Ventas - List")
    
    @task(2)
    def view_dashboard(self):
        """Dashboard principal"""
        self.client.get("/", name="Dashboard")
    
    @task(1)
    def view_clients(self):
        """Vista de clientes"""
        self.client.get("/clientes/", name="Clientes - List")
    
    @task(1)
    def view_product_create(self):
        """Formulario crear producto"""
        self.client.get("/productos/crear/", name="Productos - Create Form")
    
    # Comentado porque requiere producto_id válido
    # @task(1)
    # def view_product_detail(self):
    #     """Ver detalle de producto aleatorio"""
    #     product_id = random.randint(1, 100)
    #     self.client.get(f"/productos/{product_id}/editar/", name="Productos - Edit")


class HeavyUser(HttpUser):
    """Usuario que hace operaciones más pesadas"""
    
    wait_time = between(2, 5)
    
    def on_start(self):
        self.client.post("/login/", {
            "username": "admin",
            "password": "1003811758"
        })
    
    @task(3)
    def view_sales(self):
        """Consulta ventas (puede ser pesada sin cache)"""
        self.client.get("/ventas/")
    
    @task(2)
    def view_analytics(self):
        """Dashboard analytics (operación pesada)"""
        self.client.get("/analytics/", name="Analytics")
    
    @task(1)
    def view_reports(self):
        """Reportes"""
        self.client.get("/reportes/", name="Reportes")
