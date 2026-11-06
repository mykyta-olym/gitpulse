/* ------------------------------------------------------------------
 *  50-preferences.js - the Preferences page tour
 *
 *  Split per page like the other content modules; the engine
 *  (00-engine.js) comes earlier in the bundle.
 *
 *  Offered to EVERY role: these are the reader's own settings, and a
 *  student tunes their clock exactly the way an admin does.
 * ------------------------------------------------------------------ */
(() => {
  'use strict';

  if (!window.GP?.tour) {
    console.warn('[tours/50-preferences.js] tour engine not loaded - content not registered');
    return;
  }
  const reg = window.GP.tour.register;

  reg({
    slug: 'preferences',
    title_en: 'Preferences',
    title_sk: 'Predvoľby',
    pages: ['preferences'],
    roles: ['student', 'teacher', 'admin'],
    // Not auto-prompted: the reader came here on purpose to change one thing,
    // and a tour that opens over the control they were reaching for is an
    // interruption rather than help. Available from "Take a tour".
    autoPrompt: false,
    steps: [
      {
        title_en: 'Your preferences',
        title_sk: 'Vaše predvoľby',
        body_en:
          'Everything here belongs to your account, not to this browser &mdash; sign in anywhere and these settings come with you. Nothing on this page affects anyone else.',
        body_sk:
          'Všetko tu patrí vášmu účtu, nie tomuto prehliadaču &mdash; prihláste sa kdekoľvek a tieto nastavenia idú s vami. Nič na tejto stránke neovplyvní ostatných.',
      },
      {
        element: '[data-tour~="preferences-mode"]',
        side: 'bottom',
        title_en: 'Colour mode',
        title_sk: 'Farebný režim',
        body_en:
          'Light, dark, or follow your system. This one is the exception on the page: it applies the moment you press it and saves itself &mdash; you do not need the Save button for it. It is the same control that sits in your avatar menu.',
        body_sk:
          'Svetlý, tmavý, alebo podľa systému. Toto je výnimka na tejto stránke: použije sa okamžite po stlačení a uloží sa samo &mdash; tlačidlo Uložiť naň nepotrebujete. Je to ten istý ovládač, ktorý máte v menu pod avatarom.',
      },
      {
        element: '[data-tour~="preferences-accent"]',
        side: 'bottom',
        title_en: 'Accent colour',
        title_sk: 'Akcentová farba',
        body_en:
          'Tints the selected item in the left navigation. <strong>Default</strong> keeps the standard blue.',
        body_sk:
          'Zafarbí vybranú položku v ľavej navigácii. <strong>Predvolená</strong> ponechá štandardnú modrú.',
      },
      {
        element: '[data-tour~="preferences-syntax"]',
        side: 'top',
        title_en: 'Syntax highlighting',
        title_sk: 'Zvýrazňovanie syntaxe',
        body_en:
          'The palette used for highlighted code blocks. Each swatch is a live sample rendered '
          + 'through the scheme it offers, so what you see is what a code block will look like.',
        body_sk:
          'Paleta pre zvýraznené bloky kódu. Každá ukážka je živá vzorka vykreslená priamo '
          + 'schémou, ktorú ponúka, takže vidíte presne to, ako bude blok kódu vyzerať.',
      },
      {
        element: '[data-tour~="preferences-diffs"]',
        side: 'top',
        title_en: 'Diff colours',
        title_sk: 'Farby rozdielov',
        body_en:
          'The colours used for removed and added lines wherever code is compared &mdash; the student profile shows them, and so do the <code>+</code>/<code>&minus;</code> counters. The preview above the fields is the <strong>real</strong> diff component, so what you see is what you get. Leave a field empty to keep the standard green and red.',
        body_sk:
          'Farby odstránených a pridaných riadkov všade, kde sa porovnáva kód &mdash; vidíte ich v profile študenta aj pri počítadlách <code>+</code>/<code>&minus;</code>. Náhľad nad poliami je <strong>skutočný</strong> komponent rozdielov, takže vidíte presne to, čo dostanete. Prázdne pole ponechá štandardnú zelenú a červenú.',
      },
      {
        element: '[data-tour~="preferences-behavior"]',
        side: 'top',
        title_en: 'Behaviour',
        title_sk: 'Správanie',
        body_en:
          'Turn keyboard shortcuts on or off, let content span the full width instead of a fixed column, and choose which page you land on after signing in &mdash; only pages your role can actually open are offered. The last two are GitPulse&rsquo;s own: how many rows a table shows and whether the sidebar starts collapsed. Both are a <strong>default</strong> &mdash; a choice you make on a specific table, or on this device, still wins.',
        body_sk:
          'Zapnite alebo vypnite klávesové skratky, nechajte obsah roztiahnuť sa na celú šírku a vyberte stránku, na ktorú sa dostanete po prihlásení &mdash; ponúkajú sa len tie, ktoré vaša rola dokáže otvoriť. Posledné dve sú vlastné GitPulse: koľko riadkov ukazuje tabuľka a či sa bočný panel načíta zbalený. Obe sú <strong>predvoľba</strong> &mdash; voľba v konkrétnej tabuľke alebo na tomto zariadení má naďalej prednosť.',
      },
      {
        element: '[data-tour~="preferences-localization"]',
        side: 'top',
        title_en: 'Language and region',
        title_sk: 'Jazyk a región',
        body_en:
          'Language applies from your next page load. <strong>System default</strong> hands the choice back to your browser. The first day of the week changes every date picker in the app.',
        body_sk:
          'Jazyk sa uplatní od ďalšieho načítania stránky. <strong>Predvolené systémom</strong> vráti voľbu vášmu prehliadaču. Prvý deň týždňa zmení každý výber dátumu v aplikácii.',
      },
      {
        element: '[data-tour~="preferences-notifications"]',
        side: 'top',
        title_en: 'Notifications',
        title_sk: 'Notifikácie',
        body_en:
          'Which emails GitPulse sends you. Switching one off stops the mail on the <strong>server</strong> &mdash; it is not merely hidden from you. The welcome message has no switch: it is sent before you have ever seen this page.',
        body_sk:
          'Ktoré e-maily vám GitPulse posiela. Vypnutie zastaví e-mail na <strong>serveri</strong> &mdash; nie je len skrytý. Uvítacia správa prepínač nemá: posiela sa skôr, než túto stránku vôbec uvidíte.',
      },
      {
        element: '[data-tour~="preferences-time"]',
        side: 'top',
        title_en: 'Dates and times',
        title_sk: 'Dátumy a časy',
        body_en:
          'Relative times read as &ldquo;30 minutes ago&rdquo;; turn them off to see exact timestamps everywhere. Either way, hovering a time still shows the canonical UTC value.',
        body_sk:
          'Relatívne časy sa čítajú ako &bdquo;pred 30 minútami&ldquo;; vypnite ich, ak chcete všade presné časové značky. Tak či tak, po prejdení myšou nad časom stále uvidíte kanonickú UTC hodnotu.',
      },
      {
        element: '[data-tour~="preferences-actions"]',
        side: 'top',
        title_en: 'Saving',
        title_sk: 'Ukladanie',
        body_en:
          'Everything except the colour mode is saved together with <strong>Save changes</strong>. <strong>Restore defaults</strong> only fills the form back in &mdash; nothing is written until you save, so you can still change your mind.',
        body_sk:
          'Všetko okrem farebného režimu sa ukladá naraz tlačidlom <strong>Uložiť zmeny</strong>. <strong>Obnoviť predvolené</strong> iba vyplní formulár späť &mdash; nič sa nezapíše, kým neuložíte, takže si to stále môžete rozmyslieť.',
      },
    ],
  });
})();
