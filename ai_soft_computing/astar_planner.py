import heapq
from typing import Dict, Any, List, Set, Optional, Tuple


# Skill Knowledge Graph Definition
SKILL_CATALOG: Dict[str, Dict[str, Any]] = {
    # Foundational Programming & Tools
    "git": {
        "id": "git",
        "name": "Git & Version Control",
        "category": "Foundations",
        "effort_hours": 12,
        "prerequisites": [],
        "description": "Branching, merging, pull requests, resolving merge conflicts, and GitHub collaboration."
    },
    "linux": {
        "id": "linux",
        "name": "Linux Fundamentals & Shell Scripting",
        "category": "Foundations",
        "effort_hours": 18,
        "prerequisites": [],
        "description": "Bash commands, file permissions, process management, SSH, and basic scripting."
    },
    "python": {
        "id": "python",
        "name": "Python Fundamentals",
        "category": "Programming",
        "effort_hours": 30,
        "prerequisites": [],
        "description": "Variables, data structures, functions, comprehensions, modules, and error handling."
    },
    "oop": {
        "id": "oop",
        "name": "Object-Oriented Programming (OOP)",
        "category": "Programming",
        "effort_hours": 20,
        "prerequisites": ["python"],
        "description": "Classes, inheritance, polymorphism, encapsulation, and design patterns in Python."
    },
    "dsa": {
        "id": "dsa",
        "name": "Data Structures & Algorithms (DSA)",
        "category": "Computer Science",
        "effort_hours": 50,
        "prerequisites": ["python"],
        "description": "Arrays, linked lists, trees, graphs, sorting, searching, recursion, and dynamic programming."
    },
    "sql": {
        "id": "sql",
        "name": "SQL & Relational Databases",
        "category": "Data & Storage",
        "effort_hours": 25,
        "prerequisites": [],
        "description": "Queries, complex joins, aggregations, window functions, indexing, and schema design."
    },

    # Web & Full Stack
    "html_css": {
        "id": "html_css",
        "name": "HTML5, Modern CSS & Responsive Design",
        "category": "Frontend",
        "effort_hours": 20,
        "prerequisites": [],
        "description": "Semantic markup, flexbox, CSS grid, media queries, and accessible UI development."
    },
    "javascript": {
        "id": "javascript",
        "name": "JavaScript & TypeScript",
        "category": "Frontend",
        "effort_hours": 35,
        "prerequisites": ["html_css"],
        "description": "ES6+ syntax, asynchronous programming, DOM manipulation, promises, and TypeScript typing."
    },
    "react": {
        "id": "react",
        "name": "React & Modern Frontend Architecture",
        "category": "Frontend",
        "effort_hours": 40,
        "prerequisites": ["javascript"],
        "description": "Component lifecycle, state hooks, context API, client routing, and responsive web SPAs."
    },
    "backend_api": {
        "id": "backend_api",
        "name": "Backend APIs with FastAPI & Node.js",
        "category": "Backend",
        "effort_hours": 35,
        "prerequisites": ["python", "sql"],
        "description": "RESTful API architecture, authentication (JWT), request validation, and database ORMs."
    },
    "fullstack_project": {
        "id": "fullstack_project",
        "name": "End-to-End Full-Stack Capstone Project",
        "category": "Projects",
        "effort_hours": 45,
        "prerequisites": ["react", "backend_api", "git"],
        "description": "Production-grade web application featuring secure auth, relational database, and clean UI."
    },

    # Data Science & Machine Learning
    "stats_math": {
        "id": "stats_math",
        "name": "Probability, Statistics & Linear Algebra",
        "category": "Data Science",
        "effort_hours": 30,
        "prerequisites": [],
        "description": "Descriptive statistics, hypothesis testing, probability distributions, matrix operations."
    },
    "pandas_numpy": {
        "id": "pandas_numpy",
        "name": "Data Wrangling with Pandas & NumPy",
        "category": "Data Science",
        "effort_hours": 25,
        "prerequisites": ["python"],
        "description": "Vectorized computations, data cleaning, filtering, grouping, reshaping, and time series handling."
    },
    "data_viz": {
        "id": "data_viz",
        "name": "Data Visualization & Storytelling",
        "category": "Data Science",
        "effort_hours": 18,
        "prerequisites": ["pandas_numpy"],
        "description": "Exploratory data analysis plots, Seaborn, Matplotlib, Plotly, and dashboard communication."
    },
    "scikit_learn": {
        "id": "scikit_learn",
        "name": "Machine Learning with Scikit-Learn",
        "category": "Machine Learning",
        "effort_hours": 45,
        "prerequisites": ["pandas_numpy", "stats_math"],
        "description": "Classification, regression, cross-validation, regularization, hyperparameter tuning, metrics."
    },
    "deep_learning": {
        "id": "deep_learning",
        "name": "Deep Learning with PyTorch / TensorFlow",
        "category": "Machine Learning",
        "effort_hours": 50,
        "prerequisites": ["scikit_learn", "dsa"],
        "description": "Neural network architectures, backpropagation, CNNs, transformers, and GPU acceleration."
    },
    "ml_deployment": {
        "id": "ml_deployment",
        "name": "Model Serving & Inference Pipelines",
        "category": "MLOps",
        "effort_hours": 30,
        "prerequisites": ["scikit_learn", "backend_api"],
        "description": "Serving models via REST APIs, serialization (joblib/ONNX), low-latency inference pipelines."
    },
    "ml_capstone": {
        "id": "ml_capstone",
        "name": "Production Machine Learning Capstone",
        "category": "Projects",
        "effort_hours": 45,
        "prerequisites": ["scikit_learn", "data_viz", "git"],
        "description": "End-to-end ML project with EDA, feature engineering, model training, evaluation, and documentation."
    },

    # DevOps & Cloud Infrastructure
    "docker": {
        "id": "docker",
        "name": "Docker & Containerization",
        "category": "DevOps",
        "effort_hours": 25,
        "prerequisites": ["linux"],
        "description": "Dockerfiles, multi-stage builds, container networking, volumes, and docker-compose orchestration."
    },
    "kubernetes": {
        "id": "kubernetes",
        "name": "Kubernetes & Container Orchestration",
        "category": "DevOps",
        "effort_hours": 40,
        "prerequisites": ["docker"],
        "description": "Pods, deployments, services, ingress controllers, config maps, and cluster scaling."
    },
    "cicd": {
        "id": "cicd",
        "name": "CI/CD Automation with GitHub Actions",
        "category": "DevOps",
        "effort_hours": 20,
        "prerequisites": ["git", "docker"],
        "description": "Automated testing pipelines, linting, container building, and deployment workflows."
    },
    "cloud_aws": {
        "id": "cloud_aws",
        "name": "Cloud Architecture & Services (AWS/GCP)",
        "category": "Cloud",
        "effort_hours": 35,
        "prerequisites": ["linux", "docker"],
        "description": "Compute instances, managed databases, IAM policies, storage buckets, and serverless functions."
    },

    # Data Analyst Specific
    "excel_adv": {
        "id": "excel_adv",
        "name": "Advanced Excel & Business Analytics",
        "category": "Analytics",
        "effort_hours": 15,
        "prerequisites": [],
        "description": "Pivot tables, VLOOKUP/XLOOKUP, formulas, data modeling, and executive summary charts."
    },
    "bi_dashboards": {
        "id": "bi_dashboards",
        "name": "BI Dashboards with PowerBI / Tableau",
        "category": "Analytics",
        "effort_hours": 25,
        "prerequisites": ["sql", "excel_adv"],
        "description": "Interactive business dashboards, DAX queries, data modeling, and KPI tracking."
    },

    # Cybersecurity
    "networking": {
        "id": "networking",
        "name": "Computer Networking & Protocols",
        "category": "Security",
        "effort_hours": 28,
        "prerequisites": [],
        "description": "TCP/IP model, DNS, HTTP/HTTPS, subnetting, firewalls, and Wireshark traffic analysis."
    },
    "web_security": {
        "id": "web_security",
        "name": "Web Application Security (OWASP Top 10)",
        "category": "Security",
        "effort_hours": 35,
        "prerequisites": ["networking", "html_css", "sql"],
        "description": "SQL injection, XSS, CSRF, authentication bypass, security auditing, and mitigation."
    }
}


