from fpdf import FPDF
import string
import random
import os

def sanitize_filename(filename):
    return "".join(c for c in filename if c.isalnum() or c in (' ', '_')).rstrip()

def generate_random_string(length=6):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))

def sanitize_content(content):
    illegal_chars = "#*$&%"
    return "".join(c for c in content if c not in illegal_chars)

def create_pdf(header, description, data, no_of_questions, grade, user_input, diff):
    pdf = FPDF('P', 'mm', 'A4')
    pdf.add_page()
    pdf.set_margins(20, 30, 20)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(current_dir, 'fonts', 'DejaVuSans.ttf')
    pdf.add_font('DejaVu', '', font_path, uni=True)
    bold_font_path = os.path.join(current_dir, 'fonts', 'DejaVuSans-Bold.ttf')
    pdf.add_font('DejaVu', 'B', bold_font_path, uni=True)

    # Font for the header
    pdf.set_font('DejaVu', 'B', 26)
    pdf.set_y(10)
    pdf.multi_cell(0, 10, header, 0, 'C')

    # Font for the body text
    pdf.set_font('DejaVu', '', 12)
    pdf.multi_cell(0, 10, description, 0, 'C')
    pdf.set_font('DejaVu', 'B', 12)
    pdf.multi_cell(0, 10, f"Chapter: {user_input} | Total Questions: {no_of_questions} | Grade: {grade}", 0, 'C')
    pdf.multi_cell(0, 10, f"Difficulty: {diff}", 0, 'C')
    pdf.set_font('DejaVu', '', 12)

    # Calculate the width of the underscores line
    underscore_line = "__________________________________________________________"
    underscore_width = pdf.get_string_width(underscore_line)
    page_width = pdf.w - 2 * pdf.l_margin
    x = (page_width - underscore_width) / 2

    pdf.set_x(pdf.l_margin + x)
    pdf.cell(underscore_width, 10, underscore_line, 0, 1, 'C')

    pdf.cell(200, 10, '', 0, 1, 'C')

    # Sanitize the content
    sanitized_data = sanitize_content(data)
    pdf.multi_cell(0, 10, sanitized_data)

    sanitized_user_input = sanitize_filename(user_input)
    random_string = generate_random_string()
    filename = f"{sanitized_user_input}_{random_string}.pdf"
    output_folder = os.path.join(current_dir, 'output')
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    output_path = os.path.join(output_folder, filename)
    pdf.output(output_path)
    return filename
