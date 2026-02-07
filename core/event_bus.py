"""
Event Bus - Sistema de eventos resiliente usando Redis Pub/Sub

Proporciona comunicación asíncrona entre módulos:
- Contabilidad recibe eventos de ventas
- Analytics recibe eventos de inventario
- IA recibe eventos para actualizar contexto

Características:
- Reconexión automática a Redis
- Fallback a sistema en memoria si Redis no está disponible
- Persistencia opcional de eventos para suscriptores tardíos
"""

import json
import logging
import threading
import uuid
from datetime import datetime
from typing import Callable, Dict, List, Any, Optional

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


# Tipos de eventos predefinidos
class EventTypes:
    """Constantes para tipos de eventos del sistema"""
    # Ventas
    VENTA_REGISTRADA = 'VENTA_REGISTRADA'
    VENTA_ANULADA = 'VENTA_ANULADA'
    VENTA_MODIFICADA = 'VENTA_MODIFICADA'
    
    # Inventario
    INVENTARIO_ACTUALIZADO = 'INVENTARIO_ACTUALIZADO'
    STOCK_BAJO_DETECTADO = 'STOCK_BAJO_DETECTADO'
    PRODUCTO_CREADO = 'PRODUCTO_CREADO'
    
    # Compras
    COMPRA_REGISTRADA = 'COMPRA_REGISTRADA'
    COMPRA_RECIBIDA = 'COMPRA_RECIBIDA'
    
    # Contabilidad
    ASIENTO_CONTABLE_CREADO = 'ASIENTO_CONTABLE_CREADO'
    CIERRE_PERIODO = 'CIERRE_PERIODO'
    
    # Analytics
    ANOMALIA_DETECTADA = 'ANOMALIA_DETECTADA'
    PREDICCION_GENERADA = 'PREDICCION_GENERADA'
    
    # Sistema
    SISTEMA_INICIADO = 'SISTEMA_INICIADO'
    ERROR_CRITICO = 'ERROR_CRITICO'