CAREER_ROLES: Dict[str, Dict[str, Any]] = {
    "Data Scientist": {
        "title": "Data Scientist",
        "description": "Focuses on statistical modeling, machine learning, predictive analytics, and extracting insights from enterprise data.",
        "target_skills": ["python", "sql", "stats_math", "pandas_numpy", "data_viz", "scikit_learn", "ml_capstone"],
        "recommended_for": "Students aiming for predictive modeling, research analytics, and AI engineering roles."
    },
    "Machine Learning Engineer": {
        "title": "Machine Learning Engineer",
        "description": "Bridges data science and software engineering by building, optimizing, and deploying production ML models at scale.",
        "target_skills": ["python", "dsa", "oop", "scikit_learn", "deep_learning", "backend_api", "docker", "ml_deployment"],
        "recommended_for": "Students interested in deep learning, MLOps, model deployment, and high-performance AI."
    },
    "Full-Stack Web Developer": {
        "title": "Full-Stack Web Developer",
        "description": "Builds complete, modern web applications from responsive frontends to scalable backend databases and APIs.",
        "target_skills": ["git", "html_css", "javascript", "react", "sql", "backend_api", "fullstack_project"],
        "recommended_for": "Students targeting software engineering, web application development, and tech startup roles."
    },
    "DevOps & Cloud Engineer": {
        "title": "DevOps & Cloud Engineer",
        "description": "Specializes in infrastructure automation, container orchestration, CI/CD pipelines, and cloud reliability.",
        "target_skills": ["git", "linux", "python", "docker", "kubernetes", "cicd", "cloud_aws"],
        "recommended_for": "Students focused on cloud infrastructure, site reliability engineering, and system operations."
    },
    "Data Analyst": {
        "title": "Data Analyst",
        "description": "Transforms raw business and transactional data into actionable executive insights, dashboards, and reports.",
        "target_skills": ["excel_adv", "sql", "pandas_numpy", "data_viz", "bi_dashboards"],
        "recommended_for": "Students targeting business intelligence, analytics consulting, and market insights."
    },
    "Cybersecurity Analyst": {
        "title": "Cybersecurity Analyst",
        "description": "Protects organizational networks, applications, and digital assets from vulnerabilities and cyber threats.",
        "target_skills": ["linux", "networking", "python", "sql", "web_security"],
        "recommended_for": "Students passionate about network security, ethical hacking, and risk auditing."
    }
}


