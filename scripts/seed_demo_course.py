#!/usr/bin/env python3
"""Naplní vývojovú databázu demonštračným kurzom.

Skript vytvorí kurz s dvoma skupinami a ich projektmi, vygeneruje tikety,
žiadosti o zlúčenie, recenzné poznámky, schválenia, commity a procesy CI/CD
a nakoniec nechá skutočný kontrolný mechanizmus (``compute_team_metrics``)
vypočítať výsledky R01 až R13.  Žiadne skóre sa nezapisuje ručne.

Mechanizmus zapíše snímku len pre aktuálny týždeň, takže karta Priebeh
plnenia u študenta mala jediný bod.  Predchádzajúce týždne sa preto odvodia
z tejto snímky: kontroly, ktoré študent dnes spĺňa, mu v skorších týždňoch
prechádzajú postupne (v poradí kódov), skóre je súčet váh práve prejdených
kontrol - žiadne číslo, ktoré by mechanizmus nevedel vypočítať.

Použitie:
    DATABASE_URL=postgresql+asyncpg://gitpulse:gitpulse@localhost:5433/gitpulse \
        python scripts/seed_demo_course.py
"""

from __future__ import annotations

import asyncio
import os
import random
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.compliance.engine import compute_team_metrics
from app.models.commit import Commit
from app.models.course import Course
from app.models.course_membership import CourseMembership
from app.models.course_settings import CourseSettings
from app.models.issue import Issue
from app.models.merge_request import MergeRequest
from app.models.mr_approval import MRApproval
from app.models.mr_note import MRNote
from app.models.pipeline import Pipeline
from app.models.project import GitLabProject
from app.models.review_activity import ReviewActivity
from app.models.student import Student
from app.models.student_compliance_snapshot import StudentComplianceSnapshot
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User

RNG = random.Random(20260921)  # noqa: S311 - iba demonštračné údaje, nie kryptografia
NOW = datetime.now(UTC)
SEM_START = (NOW - timedelta(days=70)).date()
SEM_END = (NOW + timedelta(days=35)).date()

TEACHER_USERNAME = os.environ.get("DEMO_TEACHER", "demo.ucitel")
# Aktualny kod demo kurzu a kody z predchadzajucich behov, ktore sa maju premazat.
DEMO_CODES = ("ZSI-DEMO", "ZDEVOPS-DEMO")

# (meno, profil).  Profil riadi, ktore kroky student spravil - cisla
# nasledne dopocita samotny kontrolny mechanizmus.
TEAMS: dict[str, list[tuple[str, str]]] = {
    "tim-01-kniznica": [
        ("Adam Bali", "full"),
        ("Barbora Cierna", "full"),
        ("Cyril Danko", "no_review_given"),
        ("Dana Ferencova", "no_tests"),
        ("Erik Gajdos", "partial"),
        ("Filip Hudak", "web_editor"),
    ],
    "tim-02-rezervacie": [
        ("Gabriela Ivanova", "full"),
        ("Hugo Jankovic", "partial"),
        ("Ivana Kralova", "no_answer"),
        ("Jakub Lukac", "inactive"),
        ("Karol Matus", "no_pipeline"),
        ("Lucia Nemcova", "full"),
    ],
    "tim-03-notifikacie": [
        ("Marek Ondrus", "draft"),
        ("Natalia Pavlikova", "draft"),
        ("Oliver Repka", "no_mr"),
        ("Petra Sabolova", "partial"),
        ("Radovan Tkac", "inactive"),
        ("Simona Urbanova", "full"),
    ],
}

REVIEW_BODIES = [
    "Metóda robí dve veci naraz, rozdelil by som ju na načítanie a na validáciu. "
    "Inak by sa to zle testovalo a názov by prestal sedieť.",
    "Tu chýba ošetrenie prípadu, keď zoznam príde prázdny. Padne to na indexe, "
    "skús doplniť test presne na túto situáciu.",
    "Názov premennej nič nehovorí, premenuj ju podľa toho, čo naozaj obsahuje. "
    "Zvyšok zmeny je v poriadku a číta sa dobre.",
    "Tento cyklus prechádza kolekciu dvakrát, dá sa to spraviť jedným prechodom. "
    "Pri väčších dátach by to bolo znateľné.",
    "Chýba mi test na hraničnú hodnotu, ktorú spomínaš v popise. Bez neho sa nedá "
    "overiť, že oprava naozaj funguje.",
]
AUTHOR_ANSWERS = [
    "Máš pravdu, rozdelil som to na dve metódy a doplnil test, pozri commit a1b2c3d.",
    "Opravené v commite 4d5e6f7, doplnil som aj kontrolu prázdneho vstupu.",
    "Premenoval som to a upravil aj popis, zmena je v commite 9f8e7d6.",
]


