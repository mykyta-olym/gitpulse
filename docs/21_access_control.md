# Access Control & Privacy System

> **Documentation Status (2026-05-31):** Verified against current implementation.
> - **Source of truth (API):** `src/app/api/*`, `src/app/schemas/*`, runtime `/openapi.json`.
> - **Source of truth (CI/quality gates):** `.gitlab-ci.yml`, `pyproject.toml`.
> - **Local gate baseline:** `python scripts/build_bundle.py --check`, `python scripts/check_static_artifacts.py`, `ruff check src tests scripts`, `ruff format --check src tests scripts`, `mypy src/app`, `pytest -q`.


This document describes the role-based access control (RBAC) and privacy features implemented in the GitPulse.

## Overview

The system implements a three-tier role hierarchy with course-level and team-level access controls to ensure:
- **Teachers** only see courses they are assigned to
- **Students** only see their own team data
- **Admins** have full visibility and management capabilities

## Roles

### Admin
- **Access**: Full access to all courses, teams, and students
- **Capabilities**:
  - View all data across all courses
  - Manage user accounts
  - Assign teachers to courses
  - Create, archive, and configure courses
  - Access admin interfaces (`/dashboard/admin/*`)

### Teacher
- **Access**: Limited to courses where they have a `CourseMembership` with role `teacher` or `owner`
- **Capabilities**:
  - View courses where they hold a membership (any role)
  - View all teams within accessible courses
  - View all student data within accessible teams
  - Configure course settings
  - Manage checks, deadlines, sync, and grading settings
  - Cannot access admin interfaces

### Student
- **Access**: Limited to own team only
- **Capabilities**:
  - View courses where they are a team member or hold a `CourseMembership`
  - View only their own team within each course
  - View only students in their own team
  - Cannot edit any settings
  - Cannot access admin or course configuration

## Course Teacher Assignment

### How It Works

Course-level access is managed through the `course_memberships` table. Each row links a `user_id` to a `course_id` with a `role` (`owner`, `teacher`, or `student`):

```python
class CourseMembership(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "course_memberships"
    user_id: Mapped[uuid.UUID]    # FK -> users.id
    course_id: Mapped[uuid.UUID]  # FK -> courses.id
    role: Mapped[str]             # "owner" | "teacher" | "student"
```

**Access Rules:**
1. **Admins** -> can view all courses regardless of membership
2. **Users with a `CourseMembership`** -> can view the linked course (any role)
3. **Students matched via `TeamMember`** -> can view the course their team belongs to

### Managing Teachers (Admin Only)

1. Navigate to **Dashboard -> Courses** (admin menu)
2. Click **Edit** on any course
3. Enter GitLab usernames, comma-separated
4. Click **Save Changes**

**API Endpoint:**
```
POST /dashboard/admin/courses/{course_id}/teachers
Form Data: teachers=user1,user2,user3
```

### SQL Examples

```sql
-- Assign a teacher to a course via course_memberships
INSERT INTO course_memberships (user_id, course_id, role)
SELECT u.id, c.id, 'teacher'
FROM users u, courses c
WHERE u.username = 'teacher1' AND c.code = 'DEVOPS-2026'
ON CONFLICT (user_id, course_id) DO UPDATE SET role = 'teacher';

-- Remove a teacher from a course
DELETE FROM course_memberships
WHERE user_id = (SELECT id FROM users WHERE username = 'teacher1')
  AND course_id = (SELECT id FROM courses WHERE code = 'DEVOPS-2026');

-- Check current teacher assignments for a course
SELECT u.username, cm.role, cm.created_at
FROM course_memberships cm
JOIN users u ON u.id = cm.user_id
JOIN courses c ON c.id = cm.course_id
WHERE c.code = 'DEVOPS-2026' AND cm.role IN ('teacher', 'owner')
ORDER BY cm.created_at;
```

## Student Privacy

Students are automatically matched to teams via their GitLab username:

1. When a student logs in via GitLab OAuth, their `gitlab_username` is stored in the session
2. The system checks if this username exists in any `team_members` -> `students` relationship
3. Only teams containing the student are visible

### Matching Logic

```python
# Student can view team if:
TeamMember.team_id == team.id AND
Student.gitlab_username IN (session.gitlab_username, session.user)
```

## Endpoint Access Matrix

| Endpoint | Admin | Teacher | Student |
|----------|-------|---------|---------|
| `GET /dashboard/` | ✓ (all courses) | ✓ (assigned courses) | ✓ (enrolled courses) |
| `GET /courses/{id}` | ✓ | ✓ (if assigned) | ✓ (if enrolled) |
| `GET /teams/{id}` | ✓ | ✓ (if course assigned) | ✓ (if member) |
| `GET /students/{id}/team/{id}` | ✓ | ✓ (if course assigned) | ✓ (if in same team) |
| `GET /courses/{id}/settings` | ✓ | ✓ (if assigned) | ✗ |
| `POST /courses/{id}/settings` | ✓ | ✓ (if assigned) | ✗ |
| `GET /admin/users` | ✓ | ✗ | ✗ |
| `GET /admin/courses` | ✓ | ✗ | ✗ |
| `POST /admin/courses/{id}/teachers` | ✓ | ✗ | ✗ |

## Implementation Details

### Access Check Functions

