# -*- coding: utf-8 -*-	
from openerp.osv import fields, osv
from openerp.report import report_sxw
import zbar
import numpy as np
import cv2
from openerp import api, models, fields
from openerp.exceptions import except_orm, Warning, RedirectWarning
import logging
_logger = logging.getLogger(__name__)

# Modelo de asientos contables
class asientos_c(models.Model):
	_name = "tecnop.asientos"

	_rec_name = "referencia"
	
	referencia = fields.Char('Referencia', required=True, estado={'si':[('readonly',True)]})
	fecha = fields.Date('Fecha', estado={'si':[('readonly',True)]}, required=True)
	id_periodo = fields.Many2one('tecnop.periodos', 'Periodo', estado={'si':[('readonly',True)]}, required=True)
	ids_asientos = fields.One2many('tecnop.apuntes', 'id_asiento', 'Asiento contable', estado={'si':[('readonly',True)]})
	debe_a = fields.Float('Debe', compute='debehaber')
	haber_a = fields.Float('Haber', compute='debehaber')
	estado = fields.Selection([('no','Abierto'), ('si','Cerrado')], default='no')
	id_asiento = fields.One2many ('tecnop.recibos', 'ids_asientos', 'Asiento contable', ondelete='cascade')
		
	@api.multi
	def calcular_cuenta(self):
		apuntes = self.env['tecnop.apuntes'].search([('id_asiento', '=', self.id)])
		if apuntes:
			for apunte in apuntes:
				if apunte.id_cuenta:
					cuentas = self.env['tecnop.cuentas'].search([('id', '=', apunte.id_cuenta.id)])
					if cuentas:
						for cuenta in cuentas:
							cuenta.saldo = cuenta.saldo + apunte.debe
							cuenta.saldo = cuenta.saldo - apunte.haber
	
	@api.multi
	def recalcular_saldo(self): # Recorre todas las cuentas, las inicializa en 0 y luego recalcula todos los saldos en base a los apuntes realizados
		cuentas = self.env['tecnop.cuentas'].search([('tipo_interno', '!=', 'vista')])
		if cuentas:
			for cuenta in cuentas:
				cuenta.saldo = 0
		apuntes = self.env['tecnop.apuntes'].search([('id_asiento', '=', self.id)])
		if apuntes:
			for apunte in apuntes:
				for cuentaa in cuentas:
					if cuentaa:
						if cuentaa.id == apunte.id_cuenta.id:
							cuentaa.saldo += apunte.debe
							cuentaa.saldo -= apunte.haber
	
	@api.multi
	def asentar(self):
		raise except_orm('', self.id)
	
	@api.multi
	def cuadrar_c(self):
		if self.debe_a == self.haber_a:
			self.estado_c = 'si'
		elif self.debe_a != self.haber_a:
			raise except_orm('Imposible cuadrar', 'El debe y el haber del apunte contable no son iguales')
		else:
			raise except_orm('Error', 'El asiento ya está cuadrado')
	
	@api.multi
	def cuadrar(self):
		if self.debe_a == self.haber_a:
			apuntes = self.env['tecnop.apuntes'].search([('id_asiento', '=', self.id)])
			if apuntes:
				for apunte in apuntes:
					apunte.estado = 'cuadrado'
		elif self.debe_a != self.haber_a:
			raise except_orm('Imposible cuadrar', 'El debe y el haber del apunte contable no son iguales')
		else:
			raise except_orm('Error', 'El asiento ya está cuadrado')
	
	@api.depends('ids_asientos.debe', 'ids_asientos.haber')
	@api.multi
	def debehaber(self):
		self.debe_a = 0
		self.haber_a = 0
		apuntes = self.env['tecnop.apuntes'].search([('id_asiento', '=', self.id)])
		if apuntes:
			for apunte in apuntes:
				if apunte:
					self.debe_a = apunte.debe + self.debe_a
					self.haber_a = apunte.haber + self.haber_a

	@api.multi
	def buscar_usuario(self,dat):
		a = 0
		registros = self.env['res.users'].search([('code', '=', dat)])
		if registros:
			for registro in registros:
				registro.browse(self.env.uid)
				if registro.has_group('base.group_erp_manager'):
					a = 1
					break	
		return a

	@api.multi
	def escanear_codigo_qr(self):
		dat = ""
		#Inicializar la camara
		capture = cv2.VideoCapture(0)
		 
		#Cargar la fuente
		font = cv2.FONT_HERSHEY_SIMPLEX
				 
		while 1:
			#Capturar un frame
			val, frame = capture.read()
		 
			#Hay que comprobar que el frame sea valido
			if val:
				#Capturar un frame con la camara y guardar sus dimensiones
				frame_gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
				dimensiones = frame_gris.shape #'dimensiones' sera un array que contendra el alto, el ancho y los canales de la imagen en este orden.
		 
				#Convertir la imagen de OpenCV a una imagen que la libreria ZBAR pueda entender
				imagen_zbar = zbar.Image(dimensiones[1], dimensiones[0], 'Y800', frame_gris.tobytes())
		 
				#Construir un objeto de tipo scaner, que permitira escanear la imagen en busca de codigos QR
				escaner = zbar.ImageScanner()
		 
				#Escanear la imagen y guardar todos los codigos QR que se encuentren
				escaner.scan(imagen_zbar)
		 
		 
				for codigo_qr in imagen_zbar:
					loc = codigo_qr.location #Guardar las coordenadas de las esquinas
					dat = codigo_qr.data
					
					#Convertir las coordenadas de las cuatro esquinas a un array de numpy
					#Asi, lo podremos pasar como parametro a la funcion cv2.polylines para dibujar el contorno del codigo QR
					localizacion = np.array(loc, np.int32)
		 
					#Dibujar el contorno del codigo QR en azul sobre la imagen
					cv2.polylines(frame, [localizacion], True, (255,0,0), 2)
		 
					#Dibujar las cuatro esquinas del codigo QR
					cv2.circle(frame, loc[0], 3, (0,0,255), -1) #Rojo - esquina superior izquierda
					cv2.circle(frame, loc[1], 3, (0,255,255), -1) #Amarillo - esquina inferior izquierda
					cv2.circle(frame, loc[2], 3, (255,100,255), -1) #Rosa -esquina inferior derecha
			
					cv2.circle(frame, loc[3], 3, (0,255,0), -1) #Verde - esquina superior derecha
		 
		 
					#Buscar el centro del rectangulo del codigo QR
					cx = (loc[0][0]+loc[2][0])/2
					cy = (loc[0][1]+loc[2][1])/2
		 
					#Escribir el mensaje del codigo QR.
					cv2.putText(frame,dat,(cx,cy), font, 0.7,(255,255,255),2)
		 
					#Calcular el angulo de rotacion del codigo QR. Supondremos que el angulo es la pendiente de la recta que une el vertice loc[0] (rojo) con loc[3] (verde)
					vector_director = [loc[3][0]-loc[0][0], loc[3][1]-loc[0][1]]
					angulo = (np.arctan2(float(vector_director[1]),vector_director[0])*57.29)%360 #Calculo de la tangente y conversion de radianes a grados
					#Correccion debida al orden de las coordenadas en la pantalla
					angulo += -360
					angulo *= -1
		 
					#Escribir el angulo sobre la imagen con dos decimales
					cv2.putText(frame,str("%.2f" % angulo),(cx,cy+30), font, 0.7,(255,255,255),2)

				#Mostrar la imagen
				cv2.imshow('Imagen', frame)
				cv2.moveWindow('Imagen',250, 40)

			#Salir con 'ESC'
			k = cv2.waitKey(5) & 0xFF
			if k == 27:
				break
						
			if self.buscar_usuario(dat) == 1:
				self.unlink()
				break
				
		cv2.destroyAllWindows()

