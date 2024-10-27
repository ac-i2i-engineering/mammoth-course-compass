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

    #def convert_unicode_escape(text):
    #    return re.sub(r'\\u[0-9a-fA-F]{4}', lambda x: x.group(0).encode('utf-8').decode('unicode_escape'), text)
    #return convert_unicode_escape("Hawai\u2018i")


    for title_tag in course_div.find_all('h4'):
        course_title = title_tag.get_text(strip=True)
        
        
        paragraphs = []
        for sibling in title_tag.find_next_siblings():
            if sibling.name == 'h4':  # Stop if we reach the next course title
                break
            if sibling.name == 'p':
                paragraphs.append(sibling.get_text(strip=True))

        course_data = {
            "title": course_title,
            "details": paragraphs
        }
        courses.append(course_data)
    
    return json.dumps(courses, indent=4, ensure_ascii=False)


course_json = fetch_page_json("2425", "727941")
print(course_json)