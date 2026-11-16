"""EcoTech Solutions ES3: APIs, autenticación, validación y persistencia.
Python 3.10+. Solo biblioteca estándar. APIs: Open-Meteo y Frankfurter.
"""
import getpass, hashlib, hmac, json, logging, os, re, secrets, sqlite3, sys, time, unicodedata
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from logging.handlers import RotatingFileHandler
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parent
DB = BASE / "ecotech.db"
LOG = BASE / "ecotech.log"
TIMEOUT, MAX_BYTES, ITERATIONS = 10, 1_000_000, 310_000
MONEDAS = {"CLP", "USD", "EUR", "ARS", "BRL", "PEN", "COP", "MXN", "GBP", "JPY"}

logger = logging.getLogger("ecotech")
logger.setLevel(logging.INFO)
if not logger.handlers:
    h = RotatingFileHandler(LOG, maxBytes=200_000, backupCount=2, encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(h)

class ErrorAplicacion(Exception):
    pass

def ahora():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def db():
    c = sqlite3.connect(DB, timeout=5)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c

def iniciar_db():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS usuarios(
            id INTEGER PRIMARY KEY, usuario TEXT UNIQUE NOT NULL,
            salt BLOB NOT NULL, hash BLOB NOT NULL, iteraciones INTEGER NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS consultas(
            id INTEGER PRIMARY KEY, usuario_id INTEGER NOT NULL, tipo TEXT NOT NULL,
            entrada TEXT NOT NULL, resultado TEXT NOT NULL, fecha TEXT NOT NULL,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id))""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_consultas_usuario ON consultas(usuario_id)")
    try: os.chmod(DB, 0o600)
    except OSError: pass

def hash_clave(clave, salt, iteraciones=ITERATIONS):
    return hashlib.pbkdf2_hmac("sha256", clave.encode(), salt, iteraciones)

def validar_usuario(v):
    v = v.strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,30}", v):
        raise ValueError("Usuario: 3-30 caracteres, letras, números, punto, guion o guion bajo.")
    return v

def validar_clave(v):
    if not 12 <= len(v) <= 128 or not any(x.isalpha() for x in v) or not any(x.isdigit() for x in v):
        raise ValueError("La contraseña debe tener 12-128 caracteres e incluir letras y números.")
    return v

def registrar():
    print("\\n--- Registro ---")
    while True:
        try:
            usuario = validar_usuario(input("Usuario nuevo: "))
            clave = validar_clave(getpass.getpass("Contraseña nueva: "))
            if not hmac.compare_digest(clave, getpass.getpass("Repita contraseña: ")):
                print("Las contraseñas no coinciden."); continue
            salt = secrets.token_bytes(16)
            with db() as c:
                c.execute("INSERT INTO usuarios(usuario,salt,hash,iteraciones) VALUES(?,?,?,?)",
                          (usuario, salt, hash_clave(clave, salt), ITERATIONS))
            print("Cuenta creada. La contraseña no se almacena en texto plano.")
            logger.info("Cuenta local creada.")
            return
        except ValueError as e: print("Entrada inválida:", e)
        except sqlite3.IntegrityError: print("El usuario ya existe.")
        except sqlite3.Error:
            logger.exception("Fallo de base de datos al registrar")
            raise ErrorAplicacion("No fue posible crear la cuenta.")

def login():
    with db() as c: total = c.execute("SELECT COUNT(*) n FROM usuarios").fetchone()["n"]
    if not total: registrar()
    for intento in range(3):
        u, p = input("\\nUsuario: ").strip(), getpass.getpass("Contraseña: ")
        try:
            with db() as c: row = c.execute("SELECT * FROM usuarios WHERE usuario=?", (u,)).fetchone()
            salt = row["salt"] if row else b"0"*16
            esperado = row["hash"] if row else b"0"*32
            n = row["iteraciones"] if row else ITERATIONS
            ok = hmac.compare_digest(hash_clave(p, salt, n), esperado) and row is not None
            if ok:
                print("Acceso autorizado."); logger.info("Login exitoso.")
                return row["id"]
        except sqlite3.Error:
            logger.exception("Error durante login")
            print("No se pudo validar el acceso por un problema local."); return None
        logger.warning("Intento de login fallido.")
        print("Credenciales incorrectas. Intentos restantes:", 2-intento) if intento < 2 else None
    print("Acceso denegado."); return None

