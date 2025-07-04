import streamlit as st
import os
import json
import faiss
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import re


genai.configure(api_key=st.secrets["GEMINI_API_KEY"])


@st.cache_resource
def load_data():
    problems, texts = [], []
    for fname in os.listdir("data/problems"):
        if fname.endswith(".json"):
            with open(f"data/problems/{fname}", encoding="utf-8") as f:
                p = json.load(f)
                problems.append(p)
                texts.append(f"{p['title']} {p['statement']}")

    if not problems:
        st.warning("No problem files found.")
        st.stop()

    model = SentenceTransformer('all-MiniLM-L6-v2')
    vecs = model.encode(texts, show_progress_bar=False)
    idx = faiss.IndexFlatL2(vecs.shape[1])
    idx.add(vecs)
    return problems, vecs, idx, model

def match_problem(problems, q):
    m = re.search(r'(\d+[A-Z]?)', q, re.IGNORECASE)
    if m:
        pid = m.group(1).upper()
        return next((p for p in problems if p['id'].upper() == pid), None)
    q = q.lower()
    return next((p for p in problems if q in p['title'].lower()), None)

def match_tag(problems, tag):
    return [p for p in problems if any(tag.lower() in t.lower() for t in p.get('tags', []))]

GEMINI_MODEL = 'gemini-2.0-flash'
def get_solution(problem):
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        prompt = f"Title: {problem['title']}\n\n{problem['statement']}\n\nTags: {', '.join(problem['tags'])}"
        resp = model.generate_content(prompt)
        return resp.text
    except Exception as e:
        return f"Gemini error: {e}"

st.title("Codeforces Helper")
problems, vecs, index, model = load_data()
query = st.text_input("Ask for a problem or topic:")

if query:
    prob = match_problem(problems, query)
    if prob:
        st.markdown(f" {prob['id']} - {prob['title']}")
        st.markdown(f"Tags: {', '.join(prob['tags'])}")
        st.markdown(prob['statement'])
        if any(k in query.lower() for k in ["solution", "solve", "how to"]):
            with st.spinner("Generating solution..."):
                st.write(get_solution(prob))
        st.stop()

    for tag_kw in ["problems on", "questions on", "related to", "tag", "topic"]:
        if tag_kw in query.lower():
            tag = query.lower().split(tag_kw)[-1].strip().rstrip("problems questions")
            tagged = match_tag(problems, tag)
            if tagged:
                st.markdown(f"### Problems tagged with '{tag}':")
                for p in tagged[:5]:
                    st.markdown(f"- **[{p['id']}] {p['title']}**\n\n{p['statement'][:300]}...\n\nTags: {', '.join(p['tags'])}")
                if len(tagged) > 5:
                    st.info(f"And {len(tagged) - 5} more.")
                st.stop()


    vec = model.encode([query])
    _, idx = index.search(vec, k=1)
    best = problems[idx[0][0]]
    st.markdown(f" Closest match: {best['id']} - {best['title']}")
    st.markdown(f"Tags:{', '.join(best['tags'])}")
    st.markdown(best['statement'])
    if any(k in query.lower() for k in ["solution", "solve", "how to"]):
        with st.spinner("Generating solution..."):
            st.write(get_solution(best))
else:
    st.write("Enter a query to begin.")