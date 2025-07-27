# Adobe-Hackathon-1B
This project processes a folder of PDFs, extracts relevant sections using heading detection, and ranks them based on relevance to a specific **persona** and **job-to-be-done**. It generates a structured JSON output containing:

- Extracted and ranked section metadata
- A refined summary of the most relevant content from each document

---

## 📁 Folder Structure

```text
.
├── Input
│   ├── input.json              // Configuration file
│   └── pdfs/                   // Folder containing PDFs
├── Output
│   └── output_{persona}.json  // Output file (dynamic name based on persona)
├── main.py                    // Main processing script
└── README.md                  // You're reading this!
└── DockerFile                 // Defines container environment for consistent execution and deployment
````
---

## 📝 Configuration (`input.json`)

The `Input/input.json` file controls how the processing runs. Here's a sample:
```text

{
    "pdf_folder": "Input/pdfs", // This is the folder where all the pdfs to be processed are stored
    "persona": "Travel Planner", // The necessary persona needs to be given as an input here
    "job_to_be_done": "Plan a trip of 4 days for a group of 10 college friends.", // The necessary job_to_be_done needs to be given as an input here
    "output_file": "Output/output_{persona}.json" // File path where the output is saved, the file path contains the persona which was given before
}
````
### Fields:
- **pdf_folder:** Relative path to the folder containing the PDFs.

- **persona:** The role or perspective from which sections should be evaluated.

- **job_to_be_done:** The task that should be achieved using the information in the PDFs.

- **output_file:** Template for naming the output file. {persona} will be replaced with a sanitized, lowercase version of the persona.

## ▶️ Running the Script
- **To run the processor:**
  - python main.py
- **This will:**
  - Read Input/input.json
  - Process all PDFs in Input/pdfs
  - Save the results as Output/output_{persona}.json

## 🔍 What the Script Does

 ### 1. Extract Text and Headings
- **Library used:** 
  - PyMuPDF (fitz)
- **Function(s):** 
  - extract_headings_and_text()
  - is_likely_heading()
  - collect_heading_frequencies()

- **How it works:**
    
    - For each PDF page, it extracts all visible text lines.
    
    - It uses a heuristic to detect likely headings:
    
    - Ignores too long/short lines.
    
    - Prefers lines with high capitalization or title case ratio.
    
    - Counts how often each heading appears across all PDFs.
    
    - Removes noisy headings that occur in >40% of PDFs to reduce redundancy (like common section names such as "Introduction").

 ### 2. Detect Sections
- **Function:** 
  - detect_sections_between_headings()
    
- **How it works:**
    
    - **For each document:**
    
       - It iterates through the cleaned lines and captures the positions of valid headings (excluding common ones).
    
       - A section is defined as text between two headings.
    
    - **Each section is stored with:**
    
      - Its title (heading),
    
      - Page number (where it starts),
    
      - Raw text content.

 ### 3. Filter and Match Sections
 - **Library used:** 
   - fuzzywuzzy for token-based matching
    
- **Function:** 
    - match_sections()
    - refine_text()
    
- **How it works:**
    
    - The raw text of each section is cleaned and truncated (up to 3000 chars) for scoring.
    
    - Each section’s text is matched against the Job-to-be-Done using fuzz.token_set_ratio().
    
    - **For each document:**
    
       - The section with the highest similarity is chosen as the best heading match.
    
       - The best subsection is also selected independently (could be same or different from heading).
    
    - **Final result includes:**
    
      - Top 5 sections ranked by heading match score.
    
      - Most relevant refined subsection text per document (even if it’s not from the top-5 heading match).

 ### 4. Output Structured JSON
- **Function:**
      - process_pdfs()
      - save_output()
    
- **Includes:**

  - **metadata:**
      - List of input PDFs
      - persona, job-to-be-done
      - timestamp.
    
  - **extracted_sections:**
    - Top 5 matched headings across all PDFs.
    
  - **subsection_analysis:**
    - Best-matching subsection content per top-ranked document.
    
- **Output Filename:**
    
   - **Format:** 
       - "Output/output_{persona}.json"

Persona is sanitized to be filename-safe (spaces, special chars replaced with _).
```text
  {
    "metadata": {
      "input_documents": [...],
      "persona": "Travel Planner",
      "job_to_be_done": "...",
      "processing_timestamp": "..."
    },
    "extracted_sections": [
      {
        "document": "filename.pdf",
        "section_title": "Section Title",
        "importance_rank": 1,
        "page_number": 5
      },
      ...
    ],
    "subsection_analysis": [
      {
        "document": "filename.pdf",
        "refined_text": "Most relevant content...",
        "page_number": 5
      },
      ...
    ]
  }
````
### 5. Save Output
   - The output JSON is saved to a file in the Output/ folder, **e.g: Output/output_travel_planner.json**

## 🐳 Run Using Docker
  ### 🛠️ 1. Build Docker Image
  - Open Command Prompt inside the project folder and run:
     - **docker build -t 1b_adobe .**
  
  ### 🚀 2. Run the Container
  - Ensure your Input/ and Output/ folders exist and are populated.
  - **Then run the container:** 
    ```text
    docker run --rm ^
      -v "%cd%/Input:/app/Input" ^
      -v "%cd%/Output:/app/Output" ^
      1b_adobe
    ````
  
  ### 🔁 Notes:
  - %cd%/Input:/app/Input mounts the local Input folder into the container.
  - %cd%/Output:/app/Output mounts the Output folder so results are accessible after the container exits.
  - --rm removes the container after execution.