def wc(text: str) -> int:
    return len(text.split())


async def wipe(session: AsyncSession) -> None:
    """Zmaže predchádzajúci demonštračný kurz, aby bol beh opakovateľný."""
    res = await session.execute(select(Course).where(Course.code.in_(DEMO_CODES)))
    course = res.scalars().first()
    if course is None:
        # Aj bez kurzu môžu ostať študenti z prerušeného behu.
        await session.execute(delete(Student).where(Student.gitlab_user_id >= 90_000))
        await session.commit()
        return
    teams = (await session.execute(select(Team).where(Team.course_id == course.id))).scalars().all()
    for team in teams:
        projects = (
            (await session.execute(select(GitLabProject).where(GitLabProject.team_id == team.id)))
            .scalars()
            .all()
        )
        for p in projects:
            mrs = (
                (await session.execute(select(MergeRequest).where(MergeRequest.project_id == p.id)))
                .scalars()
                .all()
            )
            for mr in mrs:
                for model in (MRNote, MRApproval, ReviewActivity):
                    await session.execute(delete(model).where(model.merge_request_id == mr.id))
                await session.execute(delete(Pipeline).where(Pipeline.merge_request_id == mr.id))
            await session.execute(delete(Pipeline).where(Pipeline.project_id == p.id))
            await session.execute(delete(MergeRequest).where(MergeRequest.project_id == p.id))
            await session.execute(delete(Issue).where(Issue.project_id == p.id))
            await session.execute(delete(Commit).where(Commit.project_id == p.id))
        await session.execute(delete(GitLabProject).where(GitLabProject.team_id == team.id))
        await session.execute(delete(TeamMember).where(TeamMember.team_id == team.id))
    from app.models.metric_snapshot import MetricSnapshot
    from app.models.team_metric_snapshot import TeamMetricSnapshot

    await session.execute(delete(MetricSnapshot).where(MetricSnapshot.course_id == course.id))
    await session.execute(
        delete(TeamMetricSnapshot).where(TeamMetricSnapshot.course_id == course.id)
    )
    await session.execute(delete(Team).where(Team.course_id == course.id))
    # Demonštrační študenti majú vyhradený rozsah identifikátorov 90 000+.
    await session.execute(delete(Student).where(Student.gitlab_user_id >= 90_000))
    await session.execute(delete(CourseSettings).where(CourseSettings.course_id == course.id))
    await session.execute(delete(CourseMembership).where(CourseMembership.course_id == course.id))
    await session.execute(delete(Course).where(Course.id == course.id))
    await session.commit()
    print("  predchadzajuci demo kurz odstraneny")


