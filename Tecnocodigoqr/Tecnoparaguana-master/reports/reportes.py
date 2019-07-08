# -*- coding: utf-8 -*-	

from openerp.osv import fields, osv
from openerp.report import report_sxw
from openerp import api, models, fields
from openerp.exceptions import except_orm, Warning, RedirectWarning
import logging
_logger = logging.getLogger(__name__)

#### PARSER - Procesa las funciones!!!
class cuentas_libro_mayor(report_sxw.rml_parse):
	_name = "report_reportelibromayor.libro_mayor_template"
	
	def __init__(self, cr, uid, name, context):
		super(cuentas_libro_mayor, self).__init__(cr, uid, name, context)
	
	"""
	@api.multi
	def ids_de_cuentas(self):
		cuentas_ids = []
		registros = {}
		a = 0
		cuentas = self.env['tecnop.cuentas'].search([('id', '!=', None)])
		for cuenta in cuentas:
			if cuenta.saldo != 0:
				cuentas_ids.append(cuenta.id)
		#if cuenta:
			#for a in cuentas_ids:
				#_logger.info(a) # Cuentas
					#raise except_orm('Debug', a)
		
		asientos = self.env['tecnop.asientos'].search([('id', '!=', None)])
		_logger.info(cuentas_ids)
		for ids in cuentas_ids: # Recorre los IDs de las cuentas
			_logger.info(ids)
			for asiento in asientos:
				if asiento.id_periodo.fecha_inicio:
					#TODO: Esta función deberá de comprobar si el asiento contable encontrado se encuentra en el periodo seleccionado por el usuario
					for apuntes in asiento.ids_asientos:
						if ids == apuntes.id_cuenta.id:
							registros = {
							'cuenta': apuntes.id_cuenta.nombre,
							'fecha': asiento.fecha,
							'referencia': asiento.referencia,
							'etiqueta': apuntes.nombre,
							#'contrapartida': TODO
							'debe': apuntes.id_cuenta.debe,
							'haber': apuntes.id_cuenta.haber,
							'saldo': apuntes.id_cuenta.saldo,
							}
							if registros:
								_logger.info(registros.get("fecha"))
								_logger.info(registros.get("referencia"))
								_logger.info(registros.get("cuenta"))
			a = a + 1
			_logger.info('Valor de la variable contadora A: ')
		_logger.info(registros)
		if registros['cuenta'] == 'Honorarios Profesionales':
			_logger.info('Entro')
			_logger.info('Entro')
			_logger.info('Entro')
			_logger.info('Entro')
			
				#ESTA FUNCIÓN DEBERÁ RETORNAR UN DICCIONARIO (REGISTROS) EL CUAL SERÁ ITERADO EN EL XML PARA OBTENER Y MOSTRAR TODAS LAS CUENTAS CON ALGÚN
				#TIPO DE MOVIMIENTO, DE MANERA ORDENADA			
								#for registro in registros:
									#raise except_orm('Debug', registro.cuenta)
									#_logger.info(registro.cuenta)
									#raise except_orm('Debug', registro.cuenta)
	"""
	
class reporte_cuentas_libro_mayor(models.AbstractModel):
	_name = 'tecnop.reporte_cuentas_libro_mayor'
	_inherit = 'report.abstract_report'
	_template = 'reporte_cuentas_libro_mayor'
	_wrapped_report_class = cuentas_libro_mayor

class reporte_general_libro_mayor_wizard(models.TransientModel):
	_name = 'tecnop.reporte_general_libro_mayor_wizard'
#	_columns = {
	prueba = fields.Text('Prueba')
	ejercicio_fiscal = fields.One2many('tecnop.ejfiscal', 'id_ef', 'Ejercicio fiscal')
#		}
		#'periodo':

class reporte_general_libro_mayor_wizard(models.Model):
	_name = 'tecnop.nojoda'
#	_columns = {
	prueba = fields.Text('Prueba')
	prueba2 = fields.Text('Prueba')
	ejercicio_fiscal = fields.One2many('tecnop.ejfiscal', 'id_ef', 'Ejercicio fiscal')
#		}
		#'periodo':
	
