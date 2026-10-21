import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import sys

class JobRecommender:
    def __init__(self):
        print("Loading embedding model... (This may take a moment)")
        # Load a pre-trained model. 'all-MiniLM-L6-v2' is fast and effective.
        try:
            self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        except Exception as e:
            print(f"Error loading SentenceTransformer model: {e}")
            print("Please make sure you have an internet connection and the 'sentence-transformers' library installed.")
            sys.exit(1)
        
        # --- Our "Vector Database" ---
        # We now store a dictionary for each profile:
        # 'description': For semantic vector search
        # 'skills': A new nested dictionary for 'basic', 'intermediate', and 'advanced'
        # Skills are stored in lowercase to ensure consistent matching.
        self.job_profiles = {
            # --- Data & AI Roles ---
            "Data Scientist": {
                "description": """
                    Focuses on statistical analysis, machine learning, and data visualization. 
                    Uses Python, R, Scikit-learn, Pandas, and SQL to find insights from data. 
                    Builds predictive models with TensorFlow or PyTorch.
                """,
                "skills": {
                    "basic": ["python", "sql", "pandas", "numpy", "data visualization", "scikit-learn"],
                    "intermediate": ["r", "tensorflow", "pytorch", "statistics", "tableau"],
                    "advanced": ["deep learning", "nlp", "apache spark", "experimental design"]
                }
            },
            "Data Analyst": {
                "description": """
                    Focuses on interpreting data, analyzing results, and creating reports.
                    Expert in SQL, Microsoft Excel, and BI tools like Tableau or Power BI.
                    Cleans and visualizes data to help business make better decisions.
                """,
                "skills": {
                    "basic": ["sql", "excel", "data visualization"],
                    "intermediate": ["tableau", "power bi", "python", "pandas", "statistics"],
                    "advanced": ["r", "etl", "data modeling"]
                }
            },
            "Data Engineer": {
                "description": """
                    Builds and maintains data pipelines and infrastructure.
                    Expert in ETL processes, Apache Spark, Kafka, and data warehousing (like BigQuery, Redshift, or Snowflake).
                    Ensures data is clean, reliable, and available for Data Scientists.
                """,
                "skills": {
                    "basic": ["python", "sql", "etl"],
                    "intermediate": ["apache spark", "kafka", "data warehousing", "aws", "gcp", "azure"],
                    "advanced": ["bigquery", "redshift", "snowflake", "data modeling", "kubernetes"]
                }
            },
            "Machine Learning Engineer": {
                "description": """
                    Builds and deploys production-level machine learning models. 
                    Strong in Python, TensorFlow, PyTorch, and Scikit-learn. 
                    Understands MLOps, model optimization (like ONNX), and serving.
                """,
                "skills": {
                    "basic": ["python", "scikit-learn", "pandas", "git"],
                    "intermediate": ["tensorflow", "pytorch", "sql", "docker", "rest apis"],
                    "advanced": ["mlops", "onnx", "kubernetes", "aws sagemaker", "model optimization"]
                }
            },
            "Computer Vision Engineer": {
                "description": """
                    A specialist in machine learning for image and video analysis. 
                    Deep knowledge of OpenCV, MediaPipe, YOLO, and ONNX. 
                    Uses PyTorch or TensorFlow for custom model training. 
                    Works on tasks like object detection and image segmentation.
                """,
                "skills": {
                    "basic": ["python", "opencv", "numpy"],
                    "intermediate": ["pytorch", "tensorflow", "yolo", "scikit-learn", "image processing"],
                    "advanced": ["mediapipe", "onnx", "deep learning", "model optimization", "tensorrt", "cuda"]
                }
            },
            "NLP Engineer": {
                "description": """
                    Specializes in models that understand human language.
                    Works with text data, sentiment analysis, and chatbots.
                    Uses libraries like Hugging Face Transformers, spaCy, and NLTK.
                """,
                "skills": {
                    "basic": ["python", "nltk", "regex"],
                    "intermediate": ["spacy", "scikit-learn", "tensorflow", "pytorch", "sentiment analysis"],
                    "advanced": ["hugging face", "transformers", "large language models (llms)", "bert", "rag"]
                }
            },
            "Generative AI Engineer": {
                "description": """
                    Specializes in Large Language Models (LLMs) and diffusion models. 
                    Uses Hugging Face, transformers, and prompt engineering. 
                    Builds applications on top of generative AI, like RAG systems and AI agents.
                """,
                "skills": {
                    "basic": ["python", "pytorch", "tensorflow", "hugging face"],
                    "intermediate": ["large language models (llms)", "prompt engineering", "transformers", "api integration"],
                    "advanced": ["rag", "fine-tuning", "vector databases", "ai agents", "diffusion models"]
                }
            },
            "AI Research Scientist": {
                "description": """
                    Focuses on creating new AI models and algorithms.
                    Requires deep academic knowledge (often PhD/Masters) in math and computer science.
                    Publishes papers and pushes the boundaries of AI, working with PyTorch and TensorFlow.
                """,
                "skills": {
                    "basic": ["python", "pytorch", "tensorflow", "numpy", "linear algebra", "calculus"],
                    "intermediate": ["deep learning", "research", "statistics"],
                    "advanced": ["paper writing", "algorithm design", "phd"]
                }
            },
            "Business Intelligence (BI) Analyst": {
                "description": """
                    Creates dashboards and reports to track business performance.
                    A mix of data analyst and business strategist. Uses SQL, Tableau, Power BI, and Looker.
                    Focuses on KPIs (Key Performance Indicators) and trends.
                """,
                "skills": {
                    "basic": ["sql", "excel", "data visualization"],
                    "intermediate": ["tableau", "power bi", "looker", "business acumen"],
                    "advanced": ["data warehousing", "etl", "kpi strategy"]
                }
            },
            
            # --- Software Engineering Roles ---
            "Backend Developer": {
                "description": """
                    Builds the server-side logic of applications. 
                    Expert in Python (Django, FastAPI) or other languages like Java (Spring), Go, or Node.js.
                    Manages databases like PostgreSQL/MySQL and designs REST APIs.
                """,
                "skills": {
                    "basic": ["python", "java", "node.js", "git", "rest apis", "crud operations"],
                    "intermediate": ["django", "fastapi", "spring", "postgresql", "mysql", "mongodb"],
                    "advanced": ["microservices", "docker", "kubernetes", "system design", "redis", "rabbitmq"]
                }
            },
            "Frontend Developer": {
                "description": """
                    Builds the user interface (UI) of a website or application.
                    Expert in HTML, CSS, and JavaScript.
                    Uses frameworks like React, Angular, or Vue.js to create interactive user experiences.
                """,
                "skills": {
                    "basic": ["html", "css", "javascript", "git"],
                    "intermediate": ["react", "angular", "vue.js", "typescript", "responsive design", "api integration"],
                    "advanced": ["next.js", "webpack", "state management (redux/zustand)", "testing (jest/cypress)"]
                }
            },
            "Full-Stack Developer": {
                "description": """
                    A hybrid role that handles both frontend and backend development.
                    Comfortable with the entire stack, from UI (React, Vue) to server (Node.js, Django) and database (PostgreSQL, MongoDB).
                """,
                "skills": {
                    "basic": ["html", "css", "javascript", "python", "sql", "git", "rest apis"],
                    "intermediate": ["react", "node.js", "django", "postgresql", "mongodb"],
                    "advanced": ["docker", "aws", "system design", "ci/cd"]
                }
            },
            "Mobile Developer (Android)": {
                "description": """
                    Builds applications for Android devices.
                    Uses languages like Kotlin or Java and the Android SDK.
                    Focuses on performance and user experience on mobile.
                """,
                "skills": {
                    "basic": ["kotlin", "java", "xml", "android studio"],
                    "intermediate": ["android sdk", "jetpack compose", "api integration", "sqlite"],
                    "advanced": ["coroutines", "dependency injection (hilt)", "mvvm architecture"]
                }
            },
            "Mobile Developer (iOS)": {
                "description": """
                    Builds applications for Apple devices (iPhone, iPad).
                    Uses the Swift programming language and Apple's Xcode IDE.
                    Focuses on Apple's design guidelines and ecosystem.
                """,
                "skills": {
                    "basic": ["swift", "xcode", "uikit"],
                    "intermediate": ["swiftui", "api integration", "core data"],
                    "advanced": ["combine", "gcd", "dependency injection", "mvvm architecture"]
                }
            },
            "Mobile Developer (Cross-Platform)": {
                "description": """
                    Builds mobile applications for both iOS and Android from a single codebase.
                    Uses frameworks like React Native or Flutter (with Dart).
                    Balances code reusability with native performance.
                """,
                "skills": {
                    "basic": ["javascript", "dart", "html", "css"],
                    "intermediate": ["react native", "flutter", "api integration", "state management"],
                    "advanced": ["native module bridging", "bloc (flutter)", "redux (react native)"]
                }
            },
            "Game Developer": {
                "description": """
                    Builds video games for PC, console, or mobile.
                    Uses game engines like Unity (with C#) or Unreal Engine (with C++).
                    Focuses on physics, graphics (OpenGL/Vulkan), and gameplay logic.
                """,
                "skills": {
                    "basic": ["c#", "c++", "unity", "unreal engine"],
                    "intermediate": ["3d modeling", "game physics", "blender"],
                    "advanced": ["graphics programming", "opengl", "vulkan", "hlsl/glsl shaders"]
                }
            },
            "Blockchain Developer": {
                "description": """
                    Builds decentralized applications (dApps) and smart contracts.
                    Uses languages like Solidity (for Ethereum) or Rust.
                    Understands cryptography, web3, and blockchain protocols.
                """,
                "skills": {
                    "basic": ["solidity", "javascript", "ethereum"],
                    "intermediate": ["web3.js", "ethers.js", "smart contracts", "truffle", "hardhat"],
                    "advanced": ["rust", "cryptography", "defi", "layer 2 scaling"]
                }
            },

            # --- DevOps & Infrastructure Roles ---
            "DevOps Engineer": {
                "description": """
                    Manages the software development lifecycle (CI/CD).
                    Expert in Git, Jenkins, Docker, and Kubernetes.
                    Automates builds, testing, and deployment to cloud platforms like AWS or Azure.
                """,
                "skills": {
                    "basic": ["git", "linux", "bash scripting", "docker"],
                    "intermediate": ["ci/cd", "jenkins", "aws", "azure", "networking"],
                    "advanced": ["kubernetes", "terraform", "ansible", "prometheus"]
                }
            },
            "Site Reliability Engineer (SRE)": {
                "description": """
                    A specialized DevOps role focused on reliability, uptime, and performance.
                    Treats operations as a software problem.
                    Monitors systems (Prometheus, Grafana) and manages incident response.
                """,
                "skills": {
                    "basic": ["python", "go", "linux", "networking"],
                    "intermediate": ["docker", "kubernetes", "aws", "monitoring"],
                    "advanced": ["prometheus", "grafana", "system design", "incident response"]
                }
            },
            "Cloud Engineer": {
                "description": """
                    Specializes in a specific cloud platform like AWS, Google Cloud (GCP), or Microsoft Azure.
                    Manages virtual machines, storage, networking, and security in the cloud.
                    Often certified in their chosen platform (e.g., AWS Solutions Architect).
                """,
                "skills": {
                    "basic": ["aws", "gcp", "azure", "linux", "networking", "security"],
                    "intermediate": ["docker", "iam", "s3", "ec2", "vpc"],
                    "advanced": ["terraform", "kubernetes", "serverless (lambda)", "cloud certification"]
                }
            },
            "Database Administrator (DBA)": {
                "description": """
                    Manages and maintains company databases (PostgreSQL, MySQL, Oracle).
                    Responsible for backups, security, performance tuning, and query optimization.
                """,
                "skills": {
                    "basic": ["sql", "postgresql", "mysql"],
                    "intermediate": ["oracle", "database tuning", "backups", "security"],
                    "advanced": ["query optimization", "database replication", "sharding", "nosql"]
                }
            },
            "Security Engineer": {
                "description": """
                    Protects systems from cyber threats.
                    Performs penetration testing, vulnerability assessments, and security audits.
                    Understands network security, cryptography, and ethical hacking.
                """,
                "skills": {
                    "basic": ["network security", "linux", "cryptography"],
                    "intermediate": ["penetration testing", "wireshark", "metasploit", "vulnerability assessment"],
                    "advanced": ["ethical hacking", "cissp", "malware analysis", "incident response"]
                }
            },

            # --- QA & Operations Roles ---
            "Software Development Engineer in Test (SDET)": {
                "description": """
                    A developer focused on building automated testing frameworks.
                    Writes code (Python, Java) to test other code.
                    Uses tools like Selenium, Cypress, or Pytest.
                """,
                "skills": {
                    "basic": ["python", "java", "manual testing", "git"],
                    "intermediate": ["selenium", "pytest", "jira", "ci/cd"],
                    "advanced": ["cypress", "playwright", "test framework design", "performance testing"]
                }
            },
            "QA (Manual) Tester": {
                "description": """
                    Manually tests applications to find bugs and ensure quality.
                    Writes test cases, executes test plans, and reports defects.
                    Focuses on the user's perspective and edge cases.
                """,
                "skills": {
                    "basic": ["manual testing", "test cases", "jira", "black box testing"],
                    "intermediate": ["regression testing", "exploratory testing", "api testing (postman)"],
                    "advanced": ["sql", "test planning", "istqb certification"]
                }
            },
            "IT Support Specialist": {
                "description": """
                    Provides technical assistance to non-technical employees.
                    Troubleshoots hardware, software, and network issues.
                    Manages user accounts and system setups.
                """,
                "skills": {
                    "basic": ["troubleshooting", "customer service", "windows", "macos"],
                    "intermediate": ["active directory", "networking basics", "office 365"],
                    "advanced": ["powershell", "mdm", "itil certification"]
                }
            },

            # --- Product & Design Roles ---
            "Product Manager (Tech)": {
                "description": """
                    The "CEO" of the product. Defines the 'what' and 'why' of a product.
                    Conducts market research, prioritizes features, and creates roadmaps.
                    Works closely with engineers, designers, and business stakeholders.
                """,
                "skills": {
                    "basic": ["product management", "agile", "scrum", "communication"],
                    "intermediate": ["user research", "roadmapping", "jira", "data analysis"],
                    "advanced": ["market research", "kpi tracking", "go-to-market strategy", "a/b testing"]
                }
            },
            "UX/UI Designer": {
                "description": """
                    Focuses on the look, feel, and usability of a product.
                    UX (User Experience) Designer researches user needs and workflows.
                    UI (User Interface) Designer creates the visual layouts, buttons, and styles using tools like Figma.
                """,
                "skills": {
                    "basic": ["figma", "wireframing", "ui design"],
                    "intermediate": ["user research", "prototyping", "adobe xd", "ux design"],
                    "advanced": ["design systems", "user testing", "information architecture", "accessibility (a11y)"]
                }
            },
            "Technical Writer": {
                "description": """
                    Creates clear and concise documentation for software.
                    Writes API guides, user manuals, and tutorials.
                    Translates complex technical concepts into easy-to-understand language.
                """,
                "skills": {
                    "basic": ["technical writing", "english grammar", "markdown"],
                    "intermediate": ["api documentation", "git", "confluence"],
                    "advanced": ["docs-as-code", "swagger/openapi", "sdk documentation"]
                }
            },
            "Solutions Architect": {
                "description": """
                    Designs high-level technical solutions for complex business problems.
                    Chooses the right technologies, frameworks, and cloud services.
                    Acts as a bridge between technical teams and business leaders.
                """,
                "skills": {
                    "basic": ["system design", "aws", "azure", "gcp", "communication"],
                    "intermediate": ["microservices", "solution design", "networking", "security"],
                    "advanced": ["enterprise architecture", "cloud certification (pro)", "cost optimization"]
                }
            },
            "Scrum Master": {
                "description": """
                    A facilitator for an Agile development team.
                    Manages the Scrum process (sprints, stand-ups, retrospectives).
                    Helps the team remove obstacles and improve its productivity.
                """,
                "skills": {
                    "basic": ["agile", "scrum", "facilitation"],
                    "intermediate": ["jira", "coaching", "communication"],
                    "advanced": ["csm certification", "scaled agile (safe)", "kanban"]
                }
            }
        }
        
        # Pre-calculate the vectors for our "database"
        print("Pre-calculating job profile embeddings...")
        self.job_titles = list(self.job_profiles.keys())
        # We only embed the 'description' field
        self.job_descriptions = [profile['description'] for profile in self.job_profiles.values()]
        
        # This is the core of our "Vector DB"
        self.job_vectors = self.model.encode(self.job_descriptions)
        print(f"Vector database is ready. {len(self.job_titles)} profiles loaded.\n")

    def _create_user_profile(self, education, skills, projects):
        """
        Converts the user's structured data into two things:
        1. A descriptive text "document" (for embedding).
        2. A clean set of all skills (for gap analysis).
        """
        
        # --- 1. Create the text document for embedding ---
        skill_str = ""
        for category, skill_list in skills.items():
            skill_str += f"{category}: {', '.join(skill_list)}. "
            
        project_str = ""
        for title, details in projects.items():
            project_str += f"Project: {title}. Skills used: {details['skills']}. Description: {details['desc']}. "
            
        user_profile_text = f"""
        Education: {education['degree']} in {education['field']} with {education['cgpa']} CGPA, graduating in {education['year']}.
        Technical Skills: {skill_str}
        Projects: {project_str}
        """
        
        # --- 2. Create the normalized skill set for gap analysis ---
        # This logic remains the same, as we are flattening all user skills.
        user_skill_set = set()
        for skill_list in skills.values():
            for skill in skill_list:
                user_skill_set.add(skill.lower())
        
        # Also add skills from project descriptions for a more robust set
        for title, details in projects.items():
            project_skills = details['skills'].split(', ')
            for skill in project_skills:
                if skill: # Avoid empty strings
                    user_skill_set.add(skill.strip().lower())

        return user_profile_text, user_skill_set

    def recommend_jobs(self, education, skills, projects, top_k=3):
        """
        Finds the top_k most similar job profiles for the user
        and performs a tiered skill gap analysis.
        """
        
        # 1. Create the user's profile text and skill set
        user_profile_text, user_skill_set = self._create_user_profile(education, skills, projects)
        
        # 2. Embed the user's profile (the "query vector")
        user_vector = self.model.encode([user_profile_text])
        
        # 3. Perform the Vector Search
        similarities = cosine_similarity(user_vector, self.job_vectors)
        
        # 4. Get the results and perform tiered skill gap analysis
        top_k_indices = np.argsort(similarities[0])[-top_k:][::-1]
        
        recommendations = []
        for idx in top_k_indices:
            job_title = self.job_titles[idx]
            
            # --- Tiered Skill Gap Analysis ---
            # Get the structured skill dictionary for this job
            required_skills_dict = self.job_profiles[job_title]['skills']
            
            # Calculate gap for each level
            basic_gap = list(set(required_skills_dict.get('basic', [])) - user_skill_set)
            intermediate_gap = list(set(required_skills_dict.get('intermediate', [])) - user_skill_set)
            advanced_gap = list(set(required_skills_dict.get('advanced', [])) - user_skill_set)
            
            # Store the gaps in a structured dictionary
            skill_gap = {
                "basic_missing": basic_gap,
                "intermediate_missing": intermediate_gap,
                "advanced_missing": advanced_gap
            }
            
            recommendations.append({
                "job_profile": job_title,
                "match_score": similarities[0][idx],
                "skill_gap": skill_gap # Append the new gap dictionary
            })
            
        return recommendations

