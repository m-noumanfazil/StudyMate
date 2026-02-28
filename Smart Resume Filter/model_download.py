from huggingface_hub import snapshot_download
import spacy

# Download the model locally
model_path = snapshot_download("amjad-awad/skill-extractor", repo_type="model")

# Load it with spaCy
nlp = spacy.load(model_path)

# Example Job Description text
jd_text = """
We are looking for an AI Security Engineer who can design secure AI systems. 
Required skills include Python, TensorFlow, PyTorch, adversarial machine learning, model robustness testing, secure coding practices, threat modeling, and cloud security (AWS, GCP). 
Familiarity with container security using Docker and Kubernetes is desirable.
"""

# Process with the skill extractor
doc = nlp(jd_text)

# Extract skills
skills = [ent.text for ent in doc.ents if ent.label_ == "SKILLS"]

# Print results
print("Extracted skills:", skills)
We are hiring a Backend Developer with strong experience in Python, FastAPI, and SQL. 
The candidate should have knowledge of REST APIs and basic Docker usage. 
Minimum 3 years of professional experience required.