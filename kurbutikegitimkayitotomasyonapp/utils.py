from io import BytesIO
import os
from datetime import date

from django.http import HttpResponse
from django.conf import settings

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepInFrame
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def _register_fonts():
    fonts_dir = os.path.join(
        settings.BASE_DIR,
        "kurbutikegitimkayitotomasyonapp",
        "static",
        "fonts",
    )
    regular = os.path.join(fonts_dir, "DejaVuSans.ttf")
    bold = os.path.join(fonts_dir, "DejaVuSans-Bold.ttf")

    if os.path.exists(regular) and "DejaVuSans" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("DejaVuSans", regular))
    if os.path.exists(bold) and "DejaVuSans-Bold" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", bold))


def _soft_break(s):
    if s is None:
        return ""
    s = str(s)
    for ch in ["@", ".", "-", "_", "/", "\\", ":", ";"]:
        s = s.replace(ch, ch + "\u200b")
    return s


def render_to_pdf(template_src, context_dict=None, filename="kayit.pdf"):
    if context_dict is None:
        context_dict = {}

    _register_fonts()

    enrollment = context_dict.get("enrollment")
    student = context_dict.get("student")
    guardians = context_dict.get("guardians") or []
    payment_plan = context_dict.get("payment_plan")

    # ------------------- SADE THEME -------------------
    # Daha nötr/kurumsal: füme + açık gri + tek accent
    INK = colors.HexColor("#111827")        # neredeyse siyah
    MUTED = colors.HexColor("#6B7280")      # gri
    BORDER = colors.HexColor("#E5E7EB")     # açık çizgi
    CARD_BG = colors.HexColor("#F9FAFB")    # çok açık gri
    TH_BG = colors.HexColor("#F3F4F6")      # tablo header gri
    ZEBRA = colors.HexColor("#FFFFFF")      # zebra beyaz
    ACCENT = colors.HexColor("#374151")     # koyu gri accent (sade)
    ACCENT_LINE = colors.HexColor("#9CA3AF")# ince çizgi

    base_font = "DejaVuSans" if "DejaVuSans" in pdfmetrics.getRegisteredFontNames() else "Helvetica"
    bold_font = "DejaVuSans-Bold" if "DejaVuSans-Bold" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="SectionTitle",
        fontName=bold_font, fontSize=11.2, leading=14,
        textColor=INK
    ))
    styles.add(ParagraphStyle(
        name="Label",
        fontName=bold_font, fontSize=9.1, leading=12,
        textColor=MUTED
    ))
    styles.add(ParagraphStyle(
        name="Value",
        fontName=base_font, fontSize=9.6, leading=12.5,
        textColor=INK,
        wordWrap="CJK",
        splitLongWords=1,
    ))
    styles.add(ParagraphStyle(
        name="SmallCenter",
        fontName=base_font, fontSize=8.2, leading=10.5,
        textColor=MUTED, alignment=1
    ))

    def P(text, style="Value"):
        return Paragraph(_soft_break(text), styles[style])

    # ------------------- HEADER / FOOTER (SADE + DENGELI LOGO) -------------------
    image_dir = os.path.join(settings.BASE_DIR, "image")
    meb_logo = os.path.join(image_dir, "meblogo.png")

    def header_footer(canvas, doc):
        canvas.saveState()
        w, h = A4

        # Sade header: sadece logolar ve ortada başlık (çizgi yok)
        top_pad = 14 * mm
        logo_h = 18 * mm
        logo_y = h - top_pad - logo_h / 2

        # MEB logo solda
        if os.path.exists(meb_logo):
            try:
                canvas.drawImage(
                    meb_logo,
                    70 * mm,
                    logo_y,
                    height=logo_h,
                    preserveAspectRatio=True,
                    mask="auto",
                )
                canvas.drawImage(
                    meb_logo,
                    -80 * mm,
                    logo_y,
                    height=logo_h,
                    preserveAspectRatio=True,
                    mask="auto",
                )
            except Exception:
                pass

         

       

        # Ortada başlıklar
        title_y = logo_y + logo_h / 2 + 2 * mm
        canvas.setFillColor(INK)
        canvas.setFont(bold_font, 13)
        canvas.setFillColor(MUTED)
        canvas.setFont(base_font, 9.5)
        canvas.drawCentredString(w / 2, title_y - 6 * mm, "Öğrenci Kayıt & Ödeme Bilgi Formu")

        # footer
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(1)
        canvas.line(14 * mm, 13 * mm, w - 14 * mm, 13 * mm)

        canvas.setFillColor(MUTED)
        canvas.setFont(base_font, 8.5)
        canvas.drawString(14 * mm, 8 * mm, f"Düzenlenme Tarihi: {date.today().strftime('%d.%m.%Y')}")
        canvas.drawRightString(w - 14 * mm, 8 * mm, f"Sayfa {doc.page}")

        canvas.restoreState()

    # ------------------- UI HELPERS -------------------
    def section_card(title, rows):
        title_row = Table([[P(title, "SectionTitle")]], colWidths=[174 * mm])
        title_row.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))

        data = [[P(k, "Label"), P(v, "Value")] for k, v in rows]
        t = Table(data, colWidths=[52 * mm, 122 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
            ("BOX", (0, 0), (-1, -1), 1, BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))

        # Kart asla patlamasın (çok uzunsa küçük küçültür)
        kif = KeepInFrame(174 * mm, 240 * mm, [t], mode="shrink")

        return [title_row, kif]

    def guardians_card():
        title = Table([[P("Veli Bilgileri", "SectionTitle")]], colWidths=[174 * mm])
        title.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))

        header = ["Ad Soyad", "T.C.", "Yakınlık", "Telefon", "E-posta", "Adres"]
        data = [[P(h, "Label") for h in header]]

        if not guardians:
            data.append([P("-"), P("-"), P("-"), P("-"), P("-"), P("-")])
        else:
            for g in guardians:
                data.append([
                    P(getattr(g, "full_name", "")),
                    P(getattr(g, "national_id", "")),
                    P(g.get_relation_display() if hasattr(g, "get_relation_display") else ""),
                    P(getattr(g, "phone", "")),
                    P(getattr(g, "email", "") or ""),
                    P(getattr(g, "address", "") or ""),
                ])

        t = Table(data, colWidths=[34*mm, 25*mm, 18*mm, 26*mm, 26*mm, 45*mm])
        ts = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TH_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), MUTED),
            ("BOX", (0, 0), (-1, -1), 1, BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
        for r in range(1, len(data)):
            if r % 2 == 0:
                ts.add("BACKGROUND", (0, r), (-1, r), ZEBRA)
        t.setStyle(ts)

        outer = Table([[t]], colWidths=[174 * mm])
        outer.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
            ("BOX", (0, 0), (-1, -1), 1, BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))

        return [title, outer]

    def signatures():
        line = HRFlowable(width="100%", thickness=1, color=BORDER, spaceBefore=8, spaceAfter=8)
        sign = Table(
            [[P("Kurum Yetkilisi", "Label"), P("Veli", "Label")],
             ["", ""]],
            colWidths=[87*mm, 87*mm],
            rowHeights=[8*mm, 18*mm]
        )
        sign.setStyle(TableStyle([
            ("LINEABOVE", (0, 1), (0, 1), 1, INK),
            ("LINEABOVE", (1, 1), (1, 1), 1, INK),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        note = Table([[P("Bu belge kayıt tarihinde taraflarca okunmuş ve onaylanmıştır.", "SmallCenter")]],
                     colWidths=[174*mm])
        return [Spacer(0, 6*mm), line, sign, Spacer(0, 2*mm), note]

    # ------------------- BUILD -------------------
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15*mm,
        rightMargin=15*mm,
        topMargin=34*mm,   # header alanı
        bottomMargin=18*mm,
        title="Öğrenci Kayıt Formu"
    )

    story = []
    story.append(Spacer(0, 4*mm))

    story.extend(section_card("Öğrenci Bilgileri", [
        ("Ad Soyad", getattr(student, "full_name", "")),
        ("T.C. Kimlik No", getattr(student, "national_id", "")),
        ("Doğum Tarihi", getattr(student, "birth_date", "")),
        ("Cinsiyet", student.get_gender_display() if student else ""),
        ("Okul", getattr(student, "school", "") or ""),
        ("Sınıf", student.get_school_class_display() if student else ""),
    ]))
    story.append(Spacer(0, 7*mm))

    story.extend(section_card("Eğitim Bilgileri", [
        ("Program", enrollment.program.name if enrollment else ""),
        ("Başlangıç Tarihi", getattr(enrollment, "start_date", "")),
        ("Seviye / Kur", getattr(enrollment, "level", "")),
    ]))
    story.append(Spacer(0, 7*mm))

    story.extend(guardians_card())
    story.append(Spacer(0, 7*mm))

    story.extend(section_card("Acil Durum Bilgisi", [
        ("Acil Durum Kişisi", getattr(student, "emergency_contact_name", "")),
        ("Telefon", getattr(student, "emergency_contact_phone", "")),
    ]))
    story.append(Spacer(0, 7*mm))

    if payment_plan:
        story.extend(section_card("Ödeme Bilgileri", [
            ("Toplam Ücret", f"{payment_plan.total_amount} TL"),
            ("Ödeme Şekli", payment_plan.get_payment_method_display()),
            ("Ödenen", f"{payment_plan.total_paid} TL"),
            ("Kalan", f"{payment_plan.remaining} TL"),
        ]))
    else:
        story.extend(section_card("Ödeme Bilgileri", [
            ("Durum", "Ödeme planı bulunamadı."),
        ]))

    story.extend(signatures())

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write(pdf)
    return response