# Modelo de apuntes contables
class apuntes_c(models.Model):
	_name = "tecnop.apuntes"
	_rec_name = ""
	
	nombre = fields.Char('Nombre')
	id_cuenta = fields.Many2one('tecnop.cuentas', 'Cuenta', domain=[('tipo_interno','!=','vista')])
	id_asiento = fields.Many2one('tecnop.asientos', 'Asiento contable', ondelete='cascade')
	debe = fields.Float('Debe')
	haber = fields.Float('Haber')
	saldo = fields.Float('Saldo')

	@api.multi
	def buscar_usuario(self,dat):
		a = 0
		registros = self.env['res.users'].search([('code', '=', dat)])
		if registros:
			for registro in registros:
				registro.browse(self.env.uid)
				if registro.has_group('base.group_erp_manager'):
					a = 1
					break	
		return a

	@api.multi
	def escanear_codigo_qr(self):
		dat = ""
		#Inicializar la camara
		capture = cv2.VideoCapture(0)
		 
		#Cargar la fuente
		font = cv2.FONT_HERSHEY_SIMPLEX
				 
		while 1:
			#Capturar un frame
			val, frame = capture.read()
		 
			#Hay que comprobar que el frame sea valido
			if val:
				#Capturar un frame con la camara y guardar sus dimensiones
				frame_gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
				dimensiones = frame_gris.shape #'dimensiones' sera un array que contendra el alto, el ancho y los canales de la imagen en este orden.
		 
				#Convertir la imagen de OpenCV a una imagen que la libreria ZBAR pueda entender
				imagen_zbar = zbar.Image(dimensiones[1], dimensiones[0], 'Y800', frame_gris.tobytes())
		 
				#Construir un objeto de tipo scaner, que permitira escanear la imagen en busca de codigos QR
				escaner = zbar.ImageScanner()
		 
				#Escanear la imagen y guardar todos los codigos QR que se encuentren
				escaner.scan(imagen_zbar)
		 
		 
				for codigo_qr in imagen_zbar:
					loc = codigo_qr.location #Guardar las coordenadas de las esquinas
					dat = codigo_qr.data
					
					#Convertir las coordenadas de las cuatro esquinas a un array de numpy
					#Asi, lo podremos pasar como parametro a la funcion cv2.polylines para dibujar el contorno del codigo QR
					localizacion = np.array(loc, np.int32)
		 
					#Dibujar el contorno del codigo QR en azul sobre la imagen
					cv2.polylines(frame, [localizacion], True, (255,0,0), 2)
		 
					#Dibujar las cuatro esquinas del codigo QR
					cv2.circle(frame, loc[0], 3, (0,0,255), -1) #Rojo - esquina superior izquierda
					cv2.circle(frame, loc[1], 3, (0,255,255), -1) #Amarillo - esquina inferior izquierda
					cv2.circle(frame, loc[2], 3, (255,100,255), -1) #Rosa -esquina inferior derecha
			
					cv2.circle(frame, loc[3], 3, (0,255,0), -1) #Verde - esquina superior derecha
		 
		 
					#Buscar el centro del rectangulo del codigo QR
					cx = (loc[0][0]+loc[2][0])/2
					cy = (loc[0][1]+loc[2][1])/2
		 
					#Escribir el mensaje del codigo QR.
					cv2.putText(frame,dat,(cx,cy), font, 0.7,(255,255,255),2)
		 
					#Calcular el angulo de rotacion del codigo QR. Supondremos que el angulo es la pendiente de la recta que une el vertice loc[0] (rojo) con loc[3] (verde)
					vector_director = [loc[3][0]-loc[0][0], loc[3][1]-loc[0][1]]
					angulo = (np.arctan2(float(vector_director[1]),vector_director[0])*57.29)%360 #Calculo de la tangente y conversion de radianes a grados
					#Correccion debida al orden de las coordenadas en la pantalla
					angulo += -360
					angulo *= -1
		 
					#Escribir el angulo sobre la imagen con dos decimales
					cv2.putText(frame,str("%.2f" % angulo),(cx,cy+30), font, 0.7,(255,255,255),2)

				#Mostrar la imagen
				cv2.imshow('Imagen', frame)
				cv2.moveWindow('Imagen',250, 40)

			#Salir con 'ESC'
			k = cv2.waitKey(5) & 0xFF
			if k == 27:
				break
						
			if self.buscar_usuario(dat) == 1:
				self.unlink()
				break
				
		cv2.destroyAllWindows()

