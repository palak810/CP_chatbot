from bs4 import BeautifulSoup
import cloudscraper
import sys
import os
import json
import re
from config import PROBLEMS_DIR

sys.stdout.reconfigure(encoding='utf-8')

def scrap_ps(url, contest_id, problem_letter):
    request = cloudscraper.create_scraper()
    html_text = request.get(url).text
    soup = BeautifulSoup(html_text, 'lxml')

    title_div = soup.find("div", class_="title")
    problem_div = soup.find("div", class_="problem-statement")
    if not title_div or not problem_div:
        return

    name = title_div.text.strip()
    paragraphs = problem_div.find_all("p")
    statement = "\n".join([
        re.sub(r"\\[a-zA-Z]+", "", re.sub(r'\$\$\$(.*?)\$\$\$', r'\1', p.text))
        for p in paragraphs
    ])

    tags = [tag.text.strip() for tag in soup.find_all("span", class_="tag-box")]
    time_limit = soup.find("div", class_="time-limit").text.replace("time limit per test", "").strip()
    memory_limit = soup.find("div", class_="memory-limit").text.replace("memory limit per test", "").strip()

    input_spec = soup.find("div", class_="input-specification")
    input_text = input_spec.p.text if input_spec and input_spec.p else ""
    input_text = re.sub(r'\$\$\$(.*?)\$\$\$', r'\1', input_text)
    input_text = re.sub(r'\\le', '≤', input_text)
    input_text = re.sub(r'\\ge', '≥', input_text)
    input_text = input_text.replace('&lt;', '<').replace('&gt;', '>')

    output_spec = soup.find("div", class_="output-specification")
    output_text = output_spec.p.text if output_spec and output_spec.p else ""

    problem_id = f"{contest_id}{problem_letter}"
    file_path = os.path.join(PROBLEMS_DIR, f"{problem_id}.json")
    os.makedirs(PROBLEMS_DIR, exist_ok=True)

    data = {
        "id": problem_id,
        "contest_id": int(contest_id),
        "problem_letter": problem_letter,
        "title": name,
        "statement": statement,
        "input": input_text,
        "output": output_text,
        "time_limit": time_limit,
        "memory_limit": memory_limit,
        "tags": tags
    }

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(problem_id)


if __name__ == '__main__':
    count = 0
    max_count = 200

    for contest_id in range(1000, 1050):
        for letter in "ABCDEFGH":
            if count >= max_count:
                sys.exit(0)

            url = f"https://codeforces.com/contest/{contest_id}/problem/{letter}"
            scrap_ps(url, contest_id, letter)
            count += 1
