import unittest
from ai_soft_computing.fuzzy_readiness import FuzzyPlacementReadinessSystem, trimf, trapmf
from ai_soft_computing.astar_planner import AStarSkillPlanner, CAREER_ROLES, SKILL_CATALOG


class TestAISoftComputing(unittest.TestCase):
    """
    Comprehensive tests for the CSE3121 AI & Soft Computing module:
    Fuzzy Logic Placement Readiness and A* Heuristic Skill Planner.
    """

    def setUp(self):
        self.fuzzy = FuzzyPlacementReadinessSystem()
        self.planner = AStarSkillPlanner()

    # --- Fuzzy Logic Tests ---
    def test_membership_functions(self):
        # trimf(x, a, b, c): peak at b
        self.assertEqual(trimf(5, 0, 5, 10), 1.0)
        self.assertEqual(trimf(0, 0, 5, 10), 0.0)
        self.assertEqual(trimf(2.5, 0, 5, 10), 0.5)

        # trapmf(x, a, b, c, d): plateau between b and c
        self.assertEqual(trapmf(3, 1, 2, 4, 5), 1.0)
        self.assertEqual(trapmf(0, 1, 2, 4, 5), 0.0)

    def test_fuzzy_readiness_high_candidate(self):
        res = self.fuzzy.evaluate(cgpa=8.8, aptitude=92.0, soft_skills=4.8, projects=3, internships=2)
        self.assertGreaterEqual(res["readiness_score"], 80.0)
        self.assertEqual(res["readiness_tier"], "Highly Placement Ready")
        self.assertTrue(len(res["activated_rules"]) > 0)
        self.assertIn("Rule #1", [f"Rule #{r['rule_id']}" for r in res["activated_rules"]])

    def test_fuzzy_readiness_low_candidate(self):
        res = self.fuzzy.evaluate(cgpa=6.0, aptitude=50.0, soft_skills=2.0, projects=0, internships=0)
        self.assertLess(res["readiness_score"], 40.0)
        self.assertIn("Foundational", res["readiness_tier"])
        self.assertTrue(any(r["consequent"] == "NotReady" for r in res["activated_rules"]))

    def test_fuzzy_curves_data_structure(self):
        res = self.fuzzy.evaluate(cgpa=7.5, aptitude=75.0, soft_skills=3.5)
        self.assertIn("curves_data", res)
        self.assertIn("cgpa", res["curves_data"])
        self.assertIn("aptitude", res["curves_data"])
        self.assertIn("output", res["curves_data"])

    # --- A* Search Tests ---
    def test_astar_path_validity(self):
        """Every prerequisite in the generated path must precede the dependent skill."""
        plan = self.planner.plan_path(current_skills=[], target_role="Data Scientist")
        self.assertTrue(plan["reachable"])
        self.assertGreater(plan["total_effort_hours"], 0)

        acquired = set()
        for step in plan["steps"]:
            skill_id = step["skill_id"]
            prereqs = SKILL_CATALOG[skill_id]["prerequisites"]
            for p in prereqs:
                self.assertIn(p, acquired, f"Prerequisite '{p}' was not satisfied before '{skill_id}'")
            acquired.add(skill_id)

    def test_astar_with_existing_skills_reduces_effort(self):
        empty_plan = self.planner.plan_path(current_skills=[], target_role="Full-Stack Web Developer")
        partial_plan = self.planner.plan_path(
            current_skills=["git", "html_css", "javascript"],
            target_role="Full-Stack Web Developer"
        )
        self.assertLess(partial_plan["total_effort_hours"], empty_plan["total_effort_hours"])
        self.assertLess(partial_plan["total_steps"], empty_plan["total_steps"])

    def test_astar_already_qualified_goal(self):
        role_skills = CAREER_ROLES["Data Analyst"]["target_skills"]
        plan = self.planner.plan_path(current_skills=role_skills, target_role="Data Analyst")
        self.assertTrue(plan["already_qualified"])
        self.assertEqual(plan["total_effort_hours"], 0)
        self.assertEqual(len(plan["steps"]), 0)

    def test_astar_heuristic_admissibility(self):
        """Verify that heuristic never overestimates the true remaining cost."""
        target_skills = set(CAREER_ROLES["Machine Learning Engineer"]["target_skills"])
        closure = self.planner._get_required_closure(target_skills)

        # Test from empty set
        h_val = self.planner.heuristic(frozenset(), closure)
        plan = self.planner.plan_path(current_skills=[], target_role="Machine Learning Engineer")
        # In a graph without shortcuts, h(start) should be <= actual shortest path cost
        self.assertLessEqual(h_val, plan["total_effort_hours"])


if __name__ == "__main__":
    unittest.main()
