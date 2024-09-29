from flask import Flask, request, jsonify, render_template
import os
import easyocr
import re
from PIL import Image, ImageDraw
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize the OCR reader
reader = easyocr.Reader(['en'])

def draw_boxes(image, bounds, color='yellow', width=2):
    draw = ImageDraw.Draw(image)
    for bound in bounds:
        p0, p1, p2, p3 = bound[0]
        draw.line([*p0, *p1, *p2, *p3, *p0], fill=color, width=width)
    return image

"""image_path = '/content/vss1.jpg'
bounds = reader.readtext(image_path)
extracted_text = [entry[1] for entry in bounds]

print("Extracted Text Content:")
for text in extracted_text:
    print(text)
"""
def correct_email(email):
    email = email.replace(" @ ", "@").replace(" .", ".")
    email = email.replace(" @", "@").replace("@ ", "@")
    email = email.replace(" .", ".").replace(". ", ".")
    common_typos = {
        'gmall.com': 'gmail.com',
        'gmall': 'gmail.com',
        'gmail': 'gmail.com',
        'gmail com': 'gmail.com',
        'gnail.com': 'gmail.com',
        'yaho.com': 'yahoo.com',
        'yaho com': 'yahoo.com',
        'hotmial.com': 'hotmail.com',
        'gmaill.com': 'gmail.com',
        'vsnl': 'vsnl.com',
        'tcchsr' : 'tcchsr.com'
    }
    if "@" in email:
        local_part, domain_part = email.split("@", 1)
        for typo, correction in common_typos.items():
            if typo in domain_part:
                domain_part = correction
        return f"{local_part}@{domain_part}"
    return email
def extract_emails_from_text(text_lines):
    emails = set()
    email_pattern = r'\b[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\s*\b'
    for line in text_lines:
        matches = re.findall(email_pattern, line)
        for match in matches:
            corrected_email = correct_email(match)
            emails.add(corrected_email)
    return list(emails)


def is_valid_phone_number(number):
    cleaned_number = re.sub(r'\D', '', number)
    if len(cleaned_number) < 10:
        return False
    valid_patterns = [
        r'^\+?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{4}[-.\s]?\d{4,9}$',
        r'^\d{10}$',
        r'^\d{3}[-.\s]?\d{3}[-.\s]?\d{4}$',
        r'^\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4,7}$'
    ]
    for pattern in valid_patterns:
        if re.fullmatch(pattern, number):
            return True
    return False
def extract_phone_numbers_from_text(text_lines):
    phone_numbers = set()
    phone_patterns = [
        r'\+?\d{1,4}[-.\s]?\(?\d{1,4}?\)?[-.\s]?\d{1,4}[-.\s]?\d{4,9}',  # Matches different formats
    ]
    for line in text_lines:
        for pattern in phone_patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                if is_valid_phone_number(match):
                    phone_numbers.add(match.strip())
    return list(phone_numbers)

role_keywords = [
    'CEO', 'CTO', 'CFO', 'Manager', 'Director', 'Technical Manager',
    'Head', 'Lead', 'President', 'Vice President',
    'VP', 'Chief', 'Designer', 'Paediatrician','Document Writer',
   'Wellness Coach', 'Sales & Service Engineer', 'Dell Store Promoter',
    'Advocate', 'Executive Director', 'Proprietor', 'E.B. Approved & Electrical Contractor',
    'Consulting Civil Engineer', 'Prop', 'Proprietrix', 'Trustee & PRO, Deputy Manager',
    'Country Chief', 'Branch Manager', 'Managing Director', 'Executive Customer Support', 'Training Supervisor',
    'Chairman', 'Founding Partner', 'Business Manager', 'Energy Auditor & Consulting Engineer',
    'Group Head', 'Scientist', 'Asst. Manager', 'Engineer - Sales', 'Project Engineer',
    'Chief Executive', 'Entrepreneur', 'Chief Technology Officer', 'Director - Technical',
    'Technical Director', 'Officer', 'Assistant Manager', 'Research Assosiate', 'Human Resource'
]
role_pattern = r'(?i)\b(?:' + '|'.join(re.escape(keyword) for keyword in role_keywords) + r')\b'

def extract_roles_from_text(text_lines):
    roles = set()
    for line in text_lines:
        matches = re.findall(role_pattern, line)
        roles.update(matches)
    return list(roles)

