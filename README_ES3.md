# EcoTech Solutions — Evaluación Sumativa 3 (ES3)

## Ejecución
Requiere Python 3.10+ e Internet. No requiere instalar paquetes externos.
```bash
python ecotech_es3.py
```
En Windows puede usarse `py ecotech_es3.py`. En el primer inicio registra usuario y contraseña. Luego:
1. Consulta clima (ej.: Santiago).
2. Consulta tipo de cambio (ej.: USD a CLP).
3. Revisa historial guardado.
4. Cierra sesión.

## APIs
- Open-Meteo Geocoding: `https://geocoding-api.open-meteo.com/v1/search`
- Open-Meteo Forecast: `https://api.open-meteo.com/v1/forecast`
- Frankfurter: `https://api.frankfurter.app/latest`
Se consulta mediante HTTPS; estas APIs no requieren clave para las funciones del prototipo.

## Persistencia
`ecotech.db` almacena usuarios (sal y hash, nunca contraseña original) y consultas JSON asociadas al usuario. `ecotech.log` guarda eventos técnicos sin registrar contraseñas. SQLite usa consultas parametrizadas.

## Seguridad y continuidad
- PBKDF2-HMAC-SHA256, sal aleatoria de 16 bytes y 310.000 iteraciones.
- Comparación de hash con `hmac.compare_digest`.
- Máximo de tres intentos de acceso por ejecución.
- Validación de usuario, contraseña, ciudad, moneda y monto.
- HTTPS, timeout de 10 segundos, límite de respuesta de 1 MB, validación de JSON y reintento único acotado.
- Manejo diferenciado de HTTP 404, 429, 5xx, conexión, timeout y errores de persistencia.
- Los errores no muestran trazas internas al usuario y el menú continúa tras fallos de consulta.

## Pruebas
```bash
python -m unittest -v
```
Las pruebas unitarias comprueban validaciones de usuario, contraseña, ciudad, moneda, monto y uso de sal en el hash. Son pruebas locales; no requieren Internet.

## Trazabilidad de la rúbrica
| Indicador | Evidencia |
|---|---|
| 3.1.1.1 HTTP | `get_json()` usa `urllib.request.Request` y `urlopen`. |
| 3.1.1.2 JSON | `json.loads()` y validación de tipo y estructura. |
| 3.1.1.3 Extracción | `clima()` selecciona temperatura, humedad, sensación, precipitación, viento y condición; `cambio()` obtiene tasa y fecha. |
| 3.1.1.4 Integración/verificación | Valida coordenadas, campos obligatorios y tasa positiva antes de mostrar y persistir. |
| 3.1.2.5 Autenticación | Registro/login con PBKDF2 y sal aleatoria. |
| 3.1.2.6 Validación | `validar_*` aplica formato, lista permitida y rangos. |
| 3.1.2.7 Protección | No guarda claves en texto plano ni las registra; errores externos no exponen trazas. |
| 3.1.2.8 Restricción | `menu()` solo se ejecuta con ID de usuario autenticado. |
| 3.1.3.9 Excepciones | `try/except` en API, menú, login y SQLite. |
| 3.1.3.10 Red/timeout | Timeout de 10 s y un reintento acotado. |
| 3.1.3.11 HTTP | Manejo específico de 404, 429 y 5xx. |
| 3.1.3.12 Continuidad | Captura fallos por operación y mantiene el menú activo. |
| 3.1.4.13 Evidencia IA | Conservar capturas reales de prompts, revisión y pruebas realizadas. |
| 3.1.4.14 Explicación | Revisar secciones de APIs, persistencia y seguridad de este documento. |
| 3.1.4.15 Riesgos | Análisis crítico más abajo. |
| 3.1.4.16 Refactorización | Decisiones técnicas justificadas más abajo. |

## Evidencia de uso de IA y análisis crítico
**Prompt de apoyo:** “Desarrolla un script Python para EcoTech Solutions que consulte clima y tipo de cambio mediante APIs HTTPS, procese JSON, autentique usuarios, valide entradas, persista consultas localmente y maneje errores HTTP y de conexión. Utiliza bibliotecas estándar y evita guardar contraseñas en texto plano. Explica las decisiones de seguridad”.

**Revisión y ajustes incorporados:** se verificó que las contraseñas no se guardaran en texto plano; se incorporaron sal aleatoria, PBKDF2, comparación constante, validación de entradas, consultas SQL parametrizadas, timeout, límite de respuesta, validación de JSON, reintento acotado y mensajes de error sin trazas internas.

**Riesgos residuales:** el archivo SQLite está en el equipo local y depende de los permisos del sistema operativo; el límite de intentos se reinicia al cerrar la aplicación; no hay gestión avanzada de roles ni bloqueo persistente; las APIs gratuitas pueden tener límites y cambios de disponibilidad. Es un prototipo académico, no un sistema listo para producción.

**Justificación técnica:** `urllib` se eligió por ser parte de la biblioteca estándar; SQLite permite persistencia local sin servidor; PBKDF2 con sal es apropiado para almacenar contraseñas mediante hash no reversible; Open-Meteo y Frankfurter permiten demostrar consumo de servicios sin administrar claves privadas. Las funciones separan validación, solicitud, persistencia y presentación para facilitar pruebas y mantenimiento.

## Demostración sugerida
1. Crear cuenta y probar un inicio de sesión incorrecto.
2. Iniciar sesión correctamente.
3. Consultar el clima de Santiago.
4. Convertir USD a CLP.
5. Mostrar el historial local.
6. Probar una moneda no permitida y un monto negativo.
7. Ejecutar las pruebas unitarias.

## Antes de entregar
Ejecuta el programa y las pruebas en tu equipo; agrega capturas reales de funcionamiento y de la herramienta de IA utilizada. Lee el código para poder explicarlo. La guía solicita comprimir la carpeta con el formato de inicial del nombre + apellido paterno antes de subirla a AAI.