def validar_ciudad(v):
    v = unicodedata.normalize("NFC", v).strip()
    if not v or len(v) > 80 or not re.fullmatch(r"[\wÀ-ÿ][\wÀ-ÿ .'-]{0,78}[\wÀ-ÿ.]?", v, re.UNICODE):
        raise ValueError("Ciudad inválida. Use letras, espacios, punto, guion o apóstrofo (máximo 80).")
    return v

def validar_moneda(v):
    v = v.strip().upper()
    if v not in MONEDAS: raise ValueError("Moneda no habilitada. Ejemplos: CLP, USD, EUR, ARS.")
    return v

def validar_monto(v):
    try: n = Decimal(v.strip())
    except (InvalidOperation, AttributeError): raise ValueError("Monto numérico inválido.")
    if not n.is_finite() or n <= 0 or n > Decimal("1000000000000"):
        raise ValueError("El monto debe ser positivo y no superar 1.000.000.000.000.")
    return n

def get_json(url):
    if not url.startswith("https://"): raise ErrorAplicacion("Solicitud bloqueada: se requiere HTTPS.")
    req = Request(url, headers={"Accept":"application/json", "User-Agent":"EcoTech-ES3/1.0"})
    ultimo = None
    for intento in range(2):
        try:
            with urlopen(req, timeout=TIMEOUT) as r:
                if r.status != 200: raise ErrorAplicacion(f"Respuesta HTTP inesperada: {r.status}.")
                raw = r.read(MAX_BYTES+1)
                if len(raw) > MAX_BYTES: raise ErrorAplicacion("Respuesta demasiado grande.")
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict): raise ErrorAplicacion("Estructura JSON inválida.")
            return data
        except HTTPError as e:
            logger.warning("HTTP error %s", e.code)
            if e.code == 404: raise ErrorAplicacion("Recurso no encontrado (HTTP 404).")
            if e.code == 429: raise ErrorAplicacion("Demasiadas consultas (HTTP 429). Intente más tarde.")
            if 500 <= e.code <= 599 and intento == 0: ultimo=e; time.sleep(.5); continue
            raise ErrorAplicacion(f"El servicio respondió con error HTTP {e.code}.")
        except (URLError, TimeoutError, OSError) as e:
            ultimo=e; logger.warning("Fallo de red o timeout.")
            if intento == 0: time.sleep(.5); continue
            break
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ErrorAplicacion("El servicio devolvió JSON inválido.")
    raise ErrorAplicacion("No fue posible conectar con el servicio. Revise la red e intente nuevamente.") from ultimo

def guardar(uid, tipo, entrada, resultado):
    with db() as c:
        c.execute("INSERT INTO consultas(usuario_id,tipo,entrada,resultado,fecha) VALUES(?,?,?,?,?)",
                  (uid,tipo,entrada,json.dumps(resultado,ensure_ascii=False),ahora()))

def geocodificar(ciudad):
    d=get_json("https://geocoding-api.open-meteo.com/v1/search?"+urlencode(
        {"name":ciudad,"count":1,"language":"es","format":"json"}))
    rs=d.get("results")
    if not isinstance(rs,list) or not rs or not isinstance(rs[0],dict):
        raise ErrorAplicacion("No se encontró la ciudad.")
    loc=rs[0]; lat,lon=loc.get("latitude"),loc.get("longitude")
    if not isinstance(lat,(int,float)) or not isinstance(lon,(int,float)) or not -90<=lat<=90 or not -180<=lon<=180:
        raise ErrorAplicacion("La API no entregó coordenadas válidas.")
    return loc

