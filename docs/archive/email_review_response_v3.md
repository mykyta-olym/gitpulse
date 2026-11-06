# E-mail: Odpoveď na video recenziu - aktualizácia (v4)

**Od:** Bc. Mykyta Olym  
**Komu:** Ing. Sergej Chodarev, PhD.  
**Predmet:** GitPulse - aktualizácia stavu po video recenzii

---

Dobrý deň, pán inžinier,

posielam aktualizovaný prehľad stavu aplikácie GitPulse. Od poslednej správy boli realizované ďalšie zmeny a vylepšenia na základe Vašich pripomienok z video recenzie.

Aplikácia beží na adrese: **https://gitpulse.kpi.fei.tuke.sk**  
Dokumentácia: **https://gitpulse.kpi.fei.tuke.sk/docs/**

---

## Čo sa zmenilo od poslednej správy

### Systém e-mailových notifikácií

Implementovaný kompletný systém e-mailových notifikácií cez SMTP. Notifikácie sa odosielajú automaticky pri nasledujúcich udalostiach:

- **Support tikety** - potvrdenie vytvorenia tiketu, nový komentár, zmena stavu, priradenie tiketu
- **Správa používateľov** - zmena roly, deaktivácia/reaktivácia účtu
- **Správa kurzov** - priradenie/odobratie učiteľa z kurzu, archivácia/reaktivácia kurzu

Každý e-mail obsahuje:
- Štylizovaný HTML s GitHub-dark témou a GitPulse brandingom
- Priamy odkaz (CTA tlačidlo) na relevantný tiket alebo stránku
- Metadáta (predmet, kategória, kto vykonal akciu)
- Avatar odosielateľa (ak je dostupný)
- Aj plain-text verzia pre klientov bez HTML

E-maily sa neodosielajú samému sebe - ak prihásený používateľ pridá komentár, nedostane notifikáciu o vlastnom komentári.

### Vyhľadávanie e-mailov študentov - Arena KPI API

Na základe komunikácie s p. Gurbalom bola integrovaná služba **Arena KPI** (`arena.kpi.fei.tuke.sk/emails`), ktorá slúži ako fallback pre získavanie e-mailových adries študentov, ktorých GitLab profil má nastavenú e-mailovú adresu ako súkromnú.

Proces vyhľadávania e-mailu:
1. Najprv sa pokúsi získať e-mail z GitLab API (verejný profil)
2. Ak nie je dostupný -> dotaz na Arena API podľa GitLab username
3. Arena vráti e-mail + LDAP identitu (extern_uid)

Výsledky sú kešované v pamäti worker procesu pre optimalizáciu.

### SSE - Real-time aktualizácie tiketov

Support tikety teraz podporujú **Server-Sent Events (SSE)** pre živé aktualizácie:
- Nové komentáre sa zobrazujú okamžite bez obnovenia stránky
- Zmeny stavu, priority, kategórie a priradenia sa aktualizujú v reálnom čase
- Časová pečiatka "Last updated" v bočnom paneli sa aktualizuje zo servera pri každej zmene
- Vizuálny indikátor pripojenia (zelená bodka = pripojené, sivá = odpojené)

### Skeleton loaders pre všetky stránky

Kompletné skeleton loaders boli implementované pre:
- **Zoznam tiketov** - hlavička, vyhľadávanie, 3 filtre, tabuľka 8 stĺpcov × 6 riadkov, stránkovanie
- **Detail tiketu** - meta riadok, účastníci, vlákno s komentármi (originál + 2 komentáre + formulár odpovede), bočný panel (Details, Assignee, Timeline)

Skeleton loadery sa zobrazujú okamžite pri navigácii a nahrádzajú sa skutočným obsahom cez HTMX lazy loading.

### Ďalšie opravy

- **Duplikácia e-mailov** - implementovaná trojitá ochrana (revízia frontendu, debounce, dedup guard na serveri)
- **Oprávnenia komentárov** - komentovať tikety môžu len administrátori alebo priradený učiteľ
- **Session security** - vylepšenie overovania relácie (user-agent fingerprint ako warning, nie hard reject)
- **Chyba admin stránky** - opravený JavaScript crash (premenná `const` -> `let`)
- **Markdown editor** - prepísaný renderMarkdown() parser pre stabilitu

---

## Aktuálny stav všetkých pripomienok

### 1. Duplikácia v navigácii (tlačidlá "Nový kurz" a "Import z GitLabu")

**Stav: Vyriešené.**

Vymenil som starý panel, na ktorom bola duplikácia, za nový s Quick Access - Groups, Subgroups and Projects.

