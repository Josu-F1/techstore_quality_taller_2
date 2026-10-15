from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError
import logging
import time
import json


_logger = logging.getLogger(__name__)


class TechStoreQualityAPI(http.Controller):

    @http.route('/techstore_quality/api/operacion', type='json', auth='user', methods=['POST'], csrf=False)
    def operacion(self, **kwargs):
        inicio = time.time()

        a = kwargs.get('a', 10)
        b = kwargs.get('b', 0)
        operacion = kwargs.get('operacion', 'division')

        if not isinstance(a, (int, float)) or isinstance(a, bool):
            return {'success': False, 'error': 'El valor a debe ser numérico.'}
        if not isinstance(b, (int, float)) or isinstance(b, bool):
            return {'success': False, 'error': 'El valor b debe ser numérico.'}
        if operacion not in {'suma', 'resta', 'division', 'avg', 'percent'}:
            return {'success': False, 'error': 'Operación no reconocida.'}
        if operacion in {'division', 'percent'} and b == 0:
            return {'success': False, 'error': 'No se puede dividir entre cero.'}

        if operacion == 'suma':
            resultado = a + b
        elif operacion == 'resta':
            resultado = a - b
        elif operacion == 'division':
            resultado = a / b
        elif operacion == 'avg':
            resultado = (a + b) / 2
        elif operacion == 'percent':
            resultado = (a / b) * 100
        else:
            resultado = (a / b) * 100

        return {
            'operacion': operacion,
            'a': a,
            'b': b,
            'resultado': resultado,
            'tiempo_respuesta': round(time.time() - inicio, 4)
        }

    def _leer_json(self):
        body = request.httprequest.data

        if not body:
            return {}

        if isinstance(body, bytes):
            body = body.decode('utf-8')

        data = json.loads(body)
        if not isinstance(data, dict):
            raise ValidationError('El cuerpo debe ser un objeto JSON.')
        return data

    def _validar_campos(self, data, campos):
        faltantes = [campo for campo in campos if data.get(campo) in (None, '')]
        if faltantes:
            raise ValidationError(
                'Faltan campos obligatorios: %s.' % ', '.join(faltantes)
            )

    def _respuesta_error(self, error, status=500):
        if isinstance(error, (ValidationError, json.JSONDecodeError)):
            status = 400
        if status >= 500:
            _logger.exception('Error interno en la API TechStore')
            mensaje = 'Error interno del servidor.'
        else:
            mensaje = str(error)
        return request.make_json_response({
            'success': False,
            'error': mensaje,
        }, status=status)

    @http.route(
        '/api/clientes',
        type='http',
        auth='user',
        methods=['POST'],
        csrf=False,
    )
    def crear_cliente(self, **kwargs):
        try:
            data = self._leer_json()
            self._validar_campos(data, ['name'])

            cliente = request.env['techstore.cliente'].create({
                'name': data.get('name'),
                'cedula': data.get('cedula'),
                'email': data.get('email'),
                'telefono': data.get('telefono'),
                'activo': data.get('activo', True),
            })
            return request.make_json_response({
                'success': True,
                'id': cliente.id,
                'message': 'Cliente creado correctamente',
            })
        except Exception as error:
            return self._respuesta_error(error)

    @http.route(
        '/api/productos',
        type='http',
        auth='user',
        methods=['POST'],
        csrf=False,
    )
    def crear_producto(self, **kwargs):
        try:
            data = self._leer_json()
            self._validar_campos(data, ['name', 'precio_unitario'])

            producto = request.env['techstore.producto'].create({
                'name': data.get('name'),
                'codigo': data.get('codigo'),
                'precio_unitario': data.get('precio_unitario'),
                'stock_disponible': data.get('stock_disponible', 10),
                'activo': data.get('activo', True),
            })
            return request.make_json_response({
                'success': True,
                'id': producto.id,
                'message': 'Producto creado correctamente',
            })
        except Exception as error:
            return self._respuesta_error(error)

    @http.route(
        '/api/ventas',
        type='http',
        auth='user',
        methods=['POST'],
        csrf=False,
    )
    def crear_venta(self, **kwargs):
        try:
            data = self._leer_json()
            self._validar_campos(
                data,
                ['name', 'cliente_id', 'producto_id', 'cantidad'],
            )

            venta = request.env['techstore.venta'].create({
                'name': data.get('name', 'Nueva venta'),
                'cliente_id': data.get('cliente_id'),
                'producto_id': data.get('producto_id'),
                'cantidad': data.get('cantidad', 0),
                'descuento': data.get('descuento', 0),
                'observacion': data.get('observacion'),
            })
            return request.make_json_response({
                'success': True,
                'id': venta.id,
                'name': venta.name,
                'cliente_id': venta.cliente_id.id if venta.cliente_id else None,
                'producto_id': venta.producto_id.id if venta.producto_id else None,
                'cantidad': venta.cantidad,
                'precio_unitario': venta.precio_unitario,
                'stock_disponible': venta.stock_disponible,
                'descuento': venta.descuento,
                'subtotal': venta.subtotal,
                'iva': venta.iva,
                'total': venta.total,
                'tiempo_respuesta': venta.tiempo_respuesta,
                'estado_calidad': venta.estado_calidad,
                'message': 'Venta creada correctamente',
            })
        except Exception as error:
            return self._respuesta_error(error)
