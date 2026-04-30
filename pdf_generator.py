from fpdf import FPDF
import os
import datetime

class OrthoPDF(FPDF):
    def header(self):
        # Fondo oscuro superior corporativo (Carbon)
        self.set_fill_color(12, 12, 15)
        self.rect(0, 0, 210, 40, 'F')
        
        # Borde inferior azul clínico
        self.set_fill_color(0, 122, 255)
        self.rect(0, 39, 210, 1, 'F')
        
        if os.path.exists("static/logo.png"):
            self.image("static/logo.png", 10, 8, 33)
            
        self.set_text_color(225, 225, 230)
        self.set_font('helvetica', 'B', 20)
        self.set_xy(50, 10)
        self.cell(0, 10, 'ORTHO-CARDIO', 0, 1, 'L')
        self.set_font('helvetica', '', 10)
        self.set_xy(50, 20)
        self.cell(0, 5, 'BÚNKER DE INTELIGENCIA QUIRÚRGICA', 0, 1, 'L')

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(74, 74, 82)
        self.cell(0, 10, f'Página {self.page_no()} - Documento Confidencial de Alta Gama Ortho-Cardio', 0, 0, 'C')

    def create_quote(self, doctor_name, hospital, products, custom_filename=None):
        self.add_page()
        self.ln(25)
        
        # Título
        self.set_text_color(12, 12, 15)
        self.set_font('helvetica', 'B', 14)
        self.cell(0, 10, 'COTIZACIÓN TÉCNICA FORMAL', 0, 1, 'C')
        self.ln(5)
        
        # Datos de cabecera
        self.set_font('helvetica', '', 10)
        self.set_text_color(74, 74, 82)
        self.cell(40, 7, 'FECHA DE EMISIÓN:', 0, 0)
        self.set_text_color(12, 12, 15)
        self.cell(0, 7, datetime.date.today().strftime("%d / %m / %Y"), 0, 1)
        
        self.set_text_color(74, 74, 82)
        self.cell(40, 7, 'ATENCIÓN:', 0, 0)
        self.set_text_color(12, 12, 15)
        self.set_font('helvetica', 'B', 10)
        self.cell(0, 7, doctor_name.upper(), 0, 1)
        
        self.set_font('helvetica', '', 10)
        self.set_text_color(74, 74, 82)
        self.cell(40, 7, 'HOSPITAL / SEDE:', 0, 0)
        self.set_text_color(12, 12, 15)
        self.cell(0, 7, hospital, 0, 1)
        self.ln(10)
        
        # Tabla de Productos
        self.set_fill_color(240, 240, 245)
        self.set_text_color(12, 12, 15)
        self.set_font('helvetica', 'B', 9)
        self.cell(100, 10, ' DESCRIPCIÓN TÉCNICA DEL INSUMO', 1, 0, 'L', True)
        self.cell(30, 10, 'CANTIDAD', 1, 0, 'C', True)
        self.cell(30, 10, 'P. UNITARIO', 1, 0, 'C', True)
        self.cell(30, 10, 'SUBTOTAL', 1, 1, 'C', True)
        
        self.set_font('helvetica', '', 8)
        total = 0
        for item in products:
            # Soporte para descripción multilineal (sustento técnico)
            x_start = self.get_x()
            y_start = self.get_y()
            self.multi_cell(100, 5, f"{item['name']}\nRef: {item.get('code', 'N/A')}", 1, 'L')
            y_end = self.get_y()
            h = y_end - y_start
            
            self.set_xy(x_start + 100, y_start)
            self.cell(30, h, str(item['qty']), 1, 0, 'C')
            
            price = item.get('price', 0)
            subtotal = price * item['qty']
            total += subtotal
            
            self.cell(30, h, f"${price:,.2f}", 1, 0, 'C')
            self.cell(30, h, f"${subtotal:,.2f}", 1, 1, 'C')
            
        # Total
        self.set_font('helvetica', 'B', 10)
        self.cell(160, 10, 'TOTAL (MXN)', 1, 0, 'R')
        self.set_fill_color(0, 122, 255)
        self.set_text_color(255, 255, 255)
        self.cell(30, 10, f"${total:,.2f}", 1, 1, 'C', True)
        
        self.ln(10)
        self.set_text_color(74, 74, 82)
        self.set_font('helvetica', 'I', 8)
        self.multi_cell(0, 4, 'NOTAS LEGALES: Esta cotización refleja el tabulador histórico corporativo autorizado. Los precios no incluyen IVA. Sujeto a disponibilidad técnica inmediata en las sedes regionales de Puebla, Veracruz y Oaxaca.')
        
        if not os.path.exists("static/quotes"):
            os.makedirs("static/quotes")
            
        if not custom_filename:
            custom_filename = f"static/quotes/Cotizacion_{doctor_name.replace(' ', '_')}.pdf"
            
        self.output(custom_filename)
        return custom_filename