---

### 2. Záložky kurzu vyzerajú ako taby, ale navigujú na inú stránku

**Stav: Otvorené - zámerné architektonické rozhodnutie.**

Záložky vizuálne vyzerajú ako taby, ale v skutočnosti navigujú na samostatné stránky. Dostupné záložky (dynamicky podľa role a feature flagov):

- **Prehľad** (Overview) - vždy viditeľná
- **Nastavenia** (Settings) - len pre vlastníkov/adminov
- **Aktivita** (Activity) - vždy viditeľná
- **Roster** - len pre vlastníkov/adminov, ak je zapnutý `FEATURE_ROSTER_IMPORT`
- **Analytika** (Analytics) - len pre vlastníkov/adminov, ak je zapnutý `FEATURE_PILOT_TELEMETRY`
- **Inštruktori** (Instructors) - len pre vlastníkov/adminov

Dôvod server-side navigácie: aplikácia je server-rendered (Jinja2 + HTMX). Každá sekcia kurzu obsahuje veľké množstvo dát (roster so stovkami študentov, komplexné nastavenia), a preto boli navrhnuté ako samostatné stránky so samostatným načítaním dát.

---

### 3. Breadcrumbs (omrvinky) - zbytočné na jednoduchých stránkach

**Stav: Implementované s hierarchiou.**

Breadcrumbs zobrazujú cestu: Dashboard -> Kód kurzu -> Tím -> Aktuálna stránka. Na vnorených stránkach (kurz -> skupina -> študent -> projekt) pomáhajú s orientáciou. Na jednoduchých stránkach (napr. hlavný dashboard) je breadcrumb len "Dashboard" - minimálny vizuálny dopad.

---

### 4. Routing - prečo je URL kurzu len ID a nie kód kurzu

**Stav: Otvorené - technický dôvod.**

URL adresy kurzu používajú interný ID (`/courses/5`) namiesto kódu kurzu (`/courses/DEVOPS-2025`). Dôvod: kód kurzu nie je unikátny naprieč semestrami a akademickými rokmi. Rovnaký kurz "DEVOPS" existuje pre 2024/2025 aj 2025/2026. Interný ID zaručuje jednoznačnosť. Breadcrumbs a hlavička stránky ale vždy zobrazujú kód kurzu a akademický rok, takže používateľ vie, kde sa nachádza.

---

### 5. Stránkovanie - predvolene málo záznamov

**Stav: Vyriešené.**

Predvolená veľkosť stránky bola zmenená na 50 záznamov (pôvodne 10). K dispozícii sú aj možnosti 25, 50, 100 a "všetko". Na stránkach s menšími tabuľkami (admin, roster) sú predvolené hodnoty optimalizované individuálne (20-25).

---

### 6. Nejasné statusy / semafory - čo znamená zelená, žltá, červená

**Stav: Vyriešené.**

Semafory (zelený / žltý / červený) majú definovaný makro `traffic_light()` s tooltipy: Green = "All checks passing", Yellow = "Some issues", Red = "Critical issues", Gray = "No data". Na dashboardových kartách kurzov je nad stavom tooltip s počtom ohrozených skupín.

---

### 7. Technické informácie - ID projektu, cesta, vetva, hash viditeľné

**Stav: Vyriešené.**

Technické údaje (interné ID, GitLab cesty, haše) boli presunuté do admin-only pohľadov alebo tooltipov. Používateľ vidí len odkaz na GitLab projekt a názov/meno.

---

### 8. Filtrovanie členov tímu - zobrazujú sa nerelevantní členovia

**Stav: Vyriešené.**

Na stránke skupiny a projektu je filter s kategóriami:
- **Direct** (priami členovia) - predvolene zapnutý
- **Inherited** (zdedení z nadradenej skupiny) - predvolene vypnutý
- **Instructors** - predvolene vypnutý
- **Excluded** (manuálne vylúčení) - predvolene vypnutý

Stav filtra sa ukladá do `localStorage` pre každú stránku zvlášť (reset tlačidlo obnoví predvolené). Učiteľ tak vidí len priamych členov tímu bez šumu z inherited a inštruktorských účtov.

Navyše, správa inštruktorov kurzu má samostatnú stránku (záložka "Instructors" v detaile kurzu) s GitLab-style rozhraním: typeahead vyhľadávanie používateľov, priradenie rolí (Instructor / Course Owner), ochrana posledného vlastníka a sledovanie neuložených zmien.

---

### 9. Detekcia commitov z webového editora GitLabu

