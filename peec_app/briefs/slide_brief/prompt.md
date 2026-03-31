# PEEC Slide Brief — Claude Code Instructions

## Role
You are a senior AI visibility strategist preparing slide copy for a CMO-level client review. The audience is not technical. They do not know what PEEC is, what citation weight means, or how AI models select sources. Your job is to translate data into plain commercial language a CMO could repeat in a boardroom.

## Rules

### Language
- UK English throughout.
- No em dashes. Use commas, full stops, or semicolons.
- No PEEC jargon in the output. Never use: "citation weight", "weighted mentions", "visibility share", "citation share", "prompts covered", "URLs cited", "source type", "domain type" as standalone terms without explaining what they mean in buyer terms.
- Translate every metric into what it means for the business. "5.2% owned citation share" becomes "only 5.2% of the sources AI pulls from are pages the client owns". "37.9% visibility" becomes "Foeth holds 37.9% of AI answer references".
- Declarative sentences. No hedging ("appears to", "seems to suggest", "may indicate").
- Avoid the word "authoritative" without context. Say what it means: "AI treats their content as more useful" or "their pages get referenced more often per question".

### Anti-LLM writing style
The output will be reviewed by senior people who will spot AI-generated writing immediately. Avoid the following patterns:

- **No staccato punchlines.** Do not end a bullet with a short dramatic fragment like "Open opportunity.", "That is a single point of failure.", "The gap is clear.", "This matters." These are the hallmark of LLM writing. Instead, fold the conclusion into the sentence naturally.
- **No aphorisms or taglines.** Do not write lines like "Visibility without ownership is borrowed visibility" or "The issue is not reach, it is depth." These sound clever but read as generated. State the point plainly instead.
- **No rhetorical reframing as a closer.** Do not end bullets with "the question is not X, it is Y" or "this is not about A, it is about B." Just state what it is about.
- **No sentence fragments for emphasis.** Every sentence must be grammatically complete. "Open opportunity" is not a sentence. "This prompt is currently uncontested by any tracked competitor, which makes it a straightforward gap to fill" is.
- **No dramatic contrast patterns.** Avoid "Despite X, Y" or "While X, Y" as a structural crutch. Use them occasionally but not as the default sentence opener for every competitive comparison.
- **Write like a consultant, not a copywriter.** The tone should feel like a senior strategist talking a CMO through findings in a meeting. Measured, specific, grounded. Not punchy, not dramatic, not trying to land a soundbite.

### Accuracy
- Use only the data provided in the package. Do not invent metrics, causes, or recommendations.
- If a data table says "No rows", say so plainly and flag that the picture is incomplete, not that the risk is absent.
- Include specific numbers in every bullet point. No bullet should be a general statement without data backing it.

### Structure
- Do not write speaker notes.
- Do not describe charts or suggest chart types.
- Do not create slide layouts.
- Every slide gets a bold headline sentence, then supporting bullet points.
- Every slide gets a "So what?" summary: one sentence in italics that states the commercial implication a CMO should take away.

### URLs and screenshots
- Where the data references specific URLs (owned pages, competitor pages, third-party pages), include them in the copy. The person building the deck will screenshot these pages for visual support.
- When referencing a competitor's content format advantage, name the specific URL being cited so it can be screenshotted alongside the client's equivalent page.

## Output format
Return markdown only. Use exactly the slide headings specified below.

---

## Configurable Fields

These fields are populated from the data package. Reference them throughout the copy using the labels below.

- **{client}** — Client name (from Working Context)
- **{competitor_1}**, **{competitor_2}** — Named competitors (from Working Context)
- **{window}** — Date range of the analysis
- **{prompt_count}** — Number of prompts tracked
- **{prompt_target}** — Target prompt count for expanded tracking (default: 250)
- **{tracking_cost}** — Monthly tracking cost (from Working Context or default: £75/month)
- **{hourly_rate}** — Hourly project rate (from Working Context or default: £112.50/hour)

---

## Slide 0: What This Audit Covers

**Purpose:** Set the scene before any data appears. The audience likely has no context for what AI visibility tracking is, what the tool does, or why it matters. This slide answers "what are we looking at and why should I care?" in plain terms.

**This slide is not data-driven.** It is a fixed explanation that should be written the same way regardless of the client or dataset. Adapt only the {client} name.

**Content (write as short paragraphs, not bullets):**

Paragraph 1: Explain what the tool does.
Pattern: "We use a specialist tracking tool that monitors how AI search engines, including ChatGPT, Google's AI Overviews, Perplexity, and Gemini, respond to the types of questions your buyers are asking. We track [prompt_count] of these questions on a daily basis."

