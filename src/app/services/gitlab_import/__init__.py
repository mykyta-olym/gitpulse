"""Importing a course from GitLab: the group tree, its members and projects.

`service` is the operation (`import_gitlab_group_to_course`); `persistence`,
`email_enrichment`, `normalize` and `helpers` are its parts - the way GitLab
keeps `services/<domain>/` together. The classifiers the routes and workers
reuse are exported here.
"""

from app.services.gitlab_import.helpers import (
    extract_group_path_from_input,
    is_bot_user,
    match_team_group_path,
    select_team_group_records,
)
from app.services.gitlab_import.service import (
    GitLabGroupImportParams,
    GitLabGroupImportResult,
    import_gitlab_group_to_course,
)

__all__ = [
    "GitLabGroupImportParams",
    "GitLabGroupImportResult",
    "extract_group_path_from_input",
    "import_gitlab_group_to_course",
    "is_bot_user",
    "match_team_group_path",
    "select_team_group_records",
]