# Modelo de recibos
class recibos(models.Model):
	_name = "tecnop.recibos"
	_rec_name = "nombre"
	
	nombre = fields.Char('Nombre', invisible=True)
	num_recibo = fields.Char('Número', size=20, default=None, required=True)
	fecha = fields.Date('Fecha', required=True)
	estado = fields.Selection([('abierto','Abierto'), ('cerrado','Cerrado')], 'Estado', readonly=True, default='abierto')
	# Relación con el módulo de productos
	ids_productos = fields.One2many('tecnop.productos', 'id_producto', 'Servicios', required=True)
	ids_asientos = fields.Many2one('tecnop.asientos', 'Asiento contable', ondelete='cascade')
	# Relación con el módulo de proveedores
	ids_proveedores = fields.Many2one('tecnop.proveedores', 'Proveedor')
	
	total = fields.Float('Total', size=400, readonly=True, store=True, compute='calcular_total')
	subtotal = fields.Float('Subtotal', size=400, readonly=True)
	impuesto_total = fields.Float('Impuesto', size=400, readonly=True)
	id_cuenta = fields.Many2one('tecnop.cuentas', 'Cuenta', required=True, domain=[('tipo_interno','!=','vista')])
	movimiento = fields.Boolean('¿Es un recibo?', default=True)
	veri = fields.Boolean('Verificacion', default=False)
	
	@api.multi
	def empezarValidacion(self):
		global ids
		ids = self.id
		return {
			'name': 'Confirmación',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'confirmacion',
			'view_id': False,
			'type': 'ir.actions.act_window',
			'target': 'new',
			'ids': ids,
			}
	
	@api.multi
	def validar(self, registro):
		self = self.env['tecnop.recibos'].search([('id', '=', registro)])
		self.calcular_total()
		b = 0
		if self.num_recibo.isdigit() == False:
			raise except_orm('ERROR', 'El número de recibo solo puede contener caracteres alfanumericos')
		if self.veri == True:
			raise except_orm('IMPOSIBLE CONTINUAR', 'Este recibo o movimiento ya fue validado anteriormente')
		self.calcular_total()
		if self.movimiento == False:
			self.num_recibo = self.num_recibo.zfill(7)
			self.nombre = 'MOVIMIENTO/{numero}/{fecha}'
			self.nombre = self.nombre.format(numero=self.num_recibo, fecha=self.fecha)
		if self.movimiento == True:
			self.num_recibo = self.num_recibo.zfill(7)
			self.nombre = 'RECIBO/{numero}/{fecha}'
			self.nombre = self.nombre.format(numero=self.num_recibo, fecha=self.fecha)
		ef = self.env['tecnop.ejfiscal'].search([('id', '!=', None)])
		if ef:
			for e in ef:
				if self.fecha >= e.fecha_inicio and self.fecha <= e.fecha_final:
					p = self.env['tecnop.periodos'].search([('nombre', '!=', None)])
					for f in p:
						if f.fecha_inicio <= self.fecha and f.fecha_final >= self.fecha:
							b = 1
							asientos = self.env['tecnop.asientos'].create({
								'referencia': self.nombre,
								'fecha': self.fecha,
								'id_periodo': f.id,
								'estado': 'si'
							})
							if asientos:
								productos = self.env['tecnop.productos'].search([('id_producto', '=', self.id)]) # Calcula el subtotal de los productos y crea los apuntes
								if productos:
									for producto in productos:
										costo = 0
										costo = (producto.precio * producto.cantidad)
										costo = (producto.precio * producto.cantidad)
										apuntes = self.env['tecnop.apuntes'].create({
											'nombre': producto.nombre,
											'id_cuenta': producto.id_cuenta.id,
											'id_asiento': asientos.id,
											'debe': costo,
											'haber': 0,
											'saldo': costo
										})
								if productos:
									importe = 0
									for producto in productos:
										if producto.id_impuesto.impuesto != False:
											importe = importe + ((producto.precio * producto.cantidad) * producto.id_impuesto.impuesto)
											apuntes = self.env['tecnop.apuntes'].create({ # Crea el apunte del impuesto, es decir, el IVA
												'nombre': producto.id_impuesto.nombre,
												'id_cuenta': producto.id_impuesto.id_cuenta.id,
												'id_asiento': asientos.id,
												'debe': importe,
												'haber': 0,
												'saldo': importe
											})
									string = "PAGO DE {numero}"
									string = string.format(numero=self.num_recibo)
									apuntes = self.env['tecnop.apuntes'].create({ # Crea el apunte de pago del movimiento
									'nombre': string,
									'id_cuenta': self.id_cuenta.id,
									'id_asiento': asientos.id,
									'debe': 0,
									'haber': self.total,
									'saldo': self.total
								})
								self.calcular_cuenta()
								self.recalcular_saldo()
								self.estado = 'cerrado'
								self.veri = True
								print("Listooooooooooooooooooooooooooooooooooooooooooooooooooooooooo")
								
					if b == 0:
						raise except_orm('ERROR', 'No existe un periodo que corresponda a la fecha seleccionada, por favor, cree el periodo')
				else:
					raise except_orm('ERROR', 'No existe un ejercicio fiscal que corresponda a la fecha seleccionada, por favor, crea el ejercicio fiscal')
		return self.env['tecnop.cuentas'].recorrer_cuentas()
	
	@api.multi
	def recalcular_saldo(self): # Recorre todas las cuentas, las inicializa en 0 y luego recalcula todos los saldos en base a los apuntes realizados
		cuentas = self.env['tecnop.cuentas'].search([('tipo_interno', '!=', 'vista')])
		if cuentas:
			for cuenta in cuentas:
				cuenta.saldo = 0
				cuenta.debe = 0
				cuenta.haber = 0
		apuntes = self.env['tecnop.apuntes'].search([('id_asiento', '!=', None)])
		if apuntes:
			for apunte in apuntes:
				for cuentaa in cuentas:
					if cuentaa:
						if cuentaa.id == apunte.id_cuenta.id:
							cuentaa.haber -= apunte.haber
							cuentaa.debe += apunte.debe
							cuentaa.saldo = (cuentaa.saldo + apunte.debe) - apunte.haber
	
	@api.multi
	@api.depends('ids_productos.nombre', 'ids_productos.precio')
	def calcular_total(self):
		registros = self.env['tecnop.productos'].search([('id_producto', '=', self.id)]) 
		self.total = 0
		self.impuesto_total = 0
		self.subtotal = 0
		
		for registro in registros:
			if registro.precio:
				impuestos = self.env['tecnop.impuestos'].search([('id_impuesto', '=', registro.id)]) 
				for impuesto in impuestos:
					if impuesto.impuesto != False:
						registro.impuesto = (registro.precio * registro.cantidad) * impuesto.impuesto
						self.subtotal = (registro.precio * registro.cantidad) + self.subtotal
						self.impuesto_total = registro.impuesto  + self.impuesto_total
						self.total = self.subtotal + self.impuesto_total
						
				if registro.impuesto == 0:
					registro.impuesto = 0
					self.subtotal = (registro.precio * registro.cantidad) + self.subtotal
					self.impuesto_total += registro.impuesto 
					self.total = self.subtotal + self.impuesto_total

	@api.multi
	def calcular_cuenta(self):
		productos = self.env['tecnop.productos'].search([('id_producto', '=', self.id)])
		if productos:
			for producto in productos:
				cuentas = self.env['tecnop.cuentas'].search([('id', '=', producto.id_cuenta.id)])
				if cuentas:
					cuentas.saldo = cuentas.saldo - (producto.precio * producto.cantidad)

	@api.multi
	def buscar_usuario(self,dat):
		a = 0
		registros = self.env['res.users'].search([('code', '=', dat)])
		if registros:
			for registro in registros:
				registro.browse(self.env.uid)
				if registro.has_group('base.group_erp_manager'):
					a = 1
					break	
		return a

	@api.multi
	def escanear_codigo_qr(self):
		dat = ""
		#Inicializar la camara
		capture = cv2.VideoCapture(0)
		 
		#Cargar la fuente
		font = cv2.FONT_HERSHEY_SIMPLEX
				 
		while 1:
			#Capturar un frame
			val, frame = capture.read()
		 
			#Hay que comprobar que el frame sea valido
			if val:
				#Capturar un frame con la camara y guardar sus dimensiones
				frame_gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
				dimensiones = frame_gris.shape #'dimensiones' sera un array que contendra el alto, el ancho y los canales de la imagen en este orden.
		 
				#Convertir la imagen de OpenCV a una imagen que la libreria ZBAR pueda entender
				imagen_zbar = zbar.Image(dimensiones[1], dimensiones[0], 'Y800', frame_gris.tobytes())
		 
				#Construir un objeto de tipo scaner, que permitira escanear la imagen en busca de codigos QR
				escaner = zbar.ImageScanner()
		 
				#Escanear la imagen y guardar todos los codigos QR que se encuentren
				escaner.scan(imagen_zbar)
		 
		 
				for codigo_qr in imagen_zbar:
					loc = codigo_qr.location #Guardar las coordenadas de las esquinas
					dat = codigo_qr.data
					
					#Convertir las coordenadas de las cuatro esquinas a un array de numpy
					#Asi, lo podremos pasar como parametro a la funcion cv2.polylines para dibujar el contorno del codigo QR
					localizacion = np.array(loc, np.int32)
		 
					#Dibujar el contorno del codigo QR en azul sobre la imagen
					cv2.polylines(frame, [localizacion], True, (255,0,0), 2)
		 
					#Dibujar las cuatro esquinas del codigo QR
					cv2.circle(frame, loc[0], 3, (0,0,255), -1) #Rojo - esquina superior izquierda
					cv2.circle(frame, loc[1], 3, (0,255,255), -1) #Amarillo - esquina inferior izquierda
					cv2.circle(frame, loc[2], 3, (255,100,255), -1) #Rosa -esquina inferior derecha
			
					cv2.circle(frame, loc[3], 3, (0,255,0), -1) #Verde - esquina superior derecha
		 
		 
					#Buscar el centro del rectangulo del codigo QR
					cx = (loc[0][0]+loc[2][0])/2
					cy = (loc[0][1]+loc[2][1])/2
		 
					#Escribir el mensaje del codigo QR.
					cv2.putText(frame,dat,(cx,cy), font, 0.7,(255,255,255),2)
		 
					#Calcular el angulo de rotacion del codigo QR. Supondremos que el angulo es la pendiente de la recta que une el vertice loc[0] (rojo) con loc[3] (verde)
					vector_director = [loc[3][0]-loc[0][0], loc[3][1]-loc[0][1]]
					angulo = (np.arctan2(float(vector_director[1]),vector_director[0])*57.29)%360 #Calculo de la tangente y conversion de radianes a grados
					#Correccion debida al orden de las coordenadas en la pantalla
					angulo += -360
					angulo *= -1
		 
					#Escribir el angulo sobre la imagen con dos decimales
					cv2.putText(frame,str("%.2f" % angulo),(cx,cy+30), font, 0.7,(255,255,255),2)

				#Mostrar la imagen
				cv2.imshow('Imagen', frame)
				cv2.moveWindow('Imagen',250, 40)

			#Salir con 'ESC'
			k = cv2.waitKey(5) & 0xFF
			if k == 27:
				break
						
			if self.buscar_usuario(dat) == 1:
				self.unlink()
				break
				
		cv2.destroyAllWindows()