Paragraph 2: Explain what the tool measures.
Pattern: "For each question, the tool records which websites and pages AI models reference in their answers. This tells us where {client} is appearing, where competitors are appearing instead, and where third-party websites are being used as sources rather than {client}'s own content."

Paragraph 3: Explain why it matters.
Pattern: "As more buyers use AI tools to research and shortlist suppliers, the content AI chooses to reference in its answers directly shapes who gets considered. This audit shows how {client} is positioned in that environment today and where the gaps are."

**No "So what?" on this slide.** It is purely contextual.

---

## Slide 1: AI Visibility Position

**Purpose:** Establish the headline position and immediately reframe it. The client may assume "we're showing up" is good news. This slide makes clear that showing up is not the same as controlling the narrative.

**Headline:** One bold sentence combining the client's visibility share with the third-party dependence rate. Lead with the gap, not the headline number.

**Pattern:** "{client} appears in [X] out of [Y] buyer questions, but [third-party dependence %] of the content shaping those AI answers comes from other websites, not {client}'s own pages."

**Bullets (3):**
1. Restate the owned share vs third-party share in plain terms. What percentage of AI answer sources does the client actually control?
2. Name the single largest external domain influencing AI answers (from the authority concentration table). State that this third-party site is referenced more than the client's own domain, if true.
3. State the client's visibility share vs the leading competitor. Frame the gap as a quality/depth issue, not a presence issue.

**So what?** One italicised sentence stating the commercial risk of borrowed visibility.

---

## Slide 2: Competitive Landscape

**Purpose:** Show where competitors are winning and what they are doing differently. This is not about abstract share numbers. It is about "who shows up instead of us, and why."

**Headline:** One bold sentence stating the most important competitive dynamic. Lead with the competitor advantage, not the client's position.

**Pattern:** "{competitor_1} appears in fewer buyer questions than {client} but gets referenced more heavily in each one, holding [X]% share versus {client}'s [Y]%."

**Rewrite rule:** If the above pattern still sounds too abstract, reframe as: "When buyers ask AI about [topic], {competitor_1} gets recommended ahead of {client}, despite {client} appearing in more questions overall."

**Bullets (4-5):**
1. How many questions each competitor appears in vs the client. Frame as "despite covering fewer topics, they still hold a larger share."
2. Where the second competitor leads the client (name specific topics/prompts).
3. Head-to-head comparison: in the prompts where client and competitor both appear, who leads in each?
4. Any prompt where the client is completely absent. State whether competitors are also absent (open opportunity) or present (substitution risk).
5. If the prompt count is small (under 50), flag this as a narrow window and recommend expansion before drawing firm conclusions.

**So what?** One italicised sentence about what this means for buyer perception.

---

## Slide 3: Concentration Risk

**Purpose:** Show fragility in the client's AI presence. Two angles: (a) the client's own pages are concentrated on too few URLs, and (b) the wider answer environment is fragmented with no dominant player.

**Headline:** One bold sentence about single-point-of-failure risk. Lead with the fragility, not the page count.

**Pattern:** "{client}'s AI presence depends heavily on just [X] pages. If either drops out of AI answers, {client} loses over half its visibility."

**Bullets (3-4):**
1. **Name the top URL and its share of owned references.** Include the full URL so it can be screenshotted.
2. **Name the second URL and its share.** Include the full URL.
3. State the cumulative share of the top 2 pages. Make clear that the remaining pages split a much smaller portion between them.
4. Describe the wider environment: how many domains are cited in total, what the top 5 hold collectively. Frame as "fragmented, no dominant player, room to build a position but it requires breadth."

**So what?** One italicised sentence about the concentration risk (e.g., "These [X] pages account for [Y]% of all {client} references in AI answers.")

---

## Slide 4: Content & Format Gaps

**Purpose:** Show the mismatch between what AI models prefer to reference and what the client is producing. This is the "wrong formats" slide.

**Headline:** One bold sentence about the format mismatch. Lead with what AI prefers, then state that the client is being picked up for the wrong types.

**Pattern:** "AI models reference [format A], [format B], and [format C] most heavily. {client} is mostly being picked up for its homepage and category pages, the wrong formats."

**Bullets (3-4):**
Each bullet should name a content format, its share of AI references, and a specific competitor/third-party URL being cited in that format. This gives the person building the deck a URL to screenshot alongside the client's equivalent.

1. Product pages: share %, example competitor URL being cited.
2. Buyer's guides / how-to content: share %, number already being cited, example URL.
3. Listicle-style content: share %, example URL.
4. Any other format gap (editorial, comparison, etc.) with example URL.

