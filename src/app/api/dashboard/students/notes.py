"""Discussion rendering for the student page: one note as the template sees
it, notes grouped into threads, and the MR event a system note describes."""

import uuid
from datetime import UTC, datetime
from typing import Any

from app.api.dashboard.students.diffs import _dom_id


def _note_view(
    note: Any,
    student_map: dict[uuid.UUID, Any],
    username_map: dict[str, str],
    teacher_ids: set[uuid.UUID],
    teacher_gitlab_ids: set[int],
    page_student_id: uuid.UUID,
    avatar_by_gid: dict[int, str] | None = None,
    avatar_by_uname: dict[str, str] | None = None,
    profile_by_sid: dict[uuid.UUID, str] | None = None,
) -> dict[str, Any]:
    """Resolve a single note into a render-ready view (author name + role flags).

    Used to build GitLab-style discussion threads. Resolution order for the
    author label mirrors the rest of the page: linked Student -> @username
    (mapped to full name when known) -> GitLab numeric id -> Unknown.
    """
    author = student_map.get(note.author_id) if note.author_id else None
    if author:
        display = author.full_name or f"@{author.gitlab_username}"
    elif note.author_username:
        display = username_map.get(note.author_username.lower()) or f"@{note.author_username}"
    elif note.author_gitlab_id:
        display = f"GitLab#{note.author_gitlab_id}"
    else:
        display = "Unknown"
    is_page = note.author_id is not None and note.author_id == page_student_id
    is_teacher = bool(
        (note.author_id and note.author_id in teacher_ids)
        or (note.author_gitlab_id and note.author_gitlab_id in teacher_gitlab_ids)
    )
    avatar_url = None
    if avatar_by_gid is not None and avatar_by_uname is not None:
        avatar_url = _resolve_avatar(
            author.gitlab_user_id if author else note.author_gitlab_id,
            author.gitlab_username if author else note.author_username,
            avatar_by_gid,
            avatar_by_uname,
        )
        if not avatar_url and note.author_gitlab_id:
            avatar_url = avatar_by_gid.get(int(note.author_gitlab_id))
        if not avatar_url and note.author_username:
            avatar_url = avatar_by_uname.get(note.author_username.lower())
    profile_url = None
    if profile_by_sid is not None and author is not None:
        profile_url = profile_by_sid.get(author.id)
    return {
        "note": note,
        "author_display": display,
        "is_page_student": is_page,
        "is_teacher": is_teacher,
        "avatar_url": avatar_url,
        "profile_url": profile_url,
    }


def _build_threads(note_views: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group ordered note views into GitLab-style discussion threads.

    Notes that share a ``discussion_id`` form one thread (first = root, rest =
    replies). Notes with no ``discussion_id`` each become a standalone thread.
    A thread is "resolved" only when it is resolvable and every resolvable note
    in it is resolved. Threads are returned ordered by their root's timestamp.
    """
    by_discussion: dict[str, list[dict[str, Any]]] = {}
    order: list[str] = []
    standalone: list[list[dict[str, Any]]] = []
    for nv in note_views:
        did = nv["note"].discussion_id
        if did:
            if did not in by_discussion:
                by_discussion[did] = []
                order.append(did)
            by_discussion[did].append(nv)
        else:
            standalone.append([nv])

    grouped = [by_discussion[d] for d in order] + standalone
    threads: list[dict[str, Any]] = []
    for notes in grouped:
        root = notes[0]
        root_note = root["note"]
        thread_key = root_note.discussion_id or root_note.gitlab_note_id or root_note.id
        thread_anchor = f"thread-{_dom_id(thread_key)}"
        for idx, nv in enumerate(notes):
            note = nv["note"]
            note_key = note.gitlab_note_id or note.id
            nv["anchor"] = f"note-{_dom_id(note_key)}"
            nv["thread_anchor"] = thread_anchor
            if idx > 0:
                nv["reply_to_anchor"] = root.get("anchor")
                nv["reply_to_author"] = root["author_display"]
            else:
                nv["reply_to_anchor"] = None
                nv["reply_to_author"] = None
        resolvable = any(n["note"].is_resolvable for n in notes)
        resolved = resolvable and all(
            n["note"].is_resolved or not n["note"].is_resolvable for n in notes
        )
        code_context = root.get("code_context")
        threads.append(
            {
                "anchor": thread_anchor,
                "root": root,
                "replies": notes[1:],
                "count": len(notes),
                "is_resolvable": resolvable,
                "is_resolved": bool(resolved),
                "code_context": code_context,
                "diff_anchor": code_context.get("diff_anchor") if code_context else None,
                "participants": sorted({n["author_display"] for n in notes}),
            }
        )

    _epoch = datetime.min.replace(tzinfo=UTC)
    threads.sort(key=lambda th: th["root"]["note"].created_at or _epoch)
    return threads


def _classify_mr_event(body: str | None) -> tuple[str, str] | None:
    """Map a GitLab system-note body to a (kind, icon) for the activity feed.

    Only a curated allowlist of workflow events is surfaced (request review,
    approve, assign, merge, ready/draft, resolve, commits, close/reopen);
    label / milestone / mention / description-change noise is dropped so the
    timeline mirrors the Issue -> Branch -> MR -> Review -> Approve -> Merge ->
    Close workflow the course grades.
    """
    if not body:
        return None
    low = body.lower()
    if "requested review from" in low:
        return ("review_request", "eye")
    if "approved this merge request" in low:
        return ("approved", "check-circle")
    if "unapproved this merge request" in low:
        return ("unapproved", "x-circle")
    if "marked this merge request as ready" in low:
        return ("ready", "check-circle")
    if "marked this merge request as draft" in low:
        return ("draft", "edit-3")
    if "resolved all threads" in low:
        return ("resolved", "check-circle")
    if low.startswith("merged") or "merged this merge request" in low:
        return ("merged", "git-merge")
    if "assigned to" in low or "unassigned" in low:
        return ("assigned", "user-check")
    if "added" in low and "commit" in low:
        return ("commits", "git-commit")
    if low.startswith("closed"):
        return ("closed", "x-circle")
    if low.startswith("reopened"):
        return ("reopened", "refresh-cw")
    return None


def _resolve_avatar(
    gitlab_user_id: int | None,
    gitlab_username: str | None,
    avatar_by_gid: dict[int, str],
    avatar_by_uname: dict[str, str],
) -> str | None:
    """Look up a GitLab avatar URL by numeric id first, then by username."""
    if gitlab_user_id is not None:
        url = avatar_by_gid.get(int(gitlab_user_id))
        if url:
            return url
    if gitlab_username:
        return avatar_by_uname.get(gitlab_username.lower())
    return None
