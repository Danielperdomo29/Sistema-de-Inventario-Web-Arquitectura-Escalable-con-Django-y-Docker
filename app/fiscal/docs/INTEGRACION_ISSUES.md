# Resumen de problemas y solución

## Problemas identificados

1. **Modelo Sale sin impuestos**: Sale actual no tiene campos de IVA/impuestos separados
2. **SaleDetail simple**: Solo tiene cantidad, precio_unitario, subtotal (sin tasa de IVA)
3. **Servicio de facturación complejo**: El InvoiceService espera estructura con impuestos detallados
4. **Mapeo UBL incompatible**: UBLMapper busca campos que no existen en Sale

## Solución propuesta

### Opción 1: Adaptar el servicio existente (RECOMENDADA)

Hacer que el servicio de facturación funcione con la estructura simple actual:

- Asumir IVA del 19% en todos los productos (configurable)
- Calcular impuestos desde el total
- Generar XML válido con los datos disponibles

### Opción 2: Extender modelos (más trabajo)

Agregar campos de impuestos a Sale y SaleDetail:

- `subtotal_sin_iva`
- `iva_valor`
- `iva_tasa`
- Requiere migración y cambios en formularios

## Próximos pasos

1. Implementar adaptador simple para Sale → UBL
2. Configurar tasa de IVA por defecto
3. Generar facturas con datos básicos
4. Más adelante: extender modelos si se necesita mayor granularidad

¿Prefieres la opción 1 (rápido, funciona ya) o la opción 2 (completa, requiere más cambios)?