async def build(session: AsyncSession) -> str:
    course = Course(
        code="ZSI-DEMO",
        name="Základy softvérového inžinierstva",
        academic_year="2026/2027",
        semester="winter",
        is_active=True,
        description="Demonštračné údaje pre snímky obrazovky v diplomovej práci.",
    )
    session.add(course)
    await session.flush()

    session.add(
        CourseSettings(
            course_id=course.id,
            semester_start_date=SEM_START,
            semester_end_date=SEM_END,
            gitlab_group_path="kpi-zsi/2026",
        )
    )

    teacher = (
        await session.execute(select(User).where(User.username == TEACHER_USERNAME))
    ).scalar_one_or_none()
    if teacher is None:
        teacher = User(
            username=TEACHER_USERNAME,
            full_name="Demonštračný účet vyučujúceho",
            email="demo.ucitel@example.sk",
            password_hash="oauth:demo",  # noqa: S106 - zástupná hodnota, prihlásenie ide cez OAuth
            role="admin",
            is_active=True,
            gitlab_username=TEACHER_USERNAME,
            theme_preference="light",
        )
        session.add(teacher)
        await session.flush()
    else:
        teacher.role = "admin"
        teacher.theme_preference = "light"
    session.add(CourseMembership(user_id=teacher.id, course_id=course.id, role="owner"))

    # Also ensure 'teacher' persona exists and is owner of this demo course
    dev_teacher = (
        await session.execute(select(User).where(User.username == "teacher"))
    ).scalar_one_or_none()
    if dev_teacher is None:
        dev_teacher = User(
            username="teacher",
            full_name="Prof. Test Teacher",
            email="teacher@dev.local",
            password_hash="oauth:demo",  # noqa: S106 - zástupná hodnota, prihlásenie ide cez OAuth
            role="teacher",
            is_active=True,
            gitlab_username="teacher",
            theme_preference="light",
        )
        session.add(dev_teacher)
        await session.flush()
    else:
        dev_teacher.role = "teacher"
        dev_teacher.is_active = True
    session.add(CourseMembership(user_id=dev_teacher.id, course_id=course.id, role="owner"))

    # Also ensure 'admin' persona exists
    dev_admin = (
        await session.execute(select(User).where(User.username == "admin"))
    ).scalar_one_or_none()
    if dev_admin is None:
        dev_admin = User(
            username="admin",
            full_name="GitPulse Administrator",
            email="admin@dev.local",
            password_hash="oauth:demo",  # noqa: S106 - zástupná hodnota, prihlásenie ide cez OAuth
            role="admin",
            is_active=True,
            gitlab_username="admin",
            theme_preference="light",
        )
        session.add(dev_admin)
        await session.flush()
    else:
        dev_admin.role = "admin"
        dev_admin.is_active = True

    await session.flush()

    gl_id = 90_000
    note_id = 500_000
    team_ids: list[str] = []

    for t_index, (team_name, roster) in enumerate(TEAMS.items(), start=1):
        team = Team(
            course_id=course.id,
            name=team_name,
            gitlab_group_id=8000 + t_index,
            gitlab_group_path=f"kpi-zsi/2026/{team_name}",
            is_active=True,
            members_synced_at=NOW,
        )
        session.add(team)
        await session.flush()
        team_ids.append(str(team.id))

        project = GitLabProject(
            team_id=team.id,
            gitlab_project_id=70_000 + t_index,
            gitlab_project_path=f"kpi-zsi/2026/{team_name}/aplikacia",
            gitlab_project_name="aplikacia",
            default_branch="main",
            is_active=True,
            last_synced_at=NOW,
        )
        session.add(project)
        await session.flush()

        students: list[Student] = []
        for full_name, _profile in roster:
            gl_id += 1
            username = (
                full_name.lower()
                .replace(" ", ".")
                .translate(str.maketrans("áäčďéíĺľňóôŕšťúýž", "aacdeillnoorstuyz"))
            )
            student = Student(
                gitlab_user_id=gl_id,
                gitlab_username=username,
                full_name=full_name,
                email=f"{username}@student.university.edu",
            )
            session.add(student)
            await session.flush()
            students.append(student)
            session.add(
                TeamMember(
                    team_id=team.id,
                    student_id=student.id,
                    joined_at=NOW - timedelta(days=60),
                    gitlab_access_level=30,
                    gitlab_access_role="Developer",
                    is_active=True,
                    membership_source="direct",
                    last_synced_at=NOW,
                )
            )

        # --- tikety, ziadosti o zlucenie a vsetko okolo nich ---
        for s_index, (student, (full_name, profile)) in enumerate(
            zip(students, roster, strict=True), start=1
        ):
            if profile == "inactive":
                continue

            iid = s_index
            created = NOW - timedelta(days=RNG.randint(22, 34))
            issue_closed = profile not in {"partial", "no_answer", "draft", "no_mr"}
            issue = Issue(
                project_id=project.id,
                gitlab_id=gl_id + 1000 + iid,
                gitlab_iid=iid,
                title=f"Úloha {iid}: {['import údajov', 'filtrovanie zoznamu', 'export do CSV', 'stránkovanie', 'notifikácie', 'validácia formulára'][s_index % 6]}",
                description="Zadanie z cvičenia. Súčasťou je aj jednotkový test.",
                state="closed" if issue_closed else "opened",
                author_gitlab_id=student.gitlab_user_id,
                author_id=student.id,
                assignee_gitlab_id=student.gitlab_user_id,
                assignee_id=student.id,
                all_assignee_gitlab_ids=[student.gitlab_user_id],
                labels=["zadanie"],
                created_at=created,
                closed_at=created + timedelta(days=6) if issue_closed else None,
                updated_at=NOW,
                synced_at=NOW,
            )
            session.add(issue)
            await session.flush()

            if profile == "no_mr":
                continue

            merged = profile not in {"partial", "no_answer", "draft"}
            has_tests = profile not in {"no_tests", "draft"}
            changed = ["src/app/service.py", "README.md"]
            if has_tests:
                changed.insert(1, f"tests/test_uloha_{iid}.py")

            mr = MergeRequest(
                project_id=project.id,
                gitlab_id=gl_id + 2000 + iid,
                gitlab_iid=iid,
                title=f"Úloha {iid}: implementácia a testy",
                description=(
                    f"## Popis zmeny\nRieši #{iid}. Doplnená logika služby a jednotkové testy "
                    "pre hraničné hodnoty vstupu.\n\n## Ako to otestovať\n"
                    "Spustiť `pytest tests/` a skontrolovať zelený proces CI/CD."
                ),
                state="merged" if merged else "opened",
                source_branch=f"feature/uloha-{iid}",
                target_branch="main",
                author_gitlab_id=student.gitlab_user_id,
                author_id=student.id,
                merged_by_gitlab_id=student.gitlab_user_id if merged else None,
                merged_by_id=student.id if merged else None,
                reviewer_gitlab_ids=[],
                approved_by_gitlab_ids=[],
                linked_issue_iid=iid,
                linked_issue_id=issue.id,
                branch_naming_ok=True,
                template_compliant=True,
                has_test_changes=has_tests,
                has_issue_link=True,
                approvals_required=2,
                approvals_count=0,
                files_changed=len(changed),
                lines_added=RNG.randint(40, 190),
                lines_removed=RNG.randint(3, 40),
                changed_files=changed,
                created_at=created + timedelta(days=2),
                merged_at=created + timedelta(days=6) if merged else None,
                updated_at=NOW,
                synced_at=NOW,
            )
            session.add(mr)
            await session.flush()

            # recenzenti: dvaja spoluziaci
            reviewers = [students[(s_index + k) % len(students)] for k in (1, 2)]
            reviewers = [r for r in reviewers if r.id != student.id][:2]
            if profile == "draft":
                reviewers = []
            approvals = 0
            for r_index, reviewer in enumerate(reviewers):
                if profile == "partial" and r_index > 0:
                    continue
                disc = f"disc-{iid}-{r_index}"
                body = REVIEW_BODIES[(s_index + r_index) % len(REVIEW_BODIES)]
                note_id += 1
                session.add(
                    MRNote(
                        merge_request_id=mr.id,
                        gitlab_note_id=note_id,
                        author_gitlab_id=reviewer.gitlab_user_id,
                        author_id=reviewer.id,
                        author_username=reviewer.gitlab_username,
                        body=body,
                        word_count=wc(body),
                        char_count=len(body),
                        is_system=False,
                        is_resolvable=True,
                        is_resolved=profile != "no_answer",
                        discussion_id=disc,
                        note_type="DiffNote",
                        position_path="src/app/service.py",
                        created_at=mr.created_at + timedelta(hours=6 + r_index * 5),
                        updated_at=NOW,
                        synced_at=NOW,
                    )
                )
                session.add(
                    ReviewActivity(
                        merge_request_id=mr.id,
                        reviewer_id=reviewer.id,
                        note_count=1,
                        total_words=wc(body),
                        total_chars=len(body),
                        first_note_at=mr.created_at + timedelta(hours=6 + r_index * 5),
                        last_note_at=mr.created_at + timedelta(hours=6 + r_index * 5),
                        is_meaningful=True,
                        is_approved=True,
                        recomputed_at=NOW,
                    )
                )
                mr.reviewer_gitlab_ids = [*mr.reviewer_gitlab_ids, reviewer.gitlab_user_id]

                # odpoved autora
                if profile != "no_answer":
                    ans = AUTHOR_ANSWERS[(s_index + r_index) % len(AUTHOR_ANSWERS)]
                    note_id += 1
                    session.add(
                        MRNote(
                            merge_request_id=mr.id,
                            gitlab_note_id=note_id,
                            author_gitlab_id=student.gitlab_user_id,
                            author_id=student.id,
                            author_username=student.gitlab_username,
                            body=ans,
                            word_count=wc(ans),
                            char_count=len(ans),
                            is_system=False,
                            is_resolvable=True,
                            is_resolved=True,
                            discussion_id=disc,
                            note_type="DiffNote",
                            contains_commit_ref=True,
                            commit_refs=["a1b2c3d"],
                            created_at=mr.created_at + timedelta(hours=20 + r_index * 4),
                            updated_at=NOW,
                            synced_at=NOW,
                        )
                    )

                if merged:
                    session.add(
                        MRApproval(
                            merge_request_id=mr.id,
                            approver_gitlab_id=reviewer.gitlab_user_id,
                            approver_id=reviewer.id,
                            approved_at=mr.created_at + timedelta(days=1),
                            synced_at=NOW,
                        )
                    )
                    approvals += 1
                    mr.approved_by_gitlab_ids = [
                        *mr.approved_by_gitlab_ids,
                        reviewer.gitlab_user_id,
                    ]
            mr.approvals_count = approvals

            # commity
            n_commits = RNG.randint(5, 11)
            web = n_commits if profile == "web_editor" else 0
            for c in range(n_commits):
                title = (
                    f"Update {changed[c % len(changed)]}"
                    if c < web
                    else [
                        "Doplnenie validacie vstupu",
                        "Oprava chyby pri prazdnom zozname",
                        "Test na hranicnu hodnotu",
                        "Refaktor sluzby na dve metody",
                        "Uprava popisu v README",
                    ][c % 5]
                )
                session.add(
                    Commit(
                        project_id=project.id,
                        sha=f"{abs(hash((team_name, iid, c))):040x}"[:40],
                        short_sha=f"{abs(hash((team_name, iid, c))):x}"[:8],
                        title=title,
                        message=title,
                        author_gitlab_id=student.gitlab_user_id,
                        author_id=student.id,
                        author_name=full_name,
                        author_email=student.email,
                        parent_shas=[],
                        ref=mr.source_branch,
                        committed_at=mr.created_at + timedelta(hours=c * 7),
                        synced_at=NOW,
                    )
                )

            # proces CI/CD
            if profile == "draft":
                pass
            elif profile != "no_pipeline":
                session.add(
                    Pipeline(
                        project_id=project.id,
                        gitlab_pipeline_id=gl_id + 3000 + iid,
                        merge_request_id=mr.id,
                        ref=mr.source_branch,
                        sha=f"{abs(hash((team_name, iid))):040x}"[:40],
                        status="success",
                        source="merge_request_event",
                        has_test_job=True,
                        test_job_status="success",
                        coverage=float(RNG.randint(62, 94)),
                        total_jobs=4,
                        duration_seconds=RNG.randint(70, 260),
                        created_at=mr.created_at + timedelta(minutes=5),
                        started_at=mr.created_at + timedelta(minutes=6),
                        finished_at=mr.created_at + timedelta(minutes=10),
                        synced_at=NOW,
                    )
                )
            else:
                session.add(
                    Pipeline(
                        project_id=project.id,
                        gitlab_pipeline_id=gl_id + 3000 + iid,
                        merge_request_id=mr.id,
                        ref=mr.source_branch,
                        sha=f"{abs(hash((team_name, iid))):040x}"[:40],
                        status="failed",
                        source="merge_request_event",
                        has_test_job=False,
                        total_jobs=2,
                        duration_seconds=RNG.randint(30, 90),
                        created_at=mr.created_at + timedelta(minutes=5),
                        started_at=mr.created_at + timedelta(minutes=6),
                        finished_at=mr.created_at + timedelta(minutes=8),
                        synced_at=NOW,
                    )
                )

        await session.flush()

    await session.commit()
    print(f"  kurz {course.code}: {len(TEAMS)} skupin")
    return ",".join(team_ids)


