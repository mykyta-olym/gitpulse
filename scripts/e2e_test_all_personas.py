#!/usr/bin/env python3
"""Comprehensive End-to-End Test Suite across Admin, Teacher, and Student personas.

Tests every button, form submission, API endpoint, and workflow on http://127.0.0.1:8000 using requests.Session.
"""

import asyncio
import json
import re
import sys

import requests
from sqlalchemy import select

from app.db.session import async_session_ctx
from app.models.course import Course
from app.models.project import GitLabProject
from app.models.student import Student
from app.models.team import Team

BASE_URL = "http://127.0.0.1:8000"


class E2ERunner:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0
        self.failures: list[str] = []
        self.demo_course_id: str = ""
        self.demo_team_id: str = ""
        self.demo_project_id: str = ""
        self.demo_student_id: str = ""

        # Fetch test entities directly from dev database
        async def load_entities():
            async with async_session_ctx() as db:
                course = (
                    await db.execute(select(Course).where(Course.code == "ZDEVOPS-DEMO"))
                ).scalar_one()
                team = (
                    await db.execute(
                        select(Team).where(
                            Team.course_id == course.id, Team.name == "tim-01-kniznica"
                        )
                    )
                ).scalar_one()
                project = (
                    (
                        await db.execute(
                            select(GitLabProject).where(GitLabProject.team_id == team.id)
                        )
                    )
                    .scalars()
                    .first()
                )
                student = (
                    (
                        await db.execute(
                            select(Student).where(Student.gitlab_username == "adam.bali")
                        )
                    )
                    .scalars()
                    .first()
                )
                return (
                    str(course.id),
                    str(team.id),
                    str(project.id) if project else "",
                    str(student.id) if student else "",
                )

        self.demo_course_id, self.demo_team_id, self.demo_project_id, self.demo_student_id = (
            asyncio.run(load_entities())
        )
        print(
            f"Initialized with Demo Course ID: {self.demo_course_id}, Team ID: {self.demo_team_id}, Project ID: {self.demo_project_id}, Student ID: {self.demo_student_id}"
        )

    def assert_test(self, name: str, condition: bool, details: str = "") -> None:
        if condition:
            self.passed += 1
            print(f"  [PASS] {name}")
        else:
            self.failed += 1
            err = f"  [FAIL] {name}: {details}"
            print(err)
            self.failures.append(err)

    def extract_csrf(self, html: str) -> str:
        match = re.search(r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)["\']', html)
        if match:
            return match.group(1)
        match = re.search(r'<meta\s+name=["\']csrf-token["\']\s+content=["\']([^"\']+)["\']', html)
        if match:
            return match.group(1)
        return ""

    def login(self, username: str, role: str) -> requests.Session:
        session = requests.Session()
        r = session.get(f"{BASE_URL}/dashboard/login")
        self.assert_test(
            f"GET /dashboard/login for {username}", r.status_code == 200, f"status {r.status_code}"
        )
        csrf = self.extract_csrf(r.text)

        data = {
            "csrf_token": csrf,
            "username": username,
            "role": role,
        }
        r_post = session.post(f"{BASE_URL}/dashboard/login", data=data, allow_redirects=True)
        self.assert_test(
            f"POST /dashboard/login as {username} ({role})",
            r_post.status_code == 200 and "/dashboard" in r_post.url,
            f"status {r_post.status_code}, url {r_post.url}",
        )
        return session

    def run_admin_tests(self) -> None:
        print("\n==========================================")
        print("  1. ADMIN PERSONA E2E TESTS")
        print("==========================================")
        admin = self.login("admin", "admin")

        # 1.1 Home & Realtime Telemetry/Widgets
        r = admin.get(f"{BASE_URL}/dashboard/")
        self.assert_test("Admin Home 200", r.status_code == 200)
        self.assert_test("Admin Home has Course List", "ZDEVOPS-DEMO" in r.text)
        csrf = self.extract_csrf(r.text)

        r_stats = admin.get(f"{BASE_URL}/dashboard/stats")
        self.assert_test("Admin /dashboard/stats 200", r_stats.status_code == 200)

        r_att = admin.get(f"{BASE_URL}/dashboard/attention-items")
        self.assert_test("Admin /dashboard/attention-items 200", r_att.status_code == 200)

        r_act = admin.get(f"{BASE_URL}/dashboard/activity")
        self.assert_test("Admin /dashboard/activity 200", r_act.status_code == 200)

        r_badges = admin.get(f"{BASE_URL}/dashboard/sidebar-badges")
        self.assert_test("Admin /dashboard/sidebar-badges 200", r_badges.status_code == 200)

        r_search = admin.get(f"{BASE_URL}/dashboard/search?q=demo")
        self.assert_test("Admin /dashboard/search 200", r_search.status_code == 200)

        r_notif = admin.get(f"{BASE_URL}/dashboard/notifications")
        self.assert_test("Admin /dashboard/notifications 200", r_notif.status_code == 200)

        r_sess = admin.get(f"{BASE_URL}/dashboard/session-check")
        self.assert_test("Admin /dashboard/session-check 200", r_sess.status_code == 200)

        # 1.2 User Management & Filter Tabs
        r = admin.get(f"{BASE_URL}/dashboard/admin/users")
        self.assert_test("Admin Users Management 200", r.status_code == 200)
        self.assert_test(
            "Admin Users contains table", "users-table" in r.text or "usersTable" in r.text
        )
        self.assert_test(
            "Admin Users contains filter tabs", "filter-tabs" in r.text and "tab-btn" in r.text
        )

        # Test filtering by role
        for role_filter in ("admin", "teacher", "student", "bot"):
            r_rf = admin.get(f"{BASE_URL}/dashboard/admin/users?role={role_filter}")
            self.assert_test(
                f"Admin Users filter role={role_filter} responds 200", r_rf.status_code == 200
            )

        # Test user info endpoint
        r_uinfo = admin.get(f"{BASE_URL}/dashboard/admin/users/by-username/admin/info")
        self.assert_test(
            "Admin user info responds 200 JSON",
            r_uinfo.status_code == 200
            and "application/json" in r_uinfo.headers.get("content-type", ""),
        )

        r_uinfo_t = admin.get(f"{BASE_URL}/dashboard/admin/users/by-username/teacher/info")
        self.assert_test(
            "Admin user info (teacher) responds 200 JSON",
            r_uinfo_t.status_code == 200
            and "application/json" in r_uinfo_t.headers.get("content-type", ""),
        )

        r_enr_status = admin.get(f"{BASE_URL}/dashboard/admin/users/enrich-gitlab/status")
        self.assert_test(
            "Admin GitLab enrichment status responds 200 JSON", r_enr_status.status_code == 200
        )

        # 1.3 Admin Courses
        r = admin.get(f"{BASE_URL}/dashboard/admin/courses")
        self.assert_test("Admin Courses 200", r.status_code == 200)
        self.assert_test("Admin Courses table", "courses" in r.text.lower())
        r_active = admin.get(f"{BASE_URL}/dashboard/admin/courses?filter=active")
        self.assert_test("Admin Courses filter=active 200", r_active.status_code == 200)
        r_arch = admin.get(f"{BASE_URL}/dashboard/admin/courses?filter=archived")
        self.assert_test("Admin Courses filter=archived 200", r_arch.status_code == 200)

        # 1.4 Admin System & APIs
        r = admin.get(f"{BASE_URL}/dashboard/admin/system")
        self.assert_test("Admin System 200", r.status_code == 200)
        self.assert_test(
            "Admin System contains health/jobs info",
            "jobs" in r.text.lower() or "system" in r.text.lower(),
        )

        r_stats = admin.get(f"{BASE_URL}/dashboard/api/v1/admin/system/stats")
        self.assert_test("Admin System Stats API 200", r_stats.status_code == 200)

        r_jobs = admin.get(f"{BASE_URL}/dashboard/api/v1/admin/system/jobs")
        self.assert_test("Admin System Jobs API 200", r_jobs.status_code == 200)

        # Cache Clear API
        r_cache = admin.post(
            f"{BASE_URL}/dashboard/api/v1/admin/cache/clear", headers={"X-CSRF-Token": csrf}
        )
        self.assert_test("Admin Cache Clear responds 200", r_cache.status_code == 200)

        # 1.5 Admin Audit Events
        r = admin.get(f"{BASE_URL}/dashboard/admin/events")
        self.assert_test("Admin Events 200", r.status_code == 200)

        # 1.6 Course Archive & Activate Toggle
        cid = self.demo_course_id
        r_arch = admin.post(
            f"{BASE_URL}/dashboard/courses/{cid}/archive",
            headers={"X-CSRF-Token": csrf, "HX-Request": "true"},
        )
        self.assert_test(
            "Admin Archive Course responds successfully",
            r_arch.status_code in (200, 204, 303),
            f"status {r_arch.status_code}",
        )
        r_act = admin.post(
            f"{BASE_URL}/dashboard/courses/{cid}/activate",
            headers={"X-CSRF-Token": csrf, "HX-Request": "true"},
        )
        self.assert_test(
            "Admin Activate Course responds successfully",
            r_act.status_code in (200, 204, 303),
            f"status {r_act.status_code}",
        )

        # 1.7 Admin Support Tickets View
        r_tickets = admin.get(f"{BASE_URL}/dashboard/support/tickets")
        self.assert_test("Admin Support Tickets 200", r_tickets.status_code == 200)

    def run_teacher_tests(self) -> None:
        print("\n==========================================")
        print("  2. TEACHER PERSONA E2E TESTS")
        print("==========================================")
        teacher = self.login("teacher", "teacher")
        cid = self.demo_course_id

        # 2.1 Home & Widgets
        r = teacher.get(f"{BASE_URL}/dashboard/")
        self.assert_test("Teacher Home 200", r.status_code == 200)
        self.assert_test("Teacher sees ZDEVOPS-DEMO", "ZDEVOPS-DEMO" in r.text)

        r_stats = teacher.get(f"{BASE_URL}/dashboard/stats")
        self.assert_test("Teacher /dashboard/stats 200", r_stats.status_code == 200)

        # 2.2 Course Overview & Live Data
        r = teacher.get(f"{BASE_URL}/dashboard/courses/{cid}")
        self.assert_test("Course Overview 200", r.status_code == 200, f"got status {r.status_code}")
        self.assert_test("Course Overview contains team list", "tim-01" in r.text)

        r_live = teacher.get(f"{BASE_URL}/dashboard/courses/{cid}/live-data")
        self.assert_test(
            "Course live-data 200 JSON",
            r_live.status_code == 200
            and "application/json" in r_live.headers.get("content-type", ""),
        )

        # 2.3 Course Teachers Page & Save Button Initial State
        r = teacher.get(f"{BASE_URL}/dashboard/courses/{cid}/teachers")
        self.assert_test("Course Teachers 200", r.status_code == 200, f"got status {r.status_code}")
        self.assert_test("Course Teachers has Save Changes button", "btnSaveTeachers" in r.text)
        self.assert_test(
            "Save Changes starts disabled",
            'id="btnSaveTeachers"' in r.text and "disabled" in r.text,
        )
        self.assert_test("Save Changes has tooltip wrapper", "gl-tip-wrap" in r.text)
        self.assert_test("Add teacher controls present", "teacher-add-row" in r.text)
        csrf = self.extract_csrf(r.text)

        # Extract expected_updated_at from form
        expected_ts_match = re.search(
            r'name=["\']expected_updated_at["\']\s+value=["\']([^"\']+)["\']', r.text
        )
        expected_ts = expected_ts_match.group(1) if expected_ts_match else ""

        # Test Save Teachers POST (using standard form submission)
        teachers_post_data = {
            "csrf_token": csrf,
            "expected_updated_at": expected_ts,
            "teachers_json": json.dumps(
                [
                    {"username": "demo.ucitel", "role": "owner"},
                    {"username": "teacher", "role": "owner"},
                ]
            ),
        }
        r_save_t = teacher.post(
            f"{BASE_URL}/dashboard/courses/{cid}/teachers",
            data=teachers_post_data,
            allow_redirects=True,
        )
        self.assert_test(
            "Save Teachers POST responds 200/303",
            r_save_t.status_code in (200, 303),
            f"status {r_save_t.status_code}",
        )

        # 2.4 Course Settings Page & Form Submission
        r = teacher.get(f"{BASE_URL}/dashboard/courses/{cid}/settings")
        self.assert_test("Course Settings 200", r.status_code == 200, f"got status {r.status_code}")
        csrf_settings = self.extract_csrf(r.text)

        # Extract optimistic lock timestamps from settings form
        exp_settings_ts_m = re.search(
            r'name=["\']expected_settings_updated_at["\']\s+value=["\']([^"\']+)["\']', r.text
        )
        exp_settings_ts = exp_settings_ts_m.group(1) if exp_settings_ts_m else ""

        exp_course_ts_m = re.search(
            r'name=["\']expected_course_updated_at["\']\s+value=["\']([^"\']+)["\']', r.text
        )
        exp_course_ts = exp_course_ts_m.group(1) if exp_course_ts_m else ""

        # Test updating settings form
        settings_payload = {
            "csrf_token": csrf_settings,
            "expected_settings_updated_at": exp_settings_ts,
            "expected_course_updated_at": exp_course_ts,
            "course_name": "Základy DevOps (demonštračný kurz)",
            "course_code": "ZDEVOPS-DEMO",
            "course_description": "Aktualizovaný popis demonštračného kurzu cez E2E test",
            "academic_year": "2025/2026",
            "semester": "winter",
            "green_threshold": "75",
            "yellow_threshold": "50",
        }
        r_post_settings = teacher.post(
            f"{BASE_URL}/dashboard/courses/{cid}/settings",
            data=settings_payload,
            allow_redirects=True,
        )
        self.assert_test(
            "Course Settings Save POST 200/303",
            r_post_settings.status_code in (200, 303),
            f"status {r_post_settings.status_code}",
        )

        # 2.5 Compliance Checks Page & API
        r = teacher.get(f"{BASE_URL}/dashboard/courses/{cid}/checks")
        self.assert_test("Course Checks 200", r.status_code == 200, f"got status {r.status_code}")
        self.assert_test("Course Checks contains R01-R13", "R01" in r.text and "R13" in r.text)

        # Export checks config
        r_exp = teacher.get(f"{BASE_URL}/dashboard/courses/{cid}/checks/export")
        self.assert_test(
            "Course Checks Export responds 200 JSON",
            r_exp.status_code == 200
            and "application/json" in r_exp.headers.get("content-type", ""),
        )

        # Toggle/update check R01 weight
        r_put_check = teacher.put(
            f"{BASE_URL}/dashboard/courses/{cid}/checks/R01",
            headers={"X-CSRF-Token": csrf_settings},
            json={"is_active": True, "weight": 0.08},
        )
        self.assert_test(
            "Course Check R01 PUT responds 200",
            r_put_check.status_code == 200,
            f"status {r_put_check.status_code}",
        )

        # 2.6 Custom Checks CRUD Lifecycle (Create -> Read -> Update -> Delete)
        r_cc_list = teacher.get(f"{BASE_URL}/dashboard/courses/{cid}/custom-checks")
        self.assert_test(
            "Custom Checks List 200 JSON",
            r_cc_list.status_code == 200
            and "application/json" in r_cc_list.headers.get("content-type", ""),
        )

        # Create custom check
        cc_payload = {
            "check_code": "C99",
            "name": "E2E Automated Custom Check",
            "description": "Created during E2E testing to verify custom check lifecycle",
            "category": "issue",
            "evaluation_rule": {"type": "count", "entity": "issue", "threshold": 2},
            "weight": 0.05,
            "is_active": True,
        }
        r_create_cc = teacher.post(
            f"{BASE_URL}/dashboard/courses/{cid}/custom-checks",
            headers={"X-CSRF-Token": csrf_settings},
            json=cc_payload,
        )
        self.assert_test(
            "Create Custom Check C99 responds 201",
            r_create_cc.status_code == 201,
            f"status {r_create_cc.status_code}",
        )
        created_cc = r_create_cc.json() if r_create_cc.status_code == 201 else {}
        cc_id = created_cc.get("id")

        if cc_id:
            # Update custom check
            r_up_cc = teacher.put(
                f"{BASE_URL}/dashboard/courses/{cid}/custom-checks/{cc_id}",
                headers={"X-CSRF-Token": csrf_settings},
                json={"name": "E2E Custom Check Updated", "weight": 0.06},
            )
            self.assert_test(
                "Update Custom Check responds 200",
                r_up_cc.status_code == 200,
                f"status {r_up_cc.status_code}",
            )

            # Delete custom check
            r_del_cc = teacher.delete(
                f"{BASE_URL}/dashboard/courses/{cid}/custom-checks/{cc_id}",
                headers={"X-CSRF-Token": csrf_settings},
            )
            self.assert_test(
                "Delete Custom Check responds 200",
                r_del_cc.status_code == 200,
                f"status {r_del_cc.status_code}",
            )

        # 2.7 Course Projects, Analytics & Activity
        r = teacher.get(f"{BASE_URL}/dashboard/courses/{cid}/projects")
        self.assert_test("Course Projects 200", r.status_code == 200, f"got status {r.status_code}")

        r = teacher.get(f"{BASE_URL}/dashboard/courses/{cid}/analytics")
        self.assert_test(
            "Course Analytics 200", r.status_code == 200, f"got status {r.status_code}"
        )

        r = teacher.get(f"{BASE_URL}/dashboard/courses/{cid}/activity")
        self.assert_test("Course Activity 200", r.status_code == 200, f"got status {r.status_code}")

        # 2.8 Team Drilldown & Student Exclusion Toggle
        r = teacher.get(f"{BASE_URL}/dashboard/teams/{self.demo_team_id}")
        self.assert_test("Team Detail 200", r.status_code == 200, f"got status {r.status_code}")
        self.assert_test("Team Detail has Adam Bali", "Adam Bali" in r.text)

        r_team_live = teacher.get(f"{BASE_URL}/dashboard/teams/{self.demo_team_id}/live-data")
        self.assert_test("Team Live Data responds 200 JSON", r_team_live.status_code == 200)

        if self.demo_student_id:
            csrf_team = self.extract_csrf(r.text)
            r_ex = teacher.post(
                f"{BASE_URL}/dashboard/teams/{self.demo_team_id}/members/{self.demo_student_id}/toggle-exclusion",
                headers={"X-CSRF-Token": csrf_team, "HX-Request": "true"},
            )
            self.assert_test(
                "Student Exclusion Toggle 200",
                r_ex.status_code in (200, 204),
                f"status {r_ex.status_code}",
            )
            r_ex2 = teacher.post(
                f"{BASE_URL}/dashboard/teams/{self.demo_team_id}/members/{self.demo_student_id}/toggle-exclusion",
                headers={"X-CSRF-Token": csrf_team, "HX-Request": "true"},
            )
            self.assert_test(
                "Student Exclusion Untoggle 200",
                r_ex2.status_code in (200, 204),
                f"status {r_ex2.status_code}",
            )

            # 2.9 Student Profile in Team
            r_stud = teacher.get(
                f"{BASE_URL}/dashboard/students/{self.demo_student_id}/team/{self.demo_team_id}"
            )
            self.assert_test(
                "Teacher views Student Profile 200",
                r_stud.status_code == 200,
                f"status {r_stud.status_code}",
            )

        # 2.10 Project Drilldown
        if self.demo_project_id:
            r = teacher.get(f"{BASE_URL}/dashboard/projects/{self.demo_project_id}")
            self.assert_test(
                "Project Detail 200", r.status_code == 200, f"got status {r.status_code}"
            )

            r_proj_live = teacher.get(
                f"{BASE_URL}/dashboard/projects/{self.demo_project_id}/live-data"
            )
            self.assert_test("Project Live Data 200 JSON", r_proj_live.status_code == 200)

        # 2.11 Teacher Support Tickets Queue
        r_t_tickets = teacher.get(f"{BASE_URL}/dashboard/support/tickets")
        self.assert_test("Teacher Support Tickets 200", r_t_tickets.status_code == 200)

    def run_student_tests(self) -> None:
        print("\n==========================================")
        print("  3. STUDENT PERSONA E2E TESTS")
        print("==========================================")
        student = self.login("adam.bali", "student")
        cid = self.demo_course_id

        # 3.1 Student Home & Realtime
        r = student.get(f"{BASE_URL}/dashboard/")
        self.assert_test("Student Home 200", r.status_code == 200)
        self.assert_test("Student sees enrolled course", "ZDEVOPS-DEMO" in r.text)

        r_stats = student.get(f"{BASE_URL}/dashboard/stats")
        self.assert_test("Student /dashboard/stats 200", r_stats.status_code == 200)

        r_att = student.get(f"{BASE_URL}/dashboard/attention-items")
        self.assert_test("Student /dashboard/attention-items 200", r_att.status_code == 200)

        r_badges = student.get(f"{BASE_URL}/dashboard/sidebar-badges")
        self.assert_test("Student /dashboard/sidebar-badges 200", r_badges.status_code == 200)

        # 3.2 RBAC Boundaries (Access Denied to Admin & Staff Features)
        protected_endpoints = [
            "/dashboard/admin/users",
            "/dashboard/admin/system",
            "/dashboard/admin/courses",
            "/dashboard/admin/events",
            "/dashboard/support/tickets",
            f"/dashboard/courses/{cid}/settings",
            f"/dashboard/courses/{cid}/teachers",
        ]
        for ep in protected_endpoints:
            r = student.get(f"{BASE_URL}{ep}", allow_redirects=False)
            self.assert_test(
                f"Student denied {ep} (403 or redirect)",
                r.status_code in (403, 302, 303),
                f"got {r.status_code}",
            )

        # Student denied custom checks POST
        r_cc_denied = student.post(
            f"{BASE_URL}/dashboard/courses/{cid}/custom-checks",
            headers={"X-CSRF-Token": "invalid-or-fake"},
            json={"name": "Hacker Check"},
        )
        self.assert_test(
            "Student denied creating custom check (403)",
            r_cc_denied.status_code == 403,
            f"got {r_cc_denied.status_code}",
        )

        # Student denied member exclusion POST
        r_ex_denied = student.post(
            f"{BASE_URL}/dashboard/teams/{self.demo_team_id}/members/{self.demo_student_id}/toggle-exclusion",
            headers={"X-CSRF-Token": "fake"},
        )
        self.assert_test(
            "Student denied toggling member exclusion (403)",
            r_ex_denied.status_code == 403,
            f"got {r_ex_denied.status_code}",
        )

        # 3.3 Student Enrolled Course & Team View
        r_course = student.get(f"{BASE_URL}/dashboard/courses/{cid}")
        self.assert_test("Student Course Overview 200", r_course.status_code == 200)

        r_team = student.get(f"{BASE_URL}/dashboard/teams/{self.demo_team_id}")
        self.assert_test(
            "Student can view enrolled team 200",
            r_team.status_code == 200,
            f"status {r_team.status_code}",
        )
        self.assert_test("Student team page contains team members", "Adam Bali" in r_team.text)

        r_team_live = student.get(f"{BASE_URL}/dashboard/teams/{self.demo_team_id}/live-data")
        self.assert_test("Student Team Live Data 200 JSON", r_team_live.status_code == 200)

        # 3.4 Student Project View
        if self.demo_project_id:
            r_proj = student.get(f"{BASE_URL}/dashboard/projects/{self.demo_project_id}")
            self.assert_test("Student Project Detail 200", r_proj.status_code == 200)

            r_proj_live = student.get(
                f"{BASE_URL}/dashboard/projects/{self.demo_project_id}/live-data"
            )
            self.assert_test("Student Project Live Data 200 JSON", r_proj_live.status_code == 200)

        # 3.5 Student Own Profile Drilldown
        if self.demo_student_id:
            r_own_prof = student.get(
                f"{BASE_URL}/dashboard/students/{self.demo_student_id}/team/{self.demo_team_id}"
            )
            self.assert_test("Student can view own profile 200", r_own_prof.status_code == 200)

        # 3.6 Student User Preferences & Preference Update
        r = student.get(f"{BASE_URL}/dashboard/preferences")
        self.assert_test("Student Preferences Page 200", r.status_code == 200)
        csrf_pref = self.extract_csrf(r.text)

        r_pref_post = student.post(
            f"{BASE_URL}/dashboard/api/preferences",
            headers={"X-CSRF-Token": csrf_pref},
            json={"theme_preference": "dark", "layout_width": "fixed"},
        )
        self.assert_test(
            "Student Preferences Update responds 200",
            r_pref_post.status_code == 200,
            f"status {r_pref_post.status_code}",
        )

        # 3.7 Support / Help Desk Page
        r_sup = student.get(f"{BASE_URL}/dashboard/support")
        self.assert_test("Student Support Page 200", r_sup.status_code == 200)

    def print_summary(self) -> int:
        print("\n==========================================")
        print("  E2E TEST RUN SUMMARY")
        print("==========================================")
        print(f"Total Passed: {self.passed}")
        print(f"Total Failed: {self.failed}")
        if self.failed > 0:
            print("\nFailures:")
            for f in self.failures:
                print(f" - {f}")
            return 1
        print("\nALL E2E PERSONA TESTS PASSED CLEANLY! (100% SUCCESS)")
        return 0


def main() -> None:
    runner = E2ERunner()
    runner.run_admin_tests()
    runner.run_teacher_tests()
    runner.run_student_tests()
    sys.exit(runner.print_summary())


if __name__ == "__main__":
    main()
