class Departamento:
    def __init__(self, id_departamento: str, nombre: str, piso: int):
        self.id_departamento = id_departamento
        self.nombre = nombre
        self.piso = piso

    @property
    def id_departamento(self) -> str:
        return self._id_departamento

    @id_departamento.setter
    def id_departamento(self, id_departamento: str) -> None:
        if not isinstance(id_departamento, str) or not id_departamento.strip():
            raise ValueError("El ID del departamento no puede estar vacío.")
        self._id_departamento = id_departamento.strip()

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, nombre: str) -> None:
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("El nombre no puede estar vacío.")
        self._nombre = nombre.strip()

    @property
    def piso(self) -> int:
        return self._piso

    @piso.setter
    def piso(self, piso: int) -> None:
        if not isinstance(piso, int):
            raise ValueError("El piso debe ser un número entero.")
        self._piso = piso

    def __str__(self) -> str:
        return f"Información del departamento:\nID: {self.id_departamento}\nNombre: {self.nombre}\nPiso: {self.piso}"

    def __repr__(self) -> str:
        return f"Departamento(id_departamento='{self.id_departamento}', nombre='{self.nombre}', piso={self.piso})"