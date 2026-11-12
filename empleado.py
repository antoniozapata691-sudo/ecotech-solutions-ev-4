class Empleado:
    
    CARGOS_VALIDOS: set[str] = {"Desarrollador", "Analista", "Jefe de Proyecto", "soporte", "Otro"}

    def __init__(self, rut: str, nombre: str, edad: int, cargo: str, sueldo: float):
        self.rut = rut
        self.nombre = nombre
        self.edad = edad
        self.cargo = cargo
        self.sueldo = sueldo

    @property
    def rut(self) -> str:
        return self._rut

    @rut.setter
    def rut(self, rut: str) -> None:
        if not rut.strip():
            raise ValueError("El RUT no puede estar vacío.")
        self._rut = rut

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, nombre: str) -> None:
        if not nombre.strip():
            raise ValueError("El nombre no puede estar vacío.")
        self._nombre = nombre

    @property
    def edad(self) -> int:
        return self._edad

    @edad.setter
    def edad(self, edad: int) -> None:
        if edad < 18:
            raise ValueError("El empleado debe ser mayor de edad (>= 18).")
        self._edad = edad

    @property
    def cargo(self) -> str:
        return self._cargo

    @cargo.setter
    def cargo(self, cargo: str) -> None:
        self._cargo = cargo

    @property
    def sueldo(self) -> float:
        return self._sueldo

    @sueldo.setter
    def sueldo(self, sueldo: float) -> None:
        if sueldo < 0:
            raise ValueError("El sueldo no puede ser negativo.")
        self._sueldo = sueldo

    def __str__(self) -> str:
        return (f"Información del Empleado:\n"
                f"RUT: {self.rut}\n"
                f"Nombre: {self.nombre}\n"
                f"Edad: {self.edad}\n"
                f"Cargo: {self.cargo}\n"
                f"Sueldo: ${self.sueldo:,.0f}")

    def __repr__(self) -> str:
        return f"Empleado(rut='{self.rut}', nombre='{self.nombre}', edad={self.edad}, cargo='{self.cargo}', sueldo={self.sueldo})"