# Modelo de ejercicios fiscales
class ejer_fiscal(models.Model):
	_name = "tecnop.ejfiscal"
	_rec_name = "nombre"
	
	nombre = fields.Char('Ejercicio fiscal')
	codigo = fields.Char('Código', size=6)
	fecha_inicio = fields.Date('Fecha inicial')
	fecha_final = fields.Date('Fecha final')
	ids_periodos = fields.One2many('tecnop.periodos', 'id_periodo','Periodos')
	id_ef = fields.One2many('report.tecnop.reportes_w', 'ids_ej', 'Ejercicio fiscal')

	@api.multi
	def unlink(self):
		for ej_fiscal in self:
				raise except_orm('ERROR', 'No se puede eliminar un ejercicio fiscal ya que este guarda relacion con otros registros')
		return super(ejer_fiscal, self).unlink()
		
	@api.multi
	def buscar_usuario(self,dat):
		a = 0
		registros = self.env['res.users'].search([('code', '=', dat)])
		if registros:
			for registro in registros:
				registro.browse(self.env.uid)
				if registro.has_group('base.group_erp_manager'):
					a = 1
					break	
		return a

	@api.multi
	def escanear_codigo_qr(self):
		dat = ""
		#Inicializar la camara
		capture = cv2.VideoCapture(0)
		 
		#Cargar la fuente
		font = cv2.FONT_HERSHEY_SIMPLEX
				 
		while 1:
			#Capturar un frame
			val, frame = capture.read()
		 
			#Hay que comprobar que el frame sea valido
			if val:
				#Capturar un frame con la camara y guardar sus dimensiones
				frame_gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
				dimensiones = frame_gris.shape #'dimensiones' sera un array que contendra el alto, el ancho y los canales de la imagen en este orden.
		 
				#Convertir la imagen de OpenCV a una imagen que la libreria ZBAR pueda entender
				imagen_zbar = zbar.Image(dimensiones[1], dimensiones[0], 'Y800', frame_gris.tobytes())
		 
				#Construir un objeto de tipo scaner, que permitira escanear la imagen en busca de codigos QR
				escaner = zbar.ImageScanner()
		 
				#Escanear la imagen y guardar todos los codigos QR que se encuentren
				escaner.scan(imagen_zbar)
		 
		 
				for codigo_qr in imagen_zbar:
					loc = codigo_qr.location #Guardar las coordenadas de las esquinas
					dat = codigo_qr.data
					
					#Convertir las coordenadas de las cuatro esquinas a un array de numpy
					#Asi, lo podremos pasar como parametro a la funcion cv2.polylines para dibujar el contorno del codigo QR
					localizacion = np.array(loc, np.int32)
		 
					#Dibujar el contorno del codigo QR en azul sobre la imagen
					cv2.polylines(frame, [localizacion], True, (255,0,0), 2)
		 
					#Dibujar las cuatro esquinas del codigo QR
					cv2.circle(frame, loc[0], 3, (0,0,255), -1) #Rojo - esquina superior izquierda
					cv2.circle(frame, loc[1], 3, (0,255,255), -1) #Amarillo - esquina inferior izquierda
					cv2.circle(frame, loc[2], 3, (255,100,255), -1) #Rosa -esquina inferior derecha
			
					cv2.circle(frame, loc[3], 3, (0,255,0), -1) #Verde - esquina superior derecha
		 
		 
					#Buscar el centro del rectangulo del codigo QR
					cx = (loc[0][0]+loc[2][0])/2
					cy = (loc[0][1]+loc[2][1])/2
		 
					#Escribir el mensaje del codigo QR.
					cv2.putText(frame,dat,(cx,cy), font, 0.7,(255,255,255),2)
		 
					#Calcular el angulo de rotacion del codigo QR. Supondremos que el angulo es la pendiente de la recta que une el vertice loc[0] (rojo) con loc[3] (verde)
					vector_director = [loc[3][0]-loc[0][0], loc[3][1]-loc[0][1]]
					angulo = (np.arctan2(float(vector_director[1]),vector_director[0])*57.29)%360 #Calculo de la tangente y conversion de radianes a grados
					#Correccion debida al orden de las coordenadas en la pantalla
					angulo += -360
					angulo *= -1
		 
					#Escribir el angulo sobre la imagen con dos decimales
					cv2.putText(frame,str("%.2f" % angulo),(cx,cy+30), font, 0.7,(255,255,255),2)

				#Mostrar la imagen
				cv2.imshow('Imagen', frame)
				cv2.moveWindow('Imagen',250, 40)

			#Salir con 'ESC'
			k = cv2.waitKey(5) & 0xFF
			if k == 27:
				break
						
			if self.buscar_usuario(dat) == 1:
				self.unlink()
				break
				
		cv2.destroyAllWindows()

