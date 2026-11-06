/* ------------------------------------------------------------------
 *  40-support.js - Support tours
 *
 *  Split from the monolithic tour content registry (SRP).
 *  that re-grabs GP.tour.register; the engine (00-engine.js, 10-render.js)
 *  comes earlier in
 *  the bundle.
 * ------------------------------------------------------------------ */
(() => {
  'use strict';

  if (!window.GP?.tour) {
    console.warn('[tours/40-support.js] tour engine not loaded - content not registered');
    return;
  }
  const reg = window.GP.tour.register;

  // -- 13. SUPPORT (course picker -> category picker -> form) ---------
  // The /dashboard/support page has THREE rendering stages depending on
  // query string: stage 1 has only a course picker, stage 2 has the
  // category grid, stage 3 has the actual ticket form. compileSteps
  // drops any step whose element is missing, so a single tour with
  // steps for all three stages naturally degrades per-stage.
  reg({
    slug: 'support_form',
    title_en: 'Support',
    title_sk: 'Podpora',
    pages: ['support_form'],
    roles: ['student', 'teacher', 'admin'],
    autoPrompt: true,
    multiStage: true,
    steps: [
      {
        title_en: 'GitPulse Support',
        title_sk: 'GitPulse podpora',
        body_en: 'Submit a ticket to the team. Tickets are private (only you, the assigned admin and the support inbox see them) and have an SLA of one working day for a first response &mdash; admins reply by email and via the in-app inbox.',
        body_sk: 'Pošlite tiket podpornému tímu. Tikety sú privátne (vidíte ich iba vy, pridelený admin a support inbox) a majú SLA jeden pracovný deň na prvú odpoveď &mdash; admini odpovedia e-mailom aj v in-app inboxe.',
      },
      // -- Stage 1: course picker (no ?course_id=) --
      {
        element: '[data-tour~="support-course-picker"]',
        side: 'top',
        title_en: 'Pick the course',
        title_sk: 'Vyberte predmet',
        body_en: 'Tickets are scoped to a course so the right teacher / admin can see them. Pick the course your question is about &mdash; if the issue is platform-wide pick any course you are enrolled in.',
        body_sk: 'Tikety sú viazané na predmet, aby ich videl správny učiteľ / admin. Vyberte predmet, ktorého sa otázka týka &mdash; ak ide o platformovú vec, vyberte hocijaký predmet, na ktorom ste zapísaní.',
      },
      // -- Stage 2: category picker (?course_id=..., no &category=) --
      {
        element: '[data-tour~="support-platform-features"], .gh-products-grid',
        side: 'bottom',
        title_en: 'Platform features',
        title_sk: 'Funkcie platformy',
        body_en: 'Pick the area your question is about: <em>Dashboard</em>, <em>CI/CD</em>, <em>Code reviews</em>, <em>Evaluations</em>, <em>Reports</em> or <em>Repositories</em>. The category routes the ticket to the right specialist and pre-fills useful fields on the form.',
        body_sk: 'Vyberte oblasť, ktorej sa otázka týka: <em>Dashboard</em>, <em>CI/CD</em>, <em>Code review</em>, <em>Hodnotenie</em>, <em>Reporty</em> alebo <em>Repozitáre</em>. Kategória nasmeruje tiket správnemu špecialistovi a predvyplní užitočné polia formulára.',
      },
      {
        element: '[data-tour~="support-situations"], .gh-situations-list',
        side: 'top',
        title_en: 'Situations',
        title_sk: 'Situácie',
        body_en: 'If your problem fits one of these everyday situations &mdash; <em>Bug</em>, <em>Feature request</em>, <em>Account problem</em>, <em>Grade inquiry</em> &mdash; pick the situation card instead. Each situation triggers its own custom form with the right follow-up questions.',
        body_sk: 'Ak váš problém zapadá do jednej z týchto bežných situácií &mdash; <em>Bug</em>, <em>Návrh funkcie</em>, <em>Problém s účtom</em>, <em>Otázka o hodnotení</em> &mdash; kliknite na situačnú kartu. Každá situácia má vlastný formulár s relevantnými doplňujúcimi otázkami.',
      },
      {
        element: '[data-tour~="support-something-else"], .gh-something-else',
        side: 'top',
        title_en: 'Something else?',
        title_sk: 'Niečo iné?',
        body_en: 'If nothing fits, pick this &mdash; you get a generic ticket form. The team will route the ticket internally based on the description.',
        body_sk: 'Ak vám nič nesedí, kliknite sem &mdash; dostanete všeobecný formulár. Tím tiket interne nasmeruje podľa popisu.',
      },
      // -- Stage 3: form (?course_id=...&category=...) --
      {
        element: '[data-tour~="support-subject"], #title',
        side: 'bottom',
        title_en: 'Subject',
        title_sk: 'Predmet',
        body_en: 'A short, scannable headline (max 80 chars). Tip: start with the broken thing and the action that triggered it &mdash; e.g. <em>"CI pipeline fails on lint stage after dependency update"</em> &mdash; not <em>"help"</em>. Good subjects get answered first.',
        body_sk: 'Krátky, čitateľný titulok (max 80 znakov). Tip: začnite tým, čo nefunguje a akciou, ktorá to spustila &mdash; napr. <em>"CI pipeline padá na lint kroku po update závislostí"</em> &mdash; nie <em>"pomoc"</em>. Dobré subjekty dostávajú odpoveď ako prvé.',
      },
      {
        element: '[data-tour~="support-description"], #description',
        side: 'top',
        title_en: 'Description (Markdown)',
        title_sk: 'Popis (Markdown)',
        body_en: 'Full details. The editor supports <strong>Markdown</strong> (use the toolbar for bold / lists / links / code blocks) and <strong>Write / Preview</strong> tabs. You can paste screenshots directly &mdash; they upload as attachments. Code blocks (<code>```</code>) preserve formatting for logs and stack traces.',
        body_sk: 'Detaily. Editor podporuje <strong>Markdown</strong> (použite toolbar na bold / zoznamy / linky / bloky kódu) a záložky <strong>Write / Preview</strong>. Screenshoty môžete vložiť priamo (Ctrl+V) &mdash; nahrajú sa ako prílohy. Bloky kódu (<code>```</code>) zachovajú formátovanie logov a stack traceov.',
      },
      {
        element: '.gh-category-fields',
        side: 'top',
        title_en: 'Category-specific fields',
        title_sk: 'Polia podľa kategórie',
        body_en: 'These follow-up questions depend on the category you picked &mdash; CI repository URL, browser & OS, expected vs actual grade, etc. They are optional but a complete form usually shaves a day off the back-and-forth.',
        body_sk: 'Tieto doplňujúce otázky závisia od vybranej kategórie &mdash; URL repozitára pre CI, prehliadač a OS, očakávaný vs skutočný výsledok hodnotenia, atď. Sú voliteľné, ale úplne vyplnený formulár zvyčajne ušetrí deň komunikácie.',
      },
      {
        element: '[data-tour~="support-priority"], [name="priority"]',
        side: 'top',
        title_en: 'Priority',
        title_sk: 'Priorita',
        body_en: '<em>Low</em> &mdash; nice-to-have. <em>Medium</em> &mdash; default for most issues. <em>High</em> &mdash; affects your daily workflow. <em>Critical</em> &mdash; you cannot proceed at all (deadline at risk). Honest priority earns trust; everything-is-critical earns the opposite.',
        body_sk: '<em>Nízka</em> &mdash; nice-to-have. <em>Stredná</em> &mdash; default. <em>Vysoká</em> &mdash; ovplyvňuje denný workflow. <em>Kritická</em> &mdash; vôbec nemôžete pokračovať (deadline ohrozený). Čestná priorita budí dôveru; všetko-je-kritické naopak.',
      },
      {
        element: '[data-tour~="support-submit"], .gh-submit-btn',
        side: 'top',
        title_en: 'Submit',
        title_sk: 'Odoslať',
        body_en: 'After submit you are redirected to the ticket inbox where you can track status, reply and add attachments. You also get an email confirmation with a direct link.',
        body_sk: 'Po odoslaní budete presmerovaný do inboxu tiketov, kde môžete sledovať stav, odpovedať a pridávať prílohy. Tiež dostanete e-mailové potvrdenie s priamym linkom.',
      },
    ],
  });

  // -- 14. SUPPORT TICKETS LIST --------------------------------------
  // Two stages: course picker (stage 1) and tickets table (stage 2).
  reg({
    slug: 'support_tickets',
    title_en: 'Your tickets',
    title_sk: 'Vaše tikety',
    pages: ['support_tickets'],
    roles: ['student', 'teacher', 'admin'],
    autoPrompt: true,
    multiStage: true,
    steps: [
      {
        title_en: 'Ticket inbox',
        title_sk: 'Inbox tiketov',
        body_en: 'Every support request scoped to the selected course is listed here with status, last update and the assigned admin. Click any row for the full thread &mdash; you can reply, attach more files or close the ticket.',
        body_sk: 'Každá žiadosť o podporu pre vybraný predmet je tu so stavom, posledným updatom a prideleným adminom. Kliknutím na riadok otvoríte celé vlákno &mdash; môžete odpovedať, pridať prílohy alebo tiket zavrieť.',
      },
      // -- Stage 1: course picker --
      {
        element: '[data-tour~="support-course-picker"]',
        side: 'top',
        title_en: 'Pick the course',
        title_sk: 'Vyberte predmet',
        body_en: 'Tickets are filtered per course. Pick a course to see only its support requests &mdash; the unread badge in the sidebar shows the combined count across all your courses.',
        body_sk: 'Tikety sú filtrované podľa predmetu. Vyberte predmet a uvidíte iba jeho žiadosti o podporu &mdash; číslo neprečítaných v sidebare ukazuje spoločný počet naprieč všetkými vašimi predmetmi.',
      },
      // -- Stage 2: tickets table --
      {
        element: '[data-tour~="ticket-search"], #ticketSearch',
        side: 'bottom',
        title_en: 'Search',
        title_sk: 'Vyhľadávanie',
        body_en: 'Live filter across title, submitter, assigned admin and category. Searching is purely client-side &mdash; instant, no page reload.',
        body_sk: 'Live filter naprieč titulkom, odosielateľom, prideleným adminom a kategóriou. Hľadá sa čisto na strane klienta &mdash; okamžite, bez reloadu stránky.',
      },
      {
        element: '[data-tour~="ticket-filters"]',
        side: 'bottom',
        title_en: 'Filters',
        title_sk: 'Filtre',
        body_en: 'Narrow by <em>Status</em> (open / in progress / resolved / closed), <em>Priority</em> (critical -> low) and <em>Category</em>. Filters combine with search; the <em>Reset</em> button clears all of them at once.',
        body_sk: 'Zúžte podľa <em>Stavu</em> (open / in progress / resolved / closed), <em>Priority</em> (critical -> low) a <em>Kategórie</em>. Filtre sa kombinujú s vyhľadávaním; tlačidlo <em>Reset</em> zruší všetky naraz.',
      },
      {
        element: '#ticketsTable',
        side: 'top',
        title_en: 'Tickets table',
        title_sk: 'Tabuľka tiketov',
        body_en: 'Click any column header to sort (Shift-click for secondary sort key). The <em>#id</em> next to the title is the ticket number you can reference in chat.',
        body_sk: 'Kliknite na hlavičku stĺpca pre triedenie (Shift-klik pre sekundárny kľúč). <em>#id</em> pri titulke je číslo tiketu, na ktoré sa môžete odvolávať v chate.',
      },
      {
        element: '#ticketsTable .ticket-title-link, #ticketsTable td.col-ticket-actions, #ticketsTable a[href*="/dashboard/support/tickets/"]',
        side: 'left',
        title_en: 'Open a ticket',
        title_sk: 'Otvoriť tiket',
        body_en: 'The ticket title in the first column and the action button in the last column both open the full conversation. From the detail page you can reply with Markdown, attach files, change status / priority / assignee, or close the thread.',
        body_sk: 'Titulok tiketu v prvom stĺpci aj akčné tlačidlo v poslednom otvoria celú konverzáciu. Z detailu môžete odpovedať v Markdowne, pridať prílohy, zmeniť stav / prioritu / priradenie alebo vlákno zavrieť.',
      },
    ],
  });

  // -- 15. SUPPORT TICKET DETAIL -------------------------------------
  reg({
    slug: 'support_ticket_detail',
    title_en: 'Ticket conversation',
    title_sk: 'Konverzácia tiketu',
    pages: ['support_ticket_detail'],
    roles: ['teacher', 'admin'],
    autoPrompt: true,
    steps: [
      {
        title_en: 'Ticket conversation',
        title_sk: 'Konverzácia tiketu',
        body_en: 'Read the request, review its details, then follow the conversation. On desktop, details appear on the right; on mobile, they follow the description. New replies arrive without a refresh.',
        body_sk: 'Prečítajte si požiadavku, skontrolujte podrobnosti a sledujte konverzáciu. Na počítači sú podrobnosti vpravo, na mobile pod opisom. Nové odpovede prichádzajú bez obnovenia stránky.',
      },
      {
        element: '[data-tour~="ticket-meta"], #ghStatusRow',
        side: 'bottom',
        title_en: 'Status & meta',
        title_sk: 'Stav a meta',
        body_en: 'Status, academic period, live connection and comment count. The status badge updates when course staff change it.',
        body_sk: 'Stav, akademické obdobie, živé pripojenie a počet komentárov. Odznak stavu sa aktualizuje, keď ho personál kurzu zmení.',
      },
      {
        element: '[data-tour~="ticket-description"]',
        side: 'right',
        title_en: 'Request',
        title_sk: 'Požiadavka',
        body_en: 'The original request shows its author and date once, followed by the description and submitted form fields.',
        body_sk: 'Pôvodná požiadavka uvádza autora a dátum raz, potom opis a vyplnené polia formulára.',
      },
      {
        element: '[data-tour~="ticket-sidebar"], .gh-ticket-attributes',
        side: 'left',
        title_en: 'Details',
        title_sk: 'Podrobnosti',
        body_en: 'Course staff can change status, priority, category and assignment. Updates appear for everyone viewing this ticket without leaving the page.',
        body_sk: 'Personál kurzu môže zmeniť stav, prioritu, kategóriu a priradenie. Zmeny sa zobrazia všetkým, ktorí si tiket prezerajú, bez opustenia stránky.',
      },
      {
        element: '[data-tour~="ticket-thread"], .gh-ticket-thread',
        side: 'right',
        title_en: 'Thread',
        title_sk: 'Vlákno',
        body_en: 'Replies appear in chronological order below the request details. Markdown supports code blocks, lists and links. Internal notes are visible only to course staff.',
        body_sk: 'Odpovede sú v chronologickom poradí pod podrobnosťami požiadavky. Markdown podporuje bloky kódu, zoznamy a odkazy. Interné poznámky vidí iba personál kurzu.',
      },
      {
        element: '.gh-reply-form, [data-tour~="ticket-reply"]',
        side: 'top',
        title_en: 'Reply',
        title_sk: 'Odpovedať',
        body_en: 'Write a reply with full Markdown. Admins / assigned teachers can mark a reply as <em>Internal note</em> (visible only to staff) or <em>Close with comment</em> in one click. Use <em>Reopen and comment</em> to reopen a closed ticket.',
        body_sk: 'Napíšte odpoveď v plnom Markdowne. Admini / priradení učitelia môžu označiť odpoveď ako <em>Internú poznámku</em> (viditeľnú iba pre staff) alebo <em>Zavrieť s komentárom</em> jedným klikom. Uzavretý tiket znovu otvoríte pomocou <em>Znovu otvoriť a komentovať</em>.',
      },

    ],
  });

})();