class AStarSkillPlanner:
    """
    Implements A* Heuristic Search for Personalized Skill Development Planning (CSE3121).

    Search Formulation:
    - State: frozenset of completed skill IDs
    - Start State: initial set of student's current skills
    - Goal Condition: All target skills for the desired role are in the state
    - Valid Actions from State S: Any skill s not in S whose prerequisites are subsets of S
    - Action Cost c(S, s): effort_hours of skill s
    - Path Cost g(S): Total cumulative effort hours spent along the path
    - Heuristic h(S): Sum of effort hours for all unsatisfied skills in the prerequisite
      closure of the target role.
      Admissibility Proof: Every remaining skill in the closure MUST be acquired to fulfill
      the target goal. Since each step acquires at most one skill at cost effort_hours(s),
      and all costs are strictly positive, h(S) <= h*(S) (never overestimates).
      Hence, the heuristic is admissible and consistent, guaranteeing an optimal learning sequence!
    """

    def __init__(self, catalog: Optional[Dict[str, Dict[str, Any]]] = None):
        self.catalog = catalog or SKILL_CATALOG

    def _get_required_closure(self, target_skills: Set[str]) -> Set[str]:
        """Computes the full recursive prerequisite closure for a set of target skills."""
        closure = set(target_skills)
        changed = True
        while changed:
            changed = False
            for skill_id in list(closure):
                if skill_id in self.catalog:
                    for prereq in self.catalog[skill_id]["prerequisites"]:
                        if prereq not in closure:
                            closure.add(prereq)
                            changed = True
        return closure

    def heuristic(self, state: frozenset, target_closure: Set[str]) -> int:
        """
        Admissible and consistent heuristic function h(n).
        Returns the sum of effort hours of all missing skills required for the target role.
        """
        missing_skills = target_closure - state
        return sum(self.catalog[s]["effort_hours"] for s in missing_skills if s in self.catalog)

    def plan_path(
        self,
        current_skills: List[str],
        target_role: str
    ) -> Dict[str, Any]:
        """
        Executes A* search to compute the optimal learning trajectory.
        Returns ordered roadmap, step effort, cumulative hours, and search metrics.
        """
        if target_role not in CAREER_ROLES:
            valid_roles = list(CAREER_ROLES.keys())
            raise ValueError(f"Unknown target role '{target_role}'. Valid roles: {valid_roles}")

        role_info = CAREER_ROLES[target_role]
        raw_target_skills = set(role_info["target_skills"])

        # Normalize student's current skills
        normalized_current: Set[str] = set()
        for s in current_skills:
            s_clean = s.strip().lower().replace(" ", "_").replace("-", "_")
            # Match directly or by ID
            if s_clean in self.catalog:
                normalized_current.add(s_clean)
            else:
                # fuzzy match against names
                for cat_id, cat_data in self.catalog.items():
                    if s.strip().lower() in cat_data["name"].lower():
                        normalized_current.add(cat_id)
                        break

        # Compute required closure
        target_closure = self._get_required_closure(raw_target_skills)

        # Check if already achieved
        if raw_target_skills.issubset(normalized_current):
            return {
                "target_role": target_role,
                "already_qualified": True,
                "current_skills": list(normalized_current),
                "total_effort_hours": 0,
                "steps": [],
                "search_metrics": {
                    "nodes_expanded": 0,
                    "heuristic_type": "Admissible Prerequisite Closure (h(n) <= h*(n))",
                    "optimal": True
                },
                "summary": f"You already possess all required core competencies for '{target_role}'!"
            }

        start_state = frozenset(normalized_current)
        initial_h = self.heuristic(start_state, target_closure)

        # Priority Queue: stores (f_score, g_score, counter, state, path_history)
        counter = 0
        open_set = []
        heapq.heappush(open_set, (initial_h, 0, counter, start_state, []))

        # Best g-score observed per state
        best_g: Dict[frozenset, int] = {start_state: 0}
        nodes_expanded = 0

        optimal_path: Optional[List[str]] = None
        final_g = 0

        while open_set:
            f, g, _, current_state, path = heapq.heappop(open_set)
            nodes_expanded += 1

            # Check goal condition
            if raw_target_skills.issubset(current_state):
                optimal_path = path
                final_g = g
                break

            # If we already found a strictly better path to current_state, skip
            if g > best_g.get(current_state, float("inf")):
                continue

            # Determine candidates: skills in target_closure not yet acquired, whose prereqs are met
            unacquired_target_skills = target_closure - current_state
            for skill_id in unacquired_target_skills:
                skill_data = self.catalog.get(skill_id)
                if not skill_data:
                    continue

                # Check if prerequisites are satisfied
                prereqs = set(skill_data["prerequisites"])
                if prereqs.issubset(current_state):
                    # Valid transition
                    next_state = frozenset(current_state | {skill_id})
                    step_cost = skill_data["effort_hours"]
                    next_g = g + step_cost

                    if next_g < best_g.get(next_state, float("inf")):
                        best_g[next_state] = next_g
                        next_h = self.heuristic(next_state, target_closure)
                        next_f = next_g + next_h
                        counter += 1
                        heapq.heappush(open_set, (next_f, next_g, counter, next_state, path + [skill_id]))

        if optimal_path is None:
            return {
                "target_role": target_role,
                "already_qualified": False,
                "reachable": False,
                "error": "Goal state is unreachable given current prerequisite dependencies."
            }

        # Build detailed step items
        steps = []
        cumulative_hours = 0
        for idx, skill_id in enumerate(optimal_path, start=1):
            s_data = self.catalog[skill_id]
            cumulative_hours += s_data["effort_hours"]
            steps.append({
                "step_number": idx,
                "skill_id": skill_id,
                "name": s_data["name"],
                "category": s_data["category"],
                "effort_hours": s_data["effort_hours"],
                "cumulative_hours": cumulative_hours,
                "prerequisites": [
                    self.catalog[p]["name"] for p in s_data["prerequisites"] if p in self.catalog
                ],
                "description": s_data["description"],
                "is_core_target": skill_id in raw_target_skills,
                "status": "pending"
            })

        return {
            "target_role": target_role,
            "role_description": role_info["description"],
            "already_qualified": False,
            "reachable": True,
            "total_effort_hours": final_g,
            "total_steps": len(steps),
            "current_skills": list(normalized_current),
            "target_skills_required": list(raw_target_skills),
            "steps": steps,
            "search_metrics": {
                "nodes_expanded": nodes_expanded,
                "algorithm": "A* Heuristic Graph Search",
                "heuristic": "Prerequisite Closure Sum (Admissible, guarantees optimality)",
                "optimal": True
            },
            "summary": (
                f"Generated optimal {len(steps)}-step learning roadmap for '{target_role}'. "
                f"Estimated total investment: {final_g} hours across foundational, technical, and project milestones."
            )
        }

    def get_available_roles(self) -> List[Dict[str, Any]]:
        """Returns list of target career roles and required competencies."""
        results = []
        for role_id, info in CAREER_ROLES.items():
            req_skills = [
                {"id": s, "name": self.catalog[s]["name"], "category": self.catalog[s]["category"]}
                for s in info["target_skills"] if s in self.catalog
            ]
            results.append({
                "role_id": role_id,
                "title": info["title"],
                "description": info["description"],
                "recommended_for": info["recommended_for"],
                "required_skills": req_skills
            })
        return results

    def get_all_skills(self) -> List[Dict[str, Any]]:
        """Returns all skills in catalog."""
        return [
            {
                "id": k,
                "name": v["name"],
                "category": v["category"],
                "effort_hours": v["effort_hours"],
                "prerequisites": v["prerequisites"],
                "description": v["description"]
            }
            for k, v in self.catalog.items()
        ]
