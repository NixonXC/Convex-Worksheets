from flask import Flask, request, render_template, redirect, url_for, send_file, after_this_request
import google.generativeai as genai
import conversion as conversion
import requests
import os
from serpapi import GoogleSearch
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from bs4 import BeautifulSoup, Comment # type: ignore
from serpapi import GoogleSearch

app = Flask(__name__)

genai.configure(api_key=os.getenv("KEY"))

generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
}
generation_config_2 = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
}

model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config_2,

)
f_model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,

)

def get_data(grade, user_input, diff, no_of_questions, header, subject):
    response = model.generate_content([
            f"input: Generate {str(no_of_questions)} {subject} questions based on the chapter {user_input} of class {grade} ncert, the questions must be {diff} in difficulty. Use formatting compatible with the DejaVuSans font/latin script such as subscript and instead of latex formatting, use formatting which can be represented in the DejaVuSans font.",
            "output:",
        ])
    return response.text[1:], user_input, grade, diff, no_of_questions, header

def get_fsheet(grade, user_input, type, header, subject):
    if type == "sheet":
        response = f_model.generate_content([
            f"input: Generate a formula sheet(A document only containing identities and formulas) on subject {subject} based on the chapter {user_input} of class {grade} NCERT(CBSE). Use formatting compatible with the DejaVuSans font/latin script such as subscript and instead of latex formatting, use formatting which can be represented in the DejaVuSans font.",
            "output:",
        ])
    else:
        response = f_model.generate_content([
            f"input: Generate E-Notes(Digital notes having detailed explanations on the topics within a chapter) on subject {subject} based on the chapter {user_input} of class {grade} NCERT(CBSE). Use formatting compatible with the DejaVuSans font/latin script such as subscript and instead of latex formatting, use formatting which can be represented in the DejaVuSans font.",
            "output:",
        ])
    return response.text[1:], user_input, grade, type, subject, header

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
    subject = request.form['subject']
    response = get_data(grade, user_input, diff, no_of_questions, header, subject)
    pdf_filename = conversion.create_pdf(
    header=header,
    subject=subject,
    description="Artifically Generated worksheets and sample papers for CBSE.",
    data=response[0],
    user_input=response[1],
    grade=response[2],
    diff=response[3],
    no_of_questions=response[4]
    )
    return send_file(f"output/{pdf_filename}", as_attachment=True)

@app.route('/books')
def pdf():
    return render_template('pdf.html')

base_url = r'https://annas-archive.org'

class Annas_Archive_Parser():
    def __init__(self, params):
        self.params = params

    def get_top_five_links(self):
        book_name = self.params["book-name"]
        url = f"https://annas-archive.org/search?index=&q={book_name}"
        response = requests.get(url=url)
        data = response.text

        soup = BeautifulSoup(data, 'html.parser')

        # Find the container of each result
        result_containers = soup.find_all("div", class_="h-[125] flex flex-col justify-center")

        top_five_links = []
        for result in result_containers[:5]:
            link = result.find("a")
            top_five_links.append(link)

        links_1 = []
        for link in top_five_links:
            href_value = link.get('href')
            links_1.append(href_value)

        commented_a_tag = soup.find_all(string=lambda text: isinstance(text, Comment) and 'class="js-vim-focus custom-a' in text)

        links_2 = []
        for a_tag in commented_a_tag:
            a_soup = BeautifulSoup(a_tag, 'html.parser')
            href_value = a_soup.find('a')['href']
            links_2.append(href_value)

        links_1.extend(links_2)

        return links_1
    
    def url_returns(self): 
        links = self.get_top_five_links()
        data = links[:5]
        final_links = []
        for item in data: 
            final_url = base_url + item
            final_links.append({
                'id': final_url.replace("https://annas-archive.org/md5/",""),
                'url': final_url,
            })
        return final_links

def fetch_pdf_links_google(query):
    params = {
        "engine": "google",
        "q": query + " filetype:pdf",
        "api_key": os.getenv("SERP-KEY")
    }

    search = GoogleSearch(params).get_dict()
    results = []
    titles = []

    if "organic_results" in search:
        for res in search["organic_results"]:
            if "link" in res and res["link"].endswith(".pdf"):
                results.append(res["link"])
            if "title" in res:
                titles.append(res["title"] + "\n - " + res["source"])
    collection = []
    for i in range(len(results)):
        collection.append({
            'pdf_name': str(i+1) + ". " + titles[i],
            'pdf_url': results[i]
        })
    return collection[:5] if collection else ["/"]

def search_archive_org(book_title):
    base_url = "https://archive.org/advancedsearch.php"
    params = {
        'q': f'title:"{book_title}" AND mediatype:texts',
        'fl[]': 'identifier,title,creator',
        'output': 'json'
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        docs = data.get('response', {}).get('docs', [])

        results = []
        for doc in docs[:3]:  # Get up to three results
            identifier = doc.get('identifier', '')
            title = doc.get('title', '')
            creator = doc.get('creator', '')
            url = f"https://archive.org/details/{identifier}"

            results.append({
                'identifier': identifier,
                'title': title,
                'creator': creator,
                'url': url
            })

        return results
    else:
        return ["/"]

@app.route('/methodcore', methods=["GET"])
def formulasheets():
    return render_template('fsheet.html')

@app.route('/gen_sheet', methods=["POST"])
def generate_fsheet():
    grade = request.form['grade']
    user_input = request.form['chapter']
    type = request.form['type']
    header = request.form['header']
    subject = request.form['subject']
    response = get_fsheet(grade, user_input, type, header, subject)
    print(response)
    pdf_filename = conversion.generate_fsheet(
        header=header,
        subject=subject,
        description="Artifically Generated formula sheets and e-notes for CBSE.",
        data=response[0],
        user_input=response[1],
        grade=response[2],
        type=response[3]
    )
    return send_file(f"output/{pdf_filename}", as_attachment=True)

@app.route('/search', methods=["POST"])
def search():
    pdf_name = request.form.get("pdf_name")
    engine = request.form.get("engine")
    
    results = []

    if engine == "google":
        data = fetch_pdf_links_google(query=pdf_name)
        for pdf_link in data:
            print(pdf_link)
            filename = pdf_link["pdf_name"]
            results.append({'pdf_name': filename, 'pdf_url': pdf_link["pdf_url"]})
    elif engine == "archive":
        archive_results = search_archive_org(book_title=pdf_name)
        results = [{'pdf_name': result['title'], 'pdf_url': result['url']} for result in archive_results]
    elif engine == "anna":
        initialise = Annas_Archive_Parser(params={"book-name": "Art of war"})
        final_links = initialise.url_returns()
        results = [{'pdf_name': f"ID: {links['id']}", 'pdf_url': links['url']} for links in final_links]
    else:
        return redirect("/")

    return render_template('results.html', results=results)


if __name__ == '__main__':
        app.run(host='0.0.0.0', port=8080, debug=True)
