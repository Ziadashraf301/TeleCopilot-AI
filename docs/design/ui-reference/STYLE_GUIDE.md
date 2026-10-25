# UI Style Guide (from the reference screenshot)

Reference: Figma community "Chat UI" (https://www.figma.com/community/file/1057195320253196766/chat-ui), screenshot
shared by Ziad on 2026-10-25. Save it here as `reference-chat-ui.png`. Colour codes below are **estimated from the
screenshot**; confirm them against the Figma file if possible.

## Direction
Calm, light, professional work tool. Keep the reference's colours, rounded white cards on a soft blue canvas, and its
three-column chat layout. **Drop** the cartoon avatars, emojis and anything that looks like a chatbot/robot. Use
initials avatars (or customer photos if real), simple line icons, and dense but readable information for a busy CSR.

## Layout (mapped from the reference to TeleCopilot)
| Reference | TeleCopilot |
|---|---|
| Left sidebar: logo, Dashboard, Product, Order, Chat, Document, Setting, Logout; active item = blue text + blue left bar; red count badge | Sidebar: Inbox, Customers, Tickets, Knowledge base, Reports, Settings, Logout; status (Available / Busy / Break) at the top; red badges for waiting conversations |
| Top bar: page title, primary "+ Chat" button, bell, user avatar + name | Page title, primary "+ New ticket", notifications, CSR name + status |
| Column 1: "Inbox" + "2 New" pill, search, conversation cards (name, role, preview, time); selected card = solid blue with white text | Queue: channel icon (WhatsApp / call / web / email), customer name, line/plan, last message preview, waiting time / SLA timer; selected = solid blue |
| Column 2: header (name, role, ⋮), date separators, incoming bubble with blue outline, outgoing bubble filled light blue, voice-note player with waveform, composer with attach / send | Conversation: same bubbles; voice notes with waveform **plus transcript under it**; composer where the copilot's suggested reply is inserted for the CSR to edit and send |
| Column 3: profile card (large avatar, name, role, rating) + list "Lorem ipsum / See all" with company rows and times | **Customer 360 + Copilot**: customer card (name, number, plan, balance, area outage status), recent tickets list; below it, tabs **Copilot** (intent, next action, suggested reply, citations) and **Ticket** (form, disposition) |

## Colours (estimated)
| Token | Hex | Use |
|---|---|---|
| `primary` | `#1E6FDB` | Primary buttons, selected list item, active nav, send button, links |
| `primary-soft` | `#DCE9FB` | Outgoing bubble fill, pills ("2 New"), hover |
| `canvas` | `#D9E8FB` | App background behind cards |
| `surface` | `#FFFFFF` | Cards, sidebar, panels |
| `border` | `#E3EAF3` | Card and input borders, separators |
| `text` | `#2B3440` | Main text |
| `text-muted` | `#8A94A3` | Roles, previews, timestamps |
| `danger` | `#E5484D` | Badges, SLA breach |
| `success` | `#2E9E5B` | Available status, resolved |
| `warning` | `#E8A23A` | SLA at risk |
Dark mode: derive from the same tokens (dark navy canvas, slate surfaces); not required for M1.

## Typography
- Latin: a clean sans (Inter or similar). Arabic: a matching readable Arabic sans (e.g. IBM Plex Sans Arabic / Cairo / Noto Sans Arabic). Check download size.
- Sizes: page title 22–24 px semibold; names 14–15 px medium; body 13–14 px; meta 11–12 px muted.

## Shape and spacing
- Cards: radius 12–16 px, no heavy shadows (a 1 px border or a very soft shadow), 16–24 px padding.
- Buttons and inputs: radius 8–10 px; search input fully rounded.
- 8 px spacing grid; columns separated by 16–24 px of canvas.

## Bilingual: Arabic + English (required)
- The whole UI ships in **both Arabic and English**: every label, button, menu, message, error, empty state, date and
  number format. No hard-coded UI strings: all text comes from translation files (`ar.json`, `en.json`).
- Language switch in the top bar; the choice is saved per CSR (default from the CSR profile).
- **Arabic = full RTL mirroring**: sidebar on the right, columns reversed, icons with direction (arrows, send) flipped,
  text right-aligned. **English = LTR.** Use logical CSS properties (start/end) so one layout serves both.
- Content stays in its own language whatever the UI language: a customer's Franco or English message is shown as
  written, with per-message text direction (`dir="auto"`); phone numbers, IDs and amounts are always LTR.
- Arabic and Latin fonts are paired so mixed text looks consistent; Arabic body text gets slightly larger line height.
- A check in CI or tests fails when a key exists in one language file but not the other.

## UX rules for CSRs
- Everything for the current customer visible without scrolling on a 1366×768 laptop.
- Keyboard shortcuts: next conversation, insert suggestion, send, open ticket.
- Copilot suggestions are clearly marked as suggestions (subtle label, not a robot icon) and are never sent without a CSR action.
- Full Arabic RTL mirroring with the language toggle; numbers and phone numbers stay LTR.
- Responsive: three columns on desktop; on small screens, columns become stacked views.
