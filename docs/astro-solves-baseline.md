# Astro Solves Baseline

Last updated: 2026-06-23

## Product North Star

Astro Solves is a mobile-first Vedic astrology app for iOS and Android. The app uses a user's name, birth date, birth time, and birth place to create a personal chart context, then turns that context into practical astrological guidance for daily, weekly, monthly, and yearly decisions.

The differentiator is problem solving. The user should feel safe enough to describe what is actually happening in their life: career blockage, relationship confusion, family pressure, money anxiety, delays, fear during Saade Saati, Shani pressure, dasha shifts, or recurring patterns. Astro Solves then gives a structured astrological lens on why the problem may feel active, how long this period may need attention, what adjacent issues to watch, and what spiritual or behavioral remedies can support them.

The business model is freemium:

- Birth-profile setup, chart snapshot, period readings, and problem analysis are free.
- The first solution/remedy is free.
- Deeper remedy packs, audio practices, recurring guided recitals, and premium solution libraries require subscription access.

## What We Are Building

Astro Solves is not a generic horoscope feed. It is a private chart-based guidance companion with these core loops:

1. Onboard with name, birth date, birth time, birth place, consent, and AI-personalization choice.
2. Show an immediate chart snapshot with visible "receipts": Moon sign, ascendant, nakshatra, dasha, Saturn transit, numerology, and calculation engine.
3. Let users switch between daily, weekly, monthly, and yearly readings.
4. Invite users to share a real problem in their own words.
5. Return an empathetic astrological analysis with timeline, risk areas, chart evidence, and a first free remedy.
6. Offer premium solution depth after trust is established, not before.
7. Encourage return visits through useful check-ins, ritual reminders, and changing transit context.

## Target User

Primary early user:

- Indian or India-diaspora user, English-first with Indian spiritual vocabulary.
- Age 18-40, mobile-native, comfortable with apps and digital payments.
- Currently facing uncertainty, delay, relationship tension, career confusion, family pressure, or Saturn/Saade Saati anxiety.
- Wants privacy, reassurance, and concrete next steps more than abstract astrology.

Secondary user:

- Spiritually curious user who may not know Vedic terminology but wants chart-backed reflections.
- User who already consumes astrology content and wants something more personal than social posts.

## Research Signals

Pew's India religion survey found that 84% of Indian adults say religion is very important in their lives, 60% pray daily, and 71% visit a house of worship at least monthly. This means ritualized check-ins, devotional language, and remedy framing can feel culturally natural when handled respectfully.

Pew also found that 47% of Indian adults trust religious ritual at least somewhat for treating health problems, while 94% trust medical science. Product implication: Astro Solves should never replace professional help. It should use spiritual remedies as reflective and devotional support, with clear boundaries for medical, legal, financial, and crisis situations.

Market research from MarkNtel estimates the India astrology app market at about USD 163 million in 2024 and projects USD 1,797 million by 2030, driven by smartphone adoption, payments, and younger digital users. Product implication: astrology is already moving from offline consultation to app-based guidance, but trust and differentiation matter.

Psychology research around the Barnum/Forer effect shows that users often rate vague personality statements as personally accurate. Product implication: Astro Solves should not rely on vague flattery. It must show chart evidence and make each reading falsifiable enough to feel honest: "because your Moon is in X," "Saturn is transiting Y," "your current dasha is Z."

Research and behavioral observation around astrology use often points to uncertainty, stress, and relationship/career transitions as triggers. Product implication: the strongest retention loop is not fear. It is helping users name uncertainty, feel understood, take one manageable action, and come back when the next period changes.

Sources used:

- Pew Research Center, "Religious practices" in Religion in India, 2021: https://www.pewresearch.org/religion/2021/06/29/religious-practices-2/
- Pew Research Center, "Religious beliefs" in Religion in India, 2021: https://www.pewresearch.org/religion/2021/06/29/religious-beliefs-2/
- Pew Research Center, "Key findings about religion in India", 2021: https://www.pewresearch.org/short-reads/2021/06/29/key-findings-about-religion-in-india/
- MarkNtel Advisors, India Astrology App Market Growth: https://www.marknteladvisors.com/press-release/india-astrology-app-market-growth
- Hua et al., "A sequential mediation model of the Barnum effect and ego identity", 2023: https://pmc.ncbi.nlm.nih.gov/articles/PMC9932533/
- OpenAI API docs, Responses API and Structured Outputs: https://developers.openai.com/api/docs/guides/migrate-to-responses and https://developers.openai.com/api/docs/guides/structured-outputs

