#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  4 20:35:05 2024

@author: gabriel
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import pandas as pd
import numpy as np
import os

# webcrawling script
BASE_URL = "http://collegecatalog.uchicago.edu/"

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
})


def make_request(url):
    time.sleep(3)
    response = session.get(url)
    if response.status_code == 200:
        return response.content
    else:
        return None


def parse_course_page(content):
    soup = BeautifulSoup(content, 'html.parser')
    course_blocks = soup.select('div.courseblock')
    course_data = []
    for block in course_blocks:
        title = block.find('p', class_='courseblocktitle')
        desc = block.find('p', class_='courseblockdesc')
        detail = block.find('p', class_='courseblockdetail')

        course_info = {
            'course_number': title.get_text(strip=True) if title else None,
            'description': desc.get_text(strip=True) if desc else None,
            'extra info': detail.get_text(strip=True) if detail else None,
        }
        course_data.append(course_info)
    return course_data


def crawl_catalog():
    courses_data = []

    programs_content = make_request(BASE_URL + "thecollege/programsofstudy/")
    if programs_content:
        soup = BeautifulSoup(programs_content, 'html.parser')
        for link in soup.select('ul.nav.leveltwo a'):
            full_url = BASE_URL.rstrip('/') + link['href']
            department_content = make_request(full_url)
            if department_content:
                courses_data.extend(parse_course_page(department_content))

    return courses_data


def main():
    courses_data = crawl_catalog()
    csv_filename = 'uchicago_courses.csv'
    fieldnames = ['course_number', 'description', 'extra info']
    with open(csv_filename, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for course in courses_data:
            writer.writerow(course)

    df = pd.read_csv(csv_filename)
    return df


if __name__ == "__main__":
    csv_filename = main()
    csv_directory = "/Users/gabriel/Documents"
    os.system(f"open {csv_directory}")

    df = main()
    df.head()


# formats the extra info column and extracts all the relevant info from the string to make a new dataframe
instructors = []
terms_offered = []
prerequisites = []
notes = []
equivalent_courses = []


def extract_info(text, prefix, next_prefixes):
    start = text.find(prefix)
    if start == -1:
        return None, text
    start += len(prefix)
    end = len(text)
    for np in next_prefixes:
        temp_end = text.find(np)
        if temp_end != -1 and temp_end > start:
            end = min(end, temp_end)
    return text[start:end].strip(), text[end:]


for info in df['extra info']:
    if pd.isnull(info):
        info = ''
    else:
        info = str(info)

    instructor, info = extract_info(info, 'Instructor(s):', [
                                    'Terms Offered:', 'Prerequisite(s):', 'Note(s):', 'Equivalent Course(s):'])
    term_offered, info = extract_info(info, 'Terms Offered:', [
                                      'Prerequisite(s):', 'Note(s):', 'Equivalent Course(s):'])
    prerequisite, info = extract_info(info, 'Prerequisite(s):', [
                                      'Note(s):', 'Equivalent Course(s):'])
    note, info = extract_info(info, 'Note(s):', ['Equivalent Course(s):'])
    equivalent_course, _ = extract_info(info, 'Equivalent Course(s):', [])

    instructors.append(instructor)
    terms_offered.append(term_offered)
    prerequisites.append(prerequisite)
    notes.append(note)
    equivalent_courses.append(equivalent_course)

df2 = pd.DataFrame({
    'Instructors': instructors,
    'Terms Offered': terms_offered,
    'Prerequisites': prerequisites,
    'Notes': notes,
    'Equivalent Courses': equivalent_courses
})

# combines the two dataframes to have one final one with all the data
final_df = pd.concat([df, df2], axis=1)
final_df = final_df.drop(columns=['extra info'])
final_df

final_df.drop_duplicates(subset='course_number', inplace=True)