async def backfill_history(session: AsyncSession) -> int:
    """Odvodí týždne 1..N-1 z aktuálnej snímky každého študenta demo kurzu.

    Pre týždeň ``w`` prechádza prvých ``k`` z kontrol, ktoré prechádzajú dnes
    (``k`` rastie s týždňom, každý študent začína z inej výšky), ostatné majú
    ``pass: false`` s pôvodným zdôvodnením.  Skóre týždňa je súčet váh
    prejdených kontrol, rovnako ako to počíta mechanizmus.
    """
    course = (
        await session.execute(select(Course).where(Course.code == DEMO_CODES[0]))
    ).scalar_one()
    rows = (
        (
            await session.execute(
                select(StudentComplianceSnapshot).where(
                    StudentComplianceSnapshot.course_id == course.id
                )
            )
        )
        .scalars()
        .all()
    )
    written = 0
    for cur in rows:
        last_week = int(cur.week_number)
        if last_week < 2:
            continue
        raw = dict(cur.raw_metrics or {})
        detail = raw.get("checks_detail") or {}
        passing = sorted(code for code, c in detail.items() if c.get("pass"))
        # Kde študent začínal: 10-40 % dnešných kontrol už v prvom týždni.
        start = RNG.uniform(0.1, 0.4)
        prev_score: float | None = None
        for week in range(1, last_week):
            frac = start + (1.0 - start) * ((week - 1) / (last_week - 1)) ** 1.3
            k = round(frac * len(passing))
            passed = set(passing[:k])
            week_detail = {}
            for code, c in detail.items():
                cc = dict(c)
                if code in passing and code not in passed:
                    cc["pass"] = False
                    cc["score"] = 0.0
                week_detail[code] = cc
            score = round(sum(float(c.get("score") or 0) for c in week_detail.values()), 4)
            cat = {
                "commit_score": cur.commit_score,
                "mr_score": cur.mr_score,
                "review_score": cur.review_score,
                "ci_score": cur.ci_score,
                "issue_score": cur.issue_score,
            }
            week_raw = {
                **raw,
                "checks_detail": week_detail,
                "checks_passed": len(passed),
                "weighted_score": score,
            }
            session.add(
                StudentComplianceSnapshot(
                    course_id=cur.course_id,
                    team_id=cur.team_id,
                    student_id=cur.student_id,
                    week_number=week,
                    snapshot_date=SEM_START + timedelta(days=7 * (week - 1) + 6),
                    overall_score=score,
                    **{
                        k_: (None if v is None else round(float(v) * frac, 4))
                        for k_, v in cat.items()
                    },
                    prev_week_score=prev_score,
                    improvement_delta=(
                        None if prev_score is None else round(score - prev_score, 4)
                    ),
                    improvement_pct=(
                        None
                        if not prev_score
                        else round((score - prev_score) / prev_score * 100, 2)
                    ),
                    raw_metrics=week_raw,
                )
            )
            prev_score = score
            written += 1
        # Aktuálny týždeň nadväzuje na odvodený predchádzajúci.
        if prev_score is not None:
            cur.prev_week_score = prev_score
            cur.improvement_delta = round(float(cur.overall_score) - prev_score, 4)
            cur.improvement_pct = (
                round((float(cur.overall_score) - prev_score) / prev_score * 100, 2)
                if prev_score
                else None
            )
    await session.commit()
    return written


async def main() -> None:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL nie je nastavena", file=sys.stderr)
        raise SystemExit(1)
    engine = create_async_engine(url, echo=False)
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async with maker() as session:
        print("cistenie...")
        await wipe(session)
        print("vytvaranie demo kurzu...")
        team_ids = await build(session)

    for tid in team_ids.split(","):
        async with maker() as session:
            await compute_team_metrics(session, tid, force_all_checks=True)
            await session.commit()
        print(f"  metriky prepocitane pre skupinu {tid}")

    async with maker() as session:
        n = await backfill_history(session)
    print(f"  historia plnenia odvodena: {n} tyzdennych snimok")

    await engine.dispose()
    print("hotovo")


if __name__ == "__main__":
    asyncio.run(main())