**Stav: Vyriešené - kompletne implementované ako R13.**

Compliance kontrola **R13 - Commit Quality** detekuje commity vytvorené cez webový editor GitLabu. Rozpoznávané vzory:
- `Update/Create/Delete/Add/Upload/Rename/Replace <súbor>`
- `Apply N suggestion(s)`

Konfigurovateľný parameter `max_web_editor_ratio` - ak je pomer web editorových commitov vyšší ako nastavený limit (predvolene 30 %), kontrola zlyhá. V kurzovej konfigurácii DevOps je nastavený na 5 %, v ZSI na 4 %.

---

### 10. Merge request - chýbajú podrobnosti (source/target branch, kto mergol)

**Stav: Vyriešené.**

V detaile študenta sa zobrazujú merge requesty so:
- Stav (MERGED / OPENED / CLOSED) - farebný badge
- Názov vetvy (branch name)
- **Compliance odznaky**: Issue Link, Tests, Branch OK, Template, Approvals (počet/požadované)
- **Pipeline status**: SUCCESS / FAILED / RUNNING
- **Rozšírený pohľad**: kliknutím sa zobrazí kompletný diff so štatistikami zmien, súbormi (nové/zmazané) a diff hunkmi

Zdrojová a cieľová vetva sú dostupné v rozšírenom pohľade.

---

### 11. Tabuľky - roztiahnutie na celú šírku na veľkých obrazovkách

**Stav: Vyriešené.**

Stránky s veľkými tabuľkami (roster, compliance, zoznam MR) využívajú fluid layout. Stĺpce používajú percentuálne šírky cez `<colgroup>`, takže tabuľky sa prispôsobujú šírke monitora. Responsívne breakpointy na 768px a 900px.

---

### 12. Formuláre spätnej väzby - nie je vidieť v rozhraní

**Stav: Vyriešené.**

Spätná väzba je riešená dvoma spôsobmi:

1. **Odkaz na Google Forms** - na hlavnom dashboarde v bočnom paneli "Feedback & suggestions" je priamy odkaz na Google formulár (`forms.gle/6M56k2ELZYKVxxWp6`). Tento odkaz je vždy viditeľný pre všetkých prihlásených používateľov.

2. **Vlastný modul spätnej väzby** - GitPulse má aj zabudovaný modul (`/dashboard/feedback`), ktorý ponúka:
   - **Previazanie s kurzom** - formulár je automaticky viazaný na konkrétny kurz a semester
   - **Identifikácia respondenta** - odpovede sú priradené k prihlásenému používateľovi
   - **Integrované výsledky** - učiteľ vidí odpovede priamo v dashboarde
   - **7 typov otázok**: rating (hviezdy), škála (radio), boolean (áno/nie), text, textarea, select, multiselect
   - **E-mailová notifikácia** - pri novom feedbacku je možné odoslať e-mail učiteľovi (keď je zapnuté SMTP)
   - Navigácia: položka **Feedback** v bočnej lište, učiteľ má navyše **Feedback Results** a **Feedback Forms**

---

### 13. Import študentov - nie je jasné, ako funguje

**Stav: Implementované dvoma cestami.**

1. **Automatická synchronizácia z GitLabu** (predvolene zapnutá): Systém automaticky sťahuje členov z GitLab skupín cez API. Rozlišuje: priami členovia, zdedení, inštruktori. Zmeny sú auditované v tabuľke `membership_changes`. Pri synchronizácii sa automaticky vyhľadáva e-mail cez GitLab API + fallback na **Arena KPI API** (viď vyššie).

2. **CSV import** (za feature flagom `FEATURE_ROSTER_IMPORT`, momentálne vypnutý): Manuálny upload CSV so stĺpcami `gitlab_username`, `full_name`, `email`, `group`.

V praxi je CSV import nepotrebný - automatická synchronizácia cez `membership_sync` scheduled job je dostatočná. Preto je vypnutý.

---

### 14. Tlačidlá bez vysvetlenia - čo robia "Otočiť tajný kľúč", "Odpojiť projekt"

**Stav: Vyriešené.**

Administrátorské akcie (rotácia webhook tokenu, odpojenie projektu) sú chránené podmienkou `is_admin` - učitelia tieto tlačidlá nevidia. Všetky akčné tlačidlá majú tooltips s vysvetlením, čo akcia robí.

Dialóg "Prepojiť projekt" má auto-fill - stačí vložiť GitLab URL a polia sa automaticky vyplnia.

---

### 15. Timeline - príliš zložitý pohľad

**Stav: Odstránené.**