def clima(uid):
    city=validar_ciudad(input("Ciudad: "))
    loc=geocodificar(city)
    q=urlencode({"latitude":loc["latitude"],"longitude":loc["longitude"],
       "current":"temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m","timezone":"auto"})
    d=get_json("https://api.open-meteo.com/v1/forecast?"+q)
    a=d.get("current")
    if not isinstance(a,dict) or any(k not in a for k in ("temperature_2m","relative_humidity_2m","weather_code")):
        raise ErrorAplicacion("Respuesta meteorológica incompleta.")
    cod=int(a["weather_code"])
    condiciones={0:"Despejado",1:"Principalmente despejado",2:"Parcialmente nublado",3:"Nublado",
      45:"Niebla",48:"Niebla con escarcha",51:"Llovizna ligera",53:"Llovizna moderada",
      55:"Llovizna intensa",61:"Lluvia ligera",63:"Lluvia moderada",65:"Lluvia intensa",
      71:"Nevada ligera",73:"Nevada moderada",75:"Nevada intensa",80:"Chubascos ligeros",
      81:"Chubascos moderados",82:"Chubascos intensos",95:"Tormenta",96:"Tormenta con granizo",99:"Tormenta intensa"}
    out={"ciudad":loc.get("name",city),"pais":loc.get("country","N/D"),"fecha":a.get("time"),
      "temperatura_c":a["temperature_2m"],"humedad_pct":a["relative_humidity_2m"],
      "sensacion_c":a.get("apparent_temperature"),"precipitacion_mm":a.get("precipitation"),
      "viento_kmh":a.get("wind_speed_10m"),"condicion":condiciones.get(cod,f"Código {cod}")}
    guardar(uid,"clima",city,out)
    print("\\n",out["ciudad"],out["pais"],"|",out["fecha"])
    for k,v in out.items():
        if k not in ("ciudad","pais","fecha"): print(f"{k}: {v}")
    print("Consulta guardada localmente.")

def cambio(uid):
    print("Monedas habilitadas:",", ".join(sorted(MONEDAS)))
    src=validar_moneda(input("Moneda origen: "))
    dst=validar_moneda(input("Moneda destino: "))
    amount=validar_monto(input("Monto: "))
    if src==dst: rate=Decimal("1"); date=ahora()
    else:
        d=get_json("https://api.frankfurter.app/latest?"+urlencode({"from":src,"to":dst}))
        rates=d.get("rates")
        if not isinstance(rates,dict) or dst not in rates: raise ErrorAplicacion("No se recibió la tasa solicitada.")
        try: rate=Decimal(str(rates[dst]))
        except InvalidOperation: raise ErrorAplicacion("Tasa de cambio inválida.")
        date=d.get("date","N/D")
    if not rate.is_finite() or rate<=0: raise ErrorAplicacion("Tasa de cambio fuera de rango.")
    out={"origen":src,"destino":dst,"monto":str(amount),"tasa":str(rate),
         "resultado":str((amount*rate).quantize(Decimal("0.01"))),"fecha_tasa":date}
    guardar(uid,"cambio",f"{amount} {src} a {dst}",out)
    print(f"\\n{amount} {src} = {out['resultado']} {dst} | tasa {rate} | fecha {date}")
    print("Consulta guardada localmente.")

def historial(uid):
    with db() as c:
        rows=c.execute("SELECT tipo,entrada,resultado,fecha FROM consultas WHERE usuario_id=? ORDER BY id DESC LIMIT 10",(uid,)).fetchall()
    if not rows: print("No hay consultas guardadas."); return
    for r in rows:
        data=json.loads(r["resultado"])
        resumen=(f"{data.get('temperatura_c')} °C, {data.get('condicion')}" if r["tipo"]=="clima"
                 else f"{data.get('resultado')} {data.get('destino')}")
        print(f"{r['fecha']} | {r['tipo']} | {r['entrada']} | {resumen}")

def menu(uid):
    while True:
        print("\\n=== ECOTECH SOLUTIONS ===\\n1. Clima\\n2. Tipo de cambio\\n3. Historial\\n4. Cerrar sesión")
        op=input("Opción: ").strip()
        try:
            if op=="1": clima(uid)
            elif op=="2": cambio(uid)
            elif op=="3": historial(uid)
            elif op=="4": print("Sesión cerrada."); return
            else: print("Seleccione una opción del 1 al 4.")
        except ValueError as e: print("Entrada no válida:",e); logger.info("Entrada inválida.")
        except ErrorAplicacion as e: print("Consulta no completada:",e); logger.warning("Fallo de servicio controlado.")
        except sqlite3.Error: print("Problema de almacenamiento local; puede continuar."); logger.exception("Error SQLite.")
        except KeyboardInterrupt: print("\\nOperación cancelada."); return
        except Exception: print("Error inesperado. No se muestran detalles internos."); logger.exception("Error inesperado.")

def main():
    print("ECOTECH SOLUTIONS | ES3 - APIs seguras")
    try:
        iniciar_db()
        uid=login()
        if uid is None: sys.exit(1)
        menu(uid)
    except sqlite3.Error:
        logger.exception("No se pudo iniciar SQLite.")
        print("No fue posible iniciar el almacenamiento local."); sys.exit(1)
    except KeyboardInterrupt: print("\\nPrograma finalizado.")
    finally: logging.shutdown()

if __name__=="__main__": main()