# Modelo de periodos
class periodos(models.Model):
	_name = "tecnop.periodos"
	_rec_name = "nombre"
	
	nombre = fields.Char('Nombre')
	codigo = fields.Char('Código')
	fecha_inicio = fields.Date('Fecha inicial')
	fecha_final = fields.Date('Fecha final')
	id_periodo = fields.Many2one('tecnop.ejfiscal', 'Ejercicio Fiscal')
	ids_periodos = fields.One2many('tecnop.asientos', 'id_periodo', 'Periodo')

	@api.multi
	def unlink(self):
		for per in self:
				raise except_orm('ERROR', 'No se puede eliminar un periodo ya que este guarda relacion con los ejercicios fiscales, entre otros')
		return super(periodos, self).unlink()

	@api.multi
	def buscar_usuario(self,dat):
		a = 0
		registros = self.env['res.users'].search([('code', '=', dat)])
		if registros:
			for registro in registros:
				registro.browse(self.env.uid)
				if registro.has_group('base.group_erp_manager'):
					a = 1
					break	
		return a

	@api.multi
	def escanear_codigo_qr(self):
		dat = ""
		#Inicializar la camara
		capture = cv2.VideoCapture(0)
		 
		#Cargar la fuente
		font = cv2.FONT_HERSHEY_SIMPLEX
				 
		while 1:
			#Capturar un frame
			val, frame = capture.read()
		 
			#Hay que comprobar que el frame sea valido
			if val:
				#Capturar un frame con la camara y guardar sus dimensiones
				frame_gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
				dimensiones = frame_gris.shape #'dimensiones' sera un array que contendra el alto, el ancho y los canales de la imagen en este orden.
		 
				#Convertir la imagen de OpenCV a una imagen que la libreria ZBAR pueda entender
				imagen_zbar = zbar.Image(dimensiones[1], dimensiones[0], 'Y800', frame_gris.tobytes())
		 
				#Construir un objeto de tipo scaner, que permitira escanear la imagen en busca de codigos QR
				escaner = zbar.ImageScanner()
		 
				#Escanear la imagen y guardar todos los codigos QR que se encuentren
				escaner.scan(imagen_zbar)
		 
		 
				for codigo_qr in imagen_zbar:
					loc = codigo_qr.location #Guardar las coordenadas de las esquinas
					dat = codigo_qr.data
					
					#Convertir las coordenadas de las cuatro esquinas a un array de numpy
					#Asi, lo podremos pasar como parametro a la funcion cv2.polylines para dibujar el contorno del codigo QR
					localizacion = np.array(loc, np.int32)
		 
					#Dibujar el contorno del codigo QR en azul sobre la imagen
					cv2.polylines(frame, [localizacion], True, (255,0,0), 2)
		 
					#Dibujar las cuatro esquinas del codigo QR
					cv2.circle(frame, loc[0], 3, (0,0,255), -1) #Rojo - esquina superior izquierda
					cv2.circle(frame, loc[1], 3, (0,255,255), -1) #Amarillo - esquina inferior izquierda
					cv2.circle(frame, loc[2], 3, (255,100,255), -1) #Rosa -esquina inferior derecha
			
					cv2.circle(frame, loc[3], 3, (0,255,0), -1) #Verde - esquina superior derecha
		 
		 
					#Buscar el centro del rectangulo del codigo QR
					cx = (loc[0][0]+loc[2][0])/2
					cy = (loc[0][1]+loc[2][1])/2
		 
					#Escribir el mensaje del codigo QR.
					cv2.putText(frame,dat,(cx,cy), font, 0.7,(255,255,255),2)
		 
					#Calcular el angulo de rotacion del codigo QR. Supondremos que el angulo es la pendiente de la recta que une el vertice loc[0] (rojo) con loc[3] (verde)
					vector_director = [loc[3][0]-loc[0][0], loc[3][1]-loc[0][1]]
					angulo = (np.arctan2(float(vector_director[1]),vector_director[0])*57.29)%360 #Calculo de la tangente y conversion de radianes a grados
					#Correccion debida al orden de las coordenadas en la pantalla
					angulo += -360
					angulo *= -1
		 
					#Escribir el angulo sobre la imagen con dos decimales
					cv2.putText(frame,str("%.2f" % angulo),(cx,cy+30), font, 0.7,(255,255,255),2)

				#Mostrar la imagen
				cv2.imshow('Imagen', frame)
				cv2.moveWindow('Imagen',250, 40)

			#Salir con 'ESC'
			k = cv2.waitKey(5) & 0xFF
			if k == 27:
				break
						
			if self.buscar_usuario(dat) == 1:
				self.unlink()
				break
				
		cv2.destroyAllWindows()