name_keywords = [
    'SELVAM', 'CHANDRAPPA', 'RAMASAMY' , 'Jayachandru', 'Selvam', 'DEEPA SAMRAJ', 'Sultan Mohideen', 'VinothKumar',
    'Sanjay V.Kale', 'Ravi Kumar', 'Priya Sharma', 'Anil Agarwal', 'Vijay Patil', 'Meenakshi Iyer', 'Nikhil Rao', 'Suresh Babu', 'Radha Krishnan',
    'Pooja Singh', 'Rakesh Mehra', 'Arjun Pillai', 'Harish Menon', 'Nandini Verma', 'Amitabh Joshi', 'Tara Swaminathan', 'Vikram Desai', 
    'Shweta Nair', 'Ajay Prasad', 'Rajesh Kannan', 'Madhavi Rao', 'Girish Kulkarni', 'Sneha Pillai', 'Pradeep Naik',
    'Manoj Tiwari', 'Jyoti Mishra', 'Akash Jain', 'Sunil Kapoor','Ramesh','Murthy','Sathesh','Thangavelu'
]

name_pattern = r'(?i)\b(?:' + '|'.join(re.escape(keyword) for keyword in name_keywords) + r')\b'
def extract_names_from_text(text_lines):
    names = set()
    for line in text_lines:
        matches = re.findall(name_pattern, line)
        names.update(matches)
    return list(names)

company_keywords = [
    'Megatronics', 'Everest Instruments Pvt. Ltd', 'ZAN COMPUTECH', 'Pantech', 'Dell Exclusive Store',
    'Nutrition Centre', 'SVS', 'VEE BEE YARN TEX PRIVATE LIMITED', 'Tata Consultancy Services', 'Infosys Technologies', 
    'Reliance Industries', 'Wipro Ltd.', 'HCL Technologies', 'Tech Mahindra', 'Bajaj Auto', 'Hero MotoCorp', 
    'Asian Paints', 'Bharti Airtel', 'ICICI Bank', 'Axis Bank', 'Adani Group', 'Larsen & Toubro', 'Cipla Ltd.', 
    'Maruti Suzuki', 'Godrej Consumer Products', 'Hindustan Unilever', 'Mahindra & Mahindra', 'BHEL', 'Dr. Reddy\'s Laboratories','Sunshiv','Ashwin Hospital'
]

company_pattern = r'(?i)\b(?:' + '|'.join(re.escape(keyword) for keyword in company_keywords) + r')\b'
def extract_company_names_from_text(text_lines):
    companies = set()
    for line in text_lines:
        matches = re.findall(company_pattern, line)
        companies.update(matches)
    return list(companies)

def extract_pin_codes_from_text(text_lines):
    pin_codes = set()
    pin_code_pattern = r'\b(\d{3})\s*(\d{3})\b'
    for line in text_lines:
        cleaned_line = re.sub(r'\D', '', line)
        if len(cleaned_line) == 6:
            match = re.match(r'(\d{3})(\d{3})', cleaned_line)
            if match:
                pin_code = match.group(1) + match.group(2)
                pin_codes.add(pin_code)
    return list(pin_codes)
# def extract_websites_from_text(text_lines):
#     websites = set()
#     website_pattern = r'www\s*\.?\s*([A-Za-z0-9.-]+)\s*\.?\s*(com|in)'
#     for line in text_lines:
#         normalized_line = re.sub(r'\s+', ' ', line)
#         matches = re.findall(website_pattern, normalized_line, re.IGNORECASE)
#         for domain, tld in matches:
#             domain = domain.strip('.')
#             if not domain.endswith('.'):
#                 website = f"www.{domain}.{tld}"
#             else:
#                 website = f"www.{domain[:-1]}.{tld}"  # Remove the last dot
#             websites.add(website.lower())
#     return list(websites)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract_text():
    if 'image' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = secure_filename(file.filename)
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(image_path)

    # Read text from image using OCR
    bounds = reader.readtext(image_path)
    extracted_text = [entry[1] for entry in bounds]

    # Extract data
    emails_found = extract_emails_from_text(extracted_text)
    phone_numbers_found = extract_phone_numbers_from_text(extracted_text)
    roles_found = extract_roles_from_text(extracted_text)
    pin_codes_found = extract_pin_codes_from_text(extracted_text)
    # websites_found = extract_websites_from_text(extracted_text)
    names_found = extract_names_from_text(extracted_text)
    companies_found = extract_company_names_from_text(extracted_text)


    # Return extracted information as JSON
    result = {
        'emails': emails_found,
        'phoneNumbers': phone_numbers_found,
        'roles': roles_found,
        'pinCodes': pin_codes_found,
        'name' : names_found,
        'company' : companies_found
        # 'website' : websites_found
    }
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
