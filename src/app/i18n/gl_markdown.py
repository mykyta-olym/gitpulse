"""GitLab text as safe HTML: reference links and the Markdown subset descriptions use.

Not a full Markdown parser - just enough that MR / issue descriptions and note
bodies like ``_`Closes #3`_`` render as italic linked code instead of raw
punctuation.
"""

import re

from markupsafe import Markup
from markupsafe import escape as _esc

GL_REF_RE = re.compile(
    r"(?<![&\w])"  # not preceded by & (HTML entity) or word char
    r"(?:"
    r"(?P<mr>!(?P<mr_iid>\d{1,6}))"  # !45
    r"|(?P<issue>#(?P<issue_iid>\d{1,6}))"  # #123
    r"|(?P<user>@(?P<username>[a-zA-Z0-9_.\-]{1,80}))"  # @username
    r")"
    r"(?!\w)"  # not followed by word char
)

_MD_CODE_RE = re.compile(r"`([^`\n]+)`")
_MD_BOLD_RE = re.compile(r"\*\*(\S(?:.*?\S)?)\*\*", re.DOTALL)
_MD_ITALIC_UNDER_RE = re.compile(r"(?<![\w_])_([^\s_](?:[^_\n]*[^\s_])?)_(?![\w_])")
_MD_ITALIC_STAR_RE = re.compile(r"(?<![\w*])\*([^\s*](?:[^*\n]*[^\s*])?)\*(?![\w*])")
# Tolerate trailing spaces after the language hint and CRLF line endings -
# GitLab note bodies frequently arrive as ``` ```c\r\n...``` ``` and a bare
# ``\n`` requirement left the fence unmatched, so review comments rendered
# their backticks literally.
_MD_FENCE_RE = re.compile(r"```([a-zA-Z0-9_+\-]*)[ \t]*\r?\n([\s\S]*?)```")
_MD_ESCAPE_CHARS = "\\`*_{}[]()#+-.!|<>~\"'"
_MD_ESCAPE_RE = re.compile(r"\\([" + re.escape(_MD_ESCAPE_CHARS) + r"])")
_H_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_UL_RE = re.compile(r"^[\*\-\+]\s+(.+)$")
_OL_RE = re.compile(r"^\d+\.\s+(.+)$")


def _lower_keys(mapping: dict[str, str] | None) -> dict[str, str]:
    return {k.lower(): v for k, v in (mapping or {}).items() if k and v}


def _ref_html(
    m: re.Match[str],
    project_path: str,
    gl_base: str,
    names: dict[str, str],
    student_urls: dict[str, str],
) -> str:
    """One ``!45`` / ``#123`` / ``@user`` reference as a link, or as it was.

    A teammate (in ``student_urls``) links to their GitPulse profile, keeping
    the page connected, whatever the GitLab config; everyone else links out to
    GitLab when its base URL is configured. A user in ``names`` reads as their
    full name, with the handle as the title.
    """
    if m.group("mr") and project_path and gl_base:
        iid = m.group("mr_iid")
        url = f"{gl_base}/{project_path}/-/merge_requests/{iid}"
        return (
            f'<a href="{url}" target="_blank" rel="noopener" class="gl-ref gl-ref--mr">!{iid}</a>'
        )
    if m.group("issue") and project_path and gl_base:
        iid = m.group("issue_iid")
        url = f"{gl_base}/{project_path}/-/issues/{iid}"
        return (
            f'<a href="{url}" target="_blank" rel="noopener"'
            f' class="gl-ref gl-ref--issue">#{iid}</a>'
        )
    if m.group("user"):
        uname = m.group("username")
        full = names.get(uname.lower())
        label = str(_esc(full)) if full else f"@{uname}"
        inapp = student_urls.get(uname.lower())
        if inapp:
            return (
                f'<a href="{inapp}" class="gl-ref gl-ref--user gl-ref--student"'
                f' title="@{uname}">{label}</a>'
            )
        if gl_base:
            url = f"{gl_base}/{uname}"
            title = f' title="@{uname}"' if full else ""
            return (
                f'<a href="{url}" target="_blank" rel="noopener"'
                f' class="gl-ref gl-ref--user"{title}>{label}</a>'
            )
    return m.group(0)


