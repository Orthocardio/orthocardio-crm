from fpdf import FPDF
import os
import datetime

class OrthoPDF(FPDF):
    def header(self):
        # Fondo oscuro superior corporativo
        self.set_fill_color(19, 19, 19)
        self.rect(0, 0, 210, 40, 'F')
        
        if os.path.exists("static/logo.png"):
            self.image("static/logo.png", 10, 8, 33)
            
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 20)
        self.set_xy(50, 10)
        self.cell(0, 10, 'ORTHO-CARDIO', 0, 1, 'L')
        self.set_font('Arial', '', 10)
        self.set_xy(50, 20)
        self.cell(0, 5, 'Soluciones Tecnológicas Quirúrgicas de Alta Gama', 0, 1, 'L')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()} - Documento Confidencial Ortho-Cardio', 0, 0, 'C')

    def create_quote(self, doctor_name, hospital, products):
        self.add_page()
        self.ln(25)
        
        # Datos del Cliente
        self.set_text_color(0, 0, 0)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f'COTIZACIÓN FORMAL', 0, 1, 'C')
        self.ln(5)
        
        self.set_font('Arial', '', 11)
        self.cell(0, 7, f'Fecha: {datetime.date.today().strftime("%d/%m/%Y")}', 0, 1)
        self.cell(0, 7, f'Atención: {doctor_name}', 0, 1)
        self.cell(0, 7, f'Hospital: {hospital}', 0, 1)
        self.ln(10)
        
        # Tabla de Productos
        self.set_fill_color(230, 230, 230)
        self.set_font('Arial', 'B', 10)
        self.cell(130, 10, 'Descripción del Insumo', 1, 0, 'C', True)
        self.cell(30, 10, 'Cantidad', 1, 0, 'C', True)
        self.cell(30, 10, 'Disponibilidad', 1, 1, 'C', True)
        
        self.set_font('Arial', '', 10)
        for item in products:
            self.cell(130, 10, item['name'], 1, 0, 'L')
            self.cell(30, 10, str(item['qty']), 1, 0, 'C')
            self.cell(30, 10, 'Inmediata', 1, 1, 'C')
            
        self.ln(20)
        self.set_font('Arial', 'I', 9)
        self.multi_cell(0, 5, 'Nota: Esta cotización técnica no incluye IVA y está sujeta a cambios según el inventario hospitalario específico de Puebla, Veracruz y Oaxaca.')
        
        if not os.path.exists("static/quotes"):
            os.makedirs("static/quotes")
            
        filename = f"static/quotes/Cotizacion_{doctor_name.replace(' ', '_')}.pdf"
        self.output(filename)
        return filename
