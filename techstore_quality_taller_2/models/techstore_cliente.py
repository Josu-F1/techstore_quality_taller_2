from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TechstoreCliente(models.Model):
    _name = 'techstore.cliente'
    _description = 'Cliente TechStore'
    _order = 'name'

    name = fields.Char(string='Nombre del cliente', required=True)
    cedula = fields.Char(string='Cédula/RUC')
    email = fields.Char(string='Correo')
    telefono = fields.Char(string='Teléfono')
    activo = fields.Boolean(string='Activo', default=True)

    @api.constrains('cedula', 'email')
    def _check_email(self):
        for record in self:
            if record.cedula and not self.env.context.get('install_mode'):
                duplicate = self.search([
                    ('cedula', '=', record.cedula),
                    ('id', '!=', record.id),
                ], limit=1)
                if duplicate:
                    raise ValidationError('La cédula/RUC ya existe.')
            if record.email and ('@' not in record.email or record.email.startswith('@')):
                raise ValidationError('El correo electrónico no es válido.')