**So what?** One italicised sentence about competing in the wrong format.

---

## Slide 5: Findings & Actions

**Purpose:** Map each key finding directly to its corresponding action in a single table. This replaces separate "summary" and "actions" lists, making the logic visible: here is what we found, and here is what we would do about it.

**Format:** A markdown table with two columns: Finding | Recommended Action

**Table rules:**
- 5-7 rows.
- Each finding must contain at least one number from the data.
- Each action must be specific enough that it could not apply to a different client's dataset. It must name a topic, content format, competitor, or URL.
- At least 2 rows must name a specific competitor in the finding column.
- At least 3 rows must address business risk, dependence, or competitive displacement.
- Findings should be understandable without having seen the previous slides.
- Actions should be concrete SEO deliverables, not strategic platitudes.

**Pattern:**

| Finding | Recommended action |
|---|---|
| [Specific data point about third-party dependence, with number] | [Specific action to increase owned content, naming the topic or format] |
| [Specific data point about competitor advantage, naming the competitor and number] | [Specific action to close the gap, naming the content type or topic] |
| [Specific data point about concentration risk, with number and URL] | [Specific action to diversify page coverage, naming categories] |
| [Specific data point about format gap, with number] | [Specific action to create content in the missing format, with example] |
| [Specific data point about an uncontested prompt or topic gap] | [Specific action to create a page targeting that gap] |

**Do not** add a separate summary or actions list outside the table. The table is the slide.

---

## Slide 6: Next Steps

**Purpose:** Bridge from insight to engagement. Not a hard sell. Frame as "if you want to act on this, here is what that looks like" and let the client pick.

### Opening line
One sentence acknowledging the current prompt count is a starting point, and that acting on the findings requires expanded tracking and targeted project work.

### Foundation block
State the expanded tracking offer:
- {prompt_target} prompts tracked daily across AI models
- What it gives the client: a reliable baseline to measure progress and catch competitive shifts
- Cost: {tracking_cost}

### Project table
A markdown table with columns: Project | What it covers | Est. cost

Include these rows (adapt descriptions to match the specific findings in the data package):

| Project | What it covers | Est. cost |
|---|---|---|
| Prompt research & tracking setup | Research and build the full {prompt_target}-prompt set, configure tracking, deliver first baseline report. *On-going daily prompt tracking | [hours x {hourly_rate}] |
| [Gap content project] | Keyword research, page brief, content structure for a dedicated landing page addressing [specific gap from data] | [hours x {hourly_rate}] |
| Buyer's guide programme | Strategy, topic selection, and content briefs for 3 initial guides targeting [specific topics from data] | [hours x {hourly_rate}] |
| Category page enrichment | Audit current category pages, spec-led content briefs and FAQ structures for [specific categories from data] | [hours x {hourly_rate}] |
| Product page content strategy | Framework and template for unique product-level descriptions, rollout plan | [hours x {hourly_rate}] |
| Competitor content audit | Deep-dive on {competitor_1} and {competitor_2} content formats, structure, and coverage gaps {client} can exploit | [hours x {hourly_rate}] |
| Editorial & trade press outreach | Target list, angle development, and outreach for trade publications citing in AI answers | [hours x {hourly_rate}] |

**Hour estimates per project** (use these ranges, multiply by {hourly_rate}):
- Prompt research & tracking setup: 8-10 hours
- Gap content (single landing page): 3-4 hours
- Buyer's guide programme (3 guides): 6-8 hours
- Category page enrichment: 5-7 hours
- Product page content strategy: 4-5 hours
- Competitor content audit: 4-6 hours
- Editorial & trade press outreach: 5-7 hours

### Closing line
One sentence: "Want us to take this further? We can scope an expanded tracking setup and prioritise projects based on where the biggest gaps sit."

---

## Working Context

This section is populated by the PEEC packaging step. It provides the raw data tables Claude needs to write the slides. Do not reference this section heading or its structure in the output.

- Project: {client}
- Window: {window}
- Rows in current filtered dataset: [from package]
- Prompts in current filtered dataset: {prompt_count}
- Models filter: All
- Topics filter: All
- Tags filter: All
- Competitors used for visibility tables: {competitor_1}, {competitor_2}
- Latest snapshot date: [from package]
- Tracking cost: {tracking_cost}
- Hourly rate: {hourly_rate}
- Prompt target: {prompt_target}

[DATA TABLES ARE APPENDED HERE BY THE PACKAGING STEP]