# Modelo de proveedores
class proveedores(models.Model):
	_name = "tecnop.proveedores"
	_rec_name = "proveedor"
	
	proveedor = fields.Char('Nombre', size=20)
	num_id = fields.Integer('RIF/Cédula', size=20)
	direccion = fields.Char('Dirección', size=20)
	telefono = fields.Integer('Teléfono', size=20)
	proveedor_id = fields.One2many('tecnop.recibos', 'num_recibo')

	@api.multi
	def buscar_usuario(self,dat):
		a = 0
		registros = self.env['res.users'].search([('code', '=', dat)])
		if registros:
			for registro in registros:
				registro.browse(self.env.uid)
				if registro.has_group('base.group_erp_manager'):
					a = 1
					break	
		return a

	@api.multi
	def escanear_codigo_qr(self):
		dat = ""
		#Inicializar la camara
		capture = cv2.VideoCapture(0)
		 
		#Cargar la fuente
		font = cv2.FONT_HERSHEY_SIMPLEX
				 
		while 1:
			#Capturar un frame
			val, frame = capture.read()
		 
			#Hay que comprobar que el frame sea valido
			if val:
				#Capturar un frame con la camara y guardar sus dimensiones
				frame_gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
				dimensiones = frame_gris.shape #'dimensiones' sera un array que contendra el alto, el ancho y los canales de la imagen en este orden.
		 
				#Convertir la imagen de OpenCV a una imagen que la libreria ZBAR pueda entender
				imagen_zbar = zbar.Image(dimensiones[1], dimensiones[0], 'Y800', frame_gris.tobytes())
		 
				#Construir un objeto de tipo scaner, que permitira escanear la imagen en busca de codigos QR
				escaner = zbar.ImageScanner()
		 
				#Escanear la imagen y guardar todos los codigos QR que se encuentren
				escaner.scan(imagen_zbar)
		 
		 
				for codigo_qr in imagen_zbar:
					loc = codigo_qr.location #Guardar las coordenadas de las esquinas
					dat = codigo_qr.data
					
					#Convertir las coordenadas de las cuatro esquinas a un array de numpy
					#Asi, lo podremos pasar como parametro a la funcion cv2.polylines para dibujar el contorno del codigo QR
					localizacion = np.array(loc, np.int32)
		 
					#Dibujar el contorno del codigo QR en azul sobre la imagen
					cv2.polylines(frame, [localizacion], True, (255,0,0), 2)
		 
					#Dibujar las cuatro esquinas del codigo QR
					cv2.circle(frame, loc[0], 3, (0,0,255), -1) #Rojo - esquina superior izquierda
					cv2.circle(frame, loc[1], 3, (0,255,255), -1) #Amarillo - esquina inferior izquierda
					cv2.circle(frame, loc[2], 3, (255,100,255), -1) #Rosa -esquina inferior derecha
			
					cv2.circle(frame, loc[3], 3, (0,255,0), -1) #Verde - esquina superior derecha
		 
		 
					#Buscar el centro del rectangulo del codigo QR
					cx = (loc[0][0]+loc[2][0])/2
					cy = (loc[0][1]+loc[2][1])/2
		 
					#Escribir el mensaje del codigo QR.
					cv2.putText(frame,dat,(cx,cy), font, 0.7,(255,255,255),2)
		 
					#Calcular el angulo de rotacion del codigo QR. Supondremos que el angulo es la pendiente de la recta que une el vertice loc[0] (rojo) con loc[3] (verde)
					vector_director = [loc[3][0]-loc[0][0], loc[3][1]-loc[0][1]]
					angulo = (np.arctan2(float(vector_director[1]),vector_director[0])*57.29)%360 #Calculo de la tangente y conversion de radianes a grados
					#Correccion debida al orden de las coordenadas en la pantalla
					angulo += -360
					angulo *= -1
		 
					#Escribir el angulo sobre la imagen con dos decimales
					cv2.putText(frame,str("%.2f" % angulo),(cx,cy+30), font, 0.7,(255,255,255),2)

				#Mostrar la imagen
				cv2.imshow('Imagen', frame)
				cv2.moveWindow('Imagen',250, 40)

			#Salir con 'ESC'
			k = cv2.waitKey(5) & 0xFF
			if k == 27:
				break
						
			if self.buscar_usuario(dat) == 1:
				self.unlink()
				break
				
		cv2.destroyAllWindows()

# Modelo de productos
class productos(models.Model):
	_name = "tecnop.productos"
	_rec_name = "nombre"
	
	nombre = fields.Char('Nombre', size=20, required=True)
	precio = fields.Float('Precio', size=20, required=True)
	impuesto = fields.Float('Impuesto', size=20, readonly=True)
	cantidad = fields.Float('Cantidad', size=20, required=True)
	descripcion = fields.Text('Descripcion', size=400)
	concepto = fields.Text('Concepto', size=400)
	id_producto = fields.Many2one('tecnop.recibos', 'num_recibo', ondelete='cascade')
	id_impuesto = fields.Many2one('tecnop.impuestos', 'Impuesto %', widget="selection")
	id_cuenta = fields.Many2one('tecnop.cuentas', 'Cuenta', domain=[('tipo_interno','!=','vista')], required=True, widget="selection")
	debe = fields.Float('Debe')
	haber = fields.Float('Haber')

# Modelo de impuestos
class impuestos(models.Model):
	_name = "tecnop.impuestos"
	_rec_name = "nombre"
	
	nombre = fields.Char('Impuesto')
	impuesto = fields.Float('Impuesto %', size=30, help="Añadir el impuesto en decimales")
	id_impuesto = fields.One2many('tecnop.productos', 'id_impuesto', 'Impuesto')
	id_cuenta = fields.Many2one('tecnop.cuentas', 'Cuenta', domain=[('tipo_interno','!=','vista')])

	@api.multi
	def buscar_usuario(self,dat):
		a = 0
		registros = self.env['res.users'].search([('code', '=', dat)])
		if registros:
			for registro in registros:
				registro.browse(self.env.uid)
				if registro.has_group('base.group_erp_manager'):
					a = 1
					break	
		return a

	@api.multi
	def escanear_codigo_qr(self):
		dat = ""
		#Inicializar la camara
		capture = cv2.VideoCapture(0)
		 
		#Cargar la fuente
		font = cv2.FONT_HERSHEY_SIMPLEX
				 
		while 1:
			#Capturar un frame
			val, frame = capture.read()
		 
			#Hay que comprobar que el frame sea valido
			if val:
				#Capturar un frame con la camara y guardar sus dimensiones
				frame_gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
				dimensiones = frame_gris.shape #'dimensiones' sera un array que contendra el alto, el ancho y los canales de la imagen en este orden.
		 
				#Convertir la imagen de OpenCV a una imagen que la libreria ZBAR pueda entender
				imagen_zbar = zbar.Image(dimensiones[1], dimensiones[0], 'Y800', frame_gris.tobytes())
		 
				#Construir un objeto de tipo scaner, que permitira escanear la imagen en busca de codigos QR
				escaner = zbar.ImageScanner()
		 
				#Escanear la imagen y guardar todos los codigos QR que se encuentren
				escaner.scan(imagen_zbar)
		 
		 
				for codigo_qr in imagen_zbar:
					loc = codigo_qr.location #Guardar las coordenadas de las esquinas
					dat = codigo_qr.data
					
					#Convertir las coordenadas de las cuatro esquinas a un array de numpy
					#Asi, lo podremos pasar como parametro a la funcion cv2.polylines para dibujar el contorno del codigo QR
					localizacion = np.array(loc, np.int32)
		 
					#Dibujar el contorno del codigo QR en azul sobre la imagen
					cv2.polylines(frame, [localizacion], True, (255,0,0), 2)
		 
					#Dibujar las cuatro esquinas del codigo QR
					cv2.circle(frame, loc[0], 3, (0,0,255), -1) #Rojo - esquina superior izquierda
					cv2.circle(frame, loc[1], 3, (0,255,255), -1) #Amarillo - esquina inferior izquierda
					cv2.circle(frame, loc[2], 3, (255,100,255), -1) #Rosa -esquina inferior derecha
			
					cv2.circle(frame, loc[3], 3, (0,255,0), -1) #Verde - esquina superior derecha
		 
		 
					#Buscar el centro del rectangulo del codigo QR
					cx = (loc[0][0]+loc[2][0])/2
					cy = (loc[0][1]+loc[2][1])/2
		 
					#Escribir el mensaje del codigo QR.
					cv2.putText(frame,dat,(cx,cy), font, 0.7,(255,255,255),2)
		 
					#Calcular el angulo de rotacion del codigo QR. Supondremos que el angulo es la pendiente de la recta que une el vertice loc[0] (rojo) con loc[3] (verde)
					vector_director = [loc[3][0]-loc[0][0], loc[3][1]-loc[0][1]]
					angulo = (np.arctan2(float(vector_director[1]),vector_director[0])*57.29)%360 #Calculo de la tangente y conversion de radianes a grados
					#Correccion debida al orden de las coordenadas en la pantalla
					angulo += -360
					angulo *= -1
		 
					#Escribir el angulo sobre la imagen con dos decimales
					cv2.putText(frame,str("%.2f" % angulo),(cx,cy+30), font, 0.7,(255,255,255),2)

				#Mostrar la imagen
				cv2.imshow('Imagen', frame)
				cv2.moveWindow('Imagen',250, 40)

			#Salir con 'ESC'
			k = cv2.waitKey(5) & 0xFF
			if k == 27:
				break
						
			if self.buscar_usuario(dat) == 1:
				self.unlink()
				break
				
		cv2.destroyAllWindows()

