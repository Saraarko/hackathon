#!/usr/bin/env python
"""
Generate realistic medical credential PDFs for testing Agent 1
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.units import inch
from datetime import datetime, timedelta
import random

def generate_french_doctor_diploma():
    """Generate a realistic French medical diploma"""
    filename = "DOCTOR_DIPLOMA_FR.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#003366'),
        spaceAfter=30,
        alignment=1
    )

    story.append(Paragraph("MINISTÈRE DE L'ENSEIGNEMENT SUPÉRIEUR", title_style))
    story.append(Paragraph("ET DE LA RECHERCHE SCIENTIFIQUE", title_style))
    story.append(Spacer(1, 0.3*inch))

    # Certificate content
    content_style = ParagraphStyle(
        'Content',
        parent=styles['Normal'],
        fontSize=11,
        alignment=1,
        spaceAfter=12
    )

    story.append(Paragraph("DIPLÔME DE MÉDECINE GÉNÉRALE", content_style))
    story.append(Spacer(1, 0.2*inch))

    # Practitioner info
    names = ["Dr. Karim Belhadj", "Dr. Fatima Bennabi", "Dr. Mohamed Eddine Saidane",
             "Dr. Leila Mansouri", "Dr. Youssef Boutaleb"]
    universities = ["Université d'Alger", "Université d'Oran", "Université de Constantine",
                   "Université de Tlemcen", "Université de Sétif"]
    specialties = ["Médecine générale", "Cardiologie", "Pédiatrie", "Chirurgie générale", "Psychiatrie"]

    name = random.choice(names)
    university = random.choice(universities)
    specialty = random.choice(specialties)
    year = random.randint(2010, 2023)

    data = [
        ["Nom complet:", name],
        ["Université:", university],
        ["Spécialité:", specialty],
        ["Année d'obtention:", str(year)],
        ["Numéro d'inscription:", f"D-{year}-{random.randint(1000, 9999)}"],
        ["Date de validité:", datetime.now().strftime("%d/%m/%Y")],
    ]

    table = Table(data, colWidths=[2*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8E8E8')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))

    story.append(table)
    story.append(Spacer(1, 0.5*inch))

    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        alignment=1,
        textColor=colors.grey
    )
    story.append(Paragraph("Ce diplôme certifie que le titulaire a satisfait aux exigences du cursus de médecine.", footer_style))
    story.append(Paragraph("Délivré par l'université d'origine.", footer_style))
    story.append(Paragraph(f"Document généré le {datetime.now().strftime('%d/%m/%Y')}", footer_style))

    doc.build(story)
    print(f"[OK] Created: {filename}")
    return filename


def generate_algerian_medical_license():
    """Generate a realistic Algerian medical license"""
    filename = "ALGERIAN_MEDICAL_LICENSE.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Header
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#006600'),
        alignment=1,
        spaceAfter=20
    )

    story.append(Paragraph("ORDRE NATIONAL DES MÉDECINS", header_style))
    story.append(Paragraph("PERMIS D'EXERCER", header_style))
    story.append(Spacer(1, 0.3*inch))

    # License details
    names = ["Dr. Samir Dekhissi", "Dr. Nadia Zerbini", "Dr. Hassan Bouvier", "Dr. Rania Abdellaoui"]
    specialties = ["Médecin généraliste", "Chirurgien", "Pédiatre", "Cardiologue"]

    name = random.choice(names)
    specialty = random.choice(specialties)
    registration_num = f"OM-{random.randint(2010, 2023)}-{random.randint(10000, 99999)}"
    issue_date = datetime.now() - timedelta(days=random.randint(365, 3650))
    expiry_date = issue_date + timedelta(days=1825)

    data = [
        ["PRATICIEN", name],
        ["SPÉCIALITÉ", specialty],
        ["NUMÉRO D'INSCRIPTION", registration_num],
        ["DATE DE DÉLIVRANCE", issue_date.strftime("%d/%m/%Y")],
        ["DATE D'EXPIRATION", expiry_date.strftime("%d/%m/%Y")],
        ["RÉGIONS AUTORISÉES", "Tout le territoire algérien"],
        ["STATUT", "Actif et en règle"],
    ]

    table = Table(data, colWidths=[2.5*inch, 3.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#CCFFCC')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.green),
        ('LINEWIDTH', (0, 0), (-1, -1), 2),
    ]))

    story.append(table)
    story.append(Spacer(1, 0.5*inch))

    # Verification info
    footer = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=1,
        textColor=colors.grey
    )
    story.append(Paragraph("Pour vérification: www.ordremedecins.dz", footer))
    story.append(Paragraph(f"Certificat valide jusqu'au {expiry_date.strftime('%d/%m/%Y')}", footer))

    doc.build(story)
    print(f"[OK] Created: {filename}")
    return filename


def generate_hospital_license():
    """Generate a realistic hospital/clinic license"""
    filename = "HOSPITAL_LICENSE.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Header
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#CC0000'),
        alignment=1
    )

    story.append(Paragraph("MINISTÈRE DE LA SANTÉ", header_style))
    story.append(Paragraph("LICENCE D'EXPLOITATION - ÉTABLISSEMENT DE SANTÉ", header_style))
    story.append(Spacer(1, 0.3*inch))

    # Hospital info
    hospitals = [
        ("Clinique Al-Shifa", "Alger", "500"),
        ("Hôpital Central", "Oran", "350"),
        ("Clinique Médicale Moderne", "Constantine", "250"),
        ("Centre Hospitalier Universitaire", "Blida", "600"),
    ]

    hospital = random.choice(hospitals)
    name, city, beds = hospital
    license_num = f"LIC-HOP-{random.randint(2010, 2023)}-{random.randint(1000, 9999)}"

    data = [
        ["NOM DE L'ÉTABLISSEMENT", name],
        ["LOCALISATION", city],
        ["NUMÉRO DE LICENCE", license_num],
        ["CAPACITÉ (LITS)", beds],
        ["AGRÉMENTATION ISO", "ISO 9001:2015"],
        ["AGRÉMENT HAS", "Oui"],
        ["DATE DE DÉLIVRANCE", "01/01/2023"],
        ["DATE D'EXPIRATION", "31/12/2027"],
    ]

    table = Table(data, colWidths=[2.5*inch, 3.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#FFE6E6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.red),
    ]))

    story.append(table)
    story.append(Spacer(1, 0.5*inch))

    footer = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, alignment=1)
    story.append(Paragraph("Cet établissement est autorisé à fonctionner selon les normes en vigueur.", footer))

    doc.build(story)
    print(f"[OK] Created: {filename}")
    return filename


def generate_laboratory_accreditation():
    """Generate a realistic laboratory accreditation"""
    filename = "LABORATORY_ACCREDITATION.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Header
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0066CC'),
        alignment=1
    )

    story.append(Paragraph("LABORATOIRE D'ANALYSES MÉDICALES", header_style))
    story.append(Paragraph("ACCRÉDITATION ISO 15189", header_style))
    story.append(Spacer(1, 0.3*inch))

    # Lab info
    labs = [
        ("Lab Bioanalytique", "Dr. Mohamed Benali", "Alger"),
        ("Diagnostics Plus", "Dr. Leila Hamza", "Oran"),
        ("Centre d'Analyses Modernes", "Dr. Karim Siddiki", "Constantine"),
    ]

    lab = random.choice(labs)
    lab_name, director, city = lab
    accred_num = f"ISO15189-{random.randint(2020, 2023)}-{random.randint(1000, 9999)}"

    data = [
        ["NOM DU LABORATOIRE", lab_name],
        ["DIRECTEUR SCIENTIFIQUE", director],
        ["LOCALISATION", city],
        ["NUMÉRO D'ACCRÉDITATION", accred_num],
        ["NORME ISO", "ISO 15189:2022"],
        ["AGRÉMENT SÉCURITÉ SOCIALE", "Oui"],
        ["TYPES D'ANALYSES", "Hématologie, Biochimie, Microbiologie, Immunologie"],
        ["VALIDE JUSQU'AU", "31/12/2026"],
    ]

    table = Table(data, colWidths=[2.5*inch, 3.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E6F2FF')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.blue),
    ]))

    story.append(table)
    story.append(Spacer(1, 0.5*inch))

    footer = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, alignment=1)
    story.append(Paragraph("Accrédité pour les analyses listées ci-dessus selon ISO 15189:2022", footer))

    doc.build(story)
    print(f"[OK] Created: {filename}")
    return filename


if __name__ == "__main__":
    print("\n" + "="*60)
    print("GENERATING REALISTIC MEDICAL CREDENTIAL PDFs")
    print("="*60 + "\n")

    files = [
        generate_french_doctor_diploma(),
        generate_algerian_medical_license(),
        generate_hospital_license(),
        generate_laboratory_accreditation(),
    ]

    print("\n" + "="*60)
    print(f"[SUCCESS] Generated {len(files)} realistic test PDFs")
    print("="*60)
    print("\nNext: Test Agent 1 with these PDFs")
    print("  python agent1_extraction.py")
    print()
