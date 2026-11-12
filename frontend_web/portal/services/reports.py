import io
import os
from datetime import datetime

try:
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    class DummyCanvas:
        pass
    canvas = type('canvas', (), {'Canvas': DummyCanvas})
    letter = landscape = None
    colors = None
    SimpleDocTemplate = Paragraph = Spacer = Table = TableStyle = PageBreak = Image = KeepTogether = None
    getSampleStyleSheet = ParagraphStyle = None
    TA_CENTER = TA_LEFT = TA_RIGHT = None

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter


# ==============================================================================
# NUMBERED CANVAS (Páginas "Página X de Y" y membrete de pie de página)
# ==============================================================================
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        width = self._pagesize[0]
        now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.drawString(36, 20, f"SIGE Control Escolar • Documento de Registro • Generado: {now_str}")
        self.drawRightString(width - 36, 20, f"Página {self._pageNumber} de {page_count}")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(36, 30, width - 36, 30)
        self.restoreState()


# ==============================================================================
# ESTILOS REUTILIZABLES
# ==============================================================================
def get_pdf_styles():
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'RepTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#0f172a'),
        alignment=TA_CENTER
    )
    
    sub_style = ParagraphStyle(
        'RepSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#475569'),
        alignment=TA_CENTER
    )
    
    th_style = ParagraphStyle(
        'RepTH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=TA_CENTER
    )
    
    td_style = ParagraphStyle(
        'RepTD',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1e293b'),
        alignment=TA_LEFT
    )

    td_center = ParagraphStyle(
        'RepTDCenter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1e293b'),
        alignment=TA_CENTER
    )

    td_bold = ParagraphStyle(
        'RepTDBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#0f172a'),
        alignment=TA_CENTER
    )

    return {
        'title': title_style,
        'sub': sub_style,
        'th': th_style,
        'td': td_style,
        'td_center': td_center,
        'td_bold': td_bold,
    }


def build_institution_header(institucion, document_title, subtitle=None, width=540):
    styles = get_pdf_styles()
    header_data = []
    
    logo_widget = None
    if getattr(institucion, 'logo', None):
        try:
            logo_path = institucion.logo.path
            if os.path.exists(logo_path):
                logo_widget = Image(logo_path, width=48, height=48)
        except Exception:
            logo_widget = None

    info_paras = [
        Paragraph(f"<b>{institucion.nombre.upper()}</b>", styles['title']),
        Paragraph(f"Código MINED: {institucion.codigo_mined} • Año Lectivo: {institucion.anio_lectivo}", styles['sub']),
        Paragraph(f"<b>{document_title.upper()}</b>", ParagraphStyle('DocTitle', parent=styles['title'], fontSize=11, leading=14, textColor=colors.HexColor('#1e3a8a'))),
    ]
    if subtitle:
        info_paras.append(Paragraph(subtitle, styles['sub']))

    if logo_widget:
        table_data = [[logo_widget, info_paras]]
        header_table = Table(table_data, colWidths=[60, width - 60])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
        ]))
        return header_table
    else:
        table_data = [[info_paras]]
        header_table = Table(table_data, colWidths=[width])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
        ]))
        return header_table


# ==============================================================================
# 1. REPORTES DE ESTUDIANTES / PADRÓN DE MATRÍCULA
# ==============================================================================
def generar_pdf_estudiantes(estudiantes, institucion, query=""):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=40
    )
    styles = get_pdf_styles()
    story = []

    # Header
    subtitle = f"Padrón de Matrícula Activa ({len(estudiantes)} estudiantes registrados)"
    if query:
        subtitle += f" • Filtro: '{query}'"
    story.append(build_institution_header(institucion, "PADRÓN GENERAL DE ESTUDIANTES", subtitle, width=540))
    story.append(Spacer(1, 15))

    # Table
    table_data = [[
        Paragraph("No.", styles['th']),
        Paragraph("NIE", styles['th']),
        Paragraph("Nombre Completo del Alumno", styles['th']),
        Paragraph("Grado y Sección", styles['th']),
        Paragraph("Encargado(a)", styles['th']),
        Paragraph("Teléfono", styles['th']),
    ]]

    for i, e in enumerate(estudiantes, 1):
        table_data.append([
            Paragraph(str(i), styles['td_center']),
            Paragraph(f"<b>{e.get('nie', '---')}</b>", styles['td_center']),
            Paragraph(e.get('nombre_completo', '---'), styles['td']),
            Paragraph(e.get('grado_seccion', '---'), styles['td_center']),
            Paragraph(e.get('encargado') or '---', styles['td']),
            Paragraph(e.get('telefono') or '---', styles['td_center']),
        ])

    col_widths = [28, 56, 176, 95, 115, 70]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)

    # Signatures
    story.append(Spacer(1, 25))
    sig_data = [
        [
            Paragraph("____________________________<br/><b>Secretaría Académica</b><br/>Registro y Matrícula", styles['td_center']),
            Paragraph("____________________________<br/><b>Dirección General</b><br/>Firma y Sello de Dirección", styles['td_center'])
        ]
    ]
    sig_table = Table(sig_data, colWidths=[270, 270])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(KeepTogether([sig_table]))

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()