def linkify_gl_refs(
    text: str | None,
    project_path: str = "",
    username_map: dict[str, str] | None = None,
    *,
    gl_base: str,
) -> Markup:
    """Convert GitLab references in *text* to clickable links.

    Handles ``#123`` (issues), ``!45`` (MRs), and ``@username`` (users). The
    *project_path* is needed for issue/MR URLs - when empty, only ``@username``
    links are generated. When *username_map* is provided, each ``@username``
    whose lowercased key is present is rendered as the resolved full name
    (still linking to the GitLab profile), so description snippets like
    ``Reviewers: @sm361rw @sj795vu`` become readable names.

    The input is HTML-escaped first, then safe ``<a>`` tags are inserted.
    """
    if not text:
        return Markup("")
    names = _lower_keys(username_map)
    return Markup(
        GL_REF_RE.sub(lambda m: _ref_html(m, project_path, gl_base, names, {}), str(_esc(text)))
    )


def render_gl_description(
    text: str | None,
    project_path: str = "",
    username_map: dict[str, str] | None = None,
    student_url_map: dict[str, str] | None = None,
    *,
    gl_base: str,
) -> Markup:
    """Render a GitLab MR/issue description as safe HTML.

    Escapes the input, handles a small Markdown subset (fenced and inline code,
    ``**bold**``, ``_italic_`` / ``*italic*``, headings, lists), converts
    newlines to ``<br>``, and linkifies ``#123`` / ``!45`` / ``@username``
    references. Returns ``Markup`` so Jinja2 won't double-escape.
    """
    if not text:
        return Markup("")
    # Normalise line endings up front so every rule below (fences, inline
    # code, lists, the \n -> <br> pass) behaves the same for LF and CRLF.
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Fenced code blocks come out FIRST, so their content is not read as
    # bold, italic, headings, list bullets or references (review comments
    # often carry ```c ...```).
    fenced: list[tuple[str, str]] = []

    def _stash_fenced(m: re.Match[str]) -> str:
        # A single leading/trailing newline inside the fence would leave the
        # <pre> with a blank top/bottom line.
        fenced.append(
            ((m.group(1) or "").strip(), (m.group(2) or "").removeprefix("\n").removesuffix("\n"))
        )
        return f"\x00FENCE{len(fenced) - 1}\x00"

    staged = _MD_FENCE_RE.sub(_stash_fenced, text)
    # GitLab/GFM hard line break: a backslash at the end of a line forces a
    # <br>. Drop it, or it renders literally once newlines become <br>.
    staged = re.sub(r"\\(\r?\n)", r"\1", staged)

    # CommonMark backslash escapes: ``\`code\``` is literal backticks, ``\*``
    # a literal asterisk. Stashed so no later pass mistakes them for markup;
    # restored, escaped, at the very end.
    escapes: list[str] = []

    def _stash_escape(m: re.Match[str]) -> str:
        escapes.append(m.group(1))
        return f"\x00BS{len(escapes) - 1}\x00"

    staged = _MD_ESCAPE_RE.sub(_stash_escape, staged)

    # Inline code spans out before escaping, so their content is not read as
    # bold/italic/refs.
    code_spans: list[str] = []

    def _stash_code(m: re.Match[str]) -> str:
        code_spans.append(m.group(1))
        return f"\x00CODE{len(code_spans) - 1}\x00"

    staged = _MD_CODE_RE.sub(_stash_code, staged)

    safe = str(_esc(staged))
    safe = _MD_BOLD_RE.sub(r"<strong>\1</strong>", safe)
    safe = _MD_ITALIC_UNDER_RE.sub(r"<em>\1</em>", safe)
    safe = _MD_ITALIC_STAR_RE.sub(r"<em>\1</em>", safe)
    names, student_urls = _lower_keys(username_map), _lower_keys(student_url_map)
    safe = GL_REF_RE.sub(lambda m: _ref_html(m, project_path, gl_base, names, student_urls), safe)
    safe = re.sub(
        r"\x00CODE(\d+)\x00", lambda m: f"<code>{_esc(code_spans[int(m.group(1))])}</code>", safe
    )
    safe = _line_breaks(_blocks(safe))
    # Fenced blocks go back LAST, so the newline pass never breaks their
    # <pre>; a placeholder that sat on its own line lost its <br>s with it.
    safe = re.sub(
        r"(?:<br>)?\x00FENCE(\d+)\x00(?:<br>)?",
        lambda m: _fenced_html(*fenced[int(m.group(1))]),
        safe,
    )
    # The escaped punctuation comes back as literal, HTML-escaped characters.
    safe = re.sub(r"\x00BS(\d+)\x00", lambda m: str(_esc(escapes[int(m.group(1))])), safe)
    return Markup(safe)


