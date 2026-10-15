from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
import random


class TestTechstore(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cliente = cls.env['techstore.cliente'].create({
            'name': 'Cliente de prueba',
            'cedula': 'TEST-CLIENTE-001',
            'email': 'cliente.prueba@example.com',
        })
        cls.producto = cls.env['techstore.producto'].create({
            'name': 'Producto de prueba',
            'codigo': 'TEST-PRODUCTO-001',
            'precio_unitario': 100,
            'stock_disponible': 10,
        })

    def _venta_values(self, name, cantidad=2, descuento=5):
        return {
            'name': name,
            'cliente_id': self.cliente.id,
            'producto_id': self.producto.id,
            'cantidad': cantidad,
            'descuento': descuento,
        }

    def test_venta_calcula_totales_y_descuenta_stock(self):
        venta = self.env['techstore.venta'].create(
            self._venta_values('TEST-VENTA-001')
        )

        self.assertEqual(venta.precio_unitario, 100)
        self.assertEqual(venta.stock_disponible, 10)
        self.assertEqual(venta.subtotal, 195)
        self.assertEqual(venta.iva, 9.75)
        self.assertEqual(venta.total, 204.75)
        self.assertEqual(self.producto.stock_disponible, 8)
        self.assertGreaterEqual(venta.tiempo_respuesta, 0)

    def test_venta_rechaza_cantidad_invalida(self):
        with self.assertRaises(ValidationError):
            self.env['techstore.venta'].create(
                self._venta_values('TEST-VENTA-002', cantidad=0)
            )

        with self.assertRaises(ValidationError):
            self.env['techstore.venta'].create(
                self._venta_values('TEST-VENTA-003', cantidad=11)
            )

    def test_venta_rechaza_descuento_mayor_al_importe(self):
        with self.assertRaises(ValidationError):
            self.env['techstore.venta'].create(
                self._venta_values('TEST-VENTA-004', descuento=201)
            )

    def test_creacion_por_lotes(self):
        ventas = self.env['techstore.venta'].create([
            self._venta_values('TEST-VENTA-005', cantidad=1, descuento=0),
            self._venta_values('TEST-VENTA-006', cantidad=2, descuento=0),
        ])

        self.assertEqual(len(ventas), 2)
        self.assertEqual(self.producto.stock_disponible, 7)

    def test_rechaza_referencias_duplicadas(self):
        self.env['techstore.venta'].create(
            self._venta_values('TEST-VENTA-007')
        )

        with self.assertRaises(ValidationError):
            self.env['techstore.venta'].create(
                self._venta_values('TEST-VENTA-007')
            )

    def test_rechaza_producto_con_valores_invalidos(self):
        with self.assertRaises(ValidationError):
            self.env['techstore.producto'].create({
                'name': 'Producto invalido',
                'codigo': 'TEST-PRODUCTO-NEGATIVO',
                'precio_unitario': -1,
                'stock_disponible': 1,
            })

    def test_rechaza_cliente_duplicado(self):
        with self.assertRaises(ValidationError):
            self.env['techstore.cliente'].create({
                'name': 'Cliente duplicado',
                'cedula': 'TEST-CLIENTE-001',
            })

    def test_no_permite_cambiar_cantidad_de_venta(self):
        venta = self.env['techstore.venta'].create(
            self._venta_values('TEST-VENTA-008', cantidad=1, descuento=0)
        )

        with self.assertRaises(ValidationError):
            venta.write({'cantidad': 2})

    def test_100_ventas_aleatorias(self):
        generator = random.Random(20261010)
        total_stock_consumed = 0

        for index in range(1, 101):
            price = round(generator.uniform(1, 1000), 2)
            quantity = generator.randint(1, 10)
            stock = quantity + generator.randint(0, 25)
            gross = quantity * price
            discount = round(generator.uniform(0, gross), 2)
            product = self.env['techstore.producto'].create({
                'name': f'Producto aleatorio {index:03d}',
                'codigo': f'RANDOM-{index:03d}',
                'precio_unitario': price,
                'stock_disponible': stock,
            })

            sale = self.env['techstore.venta'].create({
                'name': f'Venta aleatoria {index:03d}',
                'cliente_id': self.cliente.id,
                'producto_id': product.id,
                'cantidad': quantity,
                'descuento': discount,
            })

            subtotal = gross - discount
            self.assertAlmostEqual(sale.subtotal, subtotal, places=2)
            self.assertAlmostEqual(sale.iva, subtotal * 0.05, places=2)
            self.assertAlmostEqual(sale.total, subtotal * 1.05, places=2)
            self.assertEqual(sale.stock_disponible, stock)
            self.assertEqual(product.stock_disponible, stock - quantity)
            total_stock_consumed += quantity

        self.assertGreater(total_stock_consumed, 0)