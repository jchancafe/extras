 def registrar_detalle_documento(self, detalle_item, invoice_id):
        existe_error = False
        for detalle in detalle_item:
            cabecera_id = detalle.get('id')

            #Obtencion del producto/servicio
            product_id = self.obtener_producto_servicio(detalle)

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

def registrar_documento(self, item):
        REGISTRO_TERMINADO = 'T'
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

            if not existe_error:
                invoice_id.write({
                    'number': data_documento.get('correlativo_documento'),
                    'move_name': data_documento.get('correlativo_documento'),
                })

                invoice_id.compute_taxes()
                invoice_id.action_invoice_open()

        return existe_error

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
