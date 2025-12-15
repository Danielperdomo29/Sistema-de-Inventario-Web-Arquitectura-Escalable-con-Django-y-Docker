# Sistema de Inventario Web - Arquitectura Escalable con Django y Docker

Este proyecto corresponde a un Sistema de Inventario Web desarrollado con Python y Django, orientado a la gestión integral de productos, movimientos de inventario, ventas, compras, clientes y proveedores. La solución está diseñada bajo principios de arquitectura limpia, desacoplamiento y escalabilidad, utilizando Docker y Docker Compose para garantizar portabilidad y reproducibilidad del entorno en cualquier equipo de desarrollo.

El sistema implementa una arquitectura MVC (Model–View–Controller) apoyada en el ORM de Django, lo que permite una interacción segura y consistente con la base de datos MySQL, evitando el uso de consultas SQL frágiles y facilitando la evolución del modelo de datos a largo plazo. La autenticación y autorización se basan en un modelo de usuario extendido, permitiendo la gestión de roles y permisos de forma flexible y profesional.

## Funcionalidades Principales

La aplicación permite administrar el ciclo completo del inventario:

*   **Dashboard:** Panel principal con estadísticas generales y visualización resumida de todos los módulos del sistema.
*   **Productos:** Gestión completa de productos con código, nombre, descripción, categoría, precios de compra/venta y control de stock.
*   **Categorías:** Organización de productos por categorías personalizables para mejor clasificación.
*   **Clientes:** Administración de clientes con datos de contacto, historial de compras y seguimiento de transacciones.
*   **Proveedores:** Gestión de proveedores con información de contacto y registro de compras realizadas.
*   **Almacenes:** Control de múltiples almacenes con capacidad, ubicación y productos asignados.
*   **Movimientos Inventario:** Registro detallado de entradas y salidas de productos con trazabilidad completa.
*   **Roles:** Sistema de permisos y roles personalizables para control de acceso granular.
*   **Ventas:** Registro de ventas con cliente, productos vendidos, cantidades, precios y métodos de pago.
*   **Detalle Ventas:** Desglose completo de cada venta con productos, cantidades, subtotales e IVA.
*   **Compras:** Gestión de compras a proveedores con productos, cantidades y costos.
*   **Detalle Compras:** Desglose detallado de cada compra realizada con precios y totales.
*   **Reportes:** Generación de reportes de ventas, compras, inventario y análisis financiero.
*   **Configuración:** Gestión de usuarios del sistema, perfiles, contraseñas y parámetros generales.
*   **Documentación:** Página completa con guía de funcionalidades, tecnologías usadas, arquitectura y usuarios de prueba.

Además, incluye un panel administrativo centralizado que facilita la supervisión operativa del sistema.

## Infraestructura y Tecnologías

El proyecto se ejecuta sobre contenedores Docker independientes para:
-   **Django:** Backend de la aplicación.
-   **MySQL 8.0:** Base de datos relacional.
-   **phpMyAdmin:** Interfaz web para administración de base de datos.

Esto garantiza aislamiento, facilidad de despliegue y consistencia entre entornos de desarrollo. El uso de variables de entorno estandarizadas permite una configuración clara y segura, alineada con buenas prácticas profesionales y preparada para futuros entornos de staging o producción.

### Asistente IA (Google Gemini)

Como componente adicional, el sistema incorpora un asistente inteligente basado en IA (**Google Gemini**) que permite realizar consultas en lenguaje natural relacionadas con productos, inventario y estadísticas básicas, mejorando la experiencia del usuario y demostrando la integración de tecnologías modernas de inteligencia artificial en aplicaciones empresariales.


---
Este proyecto representa una solución robusta y extensible, ideal como base para sistemas empresariales reales, demostrando competencias en desarrollo backend, contenedorización, diseño de bases de datos, automatización de despliegue y buenas prácticas de ingeniería de software.