def generar_excel_estudiantes(estudiantes, institucion):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Padrón de Estudiantes"

    # Encabezado institucional
    ws.merge_cells("A1:F1")
    ws["A1"] = institucion.nombre.upper()
    ws["A1"].font = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")

    ws.merge_cells("A2:F2")
    ws["A2"] = f"PADRÓN DE MATRÍCULA • CÓDIGO MINED: {institucion.codigo_mined} • AÑO LECTIVO {institucion.anio_lectivo}"
    ws["A2"].font = Font(name="Calibri", size=10, italic=True, color="475569")
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")

    headers = ["No.", "NIE", "Nombre Completo del Estudiante", "Grado y Sección", "Encargado / Responsable", "Teléfono de Contacto"]
    ws.append([])  # Blank line
    ws.append(headers)

    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    header_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    border_thin = Border(
        left=Side(style='thin', color="CBD5E1"),
        right=Side(style='thin', color="CBD5E1"),
        top=Side(style='thin', color="CBD5E1"),
        bottom=Side(style='thin', color="CBD5E1")
    )

    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=4, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border_thin

    for i, e in enumerate(estudiantes, 1):
        row_num = 4 + i
        ws.append([
            i,
            e.get("nie", ""),
            e.get("nombre_completo", ""),
            e.get("grado_seccion", ""),
            e.get("encargado", "") or "Sin asignar",
            e.get("telefono", "") or "N/A"
        ])
        for col_idx in range(1, len(headers) + 1):
            c = ws.cell(row=row_num, column=col_idx)
            c.border = border_thin
            c.font = Font(name="Calibri", size=10)
            if col_idx in [1, 2, 4, 6]:
                c.alignment = Alignment(horizontal="center", vertical="center")
            else:
                c.alignment = Alignment(horizontal="left", vertical="center")

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


