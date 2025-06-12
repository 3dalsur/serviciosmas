import reflex as rx
import pandas as pd
from datetime import datetime, timedelta
import locale
from fpdf import FPDF
import os
import io # Para manejar archivos en memoria si es necesario
import asyncio # Add this line

# Function to read and process the file
def read_file(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        # Skip the header
        next(file)
        for line in file:
            row = line.strip().split('\t')
            # Ensure enough columns exist to prevent IndexError
            if len(row) > 6:
                try:
                    dt_obj = datetime.strptime(row[6].strip(), '%Y/%m/%d %H:%M:%S')
                except ValueError:
                    dt_obj = datetime.strptime(row[6].strip(), '%Y-%m-%d %H:%M:%S')

                data.append({
                    'EnNo': row[2].strip(),
                    'Name': row[3].strip(),
                    'DateTime': dt_obj.strftime('%Y-%m-%d %H:%M:%S') # Store in consistent format
                })
            else:
                print(f"Skipping malformed row: {line.strip()}")
    # This return statement must be at the same level as 'data = []' or 'with open(...)'.
    return data

# Function to generate report for each employee
def generate_report(data, selected_month, output_dir="generated_reports"): # Added output_dir parameter as discussed
    reports = {}
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')
        except locale.Error:
            locale.setlocale(locale.LC_TIME, '') # Fallback to default locale

    date = datetime.strptime(selected_month, '%Y-%m')
    month_name = date.strftime('%B %Y').upper()

    filtered_data = [record for record in data if
                     datetime.strptime(record['DateTime'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m') == selected_month]

    employees = {}
    for record in filtered_data:
        if record['EnNo'] not in employees:
            employees[record['EnNo']] = {'Name': record['Name'], 'records': []}
        employees[record['EnNo']]['records'].append(record)

    for EnNo, info in employees.items():
        pdf = FPDF('L', 'mm', 'A4')
        pdf.add_page()
        # Ensure you're using the correct font for accents if you've added it to FPDF
        # Example: pdf.set_font('DejaVuSansCondensed', 'B', 16)
        pdf.set_font('Arial', 'B', 16) # Consider changing to 'DejaVuSansCondensed' if you have the font file
        pdf.cell(0, 10, f"Asistencia: {info['Name']} | Registro: {EnNo} | {month_name}", 0, 1, 'C')

        # Consider changing to 'DejaVuSansCondensed' for all font settings
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(150, 10, "Mañana", 0, 0, 'C')
        pdf.cell(100, 10, "Tarde", 0, 1, 'C')

        # Consider changing to 'DejaVuSansCondensed' for all font settings
        pdf.set_font('Arial', '', 10)
        pdf.cell(15, 5, "Dia", 1, 0, 'C')
        pdf.cell(20, 5, "Semana", 1, 0, 'C')
        pdf.cell(25, 5, "Entrada", 1, 0, 'C')
        pdf.cell(25, 5, "Salida", 1, 0, 'C')
        pdf.cell(25, 5, "Entrada", 1, 0, 'C')
        pdf.cell(25, 5, "Salida", 1, 0, 'C')

        pdf.cell(15, 5, "Dia", 1, 0, 'C')
        pdf.cell(20, 5, "Semana", 1, 0, 'C')
        pdf.cell(25, 5, "Entrada", 1, 0, 'C')
        pdf.cell(25, 5, "Salida", 1, 0, 'C')
        pdf.cell(25, 5, "Entrada", 1, 0, 'C')
        pdf.cell(25, 5, "Salida", 1, 1, 'C')

        records_by_day = {}
        for record in info['records']:
            try:
                date = datetime.strptime(record['DateTime'], '%Y-%m-%d %H:%M:%S')
                day = date.strftime('%d')
                weekday = date.strftime('%A')
                weekday_es = {
                    'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miercoles',
                    'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sabado', 'Sunday': 'Domingo'
                }.get(weekday, weekday)
                time = date.strftime('%H:%M:%S')

                if day not in records_by_day:
                    records_by_day[day] = {'weekday': weekday_es, 'times': []}
                if len(records_by_day[day]['times']) == 0 or (
                        datetime.strptime(time, '%H:%M:%S') - datetime.strptime(records_by_day[day]['times'][-1],
                                                                                '%H:%M:%S')).seconds > 30:
                    records_by_day[day]['times'].append(time)
            except ValueError:
                print(f"Skipping malformed DateTime in record: {record['DateTime']}")

        num_days_in_month = (date.replace(month=date.month%12+1, day=1) - timedelta(days=1)).day

        for i in range(1, (num_days_in_month // 2) + (num_days_in_month % 2) + 1):
            day_str1 = str(i).zfill(2)
            day_str2 = str(i + num_days_in_month // 2).zfill(2)

            if day_str1 in records_by_day:
                times1 = records_by_day[day_str1]['times']
                morning_entry1 = times1[0] if len(times1) > 0 else '-----'
                morning_exit1 = times1[1] if len(times1) > 1 else '-----'
                afternoon_entry1 = times1[2] if len(times1) > 2 else '-----'
                afternoon_exit1 = times1[3] if len(times1) > 3 else '-----'

                pdf.cell(15, 8, day_str1, 1, 0, 'C')
                pdf.cell(20, 8, records_by_day[day_str1]['weekday'], 1, 0, 'C')
                pdf.cell(25, 8, morning_entry1, 1, 0, 'C')
                pdf.cell(25, 8, morning_exit1, 1, 0, 'C')
                pdf.cell(25, 8, afternoon_entry1, 1, 0, 'C')
                pdf.cell(25, 8, afternoon_exit1, 1, 0, 'C')
            else:
                try:
                    current_date1 = datetime.strptime(f"{selected_month}-{day_str1}", '%Y-%m-%d')
                    weekday_es1 = {
                        'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miercoles',
                        'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sabado', 'Sunday': 'Domingo'
                    }.get(current_date1.strftime('%A'), current_date1.strftime('%A'))
                except ValueError:
                    weekday_es1 = '-----'
                pdf.cell(15, 8, day_str1, 1, 0, 'C')
                pdf.cell(20, 8, weekday_es1, 1, 0, 'C')
                pdf.cell(25, 8, "-----", 1, 0, 'C')
                pdf.cell(25, 8, "-----", 1, 0, 'C')
                pdf.cell(25, 8, "-----", 1, 0, 'C')
                pdf.cell(25, 8, "-----", 1, 0, 'C')

            if i + num_days_in_month // 2 <= num_days_in_month:
                if day_str2 in records_by_day:
                    times2 = records_by_day[day_str2]['times']
                    morning_entry2 = times2[0] if len(times2) > 0 else '-----'
                    morning_exit2 = times2[1] if len(times2) > 1 else '-----'
                    afternoon_entry2 = times2[2] if len(times2) > 2 else '-----'
                    afternoon_exit2 = times2[3] if len(times2) > 3 else '-----'

                    pdf.cell(15, 8, day_str2, 1, 0, 'C')
                    pdf.cell(20, 8, records_by_day[day_str2]['weekday'], 1, 0, 'C')
                    pdf.cell(25, 8, morning_entry2, 1, 0, 'C')
                    pdf.cell(25, 8, morning_exit2, 1, 0, 'C')
                    pdf.cell(25, 8, afternoon_entry2, 1, 0, 'C')
                    pdf.cell(25, 8, afternoon_exit2, 1, 1, 'C')
                else:
                    try:
                        current_date2 = datetime.strptime(f"{selected_month}-{day_str2}", '%Y-%m-%d')
                        weekday_es2 = {
                            'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miercoles',
                            'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sabado', 'Sunday': 'Domingo'
                        }.get(current_date2.strftime('%A'), current_date2.strftime('%A'))
                    except ValueError:
                        weekday_es2 = '-----'
                    pdf.cell(15, 8, day_str2, 1, 0, 'C')
                    pdf.cell(20, 8, weekday_es2, 1, 0, 'C')
                    pdf.cell(25, 8, "-----", 1, 0, 'C')
                    pdf.cell(25, 8, "-----", 1, 0, 'C')
                    pdf.cell(25, 8, "-----", 1, 0, 'C')
                    pdf.cell(25, 8, "-----", 1, 1, 'C')
            else:
                pdf.ln()

        # Save the PDF to the specified output_dir
        report_filename = f"{EnNo}_{month_name.replace(' ', '_')}.pdf"
        # Adjusted to use output_dir passed to the function
        report_path = os.path.join(output_dir, report_filename) # <-- Corrected to use output_dir
        pdf.output(report_path)
        reports[EnNo] = report_filename # Store only the filename, not full path
    # This return statement must be at the same level as 'reports = {}'
    return reports

# Definición del estado de la aplicación
class State(rx.State):
    """The app state."""
    uploaded_file: list[rx.UploadFile] = []
    selected_month: str = datetime.now().strftime("%Y-%m")
    reports_generated: dict = {}
    is_generating: bool = False

    async def handle_upload(self, files: list[rx.UploadFile]):
        self.uploaded_file = files
        rx.console_log(f"Archivo(s) cargado(s): {[f.name for f in self.uploaded_file]}")

    def set_month(self, month: str):
        self.selected_month = month
        rx.console_log(f"Mes seleccionado: {self.selected_month}")

    async def generate_reports_action(self):
        self.is_generating = True
        self.reports_generated = {}
        # await rx.sleep(0.1)
        await asyncio.sleep(0.1) # Changed from rx.sleep

        if not self.uploaded_file:
            self.is_generating = False
            return rx.window_alert("Por favor, sube un archivo de asistencia.")

        if not self.selected_month:
            self.is_generating = False
            return rx.window_alert("Por favor, selecciona un mes.")

        file_info = self.uploaded_file[0]
        temp_file_path = ""

        try:
            upload_dir = "temp_uploads"
            os.makedirs(upload_dir, exist_ok=True)
            temp_file_path = os.path.join(upload_dir, file_info.name)

            file_content = await file_info.read()
            with open(temp_file_path, "wb") as f:
                f.write(file_content)

            data = read_file(temp_file_path)

            output_dir = "generated_reports"
            os.makedirs(output_dir, exist_ok=True)

            # Pass the output_dir to generate_report
            self.reports_generated = generate_report(data, self.selected_month, output_dir)
            rx.console_log(f"Informes generados: {self.reports_generated}")

        except Exception as e:
            rx.window_alert(f"Error al procesar el archivo o generar informes: {e}")
            rx.console_log(f"Error: {e}")
        finally:
            self.is_generating = False
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def download_report(self, filename: str):
        return rx.download(f"/generated_reports/{filename}")

# Definición de la interfaz de usuario (fuera de cualquier clase y sin indentación extra)
def index() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("Generador de Informe de Asistencia", size="7"), # Or "8", "9", etc.
            rx.text("Sube tu archivo de asistencia (.txt) y selecciona el mes para generar informes."),
            rx.upload(
                rx.button(
                    rx.cond(
                        State.is_generating,
                        rx.hstack(rx.spinner(size="2"), rx.text("Generando...")),
                        rx.hstack(rx.icon("upload"), rx.text("Seleccionar Archivo"))
                    ),
                    is_loading=State.is_generating,
                    color_scheme="blue",
                ),
                accept={
                    "text/plain": [".txt"],
                },
                max_files=1,
                on_drop=State.handle_upload(rx.upload_files()),
                # on_change=State.handle_upload(rx.upload_files()),
                border="1px dotted",
                padding="2em",
                multiple=False,
            ),
            rx.input(
                placeholder="YYYY-MM",
                value=State.selected_month,
                on_change=State.set_month,
                type="month",
                width="100%",
                max_width="300px"
            ),
            rx.button(
                "Generar Informe",
                on_click=State.generate_reports_action,
                is_loading=State.is_generating,
                color_scheme="green",
                width="100%",
                max_width="300px"
            ),
            rx.cond(
                State.reports_generated,
                rx.vstack(
                rx.heading("Informes Generados", size="5", margin_top="1em"),
                rx.foreach(
                    State.reports_generated, # The dictionary (Var) to iterate over
                    lambda en_no, filename: rx.button( # Lambda function for each item
                        f"Descargar Informe para {en_no}",
                        on_click=State.download_report(filename),
                        color_scheme="purple",
                        width="100%",
                        max_width="300px"
                    )
                )
                )
            ),
            spacing="2",
            align_items="center"
        )
    )

# Configuración de la aplicación Reflex (estas líneas deben estar a nivel superior, sin indentación)
app = rx.App()
app.add_page(index)

# app.add_static_dir(
#    root="generated_reports",
#    endpoint="generated_reports"
#)