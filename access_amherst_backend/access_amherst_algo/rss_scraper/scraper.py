import json

import requests
from bs4 import BeautifulSoup

import re


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
        
        #TODO: make this work with a mix of text and <a> tags
        if other_years_tag and "Other years" in other_years_tag.get_text(strip=True):
            # Initialize a list to hold the text content
            years_text = []
            next_node = other_years_tag.find_next_sibling()

            while next_node:
                # If we find a <a> tag, extract its text
                if next_node.name == 'a':
                    years_text.append(next_node.get_text(strip=True))
                elif next_node.string:  # If it's a text node, we may find plain text
                    years_text.append(next_node.strip())
                # Move to the next sibling node
                next_node = next_node.find_next_sibling()

            # Filter and clean the collected text
            other_years = [year for year in years_text if re.match(r'\b(Spring|Fall) \d{4}\b', year)]


    
        # Construct course data dictionary
        course_data = {
            "title": course_title,
            "description": description,
            "details": details,
            "other_years": other_years
        }
        
        courses.append(course_data)
    
    return json.dumps(courses, indent=4, ensure_ascii=False)


course_json = fetch_page_json("2425", "727941")
print(course_json)