# ==============================================================================
# 2. CONSOLIDADO DE CALIFICACIONES (SÁBANA DE NOTAS)
# ==============================================================================
def generar_pdf_calificaciones(registros, institucion, filtros={}):
    buffer = io.BytesIO()
    # Landscape orientation for wide grade sheet
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=40
    )
    styles = get_pdf_styles()
    story = []

    # Subtitle with filters
    sub_parts = []
    if filtros.get("seccion"):
        sub_parts.append(f"Sección: {filtros['seccion']}")
    if filtros.get("asignatura"):
        sub_parts.append(f"Materia: {filtros['asignatura']}")
    if filtros.get("periodo"):
        sub_parts.append(f"Período: {filtros['periodo']}")
    sub_str = " • ".join(sub_parts) if sub_parts else "Consolidado Global Institucional"

    story.append(build_institution_header(institucion, "SÁBANA CONSOLIDADA DE CALIFICACIONES", sub_str, width=720))
    story.append(Spacer(1, 12))

    # Resumen KPI Box
    total = len(registros)
    if total > 0:
        prom = round(sum(r['nota'] for r in registros) / total, 2)
        aprobados = sum(1 for r in registros if r['aprobado'])
        reprobados = total - aprobados
        tasa = round(aprobados / total * 100, 1)
        kpi_text = f"<b>Total Evaluados:</b> {total}   |   <b>Promedio General:</b> {prom}   |   <b>Aprobados:</b> {aprobados} ({tasa}%)   |   <b>Reprobados:</b> {reprobados}"
    else:
        kpi_text = "No se encontraron calificaciones registradas con los filtros seleccionados."

    kpi_p = Paragraph(kpi_text, styles['sub'])
    kpi_table = Table([[kpi_p]], colWidths=[720])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 10))

    # Main Table
    table_data = [[
        Paragraph("No.", styles['th']),
        Paragraph("NIE", styles['th']),
        Paragraph("Estudiante", styles['th']),
        Paragraph("Grado / Sección", styles['th']),
        Paragraph("Asignatura", styles['th']),
        Paragraph("Período", styles['th']),
        Paragraph("Evaluación / Actividad", styles['th']),
        Paragraph("Nota", styles['th']),
        Paragraph("Resultado", styles['th']),
    ]]

    for i, r in enumerate(registros, 1):
        nota_val = r.get("nota", 0.0)
        aprob = r.get("aprobado", False)
        res_color = "#059669" if aprob else "#dc2626"
        res_text = f"<font color='{res_color}'><b>{'APROBADO' if aprob else 'REPROBADO'}</b></font>"

        table_data.append([
            Paragraph(str(i), styles['td_center']),
            Paragraph(f"<b>{r.get('nie', '---')}</b>", styles['td_center']),
            Paragraph(r.get('estudiante_nombre', '---'), styles['td']),
            Paragraph(r.get('grado_seccion', '---'), styles['td_center']),
            Paragraph(r.get('asignatura_nombre', '---'), styles['td']),
            Paragraph(r.get('periodo_nombre', '---'), styles['td_center']),
            Paragraph(r.get('tipo_evaluacion') or 'Evaluación General', styles['td']),
            Paragraph(f"<b>{nota_val:.1f}</b>", styles['td_center']),
            Paragraph(res_text, styles['td_center']),
        ])

    col_widths = [26, 54, 150, 90, 130, 80, 110, 40, 60]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)

    # Signatures
    story.append(Spacer(1, 20))
    sig_data = [
        [
            Paragraph("____________________________<br/><b>Docente Titular / Coordinador</b><br/>Registro de Calificaciones", styles['td_center']),
            Paragraph("____________________________<br/><b>Dirección General</b><br/>Firma y Sello de Dirección", styles['td_center'])
        ]
    ]
    sig_table = Table(sig_data, colWidths=[360, 360])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(KeepTogether([sig_table]))

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()


def generar_excel_calificaciones(registros, institucion):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Consolidado de Notas"

    ws.merge_cells("A1:H1")
    ws["A1"] = institucion.nombre.upper()
    ws["A1"].font = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")

    ws.merge_cells("A2:H2")
    ws["A2"] = f"CONSOLIDADO INSTITUCIONAL DE CALIFICACIONES • AÑO LECTIVO {institucion.anio_lectivo}"
    ws["A2"].font = Font(name="Calibri", size=10, italic=True, color="475569")
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")

    headers = ["No.", "NIE", "Estudiante", "Grado / Sección", "Asignatura", "Período", "Nota", "Resultado"]
    ws.append([])
    ws.append(headers)

    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    header_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    border_thin = Border(
        left=Side(style='thin', color="CBD5E1"),
        right=Side(style='thin', color="CBD5E1"),
        top=Side(style='thin', color="CBD5E1"),
        bottom=Side(style='thin', color="CBD5E1")
    )

    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=4, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border_thin

    pass_font = Font(name="Calibri", size=10, bold=True, color="047857")
    fail_font = Font(name="Calibri", size=10, bold=True, color="B91C1C")

    for i, r in enumerate(registros, 1):
        row_num = 4 + i
        aprob = r.get("aprobado", False)
        ws.append([
            i,
            r.get("nie", ""),
            r.get("estudiante_nombre", ""),
            r.get("grado_seccion", ""),
            r.get("asignatura_nombre", ""),
            r.get("periodo_nombre", ""),
            r.get("nota", 0.0),
            "APROBADO" if aprob else "REPROBADO"
        ])
        for col_idx in range(1, len(headers) + 1):
            c = ws.cell(row=row_num, column=col_idx)
            c.border = border_thin
            c.font = Font(name="Calibri", size=10)
            if col_idx in [1, 2, 4, 6, 7]:
                c.alignment = Alignment(horizontal="center", vertical="center")
            elif col_idx == 8:
                c.alignment = Alignment(horizontal="center", vertical="center")
                c.font = pass_font if aprob else fail_font
            else:
                c.alignment = Alignment(horizontal="left", vertical="center")

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


