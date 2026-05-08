import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from app.security import sanitize_input


def generate_teacher_report(teacher_name, total_questions, total_records, accuracy, per_question, student_stats):
    teacher_name = sanitize_input(str(teacher_name), max_length=100)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"付刷 - 教师数据报告", styles['Title']))
    elements.append(Paragraph(f"教师: {teacher_name}", styles['Normal']))
    elements.append(Spacer(1, 10 * mm))

    elements.append(Paragraph("总体统计", styles['Heading2']))
    summary_data = [
        ["指标", "数值"],
        ["题目总数", str(total_questions)],
        ["答题总次数", str(total_records)],
        ["整体正确率", f"{accuracy}%"],
    ]
    t = Table(summary_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4361ee')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 10 * mm))

    if student_stats:
        elements.append(Paragraph("学生排名", styles['Heading2']))
        student_data = [["排名", "姓名", "答题数", "正确数", "正确率"]]
        for i, s in enumerate(student_stats[:20], 1):
            student_data.append([str(i), s.get("display_name", s.get("username", "")), str(s["total"]), str(s["correct"]), f"{s['accuracy']}%"])
        st = Table(student_data)
        st.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4361ee')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        elements.append(st)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_student_report(student_name, total, correct, accuracy, subject_stats, type_stats):
    student_name = sanitize_input(str(student_name), max_length=100)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"付刷 - 学生学习报告", styles['Title']))
    elements.append(Paragraph(f"学生: {student_name}", styles['Normal']))
    elements.append(Spacer(1, 10 * mm))

    elements.append(Paragraph("总体统计", styles['Heading2']))
    summary_data = [
        ["指标", "数值"],
        ["答题总数", str(total)],
        ["正确数", str(correct)],
        ["正确率", f"{accuracy}%"],
    ]
    t = Table(summary_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4361ee')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 10 * mm))

    if subject_stats:
        elements.append(Paragraph("分科目统计", styles['Heading2']))
        sub_data = [["科目", "答题数", "正确数", "正确率"]]
        for s in subject_stats:
            sub_data.append([s["name"], str(s["total"]), str(s["correct"]), f"{s['accuracy']}%"])
        st = Table(sub_data)
        st.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4361ee')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        elements.append(st)

    doc.build(elements)
    buffer.seek(0)
    return buffer
