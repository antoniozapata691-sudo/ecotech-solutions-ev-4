import sqlite3

class BaseDatos:
    def __init__(self, nombre_db="ecotech.db"):
        self.nombre_db = nombre_db
        self.inicializar_base_datos()

    def conectar(self):
        try:
            conexion = sqlite3.connect(self.nombre_db)
            return conexion
        except sqlite3.Error as e:
            print(f"Error al conectar con la base de datos: {e}")
            return None

    def inicializar_base_datos(self):
        conexion = self.conectar()
        if conexion:
            try:
                cursor = conexion.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS empleados (
                        rut TEXT PRIMARY KEY,
                        nombre TEXT NOT NULL,
                        edad INTEGER NOT NULL,
                        cargo TEXT NOT NULL,
                        sueldo REAL NOT NULL
                    )
                """)
                conexion.commit()
            except sqlite3.Error as e:
                print(f"Error al crear la tabla: {e}")
            finally:
                conexion.close()