/* ------------------------------------------------------------------
 *  20-courses.js - Dashboard + course-page tours
 *
 *  Split from the monolithic tour content registry (SRP).
 *  that re-grabs GP.tour.register; the engine (00-engine.js, 10-render.js)
 *  comes earlier in
 *  the bundle.
 * ------------------------------------------------------------------ */
(() => {
  'use strict';

  if (!window.GP?.tour) {
    console.warn('[tours/20-courses.js] tour engine not loaded - content not registered');
    return;
  }
  const reg = window.GP.tour.register;
  // -- Appearance / "Mode" step (shared, appended to several tours) --
  // The theme switcher lives inside the profile dropdown, so this step opens
  // that menu, highlights the switcher, then closes it on the way out. The menu
  // is opened both when Driver resolves element() AND in onBefore (which runs as
  // the step is highlighted), so going Back/Forward always re-opens it. The
  // __gpTourActiveDriver guard keeps the menu shut during the passive autoPrompt
  // check on page load (the old "menu opens by itself" bug). dropdowns.css eases
  // the tour-owned menu in with a smooth opacity fade but no slide (so the
  // cut-out measures the switcher at its final position) and dropdowns.js keeps
  // it immune to click-outside, so the highlight is smooth AND accurate on every
  // step.
  const openAppearanceMenu = () => {
    if (!window.__gpTourActiveDriver) return;
    const userMenu = document.querySelector('[data-user-menu]');
    if (userMenu) window.GP.dropdown?.open(userMenu, { owner: 'tour' });
  };
  const closeAppearanceMenu = () => {
    const userMenu =
      document.querySelector('[data-user-menu][data-dropdown-owner="tour"]') ||
      document.querySelector('[data-user-menu]');
    window.GP.dropdown?.close(userMenu);
  };
  const appearanceTarget = () => {
    openAppearanceMenu();
    return document.querySelector('[data-tour~="theme-switcher"]');
  };
  window.GP.tour.registerSharedSteps('appearance', [
    {
      element: appearanceTarget,
      onBefore: openAppearanceMenu,
      onAfter: closeAppearanceMenu,
      side: 'left',
      align: 'end',
      title_en: 'Appearance &amp; account menu',
      title_sk: 'Vzhľad a účet',
      body_en: 'Your profile menu is open so you can try the control directly. <strong>Light</strong> and <strong>Dark</strong> stay fixed; <strong>System</strong> follows the operating-system setting. The choice is applied before first paint and saved to your account, so it follows you to another browser or device. You can also type <kbd>&gt;theme</kbd> in the command palette.',
      body_sk: 'Profilové menu je otvorené, takže prepínač môžete hneď vyskúšať. <strong>Svetlý</strong> a <strong>Tmavý</strong> režim zostávajú pevné; <strong>Systémový</strong> sleduje nastavenie operačného systému. Voľba sa použije ešte pred prvým vykreslením a uloží sa k účtu, takže sa prenesie aj do iného prehliadača alebo zariadenia. Použiť môžete aj príkaz <kbd>&gt;theme</kbd>.',
    },
  ]);

  // -- 1. DASHBOARD --------------------------------------------------
  reg({
    slug: 'dashboard_student',
    includeSharedSteps: true,
    title_en: 'Dashboard tour for students',
    title_sk: 'Sprievodca úvodnou stránkou (študent)',
    subtitle_en: 'Learn how to track your courses, groups and progress.',
    subtitle_sk: 'Naučte sa sledovať kurzy, skupiny a svoj postup.',
    pages: ['dashboard'],
    roles: ['student'],
    autoPrompt: true,
    steps: [
      {
        title_en: 'Welcome to GitPulse',
        title_sk: 'Vitajte v GitPulse',
        body_en: 'This is your <strong>student dashboard</strong> &mdash; the single place where every course, team and deadline you care about is rolled up. Sync completion and GitLab webhooks invalidate the affected server-rendered data so current results appear without waiting for a periodic refresh.',
        body_sk: 'Toto je vaša <strong>študentská úvodná stránka</strong> &mdash; jedno miesto, kde sú zhrnuté všetky vaše predmety, tímy a termíny. Dokončenie synchronizácie a GitLab webhooky zneplatnia dotknuté serverom renderované dáta, takže aktuálne výsledky sa zobrazia bez čakania na periodický refresh.',
      },
      {
        element: '.gl-sidebar, [data-sidebar]',
        side: 'right',
        title_en: 'Side navigation',
        title_sk: 'Bočná navigácia',
        body_en: 'The sidebar is your map. <strong>Your work</strong> contains the dashboard and the support inbox. Below it sit links to <em>Docs</em> and a collapse button at the bottom that hides the sidebar (useful on a small screen) &mdash; the choice is remembered for this device.',
        body_sk: 'Bočná lišta je vaša mapa. <strong>Vaša práca</strong> obsahuje dashboard a inbox podpory. Pod ňou nájdete linky na <em>Dokumentáciu</em> a tlačidlo na zbalenie lišty dolu (užitočné na malom displeji) &mdash; voľba sa pamätá pre dané zariadenie.',
      },
      {
        element: '#globalSearchBtn, [data-action="open-search"], .gl-topbar-search',
        side: 'bottom',
        align: 'end',
        title_en: 'Global search & command palette',
        title_sk: 'Globálne vyhľadávanie a paleta',
        body_en: '<kbd>/</kbd> or <kbd>Ctrl</kbd>+<kbd>K</kbd> opens the palette anywhere in the app. It does fuzzy match across <em>courses</em>, <em>teams</em>, your <em>commits</em> and <em>tickets</em>. Prefix the query with <kbd>></kbd> to run commands like <kbd>>theme</kbd> or <kbd>>tour</kbd>.',
        body_sk: '<kbd>/</kbd> alebo <kbd>Ctrl</kbd>+<kbd>K</kbd> otvorí paletu kdekoľvek v aplikácii. Robí fuzzy hľadanie cez <em>predmety</em>, <em>tímy</em>, vaše <em>commity</em> a <em>tikety</em>. Prefix <kbd>></kbd> spúšťa príkazy ako <kbd>>theme</kbd> alebo <kbd>>tour</kbd>.',
      },
      {
        element: '[data-tour~="my-courses"], #myCourses, .gl-courses-grid, .courses-grid',
        side: 'top',
        title_en: 'Your courses',
        title_sk: 'Vaše predmety',
        body_en: 'Every course you are enrolled in, in the academic period chosen above, appears as a card. Each card shows the course code, your team, and any <strong>pending evaluations</strong> waiting for you. Click anywhere on a card to open the course detail page; the kebab (&vellip;) gives you quick links to your team and project.',
        body_sk: 'Každý predmet, do ktorého ste zapísaní v období zvolenom vyššie, je karta. Karta ukazuje kód predmetu, váš tím a <strong>čakajúce hodnotenia</strong>. Klikom kdekoľvek na kartu otvoríte detail predmetu; kebab (&vellip;) ponúka rýchle linky na váš tím a projekt.',
      },
      {
        element: '[data-period-selector]',
        side: 'bottom',
        align: 'end',
        title_en: 'Academic period',
        title_sk: 'Akademické obdobie',
        body_en: 'The term this page shows. It opens on the newest term that holds your courses; the term the TUKE calendar is in is marked <em>Current</em>. <strong>All periods</strong> shows every term at once. Your choice is remembered until the next term starts - then the page follows the calendar again.',
        body_sk: 'Obdobie, ktoré stránka zobrazuje. Otvorí sa na najnovšom období s vašimi predmetmi; obdobie, v ktorom je kalendár TUKE, je označené <em>Aktuálne</em>. <strong>Všetky obdobia</strong> ukážu všetky obdobia naraz. Váš výber sa pamätá, kým sa nezačne ďalšie obdobie - potom stránka opäť nasleduje kalendár.',
      },
      {
        element: '[data-tour~="deadlines"], .deadlines-widget, .gl-deadlines',
        side: 'left',
        title_en: 'Upcoming deadlines',
        title_sk: 'Blížiace sa termíny',
        body_en: 'GitPulse aggregates milestones from every course you are in &mdash; sorted by date, the closest one first. Times shown are in <strong>server time</strong> (the same clock used to evaluate your hand-ins), so you and the platform always agree on "is it past midnight".',
        body_sk: 'GitPulse zhromažďuje míľniky zo všetkých vašich predmetov &mdash; zoradené podľa dátumu, najbližší ako prvý. Časy sú zobrazené v <strong>serverovom čase</strong> (tom istom, ktorý sa používa na hodnotenie odovzdaní), takže vy aj platforma sa zhodujete na "je už po polnoci?".',
      },
      {
        element: '[data-tour~="latest-feedback"], .latest-feedback, .feedback-list',
        side: 'left',
        title_en: 'Latest feedback',
        title_sk: 'Posledná spätná väzba',
        body_en: 'Anything your teachers wrote about your work lands here. Click an entry to read the full note &mdash; it links straight to the commit or merge request it refers to, so you can see exactly what the comment is about.',
        body_sk: 'Čokoľvek, čo o vašej práci napíšu učitelia, sa zobrazí tu. Klikom na položku otvoríte celú poznámku &mdash; obsahuje link priamo na commit alebo MRku, ktorej sa týka, takže presne uvidíte, o čom hovorí.',
      },
      {
        element: '#nav-language, .gp-locale-switcher, [data-locale-switcher]',
        side: 'top',
        title_en: 'Language',
        title_sk: 'Jazyk',
        body_en: 'Toggle between <strong>English</strong> and <strong>Slovenčina</strong>. The choice is stored on the server (per account), so it follows you to other devices. You can even switch mid-tour &mdash; the next step renders in the new language.',
        body_sk: 'Prepnite medzi <strong>English</strong> a <strong>Slovenčinou</strong>. Voľba sa ukladá na serveri (per účet), takže sa pamätá aj na iných zariadeniach. Môžete prepnúť aj počas sprievodcu &mdash; ďalší krok sa vykreslí v novom jazyku.',
      },
      {
        element: '[data-tour~="topbar-time"], .topbar-time, .gl-topbar-clock',
        side: 'bottom',
        align: 'end',
        title_en: 'Server clock',
        title_sk: 'Serverový čas',
        body_en: 'The clock at the top right is the <em>server</em> time, not your laptop\'s. All deadline checks happen against this clock, so you always know exactly how much time is left, even if your local time zone is different.',
        body_sk: 'Hodiny vpravo hore zobrazujú <em>serverový</em> čas, nie čas notebooku. Všetky kontroly termínov bežia voči nim &mdash; vždy presne viete, koľko času ostáva, aj keď máte iné časové pásmo.',
      },
      {
        title_en: 'Power-user shortcuts',
        title_sk: 'Skratky pre power-userov',
        body_en: '<kbd>Shift</kbd>+<kbd>?</kbd> &mdash; full keyboard cheatsheet.<br><kbd>g</kbd> then <kbd>d</kbd> &mdash; jump to dashboard from anywhere.<br><kbd>Ctrl</kbd>+<kbd>S</kbd> &mdash; save any open form.<br><kbd>?</kbd> in the top bar &mdash; re-run any tour for the current page.',
        body_sk: '<kbd>Shift</kbd>+<kbd>?</kbd> &mdash; klávesová cheatsheeta.<br><kbd>g</kbd> potom <kbd>d</kbd> &mdash; späť na dashboard kdekoľvek.<br><kbd>Ctrl</kbd>+<kbd>S</kbd> &mdash; uložiť otvorený formulár.<br><kbd>?</kbd> v hornej lište &mdash; znovu spustiť sprievodcu pre aktuálnu stránku.',
      },
      {
        title_en: 'You are ready',
        title_sk: 'Ste pripravení',
        body_en: 'Each page has its own role-aware tour &mdash; open a course or your team and click <strong>?</strong> in the top bar to relaunch the tour for that page. Good luck with the semester!',
        body_sk: 'Každá stránka má vlastného sprievodcu prispôsobeného vašej role &mdash; otvorte predmet či tím a kliknite na <strong>?</strong> v hornej lište. Veľa šťastia v semestri!',
      },
    ],
  });

  reg({
    slug: 'dashboard_teacher',
    includeSharedSteps: true,
    title_en: 'Dashboard tour for teachers',
    title_sk: 'Sprievodca úvodnou stránkou (učiteľ)',
    subtitle_en: 'See compliance heatmaps, team activity, and run quick actions.',
    subtitle_sk: 'Heatmapy compliance, aktivita tímov a rýchle akcie.',
    pages: ['dashboard'],
    roles: ['teacher', 'admin'],
    autoPrompt: true,
    steps: [
      {
        title_en: 'Teacher dashboard',
        title_sk: 'Učiteľský dashboard',
        body_en: 'This is your <strong>command centre</strong>. GitPulse rolls up GitLab data across every course you teach &mdash; <strong>compliance scores</strong>, <strong>flagged commits</strong>, <strong>CI failures</strong>, and <strong>pending evaluations</strong>. Sync completion and webhooks invalidate affected server-rendered views instead of relying on a fixed refresh interval.',
        body_sk: 'Toto je vaše <strong>riadiace centrum</strong>. GitPulse sumarizuje GitLab dáta naprieč všetkými predmetmi, ktoré učíte &mdash; <strong>compliance skóre</strong>, <strong>označené commity</strong>, <strong>zlyhania CI</strong> a <strong>čakajúce hodnotenia</strong>. Dokončenie synchronizácie a webhooky zneplatnia dotknuté serverom renderované pohľady namiesto spoliehania sa na pevný interval obnovovania.',
      },
      {
        element: '.gl-sidebar, [data-sidebar]',
        side: 'right',
        title_en: 'Side navigation',
        title_sk: 'Bočná navigácia',
        body_en: 'The sidebar is your home base. <strong>Your work</strong> contains the dashboard and the support inbox. <strong>Administration</strong> (visible because you are a teacher / admin) holds <em>Users</em>, <em>Courses</em>, <em>System</em> and <em>Events</em> &mdash; system-wide views beyond a single course. The sidebar collapses when you click <em>Collapse sidebar</em> at the bottom; your choice is saved per device.',
        body_sk: 'Bočná lišta je váš základný uzol. <strong>Vaša práca</strong> obsahuje dashboard a inbox podpory. <strong>Administrácia</strong> (viditeľná, lebo ste učiteľ / admin) má <em>Používateľov</em>, <em>Predmety</em>, <em>Systém</em> a <em>Udalosti</em> &mdash; pohľady naprieč celým systémom mimo jedného predmetu. Lišta sa zbalí kliknutím na <em>Zbaliť bočnú lištu</em> dolu; voľba sa pamätá pre dané zariadenie.',
      },
      {
        element: '#globalSearchBtn, [data-action="open-search"], .gl-topbar-search',
        side: 'bottom',
        align: 'end',
        title_en: 'Global search & command palette',
        title_sk: 'Globálne vyhľadávanie a príkazová paleta',
        body_en: '<kbd>/</kbd> or <kbd>Ctrl</kbd>+<kbd>K</kbd> opens the palette anywhere in the app. It searches across <em>courses</em>, <em>teams</em>, <em>students</em>, <em>commits</em> and <em>tickets</em> with fuzzy match. Prefix your query with <kbd>></kbd> to invoke commands (e.g. <kbd>>theme</kbd>, <kbd>>tour</kbd>). Arrow keys to navigate, Enter to jump.',
        body_sk: '<kbd>/</kbd> alebo <kbd>Ctrl</kbd>+<kbd>K</kbd> otvorí paletu kdekoľvek. Hľadá v <em>predmetoch</em>, <em>tímoch</em>, <em>študentoch</em>, <em>commitoch</em> a <em>tiketoch</em> s fuzzy match. Prefix <kbd>></kbd> spúšťa príkazy (napr. <kbd>>theme</kbd>, <kbd>>tour</kbd>). Šípky na pohyb, Enter na skok.',
      },
      {
        element: '[data-tour~="kpi-cards"], .stat-card, .gl-stat-cards, .stats-row',
        side: 'bottom',
        title_en: 'KPI cards at a glance',
        title_sk: 'KPI karty na prvý pohľad',
        body_en: 'The four cards at the top are <em>Users</em>, <em>Groups</em>, <em>Students</em> and <em>Compliance</em>. Numbers are aggregated across the courses of the academic period on screen - each card names it - and a card opens the page that shows the same figure. The compliance percentage is a <strong>weighted mean</strong> of all team scores &mdash; weights come from each course\'s settings page.',
        body_sk: 'Štyri karty hore zobrazujú <em>Používateľov</em>, <em>Skupiny</em>, <em>Študentov</em> a <em>Compliance</em>. Čísla sa agregujú naprieč predmetmi zobrazeného akademického obdobia - každá karta ho uvádza - a karta otvorí stránku s tým istým číslom. Compliance percento je <strong>vážený priemer</strong> skóre všetkých tímov &mdash; váhy pochádzajú z nastavení každého predmetu.',
      },
      {
        element: '[data-tour~="courses-list"], .gl-courses-grid, .courses-grid, #myCourses',
        side: 'top',
        title_en: 'Courses you teach',
        title_sk: 'Predmety, ktoré učíte',
        body_en: 'Each card has badges for <em>active teams</em>, <em>flagged compliance</em> and <em>pending evaluations</em>. The orange <strong>at-risk</strong> chip means at least one team is below the configured red threshold. Use the <strong>+ Group</strong> button to spin up a new team without leaving the dashboard, and the kebab (&vellip;) for archive / resync / export.',
        body_sk: 'Každá karta má odznaky pre <em>aktívne tímy</em>, <em>označený compliance</em> a <em>čakajúce hodnotenia</em>. Oranžový <strong>at-risk</strong> chip znamená aspoň jeden tím pod červeným prahom. Tlačidlo <strong>+ Group</strong> vytvorí nový tím bez opúšťania dashboardu, kebab (&vellip;) ponúka archív / resync / export.',
      },
      {
        element: '[data-period-selector]',
        side: 'bottom',
        align: 'end',
        title_en: 'Academic period',
        title_sk: 'Akademické obdobie',
        body_en: 'The term this page shows. It opens on the newest term that holds your courses; the term the TUKE calendar is in is marked <em>Current</em>. <strong>All periods</strong> shows every term at once. Your choice is remembered until the next term starts - then the page follows the calendar again.',
        body_sk: 'Obdobie, ktoré stránka zobrazuje. Otvorí sa na najnovšom období s vašimi predmetmi; obdobie, v ktorom je kalendár TUKE, je označené <em>Aktuálne</em>. <strong>Všetky obdobia</strong> ukážu všetky obdobia naraz. Váš výber sa pamätá, kým sa nezačne ďalšie obdobie - potom stránka opäť nasleduje kalendár.',
      },
      {
        element: '[data-tour~="quick-access"], .quick-access, #quickAccess',
        side: 'left',
        title_en: 'Quick access panel',
        title_sk: 'Panel rýchleho prístupu',
        body_en: 'Pinned shortcuts to the groups and projects you visit most. Tabs split it into <em>Groups</em> and <em>Subgroups & Projects</em>. Each row shows the team\'s compliance percent and member count &mdash; click anywhere on the row to jump straight in.',
        body_sk: 'Pripnuté skratky do skupín a projektov, ktoré najčastejšie navštevujete. Záložky rozdelujú zoznam na <em>Skupiny</em> a <em>Podskupiny a projekty</em>. Každý riadok ukazuje compliance % a počet členov &mdash; klikom kdekoľvek na riadku skočíte rovno dovnútra.',
      },
      {
        element: '[data-tour~="needs-attention"], .needs-attention, .attention-list, [data-widget="attention"]',
        side: 'top',
        title_en: 'Items that need your attention',
        title_sk: 'Položky vyžadujúce vašu pozornosť',
        body_en: 'Auto-curated worklist: groups at critical risk, courses with inactive webhooks, students with missed deadlines. Each row is a deep link &mdash; one click to the exact place to act. The panel is refreshed when its underlying course data changes.',
        body_sk: 'Automaticky kurátorovaný worklist: skupiny v kritickom riziku, predmety s neaktívnymi webhookmi, študenti so zmeškanými termínmi. Každý riadok je deep link &mdash; jeden klik a ste presne tam, kde treba zasiahnuť. Panel sa obnoví pri zmene podkladových dát predmetu.',
      },
      {
        element: '[data-tour~="system-health"], .system-health, #systemHealth',
        side: 'left',
        title_en: 'System health',
        title_sk: 'Stav systému',
        body_en: 'Background-job pulse: how many jobs are queued, running, completed in the last 24 h, and failed. If <strong>Failed (24 h)</strong> stays non-zero, click into <em>Administration &rarr; System</em> for the per-job error trace and a one-click retry.',
        body_sk: 'Pulz background úloh: koľko ich čaká, beží, sa dokončilo za posledných 24 h a koľko zlyhalo. Ak <strong>Failed (24 h)</strong> ostáva nenulové, kliknite do <em>Administrácia &rarr; Systém</em> &mdash; uvidíte stack trace a one-click retry.',
      },
      {
        element: '[data-tour~="latest-changes"], .latest-changes, #latestChanges',
        side: 'left',
        title_en: 'Latest changes',
        title_sk: 'Posledné zmeny',
        body_en: 'Changelog feed of the GitPulse platform itself &mdash; new features, fixes and breaking changes. Click an entry to read the full release note. Bookmark the <em>Docs</em> link in the sidebar for the complete history.',
        body_sk: 'Changelog samotnej platformy GitPulse &mdash; nové funkcie, opravy a zmeny. Klikom na položku otvoríte celú release note. Pre úplnú históriu si pozrite <em>Docs</em> v bočnej lište.',
      },
      {
        element: '#nav-language, .gp-locale-switcher, [data-locale-switcher]',
        side: 'top',
        title_en: 'Language switcher',
        title_sk: 'Prepínač jazyka',
        body_en: 'Toggle between <strong>English</strong> and <strong>Slovenčina</strong>. Your choice is stored on the server (per account) so it follows you to other devices. Mid-tour switches are picked up live &mdash; the next step renders in the new language.',
        body_sk: 'Prepnite medzi <strong>English</strong> a <strong>Slovenčinou</strong>. Voľba sa ukladá na serveri (per účet), takže sa pamätá aj na iných zariadeniach. Prepnutie počas sprievodcu sa zachytí ihneď &mdash; ďalší krok sa vykreslí v novom jazyku.',
      },
      {
        element: '[data-tour~="topbar-time"], .topbar-time, .gl-topbar-clock',
        side: 'bottom',
        align: 'end',
        title_en: 'Server clock',
        title_sk: 'Serverový čas',
        body_en: 'The clock in the top right is the <em>server</em> time, not your laptop\'s. All deadline checks happen against this clock, so you and the students always agree on "is it past midnight". The term beside it (e.g. <em>2026/2027 &middot; Winter</em>) is the one the TUKE calendar is in - the same term every period selector marks <em>Current</em> and every new course starts in.',
        body_sk: 'Hodiny vpravo hore sú <em>serverový</em> čas, nie čas notebooku. Všetky kontroly termínov bežia voči nim &mdash; vy aj študenti sa zhodujete na "je už po polnoci?". Obdobie vedľa nich (napr. <em>2026/2027 &middot; Zima</em>) je to, v ktorom je kalendár TUKE - to isté, ktoré každý výber obdobia označí <em>Aktuálne</em> a v ktorom začína každý nový predmet.',
      },
      {
        title_en: 'Links and table actions',
        title_sk: 'Odkazy a akcie v tabuľkách',
        body_en: 'Open a record through its name or an action in the <strong>Actions</strong> column. The rest of the row is for reading and selecting text. Use <kbd>Tab</kbd> to focus a link or button and <kbd>Enter</kbd> to activate it. Native links also support opening in a new tab.',
        body_sk: 'Záznam otvoríte cez jeho názov alebo akciu v stĺpci <strong>Akcie</strong>. Zvyšok riadka slúži na čítanie a označenie textu. Klávesom <kbd>Tab</kbd> prejdete na odkaz či tlačidlo a klávesom <kbd>Enter</kbd> ho aktivujete. Odkazy možno otvoriť aj na novej karte.',
      },
      {
        title_en: 'You can re-run me any time',
        title_sk: 'Tento sprievodca sa dá znovu pustiť',
        body_en: 'Click the <strong>?</strong> in the top bar to launch any tour, view the keyboard cheatsheet, or open the docs. Each page has its own role-aware tour &mdash; visit a course or team and the tour list updates automatically.',
        body_sk: 'Kliknite na <strong>?</strong> v hornej lište &mdash; spustíte ľubovoľného sprievodcu, otvoríte klávesovú nápovedu alebo dokumentáciu. Každá stránka má vlastného sprievodcu pre vašu rolu &mdash; v predmete či tíme sa zoznam aktualizuje sám.',
      },
    ],
  });

  // -- 2. COURSE DETAIL ----------------------------------------------
  reg({
    slug: 'course_detail_student',
    title_en: 'Course page for students',
    title_sk: 'Detail predmetu (študent)',
    subtitle_en: 'Find your team, evaluations and project.',
    subtitle_sk: 'Nájdite svoj tím, hodnotenia a projekt.',
    pages: ['course_detail'],
    roles: ['student'],
    autoPrompt: true,
    steps: [
      {
        title_en: 'Welcome to the course',
        title_sk: 'Vitajte v predmete',
        body_en: 'This is the <strong>course detail page</strong> &mdash; everything for one specific course in one place: the syllabus link, your team, all course deadlines and the feedback your teachers have left for you. The page header shows the course code, semester and the names of the teachers in charge.',
        body_sk: 'Toto je <strong>stránka detailu predmetu</strong> &mdash; všetko pre jeden konkrétny predmet na jednom mieste: link na sylabus, váš tím, všetky termíny predmetu aj spätnú väzbu. Hlavička stránky ukazuje kód predmetu, semester a mená vyučujúcich.',
      },
      {
        element: '[data-tour~="course-tabs"], .nav-tabs, .gl-tabs, .course-tabs, .tabs-nav',
        side: 'bottom',
        title_en: 'Tabs',
        title_sk: 'Záložky',
        body_en: 'Tabs split the course into focused views &mdash; <em>Overview</em> for the big picture, <em>Activity</em> for the live event stream, and (if available) the syllabus, materials and announcements. Tabs swap content without reloading the page; the URL updates so you can bookmark any tab.',
        body_sk: 'Záložky rozdeľujú predmet do tematických pohľadov &mdash; <em>Prehľad</em> pre celkový obraz, <em>Aktivita</em> pre živý stream udalostí a (ak sú dostupné) sylabus, materiály a oznamy. Záložky menia obsah bez prekladania stránky; URL sa aktualizuje, takže záložku si môžete uložiť.',
      },
      {
        element: '[data-tour~="my-team"], .my-team, [data-widget="my-team"]',
        side: 'right',
        title_en: 'Your team',
        title_sk: 'Váš tím',
        body_en: 'The team card highlights your group: members, the project name, and a small <strong>compliance badge</strong> showing how well your team meets the course rules. Click anywhere on the card to open the full team page where you can see commits, MRs and CI runs in real time.',
        body_sk: 'Karta tímu zvýrazňuje vašu skupinu: členov, názov projektu a malý <strong>compliance odznak</strong>, ktorý ukazuje, ako dobre váš tím spĺňa pravidlá predmetu. Klikom kdekoľvek na kartu otvoríte celú stránku tímu, kde uvidíte commity, MRky a behy CI v reálnom čase.',
      },
      {
        element: '[data-tour~="course-deadlines"], .course-deadlines',
        side: 'left',
        title_en: 'Course deadlines',
        title_sk: 'Termíny predmetu',
        body_en: 'All important dates for this course, sorted by upcoming first. A red chip means the deadline has already passed; an orange one means &lt; 24 h. Times are in <strong>server time</strong> &mdash; the same clock used to evaluate hand-ins.',
        body_sk: 'Všetky dôležité dátumy pre tento predmet, najbližšie ako prvé. Červený chip znamená, že termín už uplynul; oranžový znamená &lt; 24 h. Časy sú v <strong>serverovom čase</strong> &mdash; tom istom, ktorým sa hodnotia odovzdania.',
      },
      {
        element: '[data-tour~="latest-feedback"], .latest-feedback, .feedback-list',
        side: 'top',
        title_en: 'Feedback for this course',
        title_sk: 'Spätná väzba pre tento predmet',
        body_en: 'Comments your teachers left specifically about this course. Each entry deep-links to the commit or MR it refers to. If you reply, the teacher receives an email and a notification.',
        body_sk: 'Komentáre, ktoré učitelia napísali špeciálne k tomuto predmetu. Každá položka odkazuje priamo na commit alebo MRku. Ak odpoviete, učiteľ dostane e-mail aj notifikáciu.',
      },
    ],
  });

  reg({
    slug: 'course_detail_teacher',
    title_en: 'Course page for teachers',
    title_sk: 'Detail predmetu (učiteľ)',
    subtitle_en: 'Manage teams, settings, analytics and roster.',
    subtitle_sk: 'Spravujte tímy, nastavenia, analytiku a zoznam študentov.',
    pages: ['course_detail'],
    roles: ['teacher', 'admin'],
    autoPrompt: true,
    steps: [
      {
        title_en: 'Course command centre',
        title_sk: 'Riadiace centrum predmetu',
        body_en: 'This is the <strong>course detail page</strong> for teachers. The tabs at the top split it into focused views: <em>Overview</em>, <em>Analytics</em>, <em>Roster</em>, <em>Co-teachers</em>, <em>Settings</em> and <em>Activity</em>. The header shows the GitLab group ID, semester and a small status pill (<em>active / archived / syncing</em>).',
        body_sk: 'Toto je <strong>stránka detailu predmetu</strong> pre učiteľov. Záložky hore rozdeľujú obsah na <em>Prehľad</em>, <em>Analytiku</em>, <em>Zoznam</em>, <em>Spoluvyučujúcich</em>, <em>Nastavenia</em> a <em>Aktivitu</em>. Hlavička obsahuje GitLab group ID, semester a malý stavový chip (<em>aktívny / archivovaný / synchronizuje</em>).',
      },
      {
        element: '[data-tab="overview"], a[href*="/dashboard/courses/"][href$="/"]',
        side: 'bottom',
        title_en: 'Overview',
        title_sk: 'Prehľad',
        body_en: 'A high-level snapshot of the course: number of enrolled students, active teams, last GitLab sync, and today\'s compliance percentage. The teams grid below the snapshot is auto-sorted by <strong>at-risk first</strong> &mdash; teams below the red threshold float to the top so you spot trouble fast.',
        body_sk: 'Súhrnný pohľad: počet zapísaných študentov, aktívne tímy, posledná synchronizácia s GitLabom a dnešné compliance percento. Mriežka tímov pod prehľadom je automaticky zoradená <strong>at-risk najprv</strong> &mdash; tímy pod červeným prahom plávajú hore, aby ste hneď zbadali problém.',
      },
      {
        element: 'a[href*="/analytics"]',
        side: 'bottom',
        title_en: 'Analytics',
        title_sk: 'Analytika',
        body_en: 'Weekly charts of commits, merge requests, reviews and compliance &mdash; aggregated across every team. Hover any data point to see the exact value, click a bar to drill into that week. Useful when you want to see whether engagement drops after a holiday or before a deadline.',
        body_sk: 'Týždenné grafy commitov, merge requestov, reviews a compliance &mdash; agregované cez všetky tímy. Hover ukáže presnú hodnotu, klik na stĺpec spustí drill-down do daného týždňa. Užitočné, keď chcete vidieť, či aktivita klesne po sviatkoch alebo pred uzávierkou.',
      },
      {
        element: 'a[href*="/roster"]',
        side: 'bottom',
        title_en: 'Roster',
        title_sk: 'Zoznam študentov',
        body_en: 'Every enrolled student in this course. You can bulk-import via CSV (<code>email,name,team</code>), assign students to teams in bulk, deactivate or remove them, and export the whole list as CSV for offline grading. Live search filters the table as you type.',
        body_sk: 'Všetci zapísaní študenti v tomto predmete. Môžete robiť hromadný import cez CSV (<code>email,meno,tím</code>), priraďovať študentov do tímov hromadne, deaktivovať či odstraňovať a exportovať celý zoznam ako CSV pre offline hodnotenie. Živé hľadanie filtruje tabuľku počas písania.',
      },
      {
        element: 'a[href*="/teachers"]',
        side: 'bottom',
        title_en: 'Co-teachers',
        title_sk: 'Spoluvyučujúci',
        body_en: 'Add other teachers as <em>instructors</em> on this course so they can grade alongside you. The owner role can transfer ownership to another teacher; instructors can do everything except delete the course or change ownership.',
        body_sk: 'Pridajte ďalších učiteľov ako <em>inštruktorov</em> &mdash; môžu hodnotiť spolu s vami. Rola <em>owner</em> môže preniesť vlastníctvo na iného učiteľa; inštruktori môžu robiť všetko okrem zmazania predmetu a zmeny vlastníctva.',
      },
      {
        element: 'a[href*="/settings"]',
        side: 'bottom',
        title_en: 'Settings',
        title_sk: 'Nastavenia',
        body_en: 'Control the GitLab group ID, webhook secret, default checks, score weights, milestones and the per-course CI YAML. All changes are versioned &mdash; the audit log lets you roll back if something goes wrong.',
        body_sk: 'Riadi GitLab group ID, webhook tajomstvo, predvolené kontroly, váhy skóre, míľniky a CI YAML pre tento predmet. Všetky zmeny sú verzované &mdash; audit log umožňuje vrátiť sa späť, ak sa niečo pokazí.',
      },
      {
        element: '[data-tour~="run-checks"], #btnOpenRunChecks, .js-run-checks, [data-action=run-checks], [data-modal-open="runChecksModal"]',
        side: 'left',
        title_en: 'Run compliance checks',
        title_sk: 'Spustiť compliance kontroly',
        body_en: 'Opens a modal where you can re-run any subset of the 13 built-in checks (R01&ndash;R13) plus your custom checks for the whole course. Filter by category (commits / MRs / CI / process), pick teams, and watch the progress bar as the queue drains.',
        body_sk: 'Otvorí modal, kde môžete znovu spustiť ľubovoľnú podmnožinu 13 zabudovaných kontrol (R01&ndash;R13) plus vlastné kontroly pre celý predmet. Filtrujte podľa kategórie (commity / MRky / CI / proces), vyberte tímy a sledujte progress bar, ako sa fronta vyprázdňuje.',
      },
      {
        element: '[data-tour~="course-events"], .events-list, .activity-stream',
        side: 'top',
        title_en: 'Activity stream',
        title_sk: 'Stream aktivity',
        body_en: 'Real-time tail of every GitLab event for this course &mdash; commits, MRs, reviews, CI runs. Toggle event types to focus on what matters, pause the stream while you read, resume to catch up.',
        body_sk: 'Live stream všetkých GitLab udalostí pre tento predmet &mdash; commity, MRky, reviews, CI behy. Prepnite typy udalostí, aby ste sa sústredili na to, čo vás zaujíma, pozastavte stream počas čítania a obnovte, keď chcete dohnať zameškané.',
      },
      {
        element: '[data-tour~="add-group"], [data-modal-open="addTeamModal"]',
        side: 'bottom',
        title_en: 'Add a group',
        title_sk: 'Pridať skupinu',
        body_en: 'Opens a modal to create a brand-new group inside this course. You give it a name (matches the GitLab subgroup name) and optionally pre-link a project path. Once saved, students assigned to that group are auto-rostered into all linked projects.',
        body_sk: 'Otvorí modal na vytvorenie novej skupiny v tomto predmete. Zadáte jej meno (zhoda s názvom GitLab podskupiny) a voliteľne predlinkujete cestu projektu. Po uložení sa študenti v tejto skupine automaticky pripoja k všetkým prepojeným projektom.',
      },
      {
        element: '[data-tour~="import-gitlab"], [data-modal-open="importGitlabCourseModal"]',
        side: 'bottom',
        title_en: 'Import from GitLab',
        title_sk: 'Importovať z GitLabu',
        body_en: 'Bulk-import an entire GitLab group: every subgroup becomes a team, every project gets linked, every member is rostered in one go. Use this on day one of the semester to bootstrap the whole course in seconds.',
        body_sk: 'Hromadný import celej GitLab skupiny: každá podskupina sa stane tímom, každý projekt sa pripojí, každý člen sa zarosteruje. Použite hneď v prvý deň semestra na rýchle naštartovanie predmetu.',
      },
      {
        element: '[data-tour~="sync-all"], [data-action="triggerSyncAll"]',
        side: 'bottom',
        title_en: 'Sync all groups',
        title_sk: 'Synchronizovať všetky',
        body_en: 'Force a full re-pull from GitLab for every group at once &mdash; members, projects, pipelines, MRs, issues and commits. Use it when webhooks were dropped or after manually editing GitLab data.',
        body_sk: 'Vynúti plný re-pull z GitLabu pre všetky skupiny naraz &mdash; členov, projekty, pipeline, MRky, issues a commity. Použite, keď sa webhooky stratili, alebo po manuálnej zmene v GitLabe.',
      },
      {
        element: '#teamSearchInput',
        side: 'bottom',
        title_en: 'Filter groups',
        title_sk: 'Filtrovať skupiny',
        body_en: 'Live search across the groups table &mdash; matches by group name and traffic-light status. Empty the field to clear the filter. The match counter on the right tells you how many rows are visible.',
        body_sk: 'Živé hľadanie v tabuľke skupín &mdash; matchuje podľa názvu skupiny a stavu semaforu. Prázdne pole filter zruší. Počítadlo vpravo ukazuje, koľko riadkov je viditeľných.',
      },
      {
        element: '#teamsTable',
        side: 'top',
        title_en: 'Groups table',
        title_sk: 'Tabuľka skupín',
        body_en: 'Every group in the course with <em>Contributors</em>, <em>Avg Score</em>, <em>Status</em> traffic light and <em>Last Updated</em>. Click any header to sort. Click the chevron on a parent row to expand its linked GitLab projects in a tree view.',
        body_sk: 'Všetky skupiny v predmete s <em>Prispievatelia</em>, <em>Priemerné skóre</em>, semaforom <em>Stav</em> a <em>Posledná aktualizácia</em>. Klikom na hlavičku zoradíte. Klikom na šípku rozbalíte prepojené GitLab projekty do stromu.',
      },
      {
        element: '[data-tour~="link-project"], #teamsTable [data-action="openLinkProjectModal"]',
        side: 'left',
        title_en: 'Link a project',
        title_sk: 'Prepojiť projekt',
        body_en: 'Attaches a GitLab project to this group so commits, MRs and pipelines from that repo start counting toward the group&apos;s compliance score. One group can have multiple linked projects.',
        body_sk: 'Pripojí GitLab projekt k tejto skupine &mdash; commity, MRky a pipeline z daného repa sa začnú započítavať do compliance skóre skupiny. Jedna skupina môže mať viac projektov.',
      },
      {
        element: '[data-tour~="sync-row"], #teamsTable [data-action="triggerSync"]',
        side: 'left',
        title_en: 'Sync a single group',
        title_sk: 'Synchronizovať jednu skupinu',
        body_en: 'Cheaper than <em>Sync All</em>: re-fetches members, projects and recent activity for just this group. The icon spins while the job runs and the row&apos;s <em>Last Updated</em> ticks over when it finishes.',
        body_sk: 'Lacnejšie než <em>Synchronizovať všetky</em>: re-fetchne členov, projekty a aktivitu len tejto skupiny. Ikona sa točí počas behu, <em>Posledná aktualizácia</em> sa aktualizuje po dokončení.',
      },
      {
        element: '[data-tour~="delete-row"], #teamsTable [data-action="deleteTeam"]',
        side: 'left',
        title_en: 'Delete a group',
        title_sk: 'Zmazať skupinu',
        body_en: 'Removes the group and unlinks all its projects from the course. Students stay in the system; their compliance history is preserved. The action asks for explicit confirmation &mdash; there is no undo.',
        body_sk: 'Odstráni skupinu a odpojí všetky jej projekty od predmetu. Študenti zostávajú v systéme; ich compliance história sa zachová. Akcia žiada potvrdenie &mdash; vrátiť späť nie je možné.',
      },
    ],
  });

  // -- 3. COURSE SETTINGS --------------------------------------------
  reg({
    slug: 'course_settings_teacher',
    title_en: 'Course settings tour',
    title_sk: 'Sprievodca nastaveniami predmetu',
    subtitle_en: 'Configure GitLab, checks, weights and schedule.',
    subtitle_sk: 'Konfigurácia GitLabu, kontrol, váh a harmonogramu.',
    pages: ['course_settings'],
    roles: ['teacher', 'admin'],
    autoPrompt: true,
    steps: [
      {
        title_en: 'Settings &mdash; your control panel',
        title_sk: 'Nastavenia &mdash; váš ovládací panel',
        body_en: 'Every change here applies to <strong>every team</strong> in the course. The page is split into thematic blocks &mdash; <em>Course info</em>, <em>GitLab integration &amp; webhooks</em>, <em>Compliance checks</em>, <em>Thresholds</em>, <em>Patterns</em>, <em>Semester &amp; weekly deadlines</em>, plus optional <em>AI analysis</em>. Save with <strong>Update settings</strong> at the bottom or <kbd>Ctrl</kbd>+<kbd>S</kbd>; every save is versioned.',
        body_sk: 'Každá zmena tu platí pre <strong>všetky tímy</strong> v predmete. Stránka je rozdelená do tematických blokov &mdash; <em>Informácie o predmete</em>, <em>GitLab integrácia a webhooky</em>, <em>Compliance kontroly</em>, <em>Prahy</em>, <em>Vzory</em>, <em>Semester a týždenné termíny</em>, plus voliteľná <em>AI analýza</em>. Uložíte tlačidlom <strong>Aktualizovať</strong> dolu alebo <kbd>Ctrl</kbd>+<kbd>S</kbd>; každé uloženie je verzované.',
      },
      {
        element: '.card:has(#course_code)',
        side: 'bottom',
        title_en: 'Course information',
        title_sk: 'Informácie o predmete',
        body_en: 'Code, name, academic year, semester and a free-text description. The <strong>code</strong> shows up in breadcrumbs, e-mails and exports &mdash; keep it short (e.g. <code>DevOps</code>, <code>ZSI</code>). The <strong>academic period</strong> is the term the course belongs to: it decides where the course and its students appear in every period selector, and changing it moves the official semester dates with it (dates you set yourself stay).',
        body_sk: 'Kód, názov, akademický rok, semester a voľný popis. <strong>Kód</strong> sa zobrazuje v breadcrumb, e-mailoch a exportoch &mdash; držte ho krátky (napr. <code>DevOps</code>, <code>ZSI</code>). <strong>Akademické obdobie</strong> určuje, kam predmet patrí: podľa neho sa predmet a jeho študenti zobrazia v každom výbere obdobia a jeho zmena posunie aj oficiálne dátumy semestra (dátumy, ktoré ste nastavili sami, zostanú).',
      },
      {
        element: '.card:has(#webhook_url_display)',
        side: 'bottom',
        title_en: 'GitLab integration &mdash; delivery URL',
        title_sk: 'GitLab integrácia &mdash; URL pre delivery',
        body_en: 'A single <strong>webhook URL</strong> handles all GitLab events for this course. Copy it once and paste it into every GitLab webhook you create (Group, Sub-group, or Project &rarr; Settings &rarr; Webhooks). Each webhook configuration below issues its own per-scope secret &mdash; the URL is shared, the secrets are not.',
        body_sk: 'Jedna <strong>webhook URL</strong> obsluhuje všetky GitLab eventy pre tento predmet. Skopírujte ju raz a vložte do každého GitLab webhooku (Skupina, Podskupina alebo Projekt &rarr; Nastavenia &rarr; Webhooky). Každá konfigurácia nižšie vystaví vlastné secret &mdash; URL je zdieľaná, secrety nie.',
      },
      {
        element: '.card:has(#webhookConfigsContainer)',
        side: 'top',
        title_en: 'Webhook configurations &mdash; per-scope secrets',
        title_sk: 'Webhook konfigurácie &mdash; secrety podľa scope',
        body_en: 'Define <strong>where GitPulse listens</strong>: a whole group, a sub-group, a list of project IDs, or the whole course. Each row owns its own secret with audit, last-delivery timestamp, and one-click rotation. Rotation gives a <strong>24-hour grace</strong> on the previous secret so GitLab has time to pick up the new value without dropping events.',
        body_sk: 'Definuje, <strong>kde GitPulse počúva</strong>: celá skupina, podskupina, zoznam project ID, alebo celý predmet. Každý riadok má vlastný secret s auditom, časom poslednej delivery a rotáciou jedným klikom. Rotácia má <strong>24-hodinový grace</strong> na predchádzajúci secret, aby GitLab stihol prevziať novú hodnotu bez straty eventov.',
      },
      {
        element: '.compliance-checks-card',
        side: 'top',
        title_en: 'Compliance checks &mdash; what counts as "done"',
        title_sk: 'Compliance kontroly &mdash; čo sa počíta ako "splnené"',
        body_en: 'Tick the rules you want enforced for every team. Built-ins cover commits (R01&ndash;R04), MRs (R05&ndash;R08), reviews (R09&ndash;R10) and CI/process (R11&ndash;R13); custom checks defined elsewhere appear at the bottom. The <strong>weight</strong> column tunes how much each check pulls the final score &mdash; the total is normalised on save so only ratios matter. The "Total weight" badge in the header turns red if your weights drift far from 1.0.',
        body_sk: 'Zaškrtnite pravidlá, ktoré chcete vynucovať pre každý tím. Vstavané pokrývajú commity (R01&ndash;R04), MRky (R05&ndash;R08), reviews (R09&ndash;R10) a CI/proces (R11&ndash;R13); vlastné kontroly sa zobrazia dolu. Stĺpec <strong>weight</strong> ladí, koľko každá kontrola ťahá výsledné skóre &mdash; súčet sa pri uložení normalizuje, takže záleží len na pomeroch. Badge "Total weight" v hlavičke sčervenie, ak sa váhy odklonia od 1.0.',
      },
      {
        element: '#weightPresets',
        side: 'bottom',
        title_en: 'Weight presets',
        title_sk: 'Predvoľby váh',
        body_en: 'One-click profiles &mdash; <em>Balanced</em>, <em>Process-heavy</em>, <em>Code-heavy</em>, etc. Picking a preset rewrites every weight in the table; you can still tweak individual rows afterwards. Useful as a starting point for new courses or when re-balancing mid-semester.',
        body_sk: 'Jednoklikové profily &mdash; <em>Vyvážený</em>, <em>Process-heavy</em>, <em>Code-heavy</em>, atď. Výber predvoľby prepíše každú váhu v tabuľke; jednotlivé riadky môžete potom doladiť. Vhodné ako východiskový bod pre nové predmety alebo pri re-balancovaní v polovici semestra.',
      },
      {
        element: '.card:has(#thresholdPreview)',
        side: 'top',
        title_en: 'Traffic-light thresholds',
        title_sk: 'Prahy semaforu',
        body_en: 'The <strong>Yellow</strong> and <strong>Green</strong> handles split the 0&ndash;100% compliance band into red / yellow / green. Below yellow = at risk, between yellow and green = on track, above green = excellent. The live preview bar updates as you drag the values &mdash; mirrors exactly what students see on their dashboard chips.',
        body_sk: 'Posuvníky <strong>Yellow</strong> a <strong>Green</strong> rozdelia pásmo 0&ndash;100% compliance na červenú / žltú / zelenú. Pod žltou = v ohrození, medzi žltou a zelenou = na ceste, nad zelenou = výborné. Náhľadový pruh sa aktualizuje pri ťahaní hodnôt &mdash; presne to, čo študent vidí ako chip na dashboarde.',
      },
      {
        element: '.card:has(input[name="branch_pattern"])',
        side: 'top',
        title_en: 'Patterns &mdash; naming conventions',
        title_sk: 'Vzory &mdash; konvencie pomenovania',
        body_en: '<strong>Branch regex</strong>, <strong>required MR sections</strong> and <strong>test-file globs</strong>. Leaving any field empty turns enforcement off &mdash; students are still <em>encouraged</em>, just not penalised. Tighten branch regex to e.g. <code>^issue-\\d+</code> for stricter naming, or list <code>## Description, ## Testing</code> to require those headings in every MR description.',
        body_sk: '<strong>Branch regex</strong>, <strong>požadované sekcie MR</strong> a <strong>globy test súborov</strong>. Prázdne pole vypne vynucovanie &mdash; študenti sú stále <em>nabádaní</em>, len nie penalizovaní. Sprísnite branch regex napr. na <code>^issue-\\d+</code>, alebo uveďte <code>## Description, ## Testing</code> pre povinné nadpisy v každom popise MR.',
      },
      {
        element: '.card:has(input[name="semester_start_date"])',
        side: 'top',
        title_en: 'Semester settings &mdash; your academic clock',
        title_sk: 'Semester &mdash; akademické hodiny',
        body_en: 'The dates follow the course\'s academic period - its official TUKE FEI dates - unless you set your own; <strong>Use the official TUKE dates</strong> puts them back, and a start date that falls in another term is pointed out. The <strong>start date</strong> drives every "Week N" label across dashboards, reports and student views. The <strong>end date</strong> + 14-day grace triggers auto-archive, which stops periodic jobs to save resources. Tick <em>Skip auto-archive</em> for evergreen demo or sandbox courses.',
        body_sk: 'Dátumy nasledujú akademické obdobie predmetu - jeho oficiálne dátumy TUKE FEI - kým nezadáte vlastné; <strong>Použiť oficiálne dátumy TUKE</strong> ich vráti a začiatok v inom období je vyznačený. <strong>Začiatok</strong> určuje každé "Week N" naprieč dashboardmi, reportami a študentskými pohľadmi. <strong>Koniec</strong> + 14 dní grace spustí auto-archiváciu, ktorá zastaví periodické joby kvôli šetreniu zdrojov. Zaškrtnite <em>Skip auto-archive</em> pre evergreen demo alebo sandbox.',
      },
      {
        element: '.card:has(textarea[name="weekly_deadlines"])',
        side: 'top',
        title_en: 'Weekly deadlines &amp; expected checks',
        title_sk: 'Týždenné termíny a očakávané kontroly',
        body_en: 'Define what is expected each week &mdash; e.g. <em>Week 5: R01&ndash;R05, R12</em>. This drives <strong>progressive evaluation</strong>: early weeks require fewer checks, later weeks add more. Optional <code>mr_deadline</code> and <code>merge_deadline</code> on a week create hard cut-offs (commits past these times don\'t count). The summary table shows the current schedule; expand <em>Edit JSON</em> to bulk-edit.',
        body_sk: 'Definujte očakávania na každý týždeň &mdash; napr. <em>Week 5: R01&ndash;R05, R12</em>. To pohonom pre <strong>progresívne hodnotenie</strong>: ranné týždne vyžadujú menej, neskoršie pridávajú. Voliteľné <code>mr_deadline</code> a <code>merge_deadline</code> v týždni vytvárajú tvrdé cut-off (neskoršie commity sa nepočítajú). Prehľadová tabuľka ukazuje aktuálne nastavenie; rozbaľte <em>Edit JSON</em> pre hromadnú úpravu.',
      },
      {
        element: '.settings-sticky-footer',
        side: 'top',
        title_en: 'Save &amp; rollback',
        title_sk: 'Uloženie a rollback',
        body_en: 'Click <strong>Update settings</strong> or hit <kbd>Ctrl</kbd>+<kbd>S</kbd>. Every save creates an audit-log entry &mdash; if a change breaks something, open the audit log and click <em>Restore</em> on a previous version to roll back instantly. <strong>Cancel</strong> takes you back to the course page without persisting anything.',
        body_sk: 'Stlačte <strong>Aktualizovať</strong> alebo <kbd>Ctrl</kbd>+<kbd>S</kbd>. Každé uloženie vytvorí záznam v audit logu &mdash; ak niečo pokazí, otvorte audit log a klikom na <em>Obnoviť</em> sa vrátite. <strong>Zrušiť</strong> vás vráti na stránku predmetu bez uloženia.',
      },
      {
        element: '.card:has(#llm_course_type)',
        side: 'top',
        title_en: 'AI analysis configuration (optional)',
        title_sk: 'AI analýza (voliteľné)',
        body_en: 'Pick a <strong>course-type preset</strong> (Default / ZSI / DevOps) to load a battle-tested LLM prompt, then expand <em>Analysis Prompt</em> to customise. Add <strong>resource URLs</strong> (assignments page, grading criteria, course site) &mdash; the AI fetches their content to give answers grounded in your course materials, not generic boilerplate.',
        body_sk: 'Vyberte <strong>preset typu predmetu</strong> (Default / ZSI / DevOps) a načítajte odskúšaný LLM prompt, potom rozbaľte <em>Analysis Prompt</em> a upravte. Pridajte <strong>resource URL</strong> (stránka zadaní, hodnotiace kritériá, web predmetu) &mdash; AI ich obsah natiahne a odpovede budú založené na vašich materiáloch, nie generické.',
      },
      {
        element: '.card:has(#btnExportFullConfig)',
        side: 'top',
        title_en: 'Full configuration export / import',
        title_sk: 'Export / import celej konfigurácie',
        body_en: 'One JSON file with <strong>everything</strong> &mdash; settings, compliance checks, custom checks and weekly deadlines. Perfect for cloning a tested setup into next semester, sharing between co-teachers, or version-controlling your course config in Git.',
        body_sk: 'Jeden JSON súbor s <strong>všetkým</strong> &mdash; nastaveniami, compliance kontrolami, vlastnými kontrolami a týždennými termínmi. Ideálne na klonovanie odskúšaného nastavenia do ďalšieho semestra, zdieľanie medzi vyučujúcimi, alebo verzionovanie konfigurácie v Gite.',
      },
      {
        element: '.card.danger-zone',
        side: 'top',
        title_en: 'Danger zone',
        title_sk: 'Danger zone',
        body_en: 'Three irreversible actions: <strong>Archive</strong> (hides from active lists, data preserved &mdash; safe), <strong>Clone</strong> (copies settings &amp; checks to a new academic year, no students), and <strong>Delete forever</strong> (purges all groups, students, projects and their compliance history). Delete is gated &mdash; you must archive first. All three live here so you can never trigger them by accident from elsewhere.',
        body_sk: 'Tri nezvratné akcie: <strong>Archive</strong> (skryje z aktívnych zoznamov, dáta zostanú &mdash; bezpečné), <strong>Clone</strong> (skopíruje nastavenia a kontroly do nového akademického roka, bez študentov) a <strong>Delete forever</strong> (zmaže všetky skupiny, študentov, projekty a ich históriu súladu). Delete je zamknuté &mdash; najprv musíte archivovať. Všetky tri žijú tu, aby ste ich nemohli omylom spustiť odinakiaľ.',
      },
    ],
  });

  // -- 4. COURSE ROSTER ----------------------------------------------
  reg({
    slug: 'course_roster_teacher',
    title_en: 'Roster tour',
    title_sk: 'Sprievodca zoznamom študentov',
    subtitle_en: 'Search, inspect and export the current roster.',
    subtitle_sk: 'Hľadanie, kontrola a export aktuálneho zoznamu.',
    pages: ['course_roster'],
    roles: ['teacher', 'admin'],
    autoPrompt: true,
    steps: [
      {
        title_en: 'Roster',
        title_sk: 'Zoznam',
        body_en: 'Every active student mirrored from GitLab for this course in one table. The table supports live filtering and multi-column sort (Shift-click headers for secondary keys). The chip next to each name shows their current group.',
        body_sk: 'Každý aktívny študent zrkadlený z GitLabu pre tento predmet v jednej tabuľke. Tabuľka podporuje živý filter a multi-column triedenie (Shift-klik na hlavičku pre druhý kľúč). Chip vedľa mena ukazuje aktuálnu skupinu.',
      },
      {
        element: '[data-tour~="roster-search"], #studentSearch',
        side: 'bottom',
        title_en: 'Live search',
        title_sk: 'Živé hľadanie',
        body_en: 'Filters as you type &mdash; matches name, email and team. Use <kbd>Esc</kbd> to clear. Search is fuzzy: <code>jhn smt</code> matches "John Smith". Results stay sorted in the column you picked.',
        body_sk: 'Filtruje počas písania &mdash; hľadá v mene, e-maile aj tíme. <kbd>Esc</kbd> vyčistí pole. Vyhľadávanie je fuzzy: <code>jhn smt</code> nájde "John Smith". Výsledky ostanú zoradené podľa zvoleného stĺpca.',
      },
      {
        element: '[data-tour~="export-csv"], #btnExportRoster',
        side: 'left',
        title_en: 'Export',
        title_sk: 'Export',
        body_en: 'Download the current roster as CSV &mdash; handy for offline grading, sharing with co-teachers, or archiving at semester-end. Columns include group, GitLab username, name, email and GitLab user ID.',
        body_sk: 'Stiahnite aktuálny zoznam ako CSV &mdash; užitočné pre offline hodnotenie, zdieľanie so spoluvyučujúcimi alebo archiváciu na konci semestra. Stĺpce zahŕňajú skupinu, GitLab používateľské meno, meno, e-mail a GitLab user ID.',
      },
    ],
  });

  // -- 5. COURSE TEACHERS --------------------------------------------
  reg({
    slug: 'course_teachers_teacher',
    title_en: 'Co-teachers tour',
    title_sk: 'Sprievodca spoluvyučujúcimi',
    pages: ['course_teachers'],
    roles: ['teacher', 'admin'],
    autoPrompt: true,
    steps: [
      {
        title_en: 'Co-teachers',
        title_sk: 'Spoluvyučujúci',
        body_en: 'This page lists every teacher who can grade and configure this course. The <strong>owner</strong> (gold badge) can transfer ownership; <strong>instructors</strong> (blue badge) have full grading and configuration rights but cannot delete the course or change ownership.',
        body_sk: 'Stránka zobrazuje všetkých učiteľov, ktorí môžu hodnotiť a konfigurovať tento predmet. <strong>Owner</strong> (zlatý odznak) môže preniesť vlastníctvo; <strong>inštruktori</strong> (modrý odznak) môžu robiť všetko okrem zmazania predmetu a zmeny vlastníctva.',
      },
      {
        element: '[data-tour~="add-teacher"], #btnAddTeacher',
        side: 'bottom',
        title_en: 'Add teacher',
        title_sk: 'Pridať učiteľa',
        body_en: 'Opens a dialog: search by name or username &mdash; the user must already have a GitPulse account (admins can pre-invite from <em>Administration &rarr; Users</em>) &mdash; pick their course role and add them.',
        body_sk: 'Otvorí dialóg: hľadajte podľa mena alebo prihlasovacieho mena &mdash; používateľ musí už mať účet v GitPulse (admini môžu pozvať cez <em>Administrácia &rarr; Používatelia</em>) &mdash; vyberte jeho rolu v predmete a pridajte ho.',
      },
      {
        element: '[data-tour~="teacher-row"], #courseTeachersTable',
        side: 'top',
        title_en: 'Manage a co-teacher',
        title_sk: 'Spravovať spoluvyučujúceho',
        body_en: 'Change a teacher&rsquo;s course role in the row&rsquo;s menu, or remove them with the trash button &mdash; either applies at once. Removing a teacher does not delete their existing feedback &mdash; their name remains on every note they wrote.',
        body_sk: 'Rolu učiteľa v predmete zmeníte v ponuke v jeho riadku, odstránite ho tlačidlom koša &mdash; obe zmeny platia hneď. Odstránenie učiteľa nezmaže jeho existujúcu spätnú väzbu &mdash; meno ostáva na každej poznámke, ktorú napísal.',
      },
    ],
  });

  // -- 5b. CLASSROOM ASSISTANT --------------------------------------
  reg({
    slug: 'course_assistant_teacher',
    title_en: 'Assistant tour',
    title_sk: 'Sprievodca asistentom',
    subtitle_en: 'A bot that reviews pushes and merge requests like a colleague.',
    subtitle_sk: 'Bot, ktorý ako kolega komentuje pushe a merge requesty.',
    pages: ['course_assistant'],
    roles: ['teacher', 'admin'],
    autoPrompt: true,
    steps: [
      {
        title_en: 'Classroom assistant',
        title_sk: 'Asistent cvičení',
        body_en: 'The assistant acts in GitLab like a colleague: it comments on pushes, plants a merge conflict to resolve and reviews the merge requests of an exercise. It is the only part of GitPulse that writes to GitLab, it does so under a bot account of the course, and nothing happens until you switch a tool on.',
        body_sk: 'Asistent sa v GitLabe správa ako kolega: komentuje pushe, pripraví konflikt na vyriešenie a robí review merge requestov z cvičenia. Je to jediná časť GitPulse, ktorá do GitLabu zapisuje, robí to pod bot účtom kurzu a nič sa nestane, kým nezapnete niektorý nástroj.',
      },
      {
        element: '[data-tour~="assistant-bot"]',
        side: 'bottom',
        title_en: 'Bot account',
        title_sk: 'Bot účet',
        body_en: 'Create a group access token in GitLab (Maintainer role, <code>api</code> scope) and connect it here. GitPulse checks it with GitLab and stores it encrypted. If GitLab stops accepting it, this page says so at the top.',
        body_sk: 'V GitLabe vytvorte prístupový token skupiny (rola Maintainer, rozsah <code>api</code>) a pripojte ho tu. GitPulse ho overí v GitLabe a uloží zašifrovaný. Ak ho GitLab prestane prijímať, stránka to povie navrchu.',
      },
      {
        element: '[data-tour~="assistant-tools"]',
        side: 'top',
        title_en: 'Tools',
        title_sk: 'Nástroje',
        body_en: 'Each tool is switched on separately and saved with <strong>Save changes</strong>. The review asks only for what the course grades: the branch rule (R02) and the description sections (R05) come from the course Settings.',
        body_sk: 'Každý nástroj sa zapína zvlášť a ukladá tlačidlom <strong>Uložiť zmeny</strong>. Review žiada len to, čo kurz hodnotí: pravidlo pre vetvy (R02) a sekcie popisu (R05) sa berú z Nastavení kurzu.',
      },
      {
        element: '[data-tour~="assistant-exercise"]',
        side: 'bottom',
        title_en: 'Prepare exercise',
        title_sk: 'Pripraviť cvičenie',
        body_en: 'Gives every student of the chosen projects a file and an issue. Running it again is safe: students who already have their issue are skipped, so it is also how a student added later gets one.',
        body_sk: 'Každému študentovi vybraných projektov pripraví súbor a tiket. Spustiť ho znova je bezpečné: študenti, ktorí tiket už majú, sa preskočia, takže takto dostane tiket aj študent pridaný neskôr.',
      },
      {
        element: '[data-tour~="assistant-activity"]',
        side: 'top',
        title_en: 'Assistant activity',
        title_sk: 'Aktivita asistenta',
        body_en: 'What the assistant did, newest first. Filter by tool, search by student, and follow the link to the comment, the merge request or the commit in GitLab.',
        body_sk: 'Čo asistent urobil, od najnovšieho. Filtrujte podľa nástroja, hľadajte podľa študenta a odkazom prejdite na komentár, merge request alebo commit v GitLabe.',
      },
    ],
  });

  // -- 6. COURSE ANALYTICS -------------------------------------------
  reg({
    slug: 'course_analytics_teacher',
    title_en: 'Analytics tour',
    title_sk: 'Sprievodca analytikou',
    subtitle_en: 'Charts of commits, MRs, reviews and compliance.',
    subtitle_sk: 'Grafy commitov, MRkov, reviews a compliance.',
    pages: ['course_analytics'],
    roles: ['teacher', 'admin'],
    autoPrompt: true,
    steps: [
      {
        title_en: 'Analytics',
        title_sk: 'Analytika',
        body_en: 'Visualises engagement and compliance across this course. All charts are clickable &mdash; pick any data point or bar to drill into the underlying weeks, teams or events. Hover any chart for the exact values, including a comparison against the course average.',
        body_sk: 'Vizualizuje aktivitu a compliance v tomto predmete. Všetky grafy sú interaktívne &mdash; klikom na bod či stĺpec drilujete do podkladových týždňov, tímov či udalostí. Hover ukazuje presné hodnoty vrátane porovnania s priemerom predmetu.',
      },
      {
        element: '#metricsGrid',
        side: 'bottom',
        title_en: 'KPI cards',
        title_sk: 'KPI karty',
        body_en: 'Top-level numbers for the whole course at a glance &mdash; total students, active teams, current pass-rate, average compliance and the at-risk count. Each card animates on update so changes after a refresh are obvious.',
        body_sk: 'Najvyššie čísla pre celý predmet &mdash; počet študentov, aktívne tímy, aktuálna pass-rate, priemerné compliance a počet at-risk. Karty sa po refreshi animáciou pri zmene.',
      },
      {
        element: '[data-tour~="chart-week"], #waBarChart, #weekChart, .chart-week',
        side: 'top',
        title_en: 'Weekly engagement',
        title_sk: 'Týždenná aktivita',
        body_en: 'Stacked bars per week: blue = commits, green = MRs, purple = reviews. Click a bar to filter the rest of the page to that week. The dotted line is the rolling 4-week average &mdash; useful for spotting trends past the noise.',
        body_sk: 'Skladané stĺpce po týždňoch: modrá = commity, zelená = MRky, fialová = reviews. Klikom na stĺpec sa zvyšok stránky filtruje na daný týždeň. Bodkovaná čiara je 4-týždeňový kľzavý priemer &mdash; užitočný na odhalenie trendu pri šume.',
      },
      {
        element: '#checklistCanvas, #complianceChart',
        side: 'top',
        title_en: 'Compliance breakdown',
        title_sk: 'Rozpis compliance',
        body_en: 'Doughnut/area chart of how the course-wide compliance score breaks down per category and rule family. Drops here usually correlate with deadline weeks &mdash; students rush, skip reviews, force-push.',
        body_sk: 'Plošný graf, ako sa compliance skóre celého predmetu rozdeľuje po kategóriách a rodinách pravidiel. Prepady tu zvyčajne korelujú s týždňami pred uzávierkou &mdash; študenti ponáhľajú, vynechávajú reviews, force-pushujú.',
      },
      {
        element: '#weekNavigator, #weekPills',
        side: 'top',
        title_en: 'Week navigator',
        title_sk: 'Navigácia po týždňoch',
        body_en: 'Pills for every academic week of the semester. Click any week to load the week-specific breakdown into the right pane &mdash; per-team activity, deadline compliance and the late/missing list.',
        body_sk: 'Pilulky pre každý akademický týždeň semestra. Klikom na týždeň sa do pravého panela načíta rozpis pre daný týždeň &mdash; aktivita tímu, dodržanie deadline a zoznam meškajúcich.',
      },
    ],
  });

  // -- 7. COURSE ACTIVITY --------------------------------------------
  reg({
    slug: 'course_activity_teacher',
    title_en: 'Activity monitor tour',
    title_sk: 'Sprievodca monitorom aktivity',
    pages: ['course_activity'],
    roles: ['teacher', 'admin'],
    autoPrompt: true,
    steps: [
      {
        title_en: 'Activity monitor',
        title_sk: 'Monitor aktivity',
        body_en: 'Live snapshot of CI/CD health and merge-request flow for every group in this course. Numbers refresh on every webhook delivery (commits, pipelines, MR open/merge) and are paginated for big cohorts.',
        body_sk: 'Živý prehľad zdravia CI/CD a tokov merge-requestov pre každý tím predmetu. Čísla sa obnovujú pri každom webhooku (commity, pipeline, MR open/merge) a pre veľké skupiny sú stránkované.',
      },
      {
        element: '.pipeline-overview-grid, #pipelineDoughnut',
        side: 'bottom',
        title_en: 'CI/CD health donut',
        title_sk: 'Donut zdravia CI/CD',
        body_en: 'Each project contributes its <em>latest</em> pipeline status to this donut. The big number in the middle is your overall pass rate. Without GitLab pipeline webhooks the counts only refresh when the next sync re-fetches a finished status.',
        body_sk: 'Každý projekt prispieva <em>posledným</em> stavom pipeline. Veľké číslo v strede je celková úspešnosť. Bez GitLab pipeline webhookov sa počty obnovia až pri ďalšom synchronizačnom behu.',
      },
      {
        element: '.pipeline-stats-compact, .stats-grid-5',
        side: 'top',
        title_en: 'Stat cards',
        title_sk: 'Štatistické karty',
        body_en: 'Counters for <strong>Passed</strong>, <strong>Failed</strong>, <strong>Running</strong>, <strong>Pending</strong> pipelines and <strong>Total Projects</strong>. A spike in Failed/Pending usually means a CI outage or a broken commit just landed - drill into the table below to find the team.',
        body_sk: 'Počítadlá pre <strong>Passed</strong>, <strong>Failed</strong>, <strong>Running</strong>, <strong>Pending</strong> pipeline a <strong>Total Projects</strong>. Skok vo Failed/Pending zvyčajne znamená výpadok CI alebo zlomený commit - kliknite do tabuľky nižšie a nájdite tím.',
      },
      {
        element: '.activity-grid table, .col-activity-group',
        side: 'top',
        title_en: 'Group activity table',
        title_sk: 'Tabuľka aktivity tímov',
        body_en: 'Per-team breakdown: number of projects, pipeline pass/fail bar, MR count and overall status pill. The pass-rate bar is colour-coded: green ≥ 80%, orange ≥ 50%, red below.',
        body_sk: 'Rozpis na tím: počet projektov, lišta pass/fail pipeline, počet MRiek a stavový chip. Pass-rate je farebne odlíšený: zelená ≥ 80%, oranžová ≥ 50%, červená pod.',
      },
      {
        element: '#groupActivityTable tbody a, .activity-grid tbody a[href*="/dashboard/teams/"]',
        side: 'right',
        title_en: 'Open a team',
        title_sk: 'Otvoriť tím',
        body_en: 'The team-name link in each row jumps to the full team page where you can run compliance checks, write feedback and watch the live event tail for that group only.',
        body_sk: 'Link s názvom tímu v každom riadku otvorí celú stránku tímu &mdash; spustíte compliance kontroly, napíšete spätnú väzbu a sledujete live stream udalostí len pre danú skupinu.',
      },
      {
        element: '#recentMrsTable tbody a[target="_blank"], .activity-grid tbody a[href*="/merge_requests/"]',
        side: 'left',
        title_en: 'Open MR in GitLab',
        title_sk: 'Otvoriť MRku v GitLabe',
        body_en: 'Each MR title links straight to GitLab in a new tab so you can comment, approve or request changes without leaving your flow. The status dot at the start of the row is colour-coded for an at-a-glance read.',
        body_sk: 'Každý titulok MRky odkazuje rovno na GitLab v novej karte, takže môžete komentovať, schváliť alebo vyžiadať zmeny bez opúšťania flow. Status bodka na začiatku riadku je farebne kódovaná pre rýchly pohľad.',
      },
      {
        element: '.activity-grid table:last-of-type, #recentMrsTablePaginationControls',
        side: 'top',
        title_en: 'Recent merge requests',
        title_sk: 'Posledné merge requesty',
        body_en: 'The newest MRs across the whole course, ordered by activity. Status dot tells you at a glance - blue = open, green = merged, red = closed. Title links straight to GitLab so you can comment without leaving your flow.',
        body_sk: 'Najnovšie MRky v celom predmete, zoradené podľa aktivity. Status bodka napovie hneď - modrá = open, zelená = merged, červená = closed. Názov linkuje rovno do GitLabu, aby ste mohli komentovať bez prepínania.',
      },
      {
        element: '#refresh-activity-btn, .course-actions-bar [data-action], .course-actions-bar button',
        side: 'bottom',
        title_en: 'Refresh',
        title_sk: 'Obnoviť',
        body_en: 'Force an immediate re-fetch from GitLab. Most data updates via webhook within ~1-2 seconds; use refresh only when you suspect a webhook was dropped or right after a manual GitLab change.',
        body_sk: 'Vynútite okamžité re-fetchnutie z GitLabu. Väčšina dát sa aktualizuje webhookom do ~1-2 sekúnd; refresh použite len ak tušíte zahodený webhook alebo po manuálnej zmene v GitLabe.',
      },
    ],
  });

  reg({
    slug: 'course_activity_student',
    title_en: 'Activity monitor (student view)',
    title_sk: 'Monitor aktivity (študent)',
    pages: ['course_activity'],
    roles: ['student'],
    autoPrompt: true,
    steps: [
      {
        title_en: 'Course activity',
        title_sk: 'Aktivita predmetu',
        body_en: 'Public dashboard for the whole course - a snapshot of how every team is doing in CI/CD and merge-request flow. Use it to spot reference solutions, see how active your peers are, and find which group is leading the pass-rate ranking.',
        body_sk: 'Verejný prehľad celého predmetu - snapshot, ako sa každému tímu darí v CI/CD a v MRkach. Slúži na hľadanie vzorových riešení, sledovanie aktivity rovesníkov a zistenie, ktorý tím vedie v pass-rate.',
      },
      {
        element: '.pipeline-overview-grid, #pipelineDoughnut',
        side: 'bottom',
        title_en: 'Pipeline pass rate',
        title_sk: 'Úspešnosť pipeline',
        body_en: 'Donut shows the overall pass rate across all course projects. Above 80% is healthy; below 50% something is fundamentally broken - usually a missing CI variable or a wrong test image.',
        body_sk: 'Donut ukazuje celkovú úspešnosť pipeline naprieč predmetom. Nad 80% je zdravé; pod 50% je niečo zásadne pokazené - zvyčajne chýbajúca CI premenná alebo zlý test image.',
      },
      {
        element: '.activity-grid table, .col-activity-group',
        side: 'top',
        title_en: 'Group ranking',
        title_sk: 'Rebríček tímov',
        body_en: 'Each row is a team. Find your group, compare your pass-rate bar with others, and click any team to see what they have been doing. Healthy teamwork > silent competition.',
        body_sk: 'Každý riadok je tím. Nájdite svoj, porovnajte svoju pass-rate lištu s ostatnými a klikom na tím uvidíte, čo robili. Zdravá spolupráca > tiché súperenie.',
      },
      {
        element: '.activity-grid table:last-of-type',
        side: 'top',
        title_en: 'Recent merge requests',
        title_sk: 'Posledné merge requesty',
        body_en: 'Newest MRs course-wide. Reading other teams\' MRs is one of the fastest ways to learn - see how they structure descriptions, what reviewers ask, and how merge conflicts get resolved.',
        body_sk: 'Najnovšie MRky v celom predmete. Čítanie cudzích MRiek je jeden z najrýchlejších spôsobov učenia - uvidíte, ako píšu popisy, čo žiadajú reviewers a ako riešia merge konflikty.',
      },
    ],
  });

})();
