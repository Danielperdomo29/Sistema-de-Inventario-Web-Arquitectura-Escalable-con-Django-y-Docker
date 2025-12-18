# Sistema de Inventario Web - Arquitectura Escalable con Django y Docker

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Django](https://img.shields.io/badge/Django-5.2-green)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)

Sistema profesional de gestión de inventario desarrollado con Django 5.2, MySQL y Docker. Incluye módulo de facturación electrónica compatible con DIAN (Colombia), chatbot con IA, y arquitectura modular escalable.

## 🚀 Características Principales

### Gestión de Inventario

- ✅ **Productos**: CRUD completo con categorías, proveedores y control de stock
- ✅ **Almacenes**: Gestión multi-almacén con movimientos de inventario
- ✅ **Clientes y Proveedores**: Base de datos completa de contactos
- ✅ **Categorías**: Organización jerárquica de productos

### Ventas y Compras

- ✅ **Ventas**: Registro de ventas con detalles de productos
- ✅ **Compras**: Control de compras y actualización automática de stock
- ✅ **Reportes**: Estadísticas y análisis de ventas

### Facturación Electrónica DIAN

- ✅ **Generación XML UBL 2.1**: Formato estándar DIAN
- ✅ **Generación PDF**: Facturas imprimibles
- ✅ **Numeración Automática**: Sistema de consecutivos
- ✅ **Cálculo de Impuestos**: IVA, INC con soporte para precios con/sin impuestos
- ✅ **Protección de Datos**: Ventas facturadas no se pueden eliminar (solo anular)

### Inteligencia Artificial

- ✅ **Chatbot IA**: Asistente virtual con Google Gemini
- ✅ **Consultas en Lenguaje Natural**: Búsqueda de productos, reportes, estadísticas
- ✅ **Análisis de Inventario**: Alertas de stock bajo, productos más vendidos

### Seguridad y Autenticación

- ✅ **Sistema de Roles**: Control de acceso basado en permisos
- ✅ **Autenticación Segura**: Login con Django Auth
- ✅ **Variables de Entorno**: Configuración segura sin hardcoding
- ✅ **Protección CSRF**: Seguridad en formularios

## 📋 Requisitos Previos

- Python 3.11+
- MySQL 8.0+ (o Docker)
- Docker y Docker Compose (opcional, para desarrollo con contenedores)
- Git

## 🛠️ Instalación

### Opción 1: Desarrollo Local (Windows + venv)

1. **Clonar el repositorio**

```bash
git clone https://github.com/tu-usuario/Sistema-de-Inventario-Web-Arquitectura-Escalable-con-Django-y-Docker.git
cd Sistema-de-Inventario-Web-Arquitectura-Escalable-con-Django-y-Docker
```

2. **Crear entorno virtual**

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**

```bash
copy .env.example .env
# Editar .env con tus credenciales
```

5. **Iniciar MySQL en Docker** (si no tienes MySQL local)

```bash
docker-compose -f .docker/docker-compose.yml up -d mysql
```

6. **Aplicar migraciones**

```bash
python manage.py migrate
```

7. **Crear superusuario**

```bash
python manage.py createsuperuser
```

8. **Iniciar servidor**

```bash
python manage.py runserver
```

Accede a: `http://127.0.0.1:8000/`

### Opción 2: Docker (Full Stack)

1. **Configurar variables de entorno**

```bash
copy .env.example .env
# Asegúrate de configurar DB_HOST=mysql en .env
```

2. **Levantar todos los servicios**

```bash
docker-compose -f .docker/docker-compose.yml up -d
```

3. **Aplicar migraciones**

```bash
docker exec server_docker_python_project python manage.py migrate
```

4. **Crear superusuario**

```bash
docker exec -it server_docker_python_project python manage.py createsuperuser
```

Accede a: `http://localhost:8000/`

## ⚙️ Configuración

### Variables de Entorno (.env)

```ini
# Base de Datos
DB_HOST=127.0.0.1          # Para local, usa 'mysql' para Docker
DB_PORT=3306
DB_NAME=tu_base_datos
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña

# API Keys
GEMINI_API_KEY=tu_api_key_de_google_gemini
```

### Configuración de DIAN

Para usar el módulo de facturación electrónica:

1. Los productos deben tener configurados:

   - `tax_type_id`: Código de impuesto DIAN (01=IVA, 04=INC)
   - `tax_percentage`: Porcentaje de impuesto
   - `is_tax_included`: Si el precio incluye impuesto

2. Las facturas se generan en: `media/dian/xml/` y `media/dian/pdf/`

## 📁 Estructura del Proyecto

```
├── app/                    # Aplicación principal
│   ├── controllers/        # Controladores (lógica de negocio)
│   ├── models/            # Modelos de datos
│   ├── views/             # Vistas (presentación)
│   ├── services/          # Servicios (IA, utilidades)
│   └── static/            # Archivos estáticos (CSS, JS)
├── facturacion/           # Módulo de facturación DIAN
│   ├── models.py          # Modelo FacturaDIAN
│   ├── services/          # Generadores XML/PDF, numeración
│   └── views.py           # Vista de generación
├── config/                # Configuración Django
│   ├── settings.py        # Settings principal
│   ├── urls.py            # URLs principales
│   └── database.py        # Wrapper de conexión DB
├── media/                 # Archivos generados (PDFs, XMLs)
├── .docker/               # Configuración Docker
└── requirements.txt       # Dependencias Python
```

## 🎨 Tema Visual

El sistema utiliza una paleta de colores verde profesional:

- Verde Principal: `#72c071`
- Verde Claro: `#8bd089`
- Verde Suave: `#a5e0a2`
- Verde Pastel: `#beefba`
- Fondo: `#d7ffd2`

## 🔒 Seguridad

- ✅ Contraseñas hasheadas con Django Auth
- ✅ Protección CSRF en todos los formularios
- ✅ Variables de entorno para credenciales
- ✅ `.gitignore` configurado para excluir datos sensibles
- ✅ Validación de permisos por rol
- ✅ Sin credenciales hardcodeadas en el código

## 📚 Documentación Adicional

- [Modos de Ejecución](docs/execution_modes.md) - Configuración local vs Docker
- [Facturación DIAN](docs/technical_docs_dian.md) - Documentación técnica del módulo
- [Limpieza del Código](docs/cleanup_summary.md) - Optimizaciones aplicadas

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 👨‍💻 Autor

**Daniel Enrique Perdomo Carvajal**

## 🙏 Agradecimientos

- Django Framework
- Google Gemini AI
- Comunidad Open Source

---

⭐ Si este proyecto te fue útil, considera darle una estrella en GitHub!