def _blocks(safe: str) -> str:
    """Headings (## / ###) and bulleted / numbered lists.

    Before the newline pass, so consecutive bullets group into one <ul>
    instead of individually broken lines.
    """
    out: list[str] = []
    list_kind: str | None = None  # 'ul' | 'ol' | None

    def _close_list() -> None:
        nonlocal list_kind
        if list_kind:
            out.append(f"</{list_kind}>")
            list_kind = None

    def _open_list(kind: str) -> None:
        nonlocal list_kind
        if list_kind != kind:
            _close_list()
            out.append(f'<{kind} class="gl-desc-list">')
            list_kind = kind

    for raw in safe.replace("\r\n", "\n").split("\n"):
        line = raw.rstrip()
        stripped = line.lstrip()
        h = _H_RE.match(stripped) if stripped else None
        ul = _UL_RE.match(stripped) if stripped and not h else None
        ol = _OL_RE.match(stripped) if stripped and not h and not ul else None
        if h:
            _close_list()
            level = min(len(h.group(1)) + 2, 6)  # ## -> h4, ### -> h5 visually
            out.append(f'<h{level} class="gl-desc-h">{h.group(2)}</h{level}>')
        elif ul:
            _open_list("ul")
            out.append(f"<li>{ul.group(1)}</li>")
        elif ol:
            _open_list("ol")
            out.append(f"<li>{ol.group(1)}</li>")
        else:
            _close_list()
            out.append(line)
    _close_list()
    return "\n".join(out)


def _line_breaks(safe: str) -> str:
    """Newlines as <br>, but not around the block tags, at most two in a row.

    Newlines are stripped around both the opening and the closing tag of
    every block element: a closing </h6> followed by a blank line produced a
    visible double-<br> gap above the next paragraph.
    """
    safe = re.sub(r"(?:\n){3,}", "\n\n", safe)
    safe = re.sub(r"\n*(</?(?:h[1-6]|ul|ol|li|pre)[^>]*>)\n*", r"\1", safe)
    safe = safe.replace("\n", "<br>")
    return re.sub(r"(?:<br>\s*){3,}", "<br><br>", safe)


def _fenced_html(lang: str, body: str) -> str:
    """A fenced code block, highlighted by Pygments when it knows the language.

    Any Pygments failure (unknown lexer, import error) falls back to plain
    escaped code, so a malformed fence never blanks out the description.
    """
    if lang:
        highlighted = _highlight(lang, body)
        if highlighted is not None:
            return (
                f'<pre class="gl-desc-pre highlight"><code class="language-{_esc(lang)}">'
                f"{highlighted}</code></pre>"
            )
    cls = f' class="language-{_esc(lang)}"' if lang else ""
    return f'<pre class="gl-desc-pre"><code{cls}>{_esc(body)}</code></pre>'


def _highlight(lang: str, body: str) -> str | None:
    try:
        from pygments import highlight  # type: ignore[import-untyped]
        from pygments.formatters import HtmlFormatter  # type: ignore[import-untyped]
        from pygments.lexers import get_lexer_by_name  # type: ignore[import-untyped]
        from pygments.util import ClassNotFound  # type: ignore[import-untyped]

        try:
            lexer = get_lexer_by_name(lang, stripnl=False)
        except ClassNotFound:
            return None
        # nowrap: we provide our own <pre><code>. Pygments' trailing newline
        # would keep the closing </code> off the last line.
        return str(highlight(body, lexer, HtmlFormatter(nowrap=True, classprefix=""))).rstrip("\n")
    except Exception:
        return None