# ==============================================================================
# 3. BOLETAS DE CALIFICACIONES (1 POR PÁGINA PARA IMPRESIÓN DIRECTA)
# ==============================================================================
def generar_pdf_boletas(boletas_data, institucion, periodo_nombre="Período 1"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    styles = get_pdf_styles()
    story = []

    total_estudiantes = len(boletas_data)

    for idx, b in enumerate(boletas_data):
        est = b.get("estudiante", {})
        materias = b.get("materias", [])
        prom_general = b.get("promedio_general", 0.0)

        # Header institucional
        story.append(build_institution_header(
            institucion,
            "BOLETA DE CALIFICACIONES",
            f"Período de Evaluación: {periodo_nombre} • Régimen: {institucion.regimen}",
            width=540
        ))
        story.append(Spacer(1, 12))

        # Cuadro de datos del estudiante
        est_box = [
            [
                Paragraph(f"<b>Estudiante:</b> {est.get('nombre_completo', '---')}", styles['td']),
                Paragraph(f"<b>NIE:</b> {est.get('nie', '---')}", styles['td']),
            ],
            [
                Paragraph(f"<b>Grado y Sección:</b> {est.get('grado_seccion', '---')}", styles['td']),
                Paragraph(f"<b>Año Lectivo:</b> {institucion.anio_lectivo}", styles['td']),
            ],
            [
                Paragraph(f"<b>Encargado(a):</b> {est.get('encargado', 'Sin asignar')}", styles['td']),
                Paragraph(f"<b>Teléfono:</b> {est.get('telefono', 'N/A')}", styles['td']),
            ]
        ]
        est_table = Table(est_box, colWidths=[340, 200])
        est_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f1f5f9')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(est_table)
        story.append(Spacer(1, 12))

        # Tabla de Calificaciones: Exactamente 3 evaluaciones institucionales por período
        th_cols = [
            Paragraph("No.", styles['th']),
            Paragraph("Asignatura / Área de Aprendizaje", styles['th']),
            Paragraph("Act. 1", styles['th']),
            Paragraph("Act. 2", styles['th']),
            Paragraph("Act. 3", styles['th']),
            Paragraph("Promedio", styles['th']),
            Paragraph("Resultado", styles['th']),
        ]
        table_data = [th_cols]

        def fmt_eval_cell(val):
            if val is not None:
                c = "#047857" if val >= 6.0 else "#dc2626"
                return f"<font color='{c}'><b>{val:.1f}</b></font>"
            return "<font color='#94a3b8'>-</font>"

        if materias:
            for mi, m in enumerate(materias, 1):
                p_val = m.get("promedio", 0.0)
                aprob = m.get("aprobado", False)
                res_color = "#059669" if aprob else "#dc2626"
                res_str = f"<font color='{res_color}'><b>{'Aprobado' if aprob else 'Reprobado'}</b></font>"

                act1_val = m.get("act1")
                act2_val = m.get("act2")
                act3_val = m.get("act3")

                row = [
                    Paragraph(str(mi), styles['td_center']),
                    Paragraph(f"<b>{m.get('nombre', 'Materia')}</b>", styles['td']),
                    Paragraph(fmt_eval_cell(act1_val), styles['td_center']),
                    Paragraph(fmt_eval_cell(act2_val), styles['td_center']),
                    Paragraph(fmt_eval_cell(act3_val), styles['td_center']),
                    Paragraph(f"<b>{p_val:.1f}</b>", styles['td_center']),
                    Paragraph(res_str, styles['td_center']),
                ]
                table_data.append(row)
        else:
            empty_row = [
                Paragraph("-", styles['td_center']),
                Paragraph("<i>No se registran notas para este estudiante en el período actual.</i>", styles['td']),
                Paragraph("-", styles['td_center']),
                Paragraph("-", styles['td_center']),
                Paragraph("-", styles['td_center']),
                Paragraph("-", styles['td_center']),
                Paragraph("-", styles['td_center']),
            ]
            table_data.append(empty_row)

        col_widths = [24, 245, 52, 52, 52, 55, 60]
        grades_table = Table(table_data, colWidths=col_widths)
        grades_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(grades_table)
        story.append(Spacer(1, 10))

        # Resumen de Rendimiento y Escala
        aprob_total = sum(1 for m in materias if m.get("promedio", 0.0) >= 6.0)
        reprob_total = len(materias) - aprob_total
        estado_global = "SATISFACTORIO" if prom_general >= 6.0 else "EN OBSERVACIÓN ACADÉMICA"
        eg_color = "#059669" if prom_general >= 6.0 else "#dc2626"

        summary_box = [
            [
                Paragraph(f"<b>Promedio General del Período:</b> <font size='10' color='{eg_color}'><b>{prom_general:.2f}</b></font>", styles['td']),
                Paragraph(f"<b>Estado Académico:</b> <font color='{eg_color}'><b>{estado_global}</b></font>", styles['td']),
            ],
            [
                Paragraph(f"<b>Materias Aprobadas:</b> {aprob_total} de {len(materias)}", styles['td']),
                Paragraph("<b>Escala de Calificación:</b> 1.0 a 10.0 (Mínima de Aprobación: 6.0)", styles['td']),
            ]
        ]
        sum_table = Table(summary_box, colWidths=[270, 270])
        sum_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(sum_table)

        # Observaciones y Firmas
        story.append(Spacer(1, 20))
        obs_p = Paragraph("<b>Observaciones de Dirección:</b> La presente boleta refleja las notas acumuladas en el período. Cualquier consulta o rectificación debe gestionarse en Secretaría Académica dentro de los 5 días hábiles posteriores a su emisión.", styles['sub'])
        story.append(obs_p)

        story.append(Spacer(1, 35))
        sig_data = [
            [
                Paragraph("________________________________________<br/><b>Firma del Docente Orientador</b><br/>Guía de Sección", styles['td_center']),
                Paragraph("________________________________________<br/><b>Lic. Roberto Mendoza Mendoza</b><br/>Director General Titular", styles['td_center']),
            ]
        ]
        sig_table = Table(sig_data, colWidths=[270, 270])
        sig_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(sig_table)

        # Si hay más estudiantes en el lote, agregar salto de página para que cada boleta sea independiente
        if idx < total_estudiantes - 1:
            story.append(PageBreak())

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()


def generar_excel_boletas(boletas_data, institucion, periodo_nombre="Período 1"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Resumen de Boletas"

    ws.merge_cells("A1:G1")
    ws["A1"] = institucion.nombre.upper()
    ws["A1"].font = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")

    ws.merge_cells("A2:G2")
    ws["A2"] = f"RESUMEN DE BOLETAS • PERÍODO: {periodo_nombre.upper()} • AÑO LECTIVO {institucion.anio_lectivo}"
    ws["A2"].font = Font(name="Calibri", size=10, italic=True, color="475569")
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")

    headers = ["No.", "NIE", "Estudiante", "Grado / Sección", "Promedio Período", "Materias Aprobadas", "Estado Final"]
    ws.append([])
    ws.append(headers)

    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    header_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    border_thin = Border(
        left=Side(style='thin', color="CBD5E1"),
        right=Side(style='thin', color="CBD5E1"),
        top=Side(style='thin', color="CBD5E1"),
        bottom=Side(style='thin', color="CBD5E1")
    )

    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=4, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border_thin

    pass_font = Font(name="Calibri", size=10, bold=True, color="047857")
    fail_font = Font(name="Calibri", size=10, bold=True, color="B91C1C")

    for i, b in enumerate(boletas_data, 1):
        row_num = 4 + i
        est = b.get("estudiante", {})
        materias = b.get("materias", [])
        prom = b.get("promedio_general", 0.0)
        aprob_total = sum(1 for m in materias if m.get("promedio", 0.0) >= 6.0)
        estado_global = "PROMOVIDO / SATISFACTORIO" if prom >= 6.0 else "EN RIESGO"

        ws.append([
            i,
            est.get("nie", ""),
            est.get("nombre_completo", ""),
            est.get("grado_seccion", ""),
            round(prom, 2),
            f"{aprob_total} / {len(materias)}",
            estado_global
        ])

        for col_idx in range(1, len(headers) + 1):
            c = ws.cell(row=row_num, column=col_idx)
            c.border = border_thin
            c.font = Font(name="Calibri", size=10)
            if col_idx in [1, 2, 4, 5, 6]:
                c.alignment = Alignment(horizontal="center", vertical="center")
            elif col_idx == 7:
                c.alignment = Alignment(horizontal="center", vertical="center")
                c.font = pass_font if prom >= 6.0 else fail_font
            else:
                c.alignment = Alignment(horizontal="left", vertical="center")

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


# ==============================================================================
# 4. CONSOLIDADO DE ASISTENCIA DIARIA (PDF)
# ==============================================================================
def generar_pdf_asistencia(registros, institucion, filtros={}):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=40
    )
    styles = get_pdf_styles()
    story = []

    sub_parts = []
    if filtros.get("seccion"):
        sub_parts.append(f"Sección: {filtros['seccion']}")
    if filtros.get("fecha"):
        sub_parts.append(f"Fecha: {filtros['fecha']}")
    if filtros.get("estado"):
        sub_parts.append(f"Estado: {filtros['estado']}")
    sub_str = " • ".join(sub_parts) if sub_parts else "Control General de Asistencia Institucional"

    story.append(build_institution_header(institucion, "CONSOLIDADO DE ASISTENCIA DIARIA", sub_str, width=720))
    story.append(Spacer(1, 10))

    # Resumen KPI Box
    total = len(registros)
    if total > 0:
        presentes = sum(1 for r in registros if r.get('estado', '').lower() == 'presente')
        ausentes = sum(1 for r in registros if r.get('estado', '').lower() == 'ausente')
        justificados = sum(1 for r in registros if r.get('estado', '').lower() in ['justificado', 'tarde', 'permiso'])
        tasa = round(presentes / total * 100, 1)
        kpi_text = f"<b>Total Evaluados:</b> {total}   |   <b>Tasa de Concurrencia:</b> {tasa}%   |   <b>Presentes:</b> {presentes}   |   <b>Ausencias:</b> {ausentes}   |   <b>Justificaciones:</b> {justificados}"
    else:
        kpi_text = "No se encontraron pases de lista registrados con los filtros seleccionados."

    kpi_p = Paragraph(kpi_text, styles['sub'])
    kpi_table = Table([[kpi_p]], colWidths=[720])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 10))

    # Table headers
    headers = [
        Paragraph("<b>#</b>", styles['th']),
        Paragraph("<b>NIE</b>", styles['th']),
        Paragraph("<b>Nombre Completo del Estudiante</b>", styles['th']),
        Paragraph("<b>Grado y Sección</b>", styles['th']),
        Paragraph("<b>Fecha</b>", styles['th']),
        Paragraph("<b>Estado</b>", styles['th']),
        Paragraph("<b>Observaciones</b>", styles['th']),
    ]
    data = [headers]

    for i, r in enumerate(registros, 1):
        est = (r.get("estado") or "Presente").lower()
        if est == "presente":
            st_color = "#047857"
            st_txt = "PRESENTE (P)"
        elif est == "ausente":
            st_color = "#b91c1c"
            st_txt = "AUSENTE (A)"
        else:
            st_color = "#b45309"
            st_txt = f"{r.get('estado', 'JUSTIFICADO').upper()}"

        status_style = ParagraphStyle(
            f'status_asig_{i}',
            parent=styles['td_center'],
            textColor=colors.HexColor(st_color),
            fontName='Helvetica-Bold'
        )

        data.append([
            Paragraph(str(i), styles['td_center']),
            Paragraph(f"<font name='Courier'>{r.get('nie', '---')}</font>", styles['td_center']),
            Paragraph(r.get("estudiante_nombre", ""), styles['td']),
            Paragraph(r.get("grado_seccion", "---"), styles['td_center']),
            Paragraph(str(r.get("fecha", "---")), styles['td_center']),
            Paragraph(st_txt, status_style),
            Paragraph(r.get("observacion", "Asistencia regular"), styles['sub']),
        ])

    col_widths = [30, 75, 215, 110, 80, 95, 115]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table_styles = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    for row_idx in range(1, len(data)):
        bg = colors.HexColor('#ffffff') if row_idx % 2 != 0 else colors.HexColor('#f8fafc')
        table_styles.append(('BACKGROUND', (0, row_idx), (-1, row_idx), bg))

    table.setStyle(TableStyle(table_styles))
    story.append(table)

    # Signatures
    story.append(Spacer(1, 20))
    sig_data = [
        [
            Paragraph("_______________________________<br/><b>Docente Titular / Inspector</b><br/><font size=7 color='#64748b'>Firma y Sello</font>", styles['td_center']),
            Paragraph("_______________________________<br/><b>Secretaría Académica</b><br/><font size=7 color='#64748b'>Control y Registro Escolar</font>", styles['td_center']),
            Paragraph("_______________________________<br/><b>Dirección General</b><br/><font size=7 color='#64748b'>Complejo Educativo Santa Sofía</font>", styles['td_center'])
        ]
    ]
    sig_table = Table(sig_data, colWidths=[240, 240, 240])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(KeepTogether([sig_table]))

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()
