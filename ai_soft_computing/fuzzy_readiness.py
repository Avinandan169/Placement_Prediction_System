import numpy as np
from typing import Dict, Any, List, Tuple, Optional


def trimf(x: float, a: float, b: float, c: float) -> float:
    """Triangular membership function."""
    if x <= a or x >= c:
        return 0.0
    elif a < x <= b:
        return (x - a) / (b - a) if b != a else 1.0
    else:  # b < x < c
        return (c - x) / (c - b) if c != b else 1.0


def trapmf(x: float, a: float, b: float, c: float, d: float) -> float:
    """Trapezoidal membership function."""
    if x <= a or x >= d:
        return 0.0
    elif a < x <= b:
        return (x - a) / (b - a) if b != a else 1.0
    elif b <= x <= c:
        return 1.0
    else:  # c < x < d
        return (d - x) / (d - c) if d != c else 1.0


class FuzzyPlacementReadinessSystem:
    """
    Explainable Mamdani Fuzzy Inference System for Placement Readiness Assessment (CSE3121).

    Linguistic Input Variables:
    1. CGPA [0.0, 10.0]: Low, Medium, High
    2. Aptitude Score [0.0, 100.0]: Low, Medium, High
    3. Soft Skills [1.0, 5.0]: Low, Medium, High
    4. Practical Experience [0, 10]: Low, Medium, High (Projects + Internships combined)

    Linguistic Output Variable:
    - Placement Readiness Score [0.0, 100.0]: NotReady, Developing, Ready, HighlyReady

    Inference Method:
    - Conjunction (AND): Minimum operator (Mamdani min)
    - Implication: Min (clipping the output fuzzy set)
    - Aggregation: Maximum operator across all activated rules
    - Defuzzification: Centroid (Center of Gravity) method
    """

    def __init__(self):
        # Discretized universe of discourse for defuzzification
        self.output_universe = np.linspace(0.0, 100.0, 1001)

    # 1. Fuzzification functions for input variables
    def fuzzify_cgpa(self, val: float) -> Dict[str, float]:
        val = max(0.0, min(10.0, float(val)))
        return {
            "Low": trapmf(val, 0.0, 0.0, 6.2, 7.2),
            "Medium": trimf(val, 6.8, 7.8, 8.6),
            "High": trapmf(val, 8.0, 8.8, 10.0, 10.0)
        }

    def fuzzify_aptitude(self, val: float) -> Dict[str, float]:
        val = max(0.0, min(100.0, float(val)))
        return {
            "Low": trapmf(val, 0.0, 0.0, 55.0, 68.0),
            "Medium": trimf(val, 62.0, 75.0, 86.0),
            "High": trapmf(val, 80.0, 88.0, 100.0, 100.0)
        }

    def fuzzify_soft_skills(self, val: float) -> Dict[str, float]:
        val = max(1.0, min(5.0, float(val)))
        return {
            "Low": trapmf(val, 1.0, 1.0, 2.5, 3.4),
            "Medium": trimf(val, 3.0, 3.9, 4.4),
            "High": trapmf(val, 4.0, 4.6, 5.0, 5.0)
        }

    def fuzzify_experience(self, val: float) -> Dict[str, float]:
        val = max(0.0, min(10.0, float(val)))
        return {
            "Low": trapmf(val, 0.0, 0.0, 1.0, 2.5),
            "Medium": trimf(val, 2.0, 4.0, 6.0),
            "High": trapmf(val, 5.0, 7.0, 10.0, 10.0)
        }

    # 2. Output membership function evaluations
    def output_membership(self, z: np.ndarray, term: str) -> np.ndarray:
        if term == "NotReady":
            # Trapezoidal: 0 to 40
            return np.array([trapmf(x, 0.0, 0.0, 20.0, 40.0) for x in z])
        elif term == "Developing":
            # Triangular: 25 to 65, peak at 45
            return np.array([trimf(x, 25.0, 45.0, 65.0) for x in z])
        elif term == "Ready":
            # Triangular: 55 to 85, peak at 72
            return np.array([trimf(x, 55.0, 72.0, 88.0) for x in z])
        elif term == "HighlyReady":
            # Trapezoidal: 75 to 100
            return np.array([trapmf(x, 78.0, 90.0, 100.0, 100.0) for x in z])
        else:
            return np.zeros_like(z)

    def evaluate(
        self,
        cgpa: float,
        aptitude: float,
        soft_skills: float,
        projects: int = 1,
        internships: int = 0
    ) -> Dict[str, Any]:
        """
        Executes complete Mamdani fuzzy inference.
        Returns crisp score, activated rules, membership breakdowns, and curve points.
        """
        # Practical experience composite metric
        experience_val = float(projects * 1.5 + internships * 2.0)
        experience_val = min(10.0, experience_val)

        # Fuzzify inputs
        mu_cgpa = self.fuzzify_cgpa(cgpa)
        mu_apt = self.fuzzify_aptitude(aptitude)
        mu_soft = self.fuzzify_soft_skills(soft_skills)
        mu_exp = self.fuzzify_experience(experience_val)

        # 3. Fuzzy Rule Base (16 Expert Rules)
        # Each rule has (id, conditions, consequence, natural_language_explanation)
        rules_definition = [
            # High Tier Rules
            (1, {"cgpa": "High", "apt": "High", "soft": "High"}, "HighlyReady",
             "Strong academic performance, high aptitude, and excellent communication ensure top placement readiness."),
            (2, {"cgpa": "High", "apt": "High", "exp": "High"}, "HighlyReady",
             "High CGPA coupled with high aptitude and extensive project experience indicates exceptional readiness."),
            (3, {"cgpa": "Medium", "apt": "High", "soft": "High", "exp": "High"}, "HighlyReady",
             "High aptitude, great soft skills, and rich practical experience elevate readiness to top tier despite medium CGPA."),

            # Ready Tier Rules
            (4, {"cgpa": "High", "apt": "Medium", "soft": "Medium"}, "Ready",
             "Strong academics with solid aptitude and adequate soft skills provide dependable placement readiness."),
            (5, {"cgpa": "Medium", "apt": "High", "soft": "Medium"}, "Ready",
             "High aptitude screening scores paired with medium CGPA and communication meet company benchmarks."),
            (6, {"cgpa": "High", "apt": "Low", "exp": "High"}, "Ready",
             "Strong academic records and rich project experience compensate for lower aptitude test performance."),
            (7, {"cgpa": "Medium", "apt": "Medium", "soft": "High"}, "Ready",
             "Well-balanced academics and aptitude supported by articulate communication enable interview success."),
            (8, {"cgpa": "Medium", "apt": "Medium", "exp": "Medium"}, "Ready",
             "Consistent performance across academics, problem-solving, and practical project execution."),

            # Developing Tier Rules
            (9, {"cgpa": "Low", "apt": "High", "exp": "Medium"}, "Developing",
             "High aptitude and moderate experience demonstrate potential, but low CGPA may restrict eligibility."),
            (10, {"cgpa": "Medium", "apt": "Low", "soft": "Medium"}, "Developing",
             "Moderate academics with low aptitude indicate a need to focus on quantitative screening test prep."),
            (11, {"cgpa": "Low", "apt": "Medium", "soft": "High"}, "Developing",
             "Strong communication and moderate aptitude need strengthening in core academic foundations."),
            (12, {"cgpa": "Medium", "apt": "Medium", "soft": "Low"}, "Developing",
             "Technical competence is sound, but soft skills require targeted practice for personal interview rounds."),
            (13, {"cgpa": "High", "apt": "Low", "soft": "Low"}, "Developing",
             "High CGPA is offset by weak screening aptitude and communication scores, needing preparation."),

            # Not Ready Tier Rules
            (14, {"cgpa": "Low", "apt": "Low"}, "NotReady",
             "Both academic GPA and screening aptitude scores are low, requiring foundational remediation."),
            (15, {"cgpa": "Low", "apt": "Medium", "soft": "Low", "exp": "Low"}, "NotReady",
             "Low GPA, weak communication, and minimal practical experience limit readiness for campus drives."),
            (16, {"cgpa": "Medium", "apt": "Low", "soft": "Low", "exp": "Low"}, "NotReady",
             "Low aptitude, limited soft skills, and absence of project work place the candidate in the not-ready zone.")
        ]

        # 4. Rule Evaluation (Mamdani Min operator)
        rule_firings = []
        rule_cuts = {"NotReady": 0.0, "Developing": 0.0, "Ready": 0.0, "HighlyReady": 0.0}

        for rule_id, conds, consequent, explanation in rules_definition:
            alpha = 1.0
            if "cgpa" in conds:
                alpha = min(alpha, mu_cgpa[conds["cgpa"]])
            if "apt" in conds:
                alpha = min(alpha, mu_apt[conds["apt"]])
            if "soft" in conds:
                alpha = min(alpha, mu_soft[conds["soft"]])
            if "exp" in conds:
                alpha = min(alpha, mu_exp[conds["exp"]])

            if alpha > 0.001:
                rule_firings.append({
                    "rule_id": rule_id,
                    "conditions": conds,
                    "consequent": consequent,
                    "alpha_cut": round(float(alpha), 3),
                    "explanation": explanation
                })
                rule_cuts[consequent] = max(rule_cuts[consequent], float(alpha))

        # Sort activated rules by activation strength
        rule_firings = sorted(rule_firings, key=lambda x: x["alpha_cut"], reverse=True)

        # 5. Output Aggregation (Max operator)
        z = self.output_universe
        mu_aggregated = np.zeros_like(z)

        for term, cut in rule_cuts.items():
            if cut > 0.0:
                base_mu = self.output_membership(z, term)
                clipped_mu = np.minimum(cut, base_mu)
                mu_aggregated = np.maximum(mu_aggregated, clipped_mu)

        # 6. Defuzzification (Centroid / Center of Gravity Method)
        sum_mu = np.sum(mu_aggregated)
        if sum_mu > 1e-6:
            centroid = float(np.sum(z * mu_aggregated) / sum_mu)
        else:
            # Fallback if no rules fired (neutral midpoint)
            centroid = 50.0

        readiness_score = round(centroid, 1)

        # Categorize readiness tier
        if readiness_score >= 80.0:
            tier = "Highly Placement Ready"
            tier_badge = "success"
        elif readiness_score >= 60.0:
            tier = "Placement Ready"
            tier_badge = "primary"
        elif readiness_score >= 40.0:
            tier = "Developing Readiness"
            tier_badge = "warning"
        else:
            tier = "Needs Foundational Preparation"
            tier_badge = "danger"

        # 7. Membership Function Coordinate Curves (for frontend SVG rendering)
        curves_data = self._generate_curves_data()

        return {
            "readiness_score": readiness_score,
            "readiness_tier": tier,
            "readiness_badge": tier_badge,
            "inputs": {
                "cgpa": cgpa,
                "aptitude_score": aptitude,
                "soft_skills_rating": soft_skills,
                "projects": projects,
                "internships": internships,
                "practical_experience_index": round(experience_val, 2)
            },
            "fuzzified_memberships": {
                "CGPA": {k: round(v, 3) for k, v in mu_cgpa.items()},
                "AptitudeScore": {k: round(v, 3) for k, v in mu_apt.items()},
                "SoftSkills": {k: round(v, 3) for k, v in mu_soft.items()},
                "PracticalExperience": {k: round(v, 3) for k, v in mu_exp.items()}
            },
            "activated_rules": rule_firings,
            "output_cuts": {k: round(v, 3) for k, v in rule_cuts.items()},
            "defuzzification_method": "Centroid (Center of Gravity / Area)",
            "curves_data": curves_data,
            "explanation_summary": (
                f"Candidate evaluated to {readiness_score}/100 ({tier}) using Mamdani fuzzy inference. "
                f"{len(rule_firings)} fuzzy rules were activated. Top active rule: "
                f"Rule #{rule_firings[0]['rule_id']} with activation strength {rule_firings[0]['alpha_cut']}."
                if rule_firings else "Candidate evaluated at baseline."
            )
        }

    def _generate_curves_data(self) -> Dict[str, Any]:
        """Generates coordinate arrays for frontend membership function visualization."""
        # CGPA curves (0 to 10)
        cgpa_x = np.linspace(0, 10, 51)
        # Aptitude curves (0 to 100)
        apt_x = np.linspace(0, 100, 51)
        # Output readiness curves (0 to 100)
        out_x = np.linspace(0, 100, 51)

        return {
            "cgpa": {
                "x": [round(float(v), 2) for v in cgpa_x],
                "low": [round(float(trapmf(v, 0, 0, 6.2, 7.2)), 2) for v in cgpa_x],
                "medium": [round(float(trimf(v, 6.8, 7.8, 8.6)), 2) for v in cgpa_x],
                "high": [round(float(trapmf(v, 8.0, 8.8, 10.0, 10.0)), 2) for v in cgpa_x]
            },
            "aptitude": {
                "x": [round(float(v), 1) for v in apt_x],
                "low": [round(float(trapmf(v, 0, 0, 55, 68)), 2) for v in apt_x],
                "medium": [round(float(trimf(v, 62, 75, 86)), 2) for v in apt_x],
                "high": [round(float(trapmf(v, 80, 88, 100, 100)), 2) for v in apt_x]
            },
            "output": {
                "x": [round(float(v), 1) for v in out_x],
                "not_ready": [round(float(trapmf(v, 0, 0, 20, 40)), 2) for v in out_x],
                "developing": [round(float(trimf(v, 25, 45, 65)), 2) for v in out_x],
                "ready": [round(float(trimf(v, 55, 72, 88)), 2) for v in out_x],
                "highly_ready": [round(float(trapmf(v, 78, 90, 100, 100)), 2) for v in out_x]
            }
        }
