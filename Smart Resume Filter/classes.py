# classes.py
# classes.py
# classes.py
# classes.py
import os
import re
from groq import Groq
from dotenv import load_dotenv
import json
import fitz
# load variables from .env file
load_dotenv()

class JobDescription:
    def __init__(self):
        self.skills = []
        self.required_experience = 0
        self.raw_text = ""
        # Get Groq API key from environment
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    

    def insert_text(self):
        print("\nPaste the Job Description text below (end with empty line):")
        lines = []
        while True:
            line = input()
            if not line.strip():
                break
            lines.append(line)
    
        self.raw_text = " ".join(lines)
    
        prompt = f"""
    You are a strict data extraction engine.
    
    Extract ONLY:
    1. A list of required technical skills.
    2. Total required professional experience in years (integer).
    
    Return ONLY valid JSON.
    No explanation.
    No markdown.
    No extra text.
    
    Format exactly like this:
    
    {{
      "skills": ["skill1", "skill2"],
      "experience_years": 3
    }}
    
    If experience is not mentioned, return 0.
    If no skills found, return empty list.
    
    Job Description:
    \"\"\"{self.raw_text}\"\"\"
    """
    
        try:
            response = self.client.chat.completions.create(
                model="qwen/qwen3-32b",
                temperature=0,   # VERY IMPORTANT
                messages=[
                    {"role": "system", "content": "You extract structured job requirement information."},
                    {"role": "user", "content": prompt}
                ],
                reasoning_effort="none"
            )
            
            output_text = response.choices[0].message.content.strip()
            #print("RAW MODEL OUTPUT:")
            #print(output_text)
            # Parse safely
            result = json.loads(output_text)
    
            # Validate structure
            skills = result.get("skills", [])
            experience = result.get("experience_years", 0)
    
            if not isinstance(skills, list):
                skills = []
    
            if not isinstance(experience, (int, float)):
                experience = 0
    
            self.skills = [s.lower().strip() for s in skills]
            self.required_experience = int(experience)
    
            print("\n✅ Job Description processed successfully!")
            print("Extracted skills:", self.skills)
            print("Required experience (years):", self.required_experience)
    
        except Exception as e:
            print("❌ Error processing Job Description:", str(e))
            self.skills = []
            self.required_experience = 0

       

class Resume:
    def __init__(self, name, skills, experience):
        self.name = name
        self.skills = skills
        self.experience = experience
        self.score = 0.0
        self.skill_match_pct = 0.0  # initialize
        self.exp_score_pct = 0.0    # initialize

class ResumeRankingSystem:
    def __init__(self):
        self.job = None
        self.resumes = []
    def insert_resumes(self):
        if self.job is None:
            print("❌ Please insert a Job Description first!")
            return
    
        # 1️⃣ Collect all resume paths at once
        print("\nEnter path(s) to PDF resume(s), separated by commas:")
        paths = input().split(",")
        paths = [p.strip() for p in paths if p.strip()]
    
        if not paths:
            print("❌ No valid paths entered.")
            return
    
        # 2️⃣ Loop over each path to process resumes
        for path in paths:
            if not os.path.isfile(path):
                print(f"❌ File not found: {path}")
                continue
    
            try:
                # Extract text from PDF
                doc = fitz.open(path)
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
    
                # Clean text
                text_clean = re.sub(r'\s+', ' ', text).strip()
                #print("Text cleaned")
                #print(text_clean)
                # Prepare AI prompt
                prompt = f"""
    Extract skills and total professional experience in years from the following resume text.
    Return JSON ONLY with keys exactly: "skills" (list) and "experience_years" (number).
    
    Resume text:
    \"\"\"{text_clean}\"\"\"
    """
    
                # AI call
                response = self.job.client.chat.completions.create(
                    model="qwen/qwen3-32b",
                    temperature=0,
                    messages=[
                        {"role": "system", "content": "Extract structured resume info."},
                        {"role": "user", "content": prompt}
                    ]
                )
    
                output_text = response.choices[0].message.content.strip()
                output_text = re.sub(r"<think>.*?</think>", "", output_text, flags=re.DOTALL).strip()
                print("Output:\n ")
                print(output_text)
                if not output_text:
                   raise ValueError("Model returned empty response")

                result = json.loads(output_text)
                skills = [s.lower().strip() for s in result.get("skills", [])]
                experience = result.get("experience_years", 0)
    
                # Store in resumes list
                resume_name = os.path.basename(path)
                self.resumes.append(Resume(name=resume_name, skills=skills, experience=experience))
    
                print(f"✅ Processed: {resume_name}")
                print(f"   Skills: {skills}")
                print(f"   Experience: {experience} years")
    
            except Exception as e:
                print(f"❌ Error processing {path}: {e}")
    # Inside ResumeRankingSystem class

    def calculate_scores(self):
        if self.job is None:
            print("❌ Please insert a Job Description first!")
            return
    
        if not self.resumes:
            print("❌ No resumes to score!")
            return
    
        print("\nCalculating scores for all candidates...")
        for resume in self.resumes:
            # Skill match calculation
            required_skills = set(self.job.skills)
            candidate_skills = set(resume.skills)
            matched_skills = required_skills.intersection(candidate_skills)
    
            if required_skills:
                skill_match_pct = len(matched_skills) / len(required_skills) * 100
            else:
                skill_match_pct = 0.0
    
            # Experience score calculation
            exp_ratio = resume.experience / self.job.required_experience if self.job.required_experience > 0 else 0
            exp_score_pct = min(exp_ratio * 100, 100)
    
            # Weighted final score: 70% skills, 30% experience
            final_score = skill_match_pct * 0.7 + exp_score_pct * 0.3
    
            # Store in resume object for later reference
            resume.skill_match_pct = round(skill_match_pct, 1)
            resume.exp_score_pct = round(exp_score_pct, 1)
            resume.score = round(final_score, 1)
    
            print(f"✅ {resume.name} | Skill Match: {resume.skill_match_pct}% | Experience Score: {resume.exp_score_pct}% | Final Score: {resume.score}")
    
        # Sort resumes immediately by final score descending
        self.resumes.sort(key=lambda r: r.score, reverse=True)
        print("\n🎯 Scoring completed! Candidates sorted by score.\n\n")
        print("\n--- DEBUG INFO ---")
        print("JD Skills:", required_skills)
        print("Resume Skills:", candidate_skills)
        print("Matched Skills:", matched_skills)
        print("-------------------\n")
    
    def show_sorted_results(self):
        if not self.resumes:
            print("❌ No resumes to display!")
            return
    
        print("\n--- Ranked Candidates ---")
        for i, r in enumerate(self.resumes):
            print(f"{i+1}. {r.name} | Final Score: {r.score} | Skill Match: {r.skill_match_pct}% | Experience: {r.exp_score_pct}%")

    def reset_system(self):
        self.job = None
        self.resumes = []
        print("✅ System reset: Job Description and all resumes cleared.")