import json

import requests
from bs4 import BeautifulSoup, NavigableString

import re



def parse_semesters(text):
    # Text elements we find on the page will be one of several things:
    # 1. Single comma
    # 2. The text "Offered in"
    # 3. "Offered in" followed by a comma-separated list of semesters
    # 4. A comma-separated list of semesters


    # Remove the leading "Offered in" if it exists and strip any surrounding spaces
    if text.startswith("Offered in"):
        text = text[len("Offered in"):].strip()
    
    # If the text is empty or only a comma after trimming, return an empty list
    if not text or text == ',':
        return []

    # Split the text by commas and strip whitespace from each item
    semesters = [semester.strip() for semester in text.split(',') if semester.strip()]
    
    return semesters


def fetch_page_json(academic_year_id, mmtid):
    # academic_year_id: 2425
    # mmtid: ID of the department
    url= f'https://www.amherst.edu/academiclife/college-catalog/{academic_year_id}?mmtid={mmtid}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
    }
    
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print(f"Failed to retrieve page. Status code: {res.status_code}")
        return None
    
    soup = BeautifulSoup(res.text, 'html.parser')

    course_div = soup.find('div', class_='course-curriculum-body')
    if course_div is None:
        print("No course-curriculum-body div found.")
        return None
    

    courses = []


    for title_tag in course_div.find_all('h4'):
        course_title = title_tag.get_text(strip=True)
        
        # Initialize course data fields
        description = None
        details = None
        other_years = []

        # Gather <p> siblings for description and details
        paragraphs = title_tag.find_next_siblings('p', limit=2)
        if len(paragraphs) == 2:
            description = paragraphs[0].get_text(strip=True)
            details = paragraphs[1].get_text(strip=True)
        elif len(paragraphs) == 1:
            details = paragraphs[0].get_text(strip=True)

        # Look for "Other years" section
        other_years_tag = title_tag.find_next_sibling('b')
        
        if other_years_tag and "Other years" in other_years_tag.get_text(strip=True):
            # Initialize a list to hold the text content
            years_text = []
            next_node = other_years_tag.next_sibling

            while next_node:
                # h4 tag means we're at the next course
                if getattr(next_node, 'name', None) == 'h4':
                    break
                # <a> tag is a link to a semester
                if getattr(next_node, 'name', None) == 'a':
                    years_text.append(next_node.get_text(strip=True))
                
                elif isinstance(next_node, NavigableString):
                    text = parse_semesters(next_node.strip())
                    years_text.extend(text)
                    
                next_node = next_node.next_sibling

            # Filter and clean the collected text
            other_years = [year for year in years_text if re.match(r'\b(Spring|Fall) \d{4}\b', year)]


        course_data = {
            "title": course_title,
            "description": description,
            "details": details,
            "other_years": other_years
        }
        
        courses.append(course_data)
    
    return json.dumps(courses, indent=4, ensure_ascii=False)


course_json = fetch_page_json("2425", "727946")
print(course_json)