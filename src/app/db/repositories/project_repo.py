"""Repository for GitLab projects."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import GitLabProject


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_gitlab_id(self, gitlab_project_id: int) -> GitLabProject | None:
        stmt = select(GitLabProject).where(GitLabProject.gitlab_project_id == gitlab_project_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, project: GitLabProject) -> GitLabProject:
        self.session.add(project)
        await self.session.flush()
        return project