## Product Principles

1. Chart first, GPT second.
   Deterministic astrology calculations are the source of truth. GPT renders the reading in human language but must not invent chart placements.

2. Trust through evidence.
   Every meaningful insight should include chart receipts: Moon, ascendant, nakshatra, dasha, Saturn transit, numerology, or a clearly named transit.

3. Problem sharing before selling.
   The app earns the right to monetize by first helping the user feel understood. Paid solutions should appear after the analysis and the first free remedy.

4. No fear traps.
   Do not say a user is doomed, cursed, guaranteed to suffer, guaranteed to marry, guaranteed to earn money, or guaranteed to be cured.

5. Culturally specific, not generic mystical.
   Use Vedic language where helpful: Shani, Saade Saati, dasha, nakshatra, mantra, Hanuman Chalisa, daan, vrat, discipline, seva. Keep it understandable.

6. Spiritual support, not professional replacement.
   The app must route crisis, medical, legal, and financial-risk questions away from astrology-only answers.

## Core Beta Features

### 1. Birth Profile

Required:

- Full name
- Birth date
- Birth time
- Birth time confidence: exact, approximate, unknown
- Birthplace search
- Timezone
- Privacy consent
- AI personalization consent

### 2. Chart Snapshot

Show:

- Ascendant
- Moon sign and nakshatra
- Sun sign
- Current dasha
- Saturn transit house/sign
- Life path and personal day numerology
- Calculation engine

### 3. Period Readings

User can select:

- Daily
- Weekly
- Monthly
- Yearly

Each reading returns:

- Headline
- Summary
- Love
- Career
- Money
- Mind
- Do actions
- Avoid actions
- Lucky supports
- Astro evidence
- Safety disclaimer

### 4. Problem Solver

Inputs:

- Problem category: Shani/Saade Saati, relationship, career, money, family, health-stress, other
- Free-form problem details

Outputs:

- Problem title
- Gentle reassurance
- Astrological pattern/root lens
- Timeline framing
- Problems to watch
- First free solution
- Locked premium solutions
- Chart evidence
- Disclaimer

### 5. Solution Monetization

Free:

- First suggested remedy, such as a short Hanuman Chalisa listening/recital practice, journaling prompt, seva/daan suggestion, or discipline practice.

Paid:

- Audio recital packs
- 7-day/21-day guided remedy plans
- Planet-specific remedy libraries
- Deeper yearly solution report
- Reminder-based practice plan

Subscription copy should emphasize support and depth, not guaranteed outcomes.

## UI Direction

The UI should feel like a modern Indian astrology command center:

- Deep cosmic base colors with saffron, marigold, peacock teal, ivory, and muted ruby accents.
- Visible mandala/orbit/star-field motifs through native UI shapes, icons, and gradients.
- Dense but calm information hierarchy.
- No cheap generic horoscope styling.
- No fear-red warning overload.
- Use icon-first controls for time period, profile, notifications, remedies, and delete/account actions.
- Make problem sharing feel private and contained.
- Make locked solutions feel valuable, not coercive.

## GPT Backend Direction

Use the OpenAI Responses API with structured outputs. The backend should:

- Keep `OPENAI_API_KEY` optional for local beta.
- Return deterministic fallback readings when no key is set.
- Use JSON schema output for reliable mobile rendering.
- Include safety instructions in system prompts.
- Pass chart facts as structured JSON.
- Avoid sending unnecessary profile data beyond what is needed for personalization.

## Safety Boundaries

Block or redirect:

- Self-harm and suicide
- Medical diagnosis or urgent symptoms
- Legal decisions
- Stock, gambling, or guaranteed financial advice
- Guaranteed marriage, fertility, money, cure, or fate claims
- Abuse situations that require immediate safety planning

Default disclaimer:

"Astrology is reflective spiritual guidance, not medical, legal, financial, or crisis advice. Remedies are devotional and behavioral supports, not guaranteed fixes."

## Beta Success Criteria

The beta is ready when:

- A user can save a named birth profile.
- The app can produce chart-backed daily, weekly, monthly, and yearly readings.
- The app can analyze a user-submitted problem and return a free remedy plus locked premium options.
- The backend works without an API key using deterministic fallback content.
- The backend can use GPT via `OPENAI_API_KEY` when provided.
- The UI clearly feels like Astro Solves, not the older Trust Astro prototype.
- Tests/typechecks pass.