```python
# Dashboard: check course access (src/app/api/dashboard/_access.py)
async def _can_view_course(course, session_data, db) -> bool:
    role = session_data.get("role", "student")
    
    if role == "admin":
        return True
    
    # Check CourseMembership (owner/teacher/student)
    mem_role = await _membership_role(db, course.id, session_data)
    if mem_role is not None:
        return True
    
    # Fallback: check TeamMember -> Student matching
    return await _is_student_in_course(course.id, username, db)

# Resolve CourseMembership role for current user
async def _membership_role(db, course_id, session_data):
    user_row = await db.execute(
        select(User.id).where(User.username == session_data["user"])
    )
    user_id = user_row.scalar_one_or_none()
    if not user_id:
        return None
    result = await db.execute(
        select(CourseMembership.role).where(
            CourseMembership.user_id == user_id,
            CourseMembership.course_id == course_id,
        )
    )
    return result.scalar_one_or_none()

# API: check course staff access (src/app/security/course_roles.py)
async def is_course_staff(db, course, user, min_role="teacher") -> bool:
    if user.role == "admin":
        return True
    actual = await get_course_role(db, user.id, course.id)
    return actual is not None and role_gte(actual, min_role)
```

### Session Data

After OAuth login, the session contains:
```python
{
    "user": "gitlab_username",
    "gitlab_username": "gitlab_username",  # For matching
    "role": "admin" | "teacher" | "student",
    "user_id": "uuid",
    "email": "user@example.com"
}
```

## Support System Access Control

The support ticket system uses a combination of token-based anonymous access and role-based staff access:

### Access Matrix

| Action | Anonymous | Student | Teacher | Admin |
|--------|-----------|---------|---------|-------|
| Submit ticket via token link | Yes | Yes | Yes | Yes |
| View own submission (by token) | Yes | Yes | Yes | Yes |
| Browse ticket list | No | No | Yes (course staff) | Yes |
| View ticket detail | No | No | Yes (course staff) | Yes |
| Add comment to ticket | No | No | Yes (course staff) | Yes |
| Update ticket status/priority | No | No | Yes (course staff) | Yes |
| Delete ticket | No | No | Yes (course staff) | Yes |
| Manage forms (CRUD) | No | No | Yes (course staff) | Yes |
| Create/delete links | No | No | Yes (course staff) | Yes |
| SSE ticket stream | No | No | Yes (course staff) | Yes |

### Implementation Details

- **Anonymous submission**: Uses token-based authentication (`feedback_links.token`). No session required.
- **Dashboard pages**: `/dashboard/support/tickets`, `/dashboard/support/ticket/{id}` require `TeacherAuth` (teacher or admin role).
- **API endpoints**: All management endpoints in `support.py` and `compliance_history.py` use `get_current_teacher` dependency + `is_course_staff()` per-course validation.
- **SSE streaming**: `/api/v1/sse/support/tickets/{id}/stream` requires `ApiTeacherAuth` + course staff validation via `is_course_staff()`.
- **Email notifications**: Sent only to course staff (CourseMembership with teacher/owner role).

## Configuration

### Environment Variables

```bash
# Enable RBAC (required for access control)
FEATURE_RBAC=true

# GitLab OAuth (required for role determination)
GITLAB_OAUTH_ENABLED=true
GITLAB_OAUTH_CLIENT_ID=your_client_id
GITLAB_OAUTH_CLIENT_SECRET=your_secret

# Role determination
GITLAB_ADMIN_USERNAMES=["admin1", "admin2"]
GITLAB_TEACHER_USERNAMES=["teacher1", "teacher2"]
GITLAB_TEACHER_GROUP_IDS=[123, 456]
GITLAB_TEACHER_GROUP_PATHS=["tuke/teachers"]
```

### Role Precedence

When a user logs in via GitLab OAuth:

1. Check if username in `GITLAB_ADMIN_USERNAMES` -> **admin**
2. Check if username in `GITLAB_TEACHER_USERNAMES` -> **teacher**
3. Check if member of any `GITLAB_TEACHER_GROUP_*` -> **teacher**
4. Otherwise -> **student**

## Database Schema

### course_memberships table
```sql
CREATE TABLE course_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL DEFAULT 'student',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, course_id)
);
CREATE INDEX idx_course_memberships_user_id ON course_memberships(user_id);
CREATE INDEX idx_course_memberships_course_id ON course_memberships(course_id);
```

### Migration
```python
# alembic/versions/015_course_memberships.py
def upgrade():
    op.create_table('course_memberships',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('course_id', sa.Uuid(), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='student'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'course_id', name='uq_course_membership'),
    )
```

## Troubleshooting

### Teacher Can't See Course
1. Check `course_memberships` for the teacher:
   ```sql
   SELECT cm.role, c.code, c.name
   FROM course_memberships cm
   JOIN courses c ON c.id = cm.course_id
   JOIN users u ON u.id = cm.user_id
   WHERE u.username = 'teacher_username';
   ```
2. If no row exists, add a membership:
   ```sql
   INSERT INTO course_memberships (user_id, course_id, role)
   SELECT u.id, c.id, 'teacher'
   FROM users u, courses c
   WHERE u.username = 'teacher_username' AND c.id = 'course-uuid';
   ```

### Student Can't See Team
1. Verify student is in `team_members`:
   ```sql
   SELECT * FROM team_members tm
   JOIN students s ON tm.student_id = s.id
   WHERE s.gitlab_username = 'username';
   ```
2. Verify the GitLab username matches exactly

### Session Not Showing Correct Role
1. Log out and log back in via GitLab OAuth
2. Check `GITLAB_*_USERNAMES` and group settings
3. Verify username spelling (case-sensitive)

## Audit Logging

All access control decisions are logged:

```python
logger.info("course_access_denied", 
    user=username, 
    course_id=course_id, 
    role=role)

logger.info("course_teachers_updated",
    course_id=course_id,
    teachers=teachers,
    admin_user=admin)
```

View logs with:
```bash
docker compose logs api | grep "access\|teacher"
```
