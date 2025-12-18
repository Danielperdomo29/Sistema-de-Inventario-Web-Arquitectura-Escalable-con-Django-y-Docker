# Contribuyendo al Sistema de Inventario

¡Gracias por tu interés en contribuir! Este documento proporciona pautas para contribuir al proyecto.

## Código de Conducta

- Sé respetuoso y profesional
- Acepta críticas constructivas
- Enfócate en lo mejor para la comunidad

## Cómo Contribuir

### Reportar Bugs

1. Verifica que el bug no haya sido reportado antes
2. Crea un issue con:
   - Descripción clara del problema
   - Pasos para reproducir
   - Comportamiento esperado vs actual
   - Capturas de pantalla (si aplica)
   - Versión de Python, Django, y sistema operativo

### Sugerir Mejoras

1. Abre un issue describiendo:
   - La mejora propuesta
   - Por qué sería útil
   - Posible implementación

### Pull Requests

1. **Fork el repositorio**
2. **Crea una rama** desde `main`:

   ```bash
   git checkout -b feature/nombre-descriptivo
   ```

3. **Realiza tus cambios**:

   - Sigue el estilo de código existente
   - Agrega docstrings a funciones nuevas
   - Actualiza documentación si es necesario

4. **Prueba tus cambios**:

   ```bash
   python manage.py test
   ```

5. **Commit con mensajes descriptivos**:

   ```bash
   git commit -m "feat: agregar validación de stock en ventas"
   ```

6. **Push a tu fork**:

   ```bash
   git push origin feature/nombre-descriptivo
   ```

7. **Abre un Pull Request** con:
   - Descripción clara de los cambios
   - Referencias a issues relacionados
   - Screenshots (si aplica)

## Estilo de Código

### Python/Django

- Sigue PEP 8
- Usa nombres descriptivos en español para variables de negocio
- Máximo 100 caracteres por línea
- Docstrings en español

### JavaScript

- Usa `const` y `let`, no `var`
- Nombres de variables en camelCase
- Comentarios en español

### CSS

- Usa clases semánticas
- Prefiere flexbox/grid sobre floats
- Mantén consistencia con el tema verde

## Estructura de Commits

Usa conventional commits:

- `feat:` Nueva característica
- `fix:` Corrección de bug
- `docs:` Cambios en documentación
- `style:` Formato, punto y coma faltante, etc
- `refactor:` Refactorización de código
- `test:` Agregar tests
- `chore:` Mantenimiento

Ejemplo:

```
feat: agregar exportación de reportes a Excel

- Implementar servicio de exportación
- Agregar botón en vista de reportes
- Actualizar documentación
```

## Proceso de Revisión

1. Un mantenedor revisará tu PR
2. Puede solicitar cambios
3. Una vez aprobado, se hará merge a `main`

## Preguntas

Si tienes preguntas, abre un issue con la etiqueta `question`.

¡Gracias por contribuir! 🎉
