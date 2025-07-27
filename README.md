# adobe-hackathon-1b
This project processes a folder of PDFs, extracts relevant sections using heading detection, and ranks them based on relevance to a specific **persona** and **job-to-be-done**. It generates a structured JSON output containing:

- Extracted and ranked section metadata
- A refined summary of the most relevant content from each document

---

## 📁 Folder Structure

.
├── Input
│ ├── input.json # Configuration file
│ └── pdfs/ # Folder containing all PDF files to be processed
├── Output
│ └── output_{persona}.json # Output file will be generated here which is dynamically saved with the persona taken as the input
├── main.py # Main processing script
└── README.md # You're reading this!

---

## 📝 Configuration (`input.json`)

The `Input/input.json` file controls how the processing runs. Here's a sample:

```json
{
    "pdf_folder": "Input/pdfs", # This is the folder where all the pdfs to be processed are stored
    "persona": "Travel Planner", # The necessary persona needs to be given as an input here
    "job_to_be_done": "Plan a trip of 4 days for a group of 10 college friends.", # The necessary job_to_be_done needs to be given as an input here
    "output_file": "Output/output_{persona}.json" # File path where the output is saved, the file path contains the persona which was given before
}
Fields:
pdf_folder: Relative path to the folder containing the PDFs.

persona: The role or perspective from which sections should be evaluated.

job_to_be_done: The task that should be achieved using the information in the PDFs.

output_file: Template for naming the output file. {persona} will be replaced with a sanitized, lowercase version of the persona.

▶️ Running the Script
To run the processor:

python main.py
This will:

Read Input/input.json

Process all PDFs in Input/pdfs

Save the results as Output/output_{persona}.json

🔍 What the Script Does

1. Extract Text and Headings
  Uses PyMuPDF (fitz) to extract raw text from each PDF.
  Identifies headings based on:
    Font styling (heuristically guessed using text length and capitalization).
    Removes noisy headings that appear in too many documents.

2. Detect Sections
  Scans each document to segment text between detected headings.
  Associates each section with its page number and title.

3. Filter and Match Sections
  Fuzzy Matching (fuzz.token_set_ratio) is applied to compare each section's content with the job-to-be-done.
  For each document:
  One best heading match is selected (based on section title + text).
  One best subsection is selected (based only on content).

4. Assemble Output JSON
  Generates a structured dictionary like:
  
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
5. Save Output
  The output JSON is saved to a file in the Output/ folder, e.g.:
  Output/output_travel_planner.json

🐳 Run Using Docker
  🛠️ 1. Build Docker Image
    Open Command Prompt inside the project folder and run:
    
    docker build -t 1b_adobe .
  
  🚀 2. Run the Container
    Ensure your Input/ and Output/ folders exist and are populated.
    Then run the container:
    
    docker run --rm ^
      -v "%cd%/Input:/app/Input" ^
      -v "%cd%/Output:/app/Output" ^
      1b_adobe
  
  🔁 Notes:
    %cd%/Input:/app/Input mounts the local Input folder into the container.
    
    %cd%/Output:/app/Output mounts the Output folder so results are accessible after the container exits.
    
    --rm removes the container after execution.