class EventBus:
    """
    Bus de eventos resiliente usando Redis Pub/Sub
    
    Implementa patrón Singleton para uso global.
    Soporta fallback a sistema en memoria si Redis no está disponible.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialize()
        self._initialized = True
    
    def _initialize(self):
        """Inicializa conexión a Redis con reintentos"""
        self.redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
        self.redis_client = None
        self.pubsub = None
        self.subscribers: Dict[str, List[Callable]] = {}
        self._listening = False
        self._listener_thread = None
        self._enabled = getattr(settings, 'EVENT_BUS_ENABLED', True)
        
        if self._enabled:
            self._connect()
    
    def _connect(self, retry_count: int = 0):
        """Establece conexión a Redis con reintento exponencial"""
        try:
            import redis
            
            self.redis_client = redis.Redis.from_url(
                self.redis_url,
                socket_connect_timeout=5,
                socket_keepalive=True,
                retry_on_timeout=True,
                decode_responses=True
            )
            
            # Test de conexión
            self.redis_client.ping()
            self.pubsub = self.redis_client.pubsub(ignore_subscribe_messages=True)
            logger.info("✅ EventBus conectado a Redis exitosamente")
            
        except ImportError:
            logger.warning("⚠️  Librería redis no instalada. Usando modo memoria.")
            self.redis_client = None
            
        except Exception as e:
            logger.error(f"❌ Error conectando a Redis: {e}")
            
            if retry_count < 3:
                import time
                delay = 2 ** retry_count  # Retardo exponencial: 1, 2, 4 segundos
                logger.info(f"Reintentando conexión en {delay} segundos...")
                time.sleep(delay)
                self._connect(retry_count + 1)
            else:
                logger.warning("⚠️  Usando sistema en memoria como fallback")
                self.redis_client = None
    
    def _ensure_connection(self):
        """Verifica y restablece conexión si es necesario"""
        if not self._enabled:
            return
            
        if self.redis_client is None:
            self._connect()
        else:
            try:
                self.redis_client.ping()
            except Exception:
                logger.warning("Conexión Redis perdida, reconectando...")
                self._connect()
    
    def publish(self, event_type: str, data: dict, persistent: bool = False) -> bool:
        """
        Publica un evento a todos los suscriptores
        
        Args:
            event_type: Tipo de evento (usar EventTypes.*)
            data: Datos del evento
            persistent: Si True, guarda en cache para suscriptores tardíos
            
        Returns:
            bool: True si el evento fue publicado exitosamente
        """
        if not self._enabled:
            logger.debug(f"EventBus deshabilitado, ignorando: {event_type}")
            return False
        
        self._ensure_connection()
        
        event_data = {
            'type': event_type,
            'data': data,
            'timestamp': timezone.now().isoformat(),
            'event_id': str(uuid.uuid4())
        }
        
        success = False
        
        try:
            if self.redis_client:
                # Publicar a Redis
                channel = f'event:{event_type}'
                self.redis_client.publish(channel, json.dumps(event_data))
                
                if persistent:
                    # Guardar último evento para suscriptores tardíos
                    cache_key = f'last_event:{event_type}'
                    self.redis_client.setex(cache_key, 3600, json.dumps(event_data))
                
                logger.debug(f"📤 Evento publicado: {event_type} -> {event_data['event_id']}")
                success = True
                
            else:
                # Fallback a sistema en memoria
                self._dispatch_to_subscribers(event_type, event_data)
                success = True
                
        except Exception as e:
            logger.error(f"❌ Error publicando evento {event_type}: {e}")
        
        return success
    
    def subscribe(self, event_type: str, callback: Callable, persistent: bool = False):
        """
        Suscribe una función a un tipo de evento
        
        Args:
            event_type: Tipo de evento a suscribirse
            callback: Función que recibe (event_data: dict)
            persistent: Si True, procesa último evento guardado
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(callback)
        logger.debug(f"📥 Suscrito a evento: {event_type} ({len(self.subscribers[event_type])} suscriptores)")
        
        # Si hay Redis y es persistente, procesar último evento
        if persistent and self.redis_client:
            try:
                cache_key = f'last_event:{event_type}'
                last_event = self.redis_client.get(cache_key)
                if last_event:
                    event_data = json.loads(last_event)
                    self._safe_callback(callback, event_data)
            except Exception as e:
                logger.error(f"Error procesando evento persistente: {e}")
        
        # Iniciar listener de Redis si no está corriendo
        if self.redis_client and not self._listening:
            self._start_listener()
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """Cancela suscripción de un callback"""
        if event_type in self.subscribers and callback in self.subscribers[event_type]:
            self.subscribers[event_type].remove(callback)
            logger.debug(f"🚫 Desuscrito de evento: {event_type}")
    
    def _start_listener(self):
        """Inicia hilo para escuchar eventos de Redis"""
        if self._listening or not self.redis_client:
            return
        
        def listener():
            try:
                # Suscribirse a todos los canales de eventos
                patterns = ['event:*']
                self.pubsub.psubscribe(patterns)
                
                for message in self.pubsub.listen():
                    if message['type'] == 'pmessage':
                        try:
                            event_data = json.loads(message['data'])
                            event_type = event_data.get('type', '')
                            self._dispatch_to_subscribers(event_type, event_data)
                        except json.JSONDecodeError as e:
                            logger.error(f"Error decodificando mensaje: {e}")
                        except Exception as e:
                            logger.error(f"Error procesando mensaje Redis: {e}")
            except Exception as e:
                logger.error(f"❌ Error en listener Redis: {e}")
                self._listening = False
        
        self._listener_thread = threading.Thread(target=listener, daemon=True, name="EventBusListener")
        self._listener_thread.start()
        self._listening = True
        logger.info("🎧 Listener de eventos iniciado")
    
    def _dispatch_to_subscribers(self, event_type: str, event_data: dict):
        """Envía evento a todos los suscriptores registrados"""
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                self._safe_callback(callback, event_data)
    
    def _safe_callback(self, callback: Callable, event_data: dict):
        """Ejecuta callback de forma segura sin propagar excepciones"""
        try:
            callback(event_data)
        except Exception as e:
            logger.error(f"Error en callback: {callback.__name__} - {e}")
    
    def get_stats(self) -> dict:
        """Retorna estadísticas del EventBus"""
        return {
            'enabled': self._enabled,
            'redis_connected': self.redis_client is not None,
            'listening': self._listening,
            'subscribers': {
                event_type: len(callbacks) 
                for event_type, callbacks in self.subscribers.items()
            },
            'total_event_types': len(self.subscribers),
            'total_subscribers': sum(len(c) for c in self.subscribers.values())
        }
    
    def health_check(self) -> dict:
        """Verifica estado de salud del EventBus"""
        status = 'healthy'
        redis_status = 'disconnected'
        
        if self.redis_client:
            try:
                self.redis_client.ping()
                redis_status = 'connected'
            except Exception:
                status = 'degraded'
                redis_status = 'error'
        else:
            status = 'fallback' if self._enabled else 'disabled'
        
        return {
            'status': status,
            'redis': redis_status,
            'listening': self._listening,
            'timestamp': timezone.now().isoformat()
        }


# Singleton global para fácil acceso
event_bus = EventBus()
