# CMS Ecommerce (MVC + PHP + jQuery)

**CMS Ecommerce** es un sistema de gestión de contenidos especializado en comercio electrónico, desarrollado con **PHP** bajo el patrón **MVC** y potenciado con **jQuery** para interactividad del lado del cliente. Permite administrar productos, categorías, inventario, pedidos, usuarios y contenido web desde un panel intuitivo, mientras jQuery mejora la experiencia del usuario con animaciones, validaciones y actualizaciones dinámicas mediante AJAX.

## Demo del Proyecto

[https://ecommerce.com/](https://ecommerce.pablogarciajc.com/)

| ![Imagen 1](https://pablogarciajc.com/wp-content/uploads/2025/09/ecommerce_11_11.webp) | ![Imagen 2](https://pablogarciajc.com/wp-content/uploads/2025/01/ecommerce_6_webp.png) |
|-----------|-----------|

## Funcionalidades Principales

La plataforma cuenta con **cuatro módulos principales** que optimizan la experiencia de usuario y administración:

- **Diseño Adaptado a Móviles**: Experiencia optimizada para dispositivos móviles
- **Multilenguaje**: Soporte para múltiples idiomas.
- **Dashboard**: Visualiza métricas clave.
- **Registro y Login**: Gestión de cuentas de usuario.
- **Cuenta**: Administración de perfil y contraseñas.
- **Usuarios**: Gestión de usuarios y roles.
- **Roles**: Asigna permisos específicos a los usuarios.
- **Catálogo**: Administración de productos y servicios.
- **Pedidos**: Consulta y gestión de pedidos.
- **Carrito de Compras**: Gestión de productos en el carrito.
- **Favoritos**: Guarda productos o recursos favoritos para acceso rápido.
- **Comentarios**: Deja tus comentarios sobre la plataforma.
- **Conoce la Plataforma**: Acceso a documentación técnica.
- **Cerrar Sesión**: Logout seguro.

### Roles de Usuario Iniciales

El sistema está diseñado inicialmente con **dos roles**:

1. **Administrador**: Tiene acceso completo a todas las funcionalidades y módulos de la plataforma. El administrador puede gestionar usuarios, roles, productos, pedidos, entre otros.
2. **Cliente**: Accede principalmente a funcionalidades relacionadas con la compra de productos, visualización de su cuenta, carrito de compras, y favoritos.

## Tecnologías Usadas

| **Tecnología**             | **Descripción**                                                                                                                                                   |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **PHP y SQL**              | Lenguaje de programación para backend y bases de datos.                                                                                                           |
| **Logging**                | Herramienta para registrar eventos, errores y el estado del sistema en tiempo real.                                                                               |
| **Testing Unitario**       | Verifica que unidades individuales de código funcionen correctamente y de forma aislada.                                                                          |
| **Testing de Integración** | Asegura que los distintos módulos o servicios del sistema interactúan correctamente entre sí.                                                                    |
| **Composer**               | Gestor de dependencias en PHP.                                                                                                                                    |
| **Docker (con WSL)**       | Plataforma para contenerización y escalabilidad, con soporte para entornos Linux en Windows mediante WSL2.                                                       |
| **Docker Compose**         | Herramienta para definir y ejecutar aplicaciones multi-contenedor, facilitando la gestión de entornos complejos.                                                 |
| **Make**                   | Automatiza tareas repetitivas como pruebas, despliegues y gestión de contenedores, optimizando el flujo de trabajo.                                              |

---

## Créditos

| **Recurso**                        | **Descripción**                                                                                               | **Enlace**                                              |
|------------------------------------|---------------------------------------------------------------------------------------------------------------|---------------------------------------------------------|
| **Plantilla de la aplicación**     | Plantilla utilizada para la interfaz de usuario.                                                              | [Electro Store - Plantilla de eCommerce](https://w3layouts.com/template/electro-store-an-ecommerce-theme-bootstrap-template/)                        |
| **Licencia de la plantilla**       | Licencia de la plantilla bajo Creative Commons Attribution 3.0 Unported.                                      | [Creative Commons License](http://creativecommons.org/licenses/by/3.0/) |
| **Imágenes de productos**          | Imágenes de productos obtenidas de Amazon.                                                                     | [Amazon](https://www.amazon.com)                         |
---

## Usuarios Ficticios para Pruebas

| **Nombre**                     | **Correo**                        | **Contraseña** | **Rol**         |
|---------------------------------|-----------------------------------|----------------|-----------------|
| Administrador                   | admin@cms.com                     | password       | Administrador   |
| Luis Fernando Ramos             | luis.ramos@pablogarciajc.com       | password       | Cliente         |
| Marco Antonio Santis            | santis@pablogarciajc.com          | password       | Cliente         |
| Juan Carlos Pérez               | juan.perez@pablogarciajc.com      | password       | Cliente         |
| Ana María López                 | ana.lopez@pablogarciajc.com       | password       | Cliente         |
| Carlos Alberto Rodríguez        | carlos.rodriguez@pablogarciajc.com| password       | Cliente         |
| Lucía Fernanda Mendoza          | lucia.mendoza@pablogarciajc.com   | password       | Cliente         |
| Pedro Luis Gómez                | pedro.gomez@pablogarciajc.com     | password       | Cliente         |
| Sofía Alejandra Martínez        | sofia.martinez@pablogarciajc.com  | password       | Cliente         |
| Diego Armando Herrera           | diego.herrera@pablogarciajc.com   | password       | Cliente         |
| María Isabel González           | maria.gonzalez@pablogarciajc.com  | password       | Cliente         |
| Javier Ernesto Ortiz            | javier.ortiz@pablogarciajc.com    | password       | Cliente         |
| Laura Patricia Vega             | laura.vega@pablogarciajc.com      | password       | Cliente         |

---

## Instalación

### Requisitos Previos

- Tener **Docker** y **Docker Compose** instalados.
- **Make**: Utilizado para automatizar procesos y gestionar contenedores de manera más eficiente.

### Pasos de Instalación

1. Clona el repositorio desde GitHub.
2. Dentro del repositorio, encontrarás un archivo **Makefile** que contiene los comandos necesarios para iniciar y gestionar tu aplicación.
3. Usa los siguientes comandos de **Make** para interactuar con la aplicación:

   - **`make init-app`**: Inicializa los contenedores y configura la aplicación.
   - **`make up`**: Levanta la aplicación y sus contenedores asociados.
   - **`make down`**: Detiene los contenedores y apaga la aplicación.
   - **`make shell`**: Ingresa al contenedor para interactuar directamente con el sistema en su entorno de ejecución.
   - **`make install-dependencies`**: Instala todas las dependencias necesarias para disponer del sistema de logs y ejecutar pruebas.
   - **`make init-test`**: Ejecuta las pruebas unitarias y de integración.

4. Además de estos comandos, dentro del archivo **Makefile** puedes encontrar otros comandos que te permitirán interactuar de manera más específica con los contenedores y los diferentes servicios que conforman la aplicación.

5. Accede a los siguientes URL:
   - **Aplicación Web**: [http://localhost:8081/](http://localhost:8081/)
   - **PhpMyAdmin**: [http://localhost:8082/](http://localhost:8082/)

---

## Contáctame / Sígueme en mis redes sociales

| Red Social   | Descripción                                              | Enlace                   |
|--------------|----------------------------------------------------------|--------------------------|
| **Facebook** | Conéctate y mantente al tanto de mis actualizaciones.    | [Presiona aquí](https://www.facebook.com/PabloGarciaJC) |
| **YouTube**  | Fundamentos de la programación, tutoriales y noticias.   | [Presiona aquí](https://www.youtube.com/@pablogarciajc)     |
| **Página Web** | Más información sobre mis proyectos y servicios.        | [Presiona aquí](https://pablogarciajc.com/)              |
| **LinkedIn** | Sigue mi carrera profesional y establece conexiones.     | [Presiona aquí](https://www.linkedin.com/in/pablogarciajc) |
| **Instagram**| Fotos, proyectos y contenido relacionado.                 | [Presiona aquí](https://www.instagram.com/pablogarciajc) |
| **Twitter**  | Proyectos, pensamientos y actualizaciones.                | [Presiona aquí](https://x.com/PabloGarciaJC?t=lct1gxvE8DkqAr8dgxrHIw&s=09)   |

---
> _"El buen manejo de tus finanzas hoy construye la seguridad del mañana."_
