from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TechstoreProducto(models.Model):
    _name = 'techstore.producto'
    _description = 'Producto TechStore'
    _order = 'name'

    name = fields.Char(string='Producto', required=True)
    codigo = fields.Char(string='Código')
    precio_unitario = fields.Float(string='Precio unitario', required=True)
    stock_disponible = fields.Integer(string='Stock disponible', default=10)
    activo = fields.Boolean(string='Activo', default=True)

    @api.constrains('codigo', 'precio_unitario', 'stock_disponible')
    def _check_values(self):
        for record in self:
            if record.codigo and not self.env.context.get('install_mode'):
                duplicate = self.search([
                    ('codigo', '=', record.codigo),
                    ('id', '!=', record.id),
                ], limit=1)
                if duplicate:
                    raise ValidationError('El código del producto ya existe.')
            if record.precio_unitario < 0:
                raise ValidationError('El precio unitario no puede ser negativo.')
            if record.stock_disponible < 0:
                raise ValidationError('El stock disponible no puede ser negativo.')