Bolo úplne odstránené, pretože bolo nepotrebné.

---

### 16. Loading animácie - prázdne stránky pri načítavaní

**Stav: Vyriešené.**

Implementované dva typy loading animácií:
- **Spinner** (SVG, veľkosti sm/md/lg/xl) - pre inline stavy, tlačidlá, statusy
- **Skeleton loaders** - pre celé stránky s pulse animáciou, presne kopírujúce rozloženie skutočného obsahu (1:1 layout match)

HTMX lazy loading zobrazuje skeleton placeholder, kým sa dáta načítajú. Skeleton loadery sú implementované pre:
- Dashboard hlavnú stránku
- Zoznam support tiketov (vyhľadávanie, filtre, 8-stĺpcová tabuľka, stránkovanie)
- Detail support tiketu (meta bar, účastníci, vlákno komentárov, reply formulár, bočný panel s Details/Assignee/Timeline)
- Stránky kurzov a rozvrhy

---

### 17. Header - zbytočné informácie a duplicitné odkazy

**Stav: Vyriešené.**

Header zobrazuje:
- **Akademický rok** (napr. 2025/2026) s ikonou kalendára
- **Živé hodiny** s dátumom a časom
- **Vyhľadávací príkaz** (klávesová skratka `/`) - command palette štýl
- **Odkaz na dokumentáciu**
- **Profil menu**: Dashboard, System status, GitLab, Documentation, Sign out

Duplicitný odkaz na Help bol odstránený. Profilové menu zobrazuje avatar, meno a rolu.

---

## Vypnuté funkcie

Pre zjednodušenie rozhrania sú vypnuté funkcie, ktoré nie sú potrebné pre bežné používanie:

| Funkcia | Prečo vypnutá |
|---------|---------------|
| CSV Import (FEATURE_ROSTER_IMPORT) | Študenti sa synchronizujú automaticky z GitLabu (membership_sync job) |
| LLM Suggestions (FEATURE_LLM_SUGGESTIONS) | Vyžaduje API kľúč |

Každú funkciu je možné zapnúť jedným parametrom v konfigurácii.

---

## Konfiguračné údaje, ktoré potrebujem

Ak by ste chceli, aby systém pracoval s Vašimi prístupmi, potreboval by som:

### 1. GitLab Personal Access Token
Cesta: https://gitlab.example.com/-/user_settings/personal_access_tokens
**Scopes:** `read_api`, `read_user`
Na čítanie projektov, členov, MR, issues a pipeline stavov.

### 2. GitLab OAuth aplikácia (pre prihlasovanie cez GitLab)
Admin Area -> Applications -> New Application
- **Redirect URI:** `https://gitpulse.kpi.fei.tuke.sk/dashboard/oauth/callback`
- **Scopes:** `read_user`, `read_api`
- Potrebujem: **Application ID** a **Secret**

### 3. Zoznamy používateľov
- GitLab username-y **učiteľov**
- GitLab username-y **administrátorov**
- *(Voliteľne)* ID alebo cesty GitLab skupín, ktorých členovia majú automaticky rolu učiteľa

### 4. Arena KPI - API token pre e-maily študentov
Na základe komunikácie s p. Gurbalom ohľadom Arena API - systém už využíva endpoint `arena.kpi.fei.tuke.sk/emails/{username}` na vyhľadávanie e-mailových adries študentov, ktorých GitLab profil má súkromný e-mail.

Ak je API chránené autorizáciou, potreboval by som:
- **Bearer token** pre Arena API

Bez tokenu systém funguje, ale arena lookup môže vracať prázdne odpovede pre chránené endpointy.

### 5. SMTP nastavenia (pre e-mailové notifikácie)
Systém podporuje odosielanie e-mailov cez SMTP (notifikácie o tiketoch, zmeny rolí, správa kurzov). Momentálne je nakonfigurovaný s testovacím účtom. Ak by ste chceli používať univerzitný mailserver:
- **SMTP server** a **port** (napr. `smtp.tuke.sk:587`)
- **Prihlasovacie údaje** (username + heslo), ak je potrebná autentifikácia
- **From adresa** (napr. `gitpulse@kpi.fei.tuke.sk`)

Alternatívne je možné ponechať aktuálnu konfiguráciu s Gmailom.

### 6. LLM / AI analýza (voliteľné)
Ak by ste chceli AI analýzu MR:
- Poskytovateľ + API kľúč + model (napr. `gpt-4o-mini`)

---

Všetky údaje stačí poslať textom. Konfiguráciu nastavím ja.

S pozdravom,  
Bc. Mykyta Olym
