# -*- encoding: utf-8 -*-
##############################################################################
#
#    Autocomplete Adress from CEP for Odoo
#    Copyright (C) 2015 KMEE (http://www.kmee.com.br)
#    @author Michell Stuttgart <michell.stuttgart@kmee.com.br>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import orm, osv
from openerp.tools.translate import _

from suds.client import Client, TransportError
from suds import WebFault


class ResCompany(orm.Model):

    _inherit = 'res.company'

    def fetch_adress_from_cep(self, cr, uid, ids, context=None):

        for obj_partner in self.browse(cr, uid, ids, context=context):

            cep = obj_partner.zip

            if obj_partner.country_id and obj_partner.country_id.code != 'BR':
                msg = 'Adress from cep module work only Brazil country!'
                raise osv.except_osv(_('Error!'), _(msg))

            if cep and len(cep) == 9:

                url_prod = 'https://apps.correios.com.br/SigepMasterJPA' \
                           '/AtendeClienteService/AtendeCliente?wsdl'

                try:
                    # Remove hifen of cep
                    cep = cep.replace('-', '')

                    # Inciamos o cliente do webservice
                    res = Client(url_prod).service.consultaCEP(cep)

                    # Search state with state_code
                    state_ids = self.pool.get('res.country.state').search(
                        cr, uid, [('code', '=', str(res.uf))])

                    # city name
                    cidade = str(res.cidade.encode('utf8'))

                    # search city with name and state
                    city_ids = self.pool.get('l10n_br_base.city').search(
                        cr, uid, [('name', '=', cidade), ('state_id.id', 'in',
                                                          state_ids)])

                    # Buscar id do pais
                    country_ids = self.pool.get('res.country').search(
                        cr, uid, [('code', '=', 'BR')])

                    vals = {
                        'street': str(res.end.encode('utf8')),
                        'district': str(res.bairro.encode('utf8')),
                        'street2': str(res.complemento.encode('utf8')) if res.complemento
                        else '',
                        'l10n_br_city_id': city_ids[0] if city_ids else False,
                        'state_id': state_ids[0] if state_ids else False,
                        'country_id': country_ids[0] if country_ids else False,
                    }

                    # Write adress
                    self.write(cr, uid, ids, vals)

                except TransportError as e:
                    raise osv.except_osv(_('Error!'), _(e.message))
                except WebFault as e:
                    raise osv.except_osv(_('Error!'), _(e.message))

        return True