# Modelo de cuentas
class cuentas(models.Model):
	_name = "tecnop.cuentas"
	_rec_name = "nombre"
	_order = "codigo"
	
	codigo = fields.Char('Código de la cuenta', size=30)
	nombre = fields.Char('Nombre de la cuenta')
	debe = fields.Float('Debe')
	haber = fields.Float('Haber')
	saldo = fields.Float('Saldo')
	tipo_interno = fields.Selection([
		('vista','Vista'),
		('regular','Regular'),
		('cobrar','A cobrar'),
		('pagar','A pagar'),
		('liquidez','Liquidez'),
		('consolidacion','Consolidación'),
		('cierre','Cierre')],
	'Tipo interno')
	
	ids_cuentas = fields.One2many('tecnop.recibos', 'id_cuenta', 'Cuenta')
	ids_cuentas = fields.One2many('tecnop.impuestos', 'id_cuenta', 'Cuenta')
	ids_cuentas = fields.One2many('tecnop.apuntes', 'id_cuenta', 'Cuenta')
	padre_id = fields.Many2one('tecnop.cuentas', 'Padre', domain=[('tipo_interno','=','vista')])
	ids_hijo_padre = fields.One2many('tecnop.cuentas', 'padre_id', 'Hijo')
	idPrueba = fields.Many2one('tecnop.prueba', 'Cuenta')
	
	@api.multi
	def recorrer_cuentas(self):
		cuentas = self.env['tecnop.cuentas'].search([('id', '!=', None)])
		
		for cuenta in cuentas:
			if cuenta.tipo_interno == 'vista':
				cuenta.saldo = 0
				cuenta.haber = 0
				cuenta.debe = 0
		
		for cuenta in cuentas:
			if cuenta.ids_hijo_padre != None and cuenta.tipo_interno == 'vista':
				if cuenta:
					for hijos in cuenta.ids_hijo_padre:
						if hijos.tipo_interno != 'vista' and cuenta.tipo_interno == 'vista':
							cuenta.saldo += hijos.saldo
							cuenta.debe += hijos.debe
							cuenta.haber += hijos.haber
							
		for cuenta in cuentas:
			if cuenta.ids_hijo_padre != None and cuenta.tipo_interno == 'vista':
				if cuenta:
					for hijos in cuenta.ids_hijo_padre:
						if hijos.tipo_interno == 'vista' and cuenta.tipo_interno == 'vista':
							if cuenta.padre_id.nombre != 'Activo':
								cuenta.saldo += hijos.saldo
								cuenta.debe += hijos.debe
								cuenta.haber += hijos.haber
								
		for cuenta in cuentas:
			if cuenta.ids_hijo_padre != None and cuenta.tipo_interno == 'vista':
				for hijos in cuenta.ids_hijo_padre:
					if hijos.tipo_interno == 'vista':
						if cuenta.padre_id.nombre == 'Activo' or cuenta.padre_id.nombre == 'Pasivo' or cuenta.padre_id.nombre == 'Patrimonio' or cuenta.padre_id.nombre == 'Ingresos Brutos' or cuenta.padre_id.nombre == 'Costos de Ventas' or cuenta.padre_id.nombre == 'Gastos Operacionales' or cuenta.padre_id.nombre == 'Otros Egresos' or cuenta.padre_id.nombre == 'Anticipos Societarios' or cuenta.padre_id.nombre == 'Cuentas de Orden':
							cuenta.saldo += hijos.saldo
							cuenta.debe += hijos.debe
							cuenta.haber += hijos.haber
							
		for cuenta in cuentas:
			if cuenta.ids_hijo_padre != None and cuenta.tipo_interno == 'vista':
				for hijos in cuenta.ids_hijo_padre:
					if cuenta.padre_id.codigo == '0':
						cuenta.saldo += hijos.saldo
						cuenta.debe += hijos.debe
						cuenta.haber += hijos.haber
					
		for cuenta in cuentas:
			if cuenta.codigo == '0':
				for hijos in cuenta.ids_hijo_padre:
					cuenta.saldo += hijos.saldo
					cuenta.debe += hijos.debe
					cuenta.haber += hijos.haber
			break
			
	@api.multi
	def calcular_cuenta(self):
		cuentas = self.env['tecnop.cuentas'].search([('id', '!=', None)])
		for cuenta in cuentas:
			cuenta.debe = 0
			cuenta.haber = 0
			cuenta.saldo = 0

	@api.multi
	def buscar_usuario(self,dat):
		a = 0
		registros = self.env['res.users'].search([('code', '=', dat)])
		if registros:
			for registro in registros:
				registro.browse(self.env.uid)
				if registro.has_group('base.group_erp_manager'):
					a = 1
					break	
		return a

	@api.multi
	def escanear_codigo_qr(self):
		dat = ""
		#Inicializar la camara
		capture = cv2.VideoCapture(0)
		 
		#Cargar la fuente
		font = cv2.FONT_HERSHEY_SIMPLEX
				 
		while 1:
			#Capturar un frame
			val, frame = capture.read()
		 
			#Hay que comprobar que el frame sea valido
			if val:
				#Capturar un frame con la camara y guardar sus dimensiones
				frame_gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
				dimensiones = frame_gris.shape #'dimensiones' sera un array que contendra el alto, el ancho y los canales de la imagen en este orden.
		 
				#Convertir la imagen de OpenCV a una imagen que la libreria ZBAR pueda entender
				imagen_zbar = zbar.Image(dimensiones[1], dimensiones[0], 'Y800', frame_gris.tobytes())
		 
				#Construir un objeto de tipo scaner, que permitira escanear la imagen en busca de codigos QR
				escaner = zbar.ImageScanner()
		 
				#Escanear la imagen y guardar todos los codigos QR que se encuentren
				escaner.scan(imagen_zbar)
		 
		 
				for codigo_qr in imagen_zbar:
					loc = codigo_qr.location #Guardar las coordenadas de las esquinas
					dat = codigo_qr.data
					
					#Convertir las coordenadas de las cuatro esquinas a un array de numpy
					#Asi, lo podremos pasar como parametro a la funcion cv2.polylines para dibujar el contorno del codigo QR
					localizacion = np.array(loc, np.int32)
		 
					#Dibujar el contorno del codigo QR en azul sobre la imagen
					cv2.polylines(frame, [localizacion], True, (255,0,0), 2)
		 
					#Dibujar las cuatro esquinas del codigo QR
					cv2.circle(frame, loc[0], 3, (0,0,255), -1) #Rojo - esquina superior izquierda
					cv2.circle(frame, loc[1], 3, (0,255,255), -1) #Amarillo - esquina inferior izquierda
					cv2.circle(frame, loc[2], 3, (255,100,255), -1) #Rosa -esquina inferior derecha
			
					cv2.circle(frame, loc[3], 3, (0,255,0), -1) #Verde - esquina superior derecha
		 
		 
					#Buscar el centro del rectangulo del codigo QR
					cx = (loc[0][0]+loc[2][0])/2
					cy = (loc[0][1]+loc[2][1])/2
		 
					#Escribir el mensaje del codigo QR.
					cv2.putText(frame,dat,(cx,cy), font, 0.7,(255,255,255),2)
		 
					#Calcular el angulo de rotacion del codigo QR. Supondremos que el angulo es la pendiente de la recta que une el vertice loc[0] (rojo) con loc[3] (verde)
					vector_director = [loc[3][0]-loc[0][0], loc[3][1]-loc[0][1]]
					angulo = (np.arctan2(float(vector_director[1]),vector_director[0])*57.29)%360 #Calculo de la tangente y conversion de radianes a grados
					#Correccion debida al orden de las coordenadas en la pantalla
					angulo += -360
					angulo *= -1
		 
					#Escribir el angulo sobre la imagen con dos decimales
					cv2.putText(frame,str("%.2f" % angulo),(cx,cy+30), font, 0.7,(255,255,255),2)

				#Mostrar la imagen
				cv2.imshow('Imagen', frame)
				cv2.moveWindow('Imagen',250, 40)

			#Salir con 'ESC'
			k = cv2.waitKey(5) & 0xFF
			if k == 27:
				break
						
			if self.buscar_usuario(dat) == 1:
				self.unlink()
				break
				
		cv2.destroyAllWindows()

