import os
import json
import fitz  # PyMuPDF
from datetime import datetime
from collections import defaultdict, Counter
from fuzzywuzzy import fuzz

def is_likely_heading(line):
    line = line.strip()
    if len(line) > 100 or len(line) < 10:
        return False
    if line.endswith("."):
        return False
    words = line.split()
    if not words:
        return False
    title_case_ratio = sum(w[0].isupper() for w in words if w[0].isalpha()) / len(words)
    capital_ratio = sum(c.isupper() for c in line) / (len(line) + 1e-5)
    return title_case_ratio > 0.6 or capital_ratio > 0.4


def extract_headings_and_text(pdf_path):
    doc = fitz.open(pdf_path)
    pages_lines = []
    for page_num, page in enumerate(doc):
        lines = [line.strip() for line in page.get_text().split("\n") if line.strip()]
        pages_lines.append((page_num + 1, lines))
    return pages_lines


def collect_heading_frequencies(pdf_folder):
    heading_counts = Counter()
    doc_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith(".pdf")]
    for doc_file in doc_files:
        pages_lines = extract_headings_and_text(os.path.join(pdf_folder, doc_file))
        for _, lines in pages_lines:
            for line in lines:
                if is_likely_heading(line):
                    heading_counts[line.strip().lower()] += 1
    return heading_counts, len(doc_files)


def detect_sections_between_headings(pages_lines, filename, ignore_headings):
    sections = []
    all_lines = []
    headings = []

    for page_number, lines in pages_lines:
        for idx, line in enumerate(lines):
            abs_index = len(all_lines)
            clean_line = line.strip()
            if is_likely_heading(clean_line) and clean_line.lower() not in ignore_headings:
                headings.append((abs_index, page_number, clean_line))
            all_lines.append((page_number, clean_line))

    headings.append((len(all_lines), None, None))  # Dummy end heading

    for i in range(len(headings) - 1):
        start_idx, start_page, title = headings[i]
        end_idx, _, _ = headings[i + 1]
        content_lines = [l[1] for l in all_lines[start_idx + 1:end_idx]]
        section_text = "\n".join(content_lines).strip()
        if section_text:
            sections.append({
                "document": filename,
                "section_title": title,
                "page_number": start_page,
                "raw_text": section_text
            })

    return sections


def refine_text(raw_text, max_chars=3000):
    lines = [line.strip() for line in raw_text.splitlines() if len(line.strip()) > 30]
    return " ".join(lines)[:max_chars]


def match_sections(sections, job_description):
    doc_to_best_heading = {}
    doc_to_best_subsection = {}

    grouped_by_doc = defaultdict(list)
    for sec in sections:
        grouped_by_doc[sec["document"]].append(sec)

    for doc, doc_sections in grouped_by_doc.items():
        best_heading = {"match_score": -1}
        best_subsection = {"match_score": -1}

        for sec in doc_sections:
            refined = refine_text(sec["raw_text"])
            score = fuzz.token_set_ratio(refined.lower(), job_description.lower())
            sec["match_score"] = score
            sec["refined_text"] = refined

            if score > best_heading.get("match_score", -1):
                best_heading = sec
            if score > best_subsection.get("match_score", -1):
                best_subsection = sec

        doc_to_best_heading[doc] = best_heading
        doc_to_best_subsection[doc] = best_subsection

    return doc_to_best_heading, doc_to_best_subsection


def process_pdfs(pdf_folder, persona, job_to_be_done):
    input_docs = [f for f in os.listdir(pdf_folder) if f.lower().endswith(".pdf")]

    # Step 1: Compute heading frequencies
    heading_freqs, num_docs = collect_heading_frequencies(pdf_folder)
    threshold = int(0.4 * num_docs)  # e.g. if appears in >40% of PDFs, skip it
    ignore_headings = {h for h, count in heading_freqs.items() if count > threshold}

    all_sections = []

    for doc in input_docs:
        path = os.path.join(pdf_folder, doc)
        pages_lines = extract_headings_and_text(path)
        sections = detect_sections_between_headings(pages_lines, doc, ignore_headings)
        all_sections.extend(sections)

    # Step 2: Match by content
    headings, subsections = match_sections(all_sections, job_to_be_done)

    top_headings = sorted(headings.values(), key=lambda x: x["match_score"], reverse=True)[:5]

    metadata = {
        "input_documents": input_docs,
        "persona": persona,
        "job_to_be_done": job_to_be_done,
        "processing_timestamp": datetime.utcnow().isoformat()
    }

    extracted_sections = [
        {
            "document": sec["document"],
            "section_title": sec["section_title"],
            "importance_rank": idx + 1,
            "page_number": sec["page_number"]
        }
        for idx, sec in enumerate(top_headings)
    ]

    subsection_analysis = [
        {
            "document": subsections[sec["document"]]["document"],
            "refined_text": subsections[sec["document"]]["refined_text"],
            "page_number": subsections[sec["document"]]["page_number"]
        }
        for sec in top_headings
    ]

    return {
        "metadata": metadata,
        "extracted_sections": extracted_sections,
        "subsection_analysis": subsection_analysis
    }


def save_output(data, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    import re

    with open("Input/input.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    pdf_folder = config["pdf_folder"]
    persona = config["persona"]
    job_description = config["job_to_be_done"]
    output_template = config["output_file"]

    # Make persona filename-safe
    safe_persona = re.sub(r'[^\w\-]+', '_', persona.strip().lower())

    # Debug: Check if formatting works
    print("Template before format:", output_template)
    output_file = output_template.format(persona=safe_persona)
    print("Resolved output file:", output_file)

    result = process_pdfs(pdf_folder, persona, job_description)
    save_output(result, output_file)

    print("✅ Done! Saved to", output_file)
