import flask
from flask import Flask, request, render_template, redirect, url_for, send_file, after_this_request
import google.generativeai as genai
import conversion as conversion
import os

app = Flask(__name__)

genai.configure(api_key=os.getenv("KEY"))

generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
}

model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
)

def get_data(grade, user_input, diff, no_of_questions, header):
    response = model.generate_content([
            f"input: Generate {str(no_of_questions)} Mathematical questions based on the chapter {user_input} of class {grade} ncert, the questions must be {diff} in difficulty. Use formatting compatible with the DejaVuSans font/latin script such as subscript and instead of latex formatting, use formatting which can be represented in the DejaVuSans font.",
            "output:",
        ])
    return response.text, user_input, grade, diff, no_of_questions, header

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    grade = request.form['grade']
    user_input = request.form['chapter']
    diff = request.form['difficulty']
    no_of_questions = request.form['num_questions']
    header = request.form['header']
    response = get_data(grade, user_input, diff, no_of_questions, header)
    pdf_filename = conversion.create_pdf(
    header=header,
    description="Artifically Generated worksheets and sample papers for mathematics.",
    data=response[0],
    user_input=response[1],
    grade=response[2],
    diff=response[3],
    no_of_questions=response[4]
    )
    return send_file(f"output/{pdf_filename}", as_attachment=True)

if __name__ == '__main__':
        app.run(host='0.0.0.0', port=8080, debug=True)