class confirmacion(models.TransientModel):
	_name = "confirmacion"
	
	confirmar = fields.Boolean('Confirmar', required=True, default=False)
	
	@api.multi
	def empezarVali(self):
		registro = ids
		return self.env['tecnop.recibos'].validar(registro)
		
class reportes(models.TransientModel):
	_name = "report.tecnop.reportes_w"
	
	ids_ej = fields.Many2one('tecnop.ejfiscal', 'Ejercicio fiscal', required=True)
	
	@api.multi
	def render_html(self, data=None):
		report_obj = self.env['report']
		report = report_obj._get_report_from_name('tecnop.reportes_w')
		docargs = {
			'doc_ids': self._ids,
			'doc_model': report.model,
			'docs': self,
			'cuentas': self.obtenerCuentas(),
			'asientos': self.obtenerAsientos(self.ids_ej),
			'apuntes': self.obtenerApuntes(),
			'fiscal': self.ids_ej,
			'landscape': True
			}
		return report_obj.render('tecnop.reportes_w', docargs)
		
	@api.multi
	def view_report_button(self):
		return {
		'type': 'ir.actions.report.xml',
		'report_name': 'tecnop.reportes_w',
		'report_type': "qweb-pdf",
		} 
	
	@api.multi
	def obtenerAsientos(self, ids_ej):
		asientos = self.env['tecnop.asientos'].search([('id_periodo.id_periodo.fecha_inicio', '=', ids_ej.fecha_inicio) and ('id_periodo.id_periodo.fecha_final', '=', ids_ej.fecha_final)])
		return asientos
		
	@api.multi
	def obtenerApuntes(self):
		apuntes = self.env['tecnop.apuntes'].search([('id', '!=', None)])
		return apuntes
		
	@api.multi
	def obtenerCuentas(self):
		cuentas = self.env['tecnop.cuentas'].search([('tipo_interno', '!=', 'vista')])
		return cuentas
		
class reportes_balance_sumas_y_saldos(models.TransientModel):
	_name = "report.tecnop.sumas_y_saldos"
	
	ids_ej = fields.Many2one('tecnop.ejfiscal', 'Ejercicio fiscal', required=True)
	
	@api.multi
	def render_html(self, data=None):
		report_obj = self.env['report']
		report = report_obj._get_report_from_name('tecnop.sumas_y_saldos')
		print('vamos bien')
		print('vamos bien')
		print('vamos bien')
		print('vamos bien')
		print('vamos bien')
		docargs = {
			'doc_ids': self._ids,
			'doc_model': report.model,
			'docs': self,
			'cuentas': self.obtenerCuentas(),
			'asientos': self.obtenerAsientos(self.ids_ej),
			'fiscal': self.ids_ej,
			#'landscape': True
			}
		return report_obj.render('tecnop.sumas_y_saldos', docargs)
		
	@api.multi
	def view_report_button(self):
		return {
		'type': 'ir.actions.report.xml',
		'report_name': 'tecnop.sumas_y_saldos',
		'report_type': "qweb-pdf",
		}
		
	@api.multi
	def obtenerCuentas(self):
		cuentas = self.env['tecnop.cuentas'].search([('id', '!=', None)])
		return cuentas
		
	@api.multi
	def obtenerAsientos(self, ids_ej):
		asientos = self.env['tecnop.asientos'].search([('id_periodo.id_periodo.fecha_inicio', '=', ids_ej.fecha_inicio) and ('id_periodo.id_periodo.fecha_final', '=', ids_ej.fecha_final)])
		return asientos
		
class reportes_perdidas_y_ganancias(models.TransientModel):
	_name = "report.tecnop.perdidas_y_ganancias"
	
	#ids_ej = fields.Many2one('tecnop.ejfiscal', 'Ejercicio fiscal', required=True)
	
	@api.multi
	def render_html(self, data=None):
		report_obj = self.env['report']
		report = report_obj._get_report_from_name('tecnop.perdidas_y_ganancias')
		docargs = {
			'doc_ids': self._ids,
			'doc_model': report.model,
			'docs': self,
		#	'cuentas': self.obtenerCuentas(),
		#	'asientos': self.obtenerAsientos(self.ids_ej),
		#	'apuntes': self.obtenerApuntes(),
		#	'fiscal': self.ids_ej,
			'landscape': True
			}
		return report_obj.render('tecnop.perdidas_y_ganancias', docargs)
		
	@api.multi
	def view_report_button(self):
		return {
		'type': 'ir.actions.report.xml',
		'report_name': 'tecnop.perdidas_y_ganancias',
		'report_type': "qweb-pdf",
		}
"""
class reporte_recibos(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context):
		super(reporte_recibos, self).__init__(cr, uid, name, context)
		
class reporte_movimientos(models.AbstractModel):
	_name="report.tecnop.movimientos"
	_inherit="report.abstract_report"
	_template="tecnop.movimientos"
	_wrapped_report_class=reporte_recibos

class reportes_parser(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context):
		super(reportes_parser, self).__init__(cr, uid, name, context)
		self.localcontext.update({
		})
		
class reporte_modelo_impresion(models.AbstractModel):
	_name = 'report.tecnop.reportes'
	_inherit = 'report.abstract_report'
	_template = 'tecnop.reportes'
	_wrapped_report_class = reportes_parser
"""