# --- Example Usage ---
if __name__ == "__main__":
    
    # 1. Define the user's input (from your example)
    user_education = {
        "place": "Tier 1 College",
        "degree": "BE",
        "field": "Computer Science",
        "year": "2025",
        "cgpa": "9.0"
    }
    
    user_skills = {
        "Languages": ["Python", "C++"],
        "Backend": ["Django", "FastAPI"],
        "Databases": ["PostgreSQL"],
        "DevOps & Tools": ["Git", "FFmpeg", "REST APIs", "CRUD Operations"],
        "Machine Learning": ["PyTorch", "TensorFlow", "YOLO", "ONNX", "OpenCV", "MediaPipe", "Scikit-learn", "Numpy"],
        "Generative AI": ["Large Language Models (LLMs)", "Hugging Face"]
    }
    
    user_projects = {
        "Sign Language Captioning": {
            "skills": "Python, Scikit-learn, OpenCV, MediaPipe",
            "desc": "Trained a RandomForest model... to generate live captions... enhancing accessibility."
        },
        "Pothole Detection on Edge Devices": {
            "skills": "Python, YOLOv4, ONNX, Raspberry Pi, OpenCV",
            "desc": "Deployed a YOLOv4 computer vision model on a Raspberry Pi... efficient real-time performance on edge hardware."
        },
        "AI-Powered Floor Plan Verification": {
            "skills": "Python, OpenCV, YOLOv8",
            "desc": "Created an AI tool using a YOLOv8 model... to mitigate overfitting... Automated the analysis of CAD drawings."
        }
    }
    
    # 2. Initialize the recommender system
    recommender = JobRecommender()
    
    # 3. Get recommendations
    my_recommendations = recommender.recommend_jobs(user_education, user_skills, user_projects, top_k=3)
    
    # 4. Print the results
    print("\n--- Top 3 Job Profile Recommendations ---")
    for rec in my_recommendations:
        print(f"  - Job Profile: {rec['job_profile']}")
        print(f"  - Match Score: {rec['match_score']:.4f}")
        
        # Print the tiered skill gap
        skill_gap = rec['skill_gap']
        has_gap = False
        
        if skill_gap['basic_missing']:
            gap_str = ", ".join([s.capitalize() for s in skill_gap['basic_missing']])
            print(f"  - Missing BASIC Skills: {gap_str}")
            has_gap = True
        
        if skill_gap['intermediate_missing']:
            gap_str = ", ".join([s.capitalize() for s in skill_gap['intermediate_missing']])
            print(f"  - Missing INTERMEDIATE Skills: {gap_str}")
            has_gap = True
            
        if skill_gap['advanced_missing']:
            gap_str = ", ".join([s.capitalize() for s in skill_gap['advanced_missing']])
            print(f"  - Missing ADVANCED Skills: {gap_str}")
            has_gap = True
            
        if not has_gap:
            print(f"  - Skill Match: Excellent! You meet all listed skill requirements.")
            
        print("-" * 20)

