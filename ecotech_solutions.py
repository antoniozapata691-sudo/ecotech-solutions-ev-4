"""
EcoTech Solutions - Consulta del clima con autenticación segura
Evaluación Formativa - Unidad 3

Instalación:
    pip install -r requirements.txt

Ejecución:
    python ecotech_solutions.py

En el primer inicio se crea un usuario. En los siguientes inicios se solicita
iniciar sesión. La información de acceso se cifra con Fernet y la contraseña
se almacena como hash PBKDF2-HMAC-SHA256 (no como texto legible).
"""

import json
import os
import re
import secrets
import hashlib
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


ARCHIVO_CLAVE = Path("clave_ecotech.key")
ARCHIVO_USUARIO = Path("usuario_ecotech.dat")
ITERACIONES = 600_000


def obtener_cifrador():
    """Carga o crea la clave utilizada para cifrar el archivo de usuario."""
    if not ARCHIVO_CLAVE.exists():
        clave = Fernet.generate_key()
        ARCHIVO_CLAVE.write_bytes(clave)
        try:
            os.chmod(ARCHIVO_CLAVE, 0o600)
        except OSError:
            pass
    else:
        clave = ARCHIVO_CLAVE.read_bytes()

    return Fernet(clave)


def guardar_usuario(cifrador, nombre_usuario, contrasena):
    """Guarda los datos de acceso cifrados y la contraseña derivada con PBKDF2."""
    sal = secrets.token_bytes(16)
    hash_contrasena = hashlib.pbkdf2_hmac(
        "sha256",
        contrasena.encode("utf-8"),
        sal,
        ITERACIONES
    )

    datos = {
        "usuario": nombre_usuario,
        "sal": sal.hex(),
        "hash": hash_contrasena.hex()
    }

    datos_json = json.dumps(datos).encode("utf-8")
    ARCHIVO_USUARIO.write_bytes(cifrador.encrypt(datos_json))

    try:
        os.chmod(ARCHIVO_USUARIO, 0o600)
    except OSError:
        pass


def cargar_usuario(cifrador):
    """Descifra y devuelve los datos del usuario registrado."""
    contenido_cifrado = ARCHIVO_USUARIO.read_bytes()
    contenido = cifrador.decrypt(contenido_cifrado)
    return json.loads(contenido.decode("utf-8"))


def validar_nombre_usuario(nombre):
    """Acepta letras, números y guion bajo; longitud de 4 a 20 caracteres."""
    return re.fullmatch(r"[A-Za-z0-9_]{4,20}", nombre) is not None


def validar_contrasena(contrasena):
    """Comprueba una longitud mínima y que no esté vacía."""
    return len(contrasena) >= 8 and len(contrasena) <= 128


def registrar_usuario(cifrador):
    print("\n=== Registro inicial de EcoTech Solutions ===")

    while True:
        usuario = input("Crea un nombre de usuario (4 a 20 caracteres): ").strip()
        if validar_nombre_usuario(usuario):
            break
        print("Usuario no válido. Usa letras, números o guion bajo.")

    while True:
        contrasena = input("Crea una contraseña (8 a 128 caracteres): ")
        if not validar_contrasena(contrasena):
            print("La contraseña debe tener entre 8 y 128 caracteres.")
            continue

        confirmacion = input("Confirma la contraseña: ")
        if contrasena != confirmacion:
            print("Las contraseñas no coinciden.")
            continue
        break

    guardar_usuario(cifrador, usuario, contrasena)
    print("Usuario registrado correctamente.\n")


def verificar_contrasena(datos, contrasena_ingresada):
    """Compara el hash ingresado con el hash almacenado."""
    sal = bytes.fromhex(datos["sal"])
    hash_guardado = bytes.fromhex(datos["hash"])
    hash_ingresado = hashlib.pbkdf2_hmac(
        "sha256",
        contrasena_ingresada.encode("utf-8"),
        sal,
        ITERACIONES
    )
    return secrets.compare_digest(hash_guardado, hash_ingresado)


def iniciar_sesion(cifrador):
    print("=== Inicio de sesión ===")

    try:
        datos = cargar_usuario(cifrador)
    except (OSError, InvalidToken, json.JSONDecodeError, KeyError, ValueError):
        print("No se pudo leer el registro de usuario. Revisa los archivos de acceso.")
        return False

    for intento in range(1, 4):
        usuario = input("Usuario: ").strip()
        contrasena = input("Contraseña: ")

        if (
            secrets.compare_digest(usuario, datos["usuario"])
            and verificar_contrasena(datos, contrasena)
        ):
            print("\nAcceso autorizado. Bienvenido/a a EcoTech Solutions.\n")
            return True

        restantes = 3 - intento
        print("Credenciales incorrectas.")
        if restantes:
            print(f"Intentos restantes: {restantes}")

    print("Acceso bloqueado por superar el máximo de intentos.")
    return False


