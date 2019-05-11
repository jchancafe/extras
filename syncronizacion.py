# -*- coding: utf-8 -*-
from odoo import api, fields, models
from contextlib import closing
from datetime import datetime
import json
import cx_Oracle
from cx_Oracle import Error

class SyncDataIn(models.Model):
    _name = 'sync.data.in'
    _order = 'fecha_proceso'

    name = fields.Char('Numero de Transaccion')
    fecha_proceso = fields.Datetime('Fecha proceso')
    tipo = fields.Selection([('I', 'Ingreso'), ('S','Salida')], 'tipo de proceso')
    datas_json = fields.Text("JSON Data", readonly=True)

    def registrar_documento(self, item):
        REGISTRO_TERMINADO = 'T'

        existe_error = False
        cabecera_id = item.get('id')
        partner_id = self.obtener_receptor(item.get('receptor'), item.get('id'))

        if not partner_id:
            existe_error = True
            str_error = 'No existe cliente'
            self.registrar_error_proceso(str_error, cabecera_id)

        data_documento = item.get('documento')
        existe_documento = self.existe_registro(data_documento)

        equipo_venta_id = self.obtener_canal_venta(item.get('equipo_venta'))

        if existe_documento:
            existe_error = True
            str_error = 'Documento ya registrado'
            self.registrar_error_proceso(str_error, cabecera_id)

        journal_id = self.env['account.journal'].search([('pe_invoice_code', '=', data_documento.get('codigo_tipo_documento'))])

        if not journal_id:
            existe_error = True
            str_error = 'No existe Journal'
            self.registrar_error_proceso(str_error, cabecera_id)

        date_invoice = datetime.strptime(data_documento.get('fecha_emision'), '%Y-%m-%d').date()
        today = fields.Date.context_today(self, datetime.now())
        days = datetime.strptime(today, '%Y-%m-%d').date() - date_invoice
        if days.days > 6 or days.days < 0:
            existe_error = True
            str_error = 'La fecha de emision no puede ser menor a 6 dias de hoy ni mayor a la fecha de hoy.'
            self.registrar_error_proceso(str_error, cabecera_id)

        if not existe_error:
            nota_cred_deb = False
            inv = {
                'partner_id': partner_id.id,
                'partner_shipping_id': partner_id.id,
                'date_invoice': data_documento.get('fecha_emision'),
                'date_due': data_documento.get('fecha_vencimiento'),
                'type' : data_documento.get('tipo'),
                'journal_id': journal_id.id,
                'cabecera_id': cabecera_id,
                'team_id': equipo_venta_id.id
            }
            invoice_id = self.env['account.invoice'].create(inv)

            existe_error = self.registrar_detalle_documento(item.get('detalle_docuento'), invoice_id)
            #if existe_error:
            #    print('borrando invoice', invoice_id.id)
            #    invoice_id.unlink()

            if not existe_error:
                invoice_id.write({
                    'number': data_documento.get('correlativo_documento'),
                    'move_name': data_documento.get('correlativo_documento'),
                })

                invoice_id.compute_taxes()
                invoice_id.action_invoice_open()
        return existe_error

    def obtener_canal_venta(self, equipo_venta):
        nombre_equipo_venta = equipo_venta.get('nombre_equipo_venta')
        equipo_venta_id = self.env['crm.team'].search([('name','=', nombre_equipo_venta)])
        if not equipo_venta_id:
            equipo_venta_id = self.env['crm.team'].create({'name':nombre_equipo_venta, 'team_type': 'sales'})

        return equipo_venta_id

    def obtener_producto_servicio(self, detalle):
        TYPE2TIPOPRODUCTO = {'SERVICES': 'service', 'PRODUCT': 'product'}
        tipo = detalle.get('tipo')
        codigo_producto = detalle.get('codigo_producto')

        product_id = self.env['product.product'].search([('default_code', '=', codigo_producto)])

        if product_id:
            product_id = product_id[0]
        else:
            company_id = self.env.user.company_id
            if tipo == 'PRODUCT':
                product_id = company_id.product_varios_id
            if tipo == 'SERVICES':
                product_id = company_id.service_varios_id

            nombre_producto = detalle.get('descripcion_producto')
            print('nombre_producto:', nombre_producto)

            #buscando product_template
            product_template_id = self.env['product.template'].search([('type', '=', tipo),('default_code', '=', codigo_producto)])

            if not product_template_id:
                val_producto = {
                    'name': detalle.get('descripcion_producto'),
                    'type': TYPE2TIPOPRODUCTO[tipo],
                    'uom_id': product_id.uom_id.id,
                    'uom_po_id': product_id.uom_po_id.id,
                    'default_code': codigo_producto,
                    #'categ_id': product_id.categ_id.id,
                    'list_price': product_id.list_price,
                    'standard_price': product_id.standard_price,
                    'taxes_id': [(6, 0, [product_id.taxes_id.id])],
                    'supplier_taxes_id': [(6, 0, [product_id.supplier_taxes_id.id])],
                    'invoice_policy': product_id.invoice_policy
                }
                product_template_id = self.env['product.template'].create(val_producto)

            #creando producto.
            val_producto = {
                'description': detalle.get('descripcion_producto'),
                'name': detalle.get('descripcion_producto'),
                #'categ_id': product_template_id.id,
                'default_code': codigo_producto,
                #'categ_id': product_id.categ_id.id,
                'list_price': product_id.list_price,
                'invoice_policy': product_id.invoice_policy
            }
            product_id = self.env['product.product'].create(val_producto)

            #except:
            #    pass
        print("obtener_producto_servicio product_id:", product_id)
        return product_id

    def registrar_detalle_documento(self, detalle_item, invoice_id):
        existe_error = False
        for detalle in detalle_item:
            cabecera_id = detalle.get('id')

            #Obtencion del producto/servicio
            product_id = self.obtener_producto_servicio(detalle)
            print("product_id:", product_id)

            #Obtener impuesto
            porc_tax = detalle.get('porcentaje_impuesto')
            tax_id = self.env['account.tax'].search([('amount', '=', float(porc_tax)), ('type_tax_use', '=', 'sale')])

            if not tax_id:
                existe_error = True
                str_error = 'No existe Impuesto'
                self.registrar_error_proceso(str_error, cabecera_id)

            #Obtener medida
            if not product_id.uom_id:
                existe_error = True
                str_error = 'No existe Medida'
                self.registrar_error_proceso(str_error, cabecera_id)


            if not invoice_id.journal_id:
                existe_error = True
                str_error = 'No existe Diario'
                self.registrar_error_proceso(str_error, cabecera_id)

            if not invoice_id.journal_id.default_debit_account_id:
                existe_error = True
                str_error = 'No existe Cuenta'
                self.registrar_error_proceso(str_error, cabecera_id)

            #registro de linea
            if not existe_error:
                self.env['account.invoice.line'].create({
                    'invoice_id': invoice_id.id,
                    'discount' : detalle.get('porcentaje_descuento'),
                    'name' : detalle.get('codigo_producto') + '-' + detalle.get('descripcion_producto'),
                    'quantity': detalle.get('numero_item'),
                    'invoice_line_tax_ids': [(6, 0, [tax_id.id])],
                    'pe_affectation_code': '10',
                    'uom_id': product_id.uom_id.id,
                    'price_unit': detalle.get('precio_unitario'),
                    'account_id': invoice_id.journal_id.default_debit_account_id.id,
                    'product_id': product_id.id,
                    'detalle_id': detalle.get('detalle_id')
                })
        return existe_error

    def obtener_receptor(self, data_receptor, cabecera_id):
        doc_type = data_receptor.get('tipo_documento')
        numero_documento = data_receptor.get('numero_documento')
        nombre = data_receptor.get('razon_social')
        cliente_id = False

        cliente_id = self.env['res.partner'].search([('doc_type', '=', doc_type),('doc_number', '=', numero_documento)])
        if not cliente_id:
            cliente_id =self.env['res.partner'].create({
                'doc_type': doc_type,
                'doc_number': numero_documento,
                'name': nombre
            })

            existe_error = False
            if doc_type == '1':
                company_id = self.env.user.company_id
                if len(numero_documento) != 8:
                    existe_error = True
                    str_error = 'El DNI no es correcto'
                    self.registrar_advertencia_proceso(str_error, cabecera_id)
                if not existe_error:
                    respuesta = cliente_id.buscar_dni(numero_documento.strip())
                    if not respuesta or respuesta['detail'] == 'Not found.':
                        existe_error = True
                        str_error = 'El Numero de DNI ingresado es incorrecto o no existe'
                        self.registrar_advertencia_proceso(str_error, cabecera_id)

                if existe_error and not company_id.anonymous_id:
                    self.registrar_error_proceso(str_error, cabecera_id)
                if existe_error and company_id.anonymous_id:
                    cliente_id = company_id.anonymous_id
            if not existe_error:
                cliente_id.update_document()

        return cliente_id

    def procesar(self):
        REGISTRO_PENDIENTE = 'P'
        data_json = self.datas_json
        data_json = json.loads(data_json)
        for item in data_json:
            existe_error = self.registrar_documento(item)
            if not existe_error:
                sql_update = ("""UPDATE CLI_DOCUMENTO SET ESTADO_PROCESO = '%s' where ID_DOCUMENTO_FAC = %s """%(REGISTRO_PENDIENTE, item.get('id')))
                self.ejecutar_script(sql_update)

        self.fecha_proceso = fields.Date.context_today(self, datetime.now())

    def validar_documento_receptor(self, datos_receptor = {}):
        if not datos_receptor:
            datos_partner = self.env['res.partner'].browser([('doc_type', datos_receptor.get('tipo_documento')), ('doc_number', datos_receptor.get('numero_documento'))])
            if datos_partner:
                return datos_partner.id
            else:
                return -1

    def registrar_advertencia_proceso(self, detalle_error, id_cabecera):
        REGISTRO_ERROR = 'A'
        sql_update = ("""
            UPDATE CLI_DOCUMENTO SET DESCRIPCION_VALIDACION = substr(DESCRIPCION_VALIDACION|| ' '  || '%s', 0, 50), ESTADO_PROCESO = '%s' WHERE ID_DOCUMENTO_FAC = %s
        """)%(detalle_error, REGISTRO_ERROR, id_cabecera)

        self.ejecutar_script(sql_update)

    def registrar_error_proceso(self, detalle_error, id_cabecera):
        REGISTRO_ERROR = 'E'
        sql_update = ("""
            UPDATE CLI_DOCUMENTO SET DESCRIPCION_VALIDACION = substr(DESCRIPCION_VALIDACION|| ' '  || '%s', 0, 50), ESTADO_PROCESO = '%s' WHERE ID_DOCUMENTO_FAC = %s
        """)%(detalle_error, REGISTRO_ERROR, id_cabecera)

        self.ejecutar_script(sql_update)

    def existe_registro(self, data_documento):
        invoice_id = self.env['account.invoice'].search([('number', '=', data_documento.get('correlativo_documento'))])
        return invoice_id

    def select_detalle_in(self, id_cabecera):
        sql_select = ("""
            SELECT 
                NULL AS ID_DOCUMENTO_DETALLE,
                ID_DOCUMENTO_FAC,
                COD_PRODUCTO,
                DESCRIPCION,
                CANTIDAD,
                UNIDAD_MEDIDA,
                PRECIO_VENTA,
                CODIGO_IMPUESTO,
                MONTO_BASE,
                MONTO_IMPUESTO,
                PORCENTAJE, 
                TIPO_PRODUCTO,
                MONTO_DESCUENTO,
                FACTOR_DESCUENTO*100 as FACTOR_DESCUENTO,
                VALOR_UNITARIO
            FROM VW_DETALLE
            WHERE ID_DOCUMENTO_FAC = %s
            """)%(id_cabecera)

        registros = self.ejecutar_script(sql_select)
        registro = {}
        lista_id_procesado = []
        lista_registro = []
        if registros is not None and len(registros) > 0:
            for r in registros:
                r = list(r)
                id_detalle = r[0]
                id_cabecera = r[1]
                codigo_producto = r[2]
                descripcion_producto = r[3]
                numero_item = r[4]
                unidad_medida = r[5]
                precio_venta = r[6]
                codigo_impuesto = r[7]
                monto_base_impuesto = r[8]
                monto_impuesto = r[9]
                porcentaje_impuesto = r[10]
                tipo = r[11]
                descuento = r[12]
                porcentaje_descuento = r[13]
                precio_unitario = r[14]

                lista_id_procesado.append(id_detalle)
                detalle = {
                    'id': id_cabecera,
                    'id_detalle': id_detalle,
                    'codigo_producto': codigo_producto,
                    'descripcion_producto': descripcion_producto,
                    'numero_item': numero_item,
                    'unidad_medida': unidad_medida,
                    'precio_unitario': precio_unitario,
                    'codigo_impuesto': codigo_impuesto,
                    'monto_base_impuesto': monto_base_impuesto,
                    'monto_impuesto': monto_impuesto,
                    'porcentaje_impuesto': porcentaje_impuesto,
                    'tipo': tipo,
                    'descuento': descuento,
                    'porcentaje_descuento': porcentaje_descuento
                }

                #print("cabecera: ", detalle)

                lista_registro.append(detalle)

        return lista_registro

    def select_automatic_in(self):
        TYPE2JOURNAL = {'01':'out_invoice',
                        '03':'out_invoice',
                        '07':'out_refund',
                        '08':'out_invoice'}
        REGISTRO_NUEVO = 'N'

        sql_select = ("""
        SELECT 
            ID_DOCUMENTO_FAC, 
            TIPO_DOC_ENTIDAD, 
            NUM_DOC_IDENTIDAD, 
            RAZON_SOCIAL, 
            DIRECCION, 
            SUBSTR(TIPO_DOC_IDEN, 2, 1) AS TIPO_DOC_IDEN, 
            NUM_DOC_IDE, 
            APELLIDOS,
            DIRECCION_CLIENTE,
            SERIE, 
            NUMERACION,
            TO_CHAR(FECHA, 'YYYY-MM-DD') AS FECHA,
            CODIGO_TIPO_DOC,
            TIPO_MONEDA,
            TO_CHAR(FECHA_VENCIMIENTO, 'YYYY-MM-DD') AS FECHA_VENCIMIENTO, 
            TOTAL_VALOR_VENTAS,
            TIPO_COMPROBANTE, 
            NUMERO_OTRO_DOC,
            CODIGO_MOTIVO_GENE,
            NULL AS DESCRIPCION_MOT_NC_ND,
            ID_BODEGA, 
            NOMBRE_BODEGA
        FROM VW_CABECERA
          WHERE ESTADO_PROCESO = '%s' """%REGISTRO_NUEVO)

        registros = self.ejecutar_script(sql_select)

        registro = {}
        lista_id_procesado = []
        lista_registro = []
        if registros is not None and len(registros) > 0:
            for r in registros:
                r = list(r)
                p_id = r[0]

                emisor_tipo_documento = r[1]
                emisor_numero_documento =  r[2]
                emisor_razon_social = r[3]
                emisor_direccion = r[4]

                receptor_tipo_documento = r[5]
                receptor_numero_documento = r[6]
                receptor_razon_social = r[7]
                receptor_direccion = r[8]

                documento_serie_documento = r[9]
                documento_numero_documento = r[10]
                documento_fecha_emision = r[11]
                documento_tipo_documento = r[12]
                documento_codigo_moneda = r[13]
                documento_fecha_vencimiento = r[14]
                documento_importe_total = r[15]

                id_equipo_venta = r[20]
                nombre_equipo_venta = r[21]

                p_estado = 'N' #r[20]
                lista_id_procesado.append(p_id)
                type = TYPE2JOURNAL[documento_tipo_documento]
                registro = {
                    'id': p_id,
                    'emisor': {
                        'tipo_documento': emisor_tipo_documento,
                        'numero_documento': emisor_numero_documento,
                        'razon_social': emisor_razon_social,
                        'direccion': emisor_direccion,
                    },
                    'receptor': {
                        'tipo_documento': receptor_tipo_documento,
                        'numero_documento': receptor_numero_documento,
                        'razon_social': receptor_razon_social,
                        'direccion': receptor_direccion,
                    },
                    'documento': {
                        'serie_documento': documento_serie_documento,
                        'numero_documento': documento_numero_documento,
                        'correlativo_documento': (str(documento_serie_documento)+'-'+str(documento_numero_documento)),
                        'fecha_emision': documento_fecha_emision,
                        'codigo_tipo_documento': documento_tipo_documento,
                        'codigo_moneda': documento_codigo_moneda,
                        'fecha_vencimiento': documento_fecha_vencimiento,
                        'importe_total': documento_importe_total,
                        'tipo': type
                    },
                    'equipo_venta':{
                        'id_equipo_venta': id_equipo_venta,
                        'nombre_equipo_venta': nombre_equipo_venta
                    },
                    'nota_credito': {},
                    'nota_debito': {},
                    'detalle_docuento' : [],
                    'estado': p_estado
                }
                detalle_documento = self.select_detalle_in(p_id)

                if detalle_documento:
                    registro['detalle_docuento'] = detalle_documento

                lista_registro.append(registro)

            record = self.with_context(tz="America/Lima")
            fecha_actual = fields.Datetime.context_timestamp(record, datetime.now())
            local_date = datetime.strptime(fecha_actual.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S").date().strftime("%Y-%m-%d")
            reg_in = {
                'name': self.env['ir.sequence'].with_context(ir_sequence_date=local_date).next_by_code('sync.data.in'),
                'tipo': 'I',
                'datas_json' : str(json.dumps(lista_registro))
            }

            registro_id = self.env['sync.data.in'].create(reg_in)
            registro_id.procesar()


    def select_automatic_out(self):
        REGISTRO_PENDIENTE = 'P'
        REGISTRO_TERMINADO = 'T'
        sql_select = """
            SELECT ID_DOCUMENTO_FAC FROM CLI_DOCUMENTO WHERE ESTADO_PROCESO = '%s'
        """%(REGISTRO_PENDIENTE)
        registros = self.ejecutar_script(sql_select)
        if registros is not None and len(registros) > 0:
            for registro in registros:
                cabecera_id = registro[0]
                invoice_ids = self.env['account.invoice'].search([('cabecera_id', '=', cabecera_id)])

                for invoice_id in invoice_ids:
                    pe_response = ''
                    if invoice_id.pe_response:
                        pe_response = invoice_id.pe_response[:49] or ''
                    if invoice_id.pe_digest:
                        sql_update = """
                            UPDATE CLI_DOCUMENTO SET CODIGO_HASH = '%s', DESCRIPCION_VALIDACION = '%s', ESTADO_PROCESO = '%s', FECHA_PROCESO = SYSDATE WHERE ID_DOCUMENTO_FAC = %s 
                        """%(invoice_id.pe_digest, pe_response, REGISTRO_TERMINADO, cabecera_id)

                        self.ejecutar_script(sql_update)

    def select_automatic_annul(self):
        REGISTRO_ANULADO = 'A'
        REGISTRO_TERMINADO = 'T'

        sql_select = """
                    SELECT ID_DOCUMENTO_FAC FROM CLI_DOCUMENTO WHERE ESTADO_PROCESO = '%s'
                """ % (REGISTRO_ANULADO)
        registros = self.ejecutar_script(sql_select)

        if registros is not None and len(registros) > 0:
            for registro in registros:
                registro = list(registro)
                cabecera_id = registro[0]
                invoice_ids = self.env['account.invoice'].search([('cabecera_id', '=', cabecera_id)])
                for invoice_id in invoice_ids:
                    invoice_id.action_invoice_annul()
                    sql_update = """UPDATE CLI_DOCUMENTO SET ESTADO_PROCESO = '%s' where ID_DOCUMENTO_FAC = %s """ \
                                 % (REGISTRO_TERMINADO, cabecera_id)
                    self.ejecutar_script(sql_update)

    def ejecutar_script(self, sql):
        company_id = self.env.user.company_id
        username = company_id.sync_data_server_id.usuario
        clave = company_id.sync_data_server_id.password
        puerto = company_id.sync_data_server_id.puerto
        nombre_servicio = company_id.sync_data_server_id.nombre_servicio
        servidor = company_id.sync_data_server_id.servidor

        if username and clave and puerto and nombre_servicio and servidor:
            try:
                dsn_tns = cx_Oracle.makedsn(servidor, puerto, service_name=nombre_servicio)
                conexion = cx_Oracle.connect(user=username, password=clave, dsn=dsn_tns)
                cursor = conexion.cursor()
                sql_alter_session = """alter session set nls_date_format ='DD-MM-RR'"""
                cursor.execute(sql_alter_session)
                cursor.execute(sql)

                if sql.upper().find('UPDATE') != -1:
                    conexion.commit()
                if sql.upper().find('SELECT') != -1:
                    result = cursor.fetchall()
                    #print("sql:", sql)
                    #print("longitud de datos: %s"%result)
                    return result
            except:
                print("error en conexion")
                return None
        else:
            print('sin conexion')

    def ejecutar_script_13(self, sql):
        company_id = self.env['res.company'].search([])[0]
        username = company_id.sync_data_server_id.usuario
        clave = company_id.sync_data_server_id.password
        puerto = company_id.sync_data_server_id.puerto
        nombre_servicio = company_id.sync_data_server_id.nombre_servicio
        servidor = company_id.sync_data_server_id.servidor

        dsn_tns = cx_Oracle.makedsn(servidor, puerto, service_name=nombre_servicio)
        conn = cx_Oracle.connect(user=username, password=clave, dsn=dsn_tns)

        with closing(cx_Oracle.connect(conn)) as conexion:
            with closing(conexion.cursor()) as cursor:
                cursor.execute(sql)
                if sql.upper().find('INSERT'):
                    conexion.commit()
                if sql.upper().find('SELECT'):

                    result = cursor.fetchall()
                    return result
        try:
            cursor.execute(sql)
            if sql.upper().find('INSERT'):
                conexion.commit()
            if sql.upper().find('SELECT'):
                result = cursor.fetchall()
                return result
        except cx_Oracle.ProgrammingError:
            print('my_curs is closed')
        if conexion.open:
            print ('La conexion está abierta ')
        else:
            print('La conexión está cerrada')

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    cabecera_id = fields.Char(string='Id de tabla')

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
    detalle_id = fields.Char(string='id de tabla detalle')
