from odoo import api, fields, models
from odoo.exceptions import ValidationError
import time


class TechstoreVenta(models.Model):
    _name = 'techstore.venta'
    _description = 'Venta TechStore'
    _order = 'create_date desc'

    name = fields.Char(string='Referencia', required=True, default='Nueva venta')

    cliente_id = fields.Many2one(
        'techstore.cliente',
        string='Cliente',
    )

    producto_id = fields.Many2one(
        'techstore.producto',
        string='Producto',
    )

    cantidad = fields.Integer(string='Cantidad', required=True)
    precio_unitario = fields.Float(string='Precio unitario')
    stock_disponible = fields.Integer(string='Stock disponible')
    descuento = fields.Float(string='Descuento')
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)
    iva = fields.Float(string='IVA', compute='_compute_totales', store=True)
    total = fields.Float(string='Total', compute='_compute_totales', store=True)
    tiempo_respuesta = fields.Float(string='Tiempo de respuesta')
    estado_calidad = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('observado', 'Observado'),
        ('aceptable', 'Aceptable'),
    ], string='Estado de calidad', default='pendiente')

    observacion = fields.Text(string='Observación del estudiante')

    @api.onchange('producto_id')
    def _onchange_producto_id(self):
        for rec in self:
            if rec.producto_id:
                rec.precio_unitario = rec.producto_id.precio_unitario
                rec.stock_disponible = rec.producto_id.stock_disponible

    @api.depends('cantidad', 'precio_unitario', 'descuento')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.cantidad * rec.precio_unitario - rec.descuento

    @api.depends('subtotal')
    def _compute_totales(self):
        for rec in self:
            rec.iva = rec.subtotal * 0.05
            rec.total = rec.subtotal + rec.iva

    @api.constrains('name', 'cantidad', 'precio_unitario', 'descuento')
    def _check_values(self):
        for record in self:
            duplicate = self.search([
                ('name', '=', record.name),
                ('id', '!=', record.id),
            ], limit=1)
            if duplicate and not self.env.context.get('install_mode'):
                raise ValidationError('La referencia de venta ya existe.')
            if record.cantidad <= 0:
                raise ValidationError('La cantidad debe ser mayor que cero.')
            if record.precio_unitario < 0:
                raise ValidationError('El precio unitario no puede ser negativo.')
            if record.descuento < 0:
                raise ValidationError('El descuento no puede ser negativo.')
            if record.descuento > record.cantidad * record.precio_unitario:
                raise ValidationError('El descuento no puede superar el importe bruto.')

    @api.model_create_multi
    def create(self, vals_list):
        inicio = time.time()
        prepared_values = []

        for values in vals_list:
            values = dict(values)
            client = self.env['techstore.cliente'].browse(values.get('cliente_id'))
            if not client.exists():
                raise ValidationError('Debe seleccionar un cliente válido.')

            product = self.env['techstore.producto'].browse(values.get('producto_id'))
            if not product.exists():
                raise ValidationError('Debe seleccionar un producto válido.')

            quantity = values.get('cantidad', 0)
            if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
                raise ValidationError('La cantidad debe ser mayor que cero.')

            self.env['techstore.producto'].flush_model(['stock_disponible'])
            self.env.cr.execute(
                'SELECT stock_disponible FROM techstore_producto WHERE id = %s FOR UPDATE',
                (product.id,),
            )
            stock = self.env.cr.fetchone()[0]
            if quantity > stock:
                raise ValidationError('No hay stock suficiente para la venta.')

            values['precio_unitario'] = product.precio_unitario
            values['stock_disponible'] = stock
            values['tiempo_respuesta'] = 0
            prepared_values.append(values)
            self.env.cr.execute(
                'UPDATE techstore_producto SET stock_disponible = %s WHERE id = %s',
                (stock - quantity, product.id),
            )
            product.invalidate_recordset(['stock_disponible'])

        records = super().create(prepared_values)
        elapsed = round(time.time() - inicio, 4)
        records.write({'tiempo_respuesta': elapsed})
        return records

    def write(self, values):
        if {'producto_id', 'cantidad'} & set(values):
            raise ValidationError(
                'No se puede cambiar el producto o la cantidad de una venta creada.'
            )
        return super().write(values)

    def action_marcar_aceptable(self):
        for rec in self:
            rec.estado_calidad = 'aceptable'

    def action_marcar_observado(self):
        for rec in self:
            rec.estado_calidad = 'observado'