def validar_ciudad(ciudad):
    """Evita entradas vacías, excesivas o con caracteres inesperados."""
    patron = r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' -]{2,60}"
    return re.fullmatch(patron, ciudad) is not None


def solicitar_json(url):
    """Realiza una solicitud HTTP GET y procesa la respuesta JSON."""
    solicitud = urllib.request.Request(
        url,
        headers={"User-Agent": "EcoTechSolutions/1.0"}
    )

    with urllib.request.urlopen(solicitud, timeout=15) as respuesta:
        if respuesta.status != 200:
            raise RuntimeError(f"El servicio respondió con estado {respuesta.status}.")
        contenido = respuesta.read().decode("utf-8")
        return json.loads(contenido)


def consultar_clima(ciudad):
    """Busca las coordenadas de una ciudad y consulta su clima actual."""
    parametros = urllib.parse.urlencode({
        "name": ciudad,
        "count": 1,
        "language": "es",
        "format": "json"
    })
    url_geocoding = (
        "https://geocoding-api.open-meteo.com/v1/search?" + parametros
    )

    datos_lugar = solicitar_json(url_geocoding)
    resultados = datos_lugar.get("results", [])

    if not resultados:
        print("No se encontró la ciudad. Revisa el nombre e inténtalo nuevamente.")
        return

    lugar = resultados[0]
    latitud = lugar["latitude"]
    longitud = lugar["longitude"]
    nombre = lugar.get("name", ciudad)
    pais = lugar.get("country", "No informado")

    parametros_clima = urllib.parse.urlencode({
        "latitude": latitud,
        "longitude": longitud,
        "current": (
            "temperature_2m,relative_humidity_2m,apparent_temperature,"
            "precipitation,weather_code,wind_speed_10m"
        ),
        "timezone": "auto"
    })
    url_clima = "https://api.open-meteo.com/v1/forecast?" + parametros_clima
    datos_clima = solicitar_json(url_clima)
    actual = datos_clima.get("current")

    if not actual:
        print("La API no entregó información meteorológica actual.")
        return

    print("\n=== Información meteorológica ===")
    print(f"Ciudad: {nombre}, {pais}")
    print(f"Temperatura: {actual.get('temperature_2m', 'N/D')} °C")
    print(f"Sensación térmica: {actual.get('apparent_temperature', 'N/D')} °C")
    print(f"Humedad: {actual.get('relative_humidity_2m', 'N/D')} %")
    print(f"Precipitación: {actual.get('precipitation', 'N/D')} mm")
    print(f"Viento: {actual.get('wind_speed_10m', 'N/D')} km/h")
    print(f"Código del estado del clima: {actual.get('weather_code', 'N/D')}")
    print(f"Hora de actualización: {actual.get('time', 'N/D')}")
    print("=================================\n")


def menu_principal():
    print("======================================")
    print("       ECOTECH SOLUTIONS")
    print("       Consulta del clima")
    print("======================================")

    try:
        cifrador = obtener_cifrador()
    except (OSError, ValueError):
        print("No fue posible preparar el sistema de seguridad.")
        return

    if not ARCHIVO_USUARIO.exists():
        registrar_usuario(cifrador)

    if not iniciar_sesion(cifrador):
        return

    while True:
        print("1. Consultar clima de una ciudad")
        print("2. Cerrar sesión")
        opcion = input("Selecciona una opción: ").strip()

        if opcion == "1":
            ciudad = input("Ingresa el nombre de una ciudad: ").strip()

            if not validar_ciudad(ciudad):
                print("Nombre no válido. Usa entre 2 y 60 letras, espacios o guiones.\n")
                continue

            try:
                consultar_clima(ciudad)
            except urllib.error.HTTPError as error:
                print(f"Error HTTP {error.code}: no se pudo consultar el servicio.")
            except urllib.error.URLError:
                print("Error de conexión. Revisa tu conexión a Internet.")
            except (TimeoutError, json.JSONDecodeError, KeyError, ValueError) as error:
                print(f"No se pudieron procesar los datos recibidos: {error}")
            except Exception as error:
                print(f"Ocurrió un error inesperado: {error}")

        elif opcion == "2":
            print("Sesión cerrada correctamente.")
            break
        else:
            print("Opción no válida. Selecciona 1 o 2.\n")


if __name__ == "__main__":
    menu_principal()
