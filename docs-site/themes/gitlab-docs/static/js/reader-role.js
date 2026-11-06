/**
 * Tell the reader which documentation their account opens.
 *
 * The site is static HTML, so it cannot see the role Caddy passes to the docs
 * container. It asks the application instead, once per page, and fills a note
 * that is already in the markup - so a reader learns what they may open rather
 * than finding out by being refused.
 *
 * The note is written into the theme's own `alert` markup, so it looks like
 * every other notice on the page rather than a second style.
 *
 * Fails silently. This is an enhancement: if the endpoint is unreachable the
 * page must read exactly as it did before.
 */
(() => {
  /* The whole sentence per role, not a noun slotted into one template: an
     anonymous reader is not "signed in as" anything, and the template produced
     "Ste prihlásený ako neprihlásený čitateľ".

     Per language, because the note said the same Slovak sentence on an English
     page - this file could not reach the site's translations, being a static
     script rather than part of the Vue bundle, so it carried one language. */
  const LABELS = {
    sk: {
      admin:
        "<strong>Ste prihlásený ako administrátor.</strong> Máte prístup k celej dokumentácii vrátane prevádzky a bezpečnosti.",
      teacher:
        "<strong>Ste prihlásený ako učiteľ.</strong> Máte prístup k príručke pre učiteľov a k integrácii s GitLabom. Prevádzka a bezpečnosť sú vyhradené administrátorom.",
      student:
        "<strong>Ste prihlásený ako študent.</strong> Máte prístup k verejným častiam: úvod, príručka pre študentov, API, vývoj, diplomová práca a právne informácie.",
      anonymous:
        "<strong>Nie ste prihlásený.</strong> Vidíte verejné časti dokumentácie. Príručka pre učiteľov a prevádzková dokumentácia vyžadujú prihlásenie.",
    },
    en: {
      admin:
        "<strong>You are signed in as an administrator.</strong> You can open the whole documentation, including operations and security.",
      teacher:
        "<strong>You are signed in as a teacher.</strong> You can open the teacher's handbook and the GitLab integration. Operations and security are reserved for administrators.",
      student:
        "<strong>You are signed in as a student.</strong> You can open the public sections: introduction, the student guide, API, development, the thesis and legal information.",
      anonymous:
        "<strong>You are not signed in.</strong> You are seeing the public sections. The teacher's handbook and the operations documentation require signing in.",
    },
  };

  const slot = document.querySelector("[data-reader-role]");
  if (!slot) return;

  const lang = (document.documentElement.lang || "").toLowerCase().split("-")[0];
  const labels = LABELS[lang] || LABELS.sk;

  fetch("/internal/docs-role", { credentials: "same-origin", cache: "no-store" })
    .then((r) => (r.ok ? r.json() : null))
    .then((data) => {
      if (!data) return;
      const text = labels[data.role] || labels.anonymous;
      slot.innerHTML =
        '<div class="alert alert-type-note gl-rounded-lg">' +
        '<div class="alert-icon"></div>' +
        '<div class="gl-min-w-0"><p>' + text + "</p></div></div>";
      slot.hidden = false;
    })
    .catch(() => {
      /* enhancement only - leave the page as it was */
    });
})();
