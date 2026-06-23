# Astro Solves Prototype V1 Strategy

## Product Direction

Astro Solves should feel like a private royal guidance chamber, not a generic horoscope feed. The beta promise is simple:

- Save a birth profile once.
- Choose one free period reading each day: daily, weekly, monthly, or yearly.
- Share a real life problem and receive two free detailed problem analyses with remedy paths.
- After trust is formed, offer paid depth for extra readings, deeper problem maps, audio remedies, and longer Shani/Saade Saati support.

## User Psychology

Indian users already have a cultural frame for fate, auspicious timing, remedies, and planetary pressure. Pew Research Center's India religion survey reports that 44% of Indians believe astrology can influence events, and 83% say important dates are fixed by auspicious dates or times. This means the app does not need to over-explain why astrology matters; it needs to make the reading feel personally accurate, respectful, and practically useful.

The hook should be ethical retention, not fear. The user is often arriving with uncertainty, delay, relationship pressure, career stress, or Shani/Saade Saati anxiety. The app earns attention when it:

- Names the problem in the user's own language.
- Gives a calm root pattern without doom.
- Shows a few chart receipts so it feels knowledgeable.
- Offers one immediately usable remedy.
- Saves memory so future readings feel more personal.

## Engagement Loops

- Daily choice: one free unlock each day, but the user must choose daily, weekly, monthly, or yearly. Choice creates ownership and reduces the feeling of a generic feed.
- Problem-first trust: the first two problem analyses and solution paths are free. This lets the user feel understood before seeing paid depth.
- Saade Saati pathway: a Shani-focused track for delay, discipline, fear, family pressure, and repeated obstacles.
- Memory continuity: remembered categories, repeated problems, and remedy history should make future insights feel sharper.
- Ritual completion: short practices like Hanuman Chalisa listening, Saturday seva, journaling, or breath reset should feel achievable.

## Output Style

- Keep readings short, direct, and mobile-sized.
- Use astrology terms only when necessary, and explain them plainly.
- Keep Do/Avoid as one short line each.
- Avoid Hinglish mixing, draft notes, self-corrections, and overlong "analysis" prose.
- Never guarantee outcomes, marriage, wealth, cure, or fixed fate.

## Paid Plan Ideas

- Extra period readings: unlock more than one daily/weekly/monthly/yearly reading on the same day.
- Deep problem map: longer root-cause view across dasha, Saturn, Moon, house pressure, timeline, watchouts, and remedies.
- Remedy audio vault: Hanuman Chalisa, Shani discipline, breath reset, and guided reflection audios.
- 21-day Shani care: small daily actions, Saturday prompts, reminders, and progress tracking.
- Monthly pressure planner: upcoming transit notes, caution windows, and calm action plan.
- Family and relationship lens: partner/family dynamics with boundaries and communication remedies.

## Current Prototype Implementation

- API enforces one free period reading per user per local date.
- API enforces two free problem analyses per user.
- Mobile UI uses tabs for Profile, Reading, Problems, and Royal depth.
- The renderer uses compact chart context, capped output tokens, low verbosity, and draft-artifact rejection.
- Harmony tab adds zodiac match guidance, partner numerology, marriage/relationship lenses, and peace practices without using model tokens.
- Settings now owns profile, user data, privacy controls, reminder setup, and account deletion so destructive actions are not on the main page.

## Research Notes

- Pew Research Center, "Religious beliefs" India survey, 2021.
- OpenAI Help, "Controlling the length of OpenAI model responses", updated June 2026.
- Public astrology-app market coverage suggests Indian astrology apps monetize through repeat usage, consultations, reports, remedies, and paid depth after a free entry point.
