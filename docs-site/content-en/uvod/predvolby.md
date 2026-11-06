---
title: "Personal preferences"
description: "Appearance, behaviour, language and time settings that belong to your account"
---
{{< details >}}
- For: Everyone
- Requires: Sign-in
{{< /details >}}
## Where to find them

Click your avatar in the top right and choose **Preferences**, or go straight
to `/dashboard/preferences`.

**Every role** has this page - student, teacher and admin alike. These are your
own settings: they change nothing for anyone else, and nobody else can see them.

## They belong to the account, not the browser

Every preference is stored against your account rather than in the browser.
Sign in on another machine or in another browser and they come with you. That
is why they live on the server and not in `localStorage`.

## Colour mode

Light, dark, or follow your system.

This is the **one** exception on the page: it applies the moment you press it
and saves itself - you do not need the *Save changes* button for it. It is the
same control that sits in your avatar menu, so there is exactly one way to
change the mode.

## Theme

The accent colour of the interface. The preview shows precisely what changes:
it tints the selected item in the left navigation. **Default** keeps the
standard blue.

## Diffs

The colours for removed and added lines in diff views - used by the student
profile when it shows code context, and by the `+`/`−` counters in the profile
header and the commit table.

Enter any hex colour as `#RRGGBB`, or click one of the suggested swatches.
**The preview above the fields is the real diff component**, not a picture, so
what you see is what you get. Clearing a field returns that colour to the
standard green/red.

## Behaviour

| Setting | What it does |
|---|---|
| Keyboard shortcuts | Turns on the search palette (`/`, `Ctrl+K`) and the other global shortcuts. Turning them off does not affect `Esc` - dialogs still close. |
| Layout width | **Fixed** caps content at 1280 pixels; **Fluid** spans the full width. |
| Homepage | Where `/dashboard/` lands you after signing in. Only pages **your role can actually open** are offered. |
| Rows per page | How many rows a table shows. It is a **default** - a choice made on a specific table still wins for that table. |
| Sidebar | Whether it starts collapsed. Applied only on a device where you have not collapsed it yourself. |

## Notifications

Which emails GitPulse sends you: **support tickets**, **courses** (assignment,
archival, reactivation) and **account** (role changes, reactivation).

Switching one off stops the mail **on the server** - it is not merely hidden
from you. The welcome message deliberately has no switch: it is sent before you
have ever seen this page.

## Localization

**Language** applies from your next page load. *System default* hands the
choice back to your browser.

**First day of the week** changes every date picker in the app.

## Time preferences

**Relative times** read as "30 minutes ago". Turn them off to see exact
timestamps everywhere. Either way, hovering a time still shows the canonical
UTC value.

**Time format** switches between 24-hour (`14:34`) and 12-hour (`2:34 PM`).

## Saving

Everything except the colour mode is saved together with **Save changes**.

**Restore defaults** only fills the form back in - nothing is written until you
save, so you can still change your mind.

{{< alert type="note" >}}
If you are unsure what a setting does, run the guided tour:
avatar → **Take a tour**. It walks through every section of this page.
{{< /alert >}}
