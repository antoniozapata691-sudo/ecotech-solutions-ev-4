import unittest
from decimal import Decimal
from ecotech_es3 import validar_usuario, validar_clave, validar_ciudad, validar_moneda, validar_monto, hash_clave

class Validaciones(unittest.TestCase):
    def test_usuario(self): self.assertEqual(validar_usuario("ana_123"), "ana_123")
    def test_usuario_invalido(self):
        with self.assertRaises(ValueError): validar_usuario("a")
    def test_clave(self): self.assertEqual(validar_clave("ClaveSegura123"), "ClaveSegura123")
    def test_clave_debil(self):
        with self.assertRaises(ValueError): validar_clave("12345")
    def test_ciudad(self): self.assertEqual(validar_ciudad("Concepción"), "Concepción")
    def test_ciudad_maliciosa(self):
        with self.assertRaises(ValueError): validar_ciudad("Santiago<script>")
    def test_moneda(self): self.assertEqual(validar_moneda("clp"), "CLP")
    def test_moneda_invalida(self):
        with self.assertRaises(ValueError): validar_moneda("XXX")
    def test_monto(self): self.assertEqual(validar_monto("10.50"), Decimal("10.50"))
    def test_monto_negativo(self):
        with self.assertRaises(ValueError): validar_monto("-1")
    def test_sal(self):
        self.assertNotEqual(hash_clave("ClaveSegura123",b"sal-uno-12345678"),
                            hash_clave("ClaveSegura123",b"sal-dos-1234567"))
if __name__=="__main__": unittest.main(verbosity=2)
