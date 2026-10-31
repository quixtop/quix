# ASD-STE100 writing rules — restated for software docs
<!-- author: shrix -->

Every rule of ASD-STE100 Issue 9 (January 2025, 53 rules in 9 sections, plus 8
general recommendations), restated in our own words. The ASD text and dictionary
are copyrighted and are not reproduced here; the full standard is a free download
from asd-ste100.org.

**Check** says who catches a break: `auto` = `ste100.py lint` flags it, `count` =
the word counter applies it, `judge` = you decide while rewriting.

## Section 1 — Words

| Rule | What it asks | Check |
|---|---|---|
| 1.1 | Use only approved words, technical nouns and technical verbs. | auto (our list) + judge |
| 1.2 | Use an approved word only as its listed part of speech ("close" the verb, never "close" meaning near). | judge |
| 1.3 | Use an approved word only with its approved meaning. | judge |
| 1.4 | Use only the approved forms of verbs and adjectives. | judge |
| 1.5 | You can use words that belong to a technical noun category. | judge |
| 1.6 | A word that is not approved is allowed only as a technical noun or part of one. | judge |
| 1.7 | Do not use a technical noun as a verb ("to cache the reply" → "keep the reply in the cache"). | judge |
| 1.8 | Use the technical nouns your company, industry or field approves. | project dictionary |
| 1.9 | When you must pick a technical noun, pick a short, clear one. | judge |
| 1.10 | No regional, slang or jargon words as technical nouns. | judge |
| 1.11 | One item, one technical noun: never two names for the same thing. | auto (dictionary `not`) |
| 1.12 | You can use verbs that belong to a technical verb category. | judge |
| 1.13 | Do not use a technical verb as a noun. | judge |
| 1.14 | Use American spelling unless a directive says otherwise (`meta.spelling: en-GB`). | auto (check) |

## Section 2 — Multi-word nouns

| Rule | What it asks | Check |
|---|---|---|
| 2.1 | A multi-word noun has no more than three words. Break longer ones up with a preposition. | auto (check) |
| 2.2 | A technical name of more than three words stays complete; do not shorten it. | judge |

## Section 3 — Verbs

| Rule | What it asks | Check |
|---|---|---|
| 3.1 | Use only the verb forms the dictionary gives. | judge |
| 3.2 | Allowed: infinitive, imperative, simple present, simple past, simple future, past participle as an adjective. | auto (progressive) |
| 3.3 | Use the past participle only as an adjective ("the closed valve"). | auto (via 3.4/3.6) |
| 3.4 | No auxiliaries to build complex forms: no perfect tense, no "must be done", no "is to be". | auto |
| 3.5 | Use the -ing form only as, or inside, a technical noun ("load balancing"). | auto (check) |
| 3.6 | Use the active voice. Descriptive text can use the passive only when the agent is unknown. | auto (fail in steps, check in descriptions) |
| 3.7 | Show an action with a verb, not a noun ("do an inspection of" → "inspect"). | judge |

## Section 4 — Sentences

| Rule | What it asks | Check |
|---|---|---|
| 4.1 | Write short, clear sentences. | auto (length) |
| 4.2 | Do not drop words or use contractions to make a sentence shorter. | auto (contractions) + judge |
| 4.3 | Use a vertical list for complex text. | auto (check) |
| 4.4 | Use connecting words and phrases to link sentences on related topics. | judge |
| 4.5 | Put an article ("the", "a", "an") or "this"/"these" before a noun where it applies. | judge |

## Section 5 — Procedural writing (instructions)

| Rule | What it asks | Check |
|---|---|---|
| 5.1 | No more than 20 words in a sentence. Safety instructions obey this too. | auto |
| 5.2 | One instruction in each sentence, unless the actions happen at the same time. | auto |
| 5.3 | Write instructions as commands. | count (sets the type) |
| 5.4 | If the reader must know a condition first, start with it, then a comma, then the command. | judge |
| 5.5 | A note gives information, never an instruction. | auto (check) |

## Section 6 — Descriptive writing

| Rule | What it asks | Check |
|---|---|---|
| 6.1 | Give information gradually: one subject in each sentence. | judge |
| 6.2 | Use key words and phrases to give the text a logical structure. | judge |
| 6.3 | No more than 25 words in a sentence. | auto |
| 6.4 | Use paragraphs to group related information. | judge |
| 6.5 | Each paragraph has one topic. | judge |
| 6.6 | No more than six sentences in a paragraph. | auto |

## Section 7 — Safety instructions

| Rule | What it asks | Check |
|---|---|---|
| 7.1 | Use a signal word for the risk level: a warning means risk of injury or death, a caution means risk of damage. | judge |
| 7.2 | Start with a clear, exact command or condition. | auto (check) |
| 7.3 | Then explain the risk or what can happen. | judge |

## Section 8 — Punctuation and word count

| Rule | What it asks | Check |
|---|---|---|
| 8.1 | Any standard punctuation except the semicolon. | auto |
| 8.2 | Use a hyphen to join words that are directly related. | judge |
| 8.3 | Parentheses only for: references, item or step identifiers, abbreviations, singular-and-plural, a short explanation, an alternative. | judge |
| 8.4 | In a vertical list, a colon ends the sentence for the word count. | count |
| 8.5 | Text in parentheses counts as one word. | count |
| 8.6 | One word each: a number, a number with its unit, an abbreviation, an alphanumeric identifier, quoted text, a title or label, a proper noun. | count |
| 8.7 | A hyphenated word counts as one word. | count |

## Section 9 — Writing practices

| Rule | What it asks | Check |
|---|---|---|
| 9.1 | When a word-for-word swap does not work, build the sentence again. | judge |
| 9.2 | Use each approved word correctly. | judge |
| 9.3 | Do not make phrasal verbs ("carry out" → "do"). | auto (our list) |
| 9.4 | Keep terminology and wording consistent. | auto (dictionary) + judge |

## General recommendations

| # | What it asks |
|---|---|
| GR-1 | Keep "that" after verbs such as "make sure" and "show": "Make sure that the tests pass." |
| GR-2 | "with" has three meanings and can be ambiguous; say which one you mean. |
| GR-3 | Make it clear what each pronoun refers to. |
| GR-4 | Use "this" only when the reader knows what it refers to; repeat the noun if not. |
| GR-5 | Watch for false friends: words that look like words in another language but mean something else. |
| GR-6 | No Latin abbreviations: "for example", not "e.g."; "that is", not "i.e."; "and so on", not "etc." (auto, check) |
| GR-7 | Use inclusive language. |
| GR-8 | The possessive ('s) is allowed; if you are not sure it is correct, do not use it. |

## How these apply to software docs (our practice)

- Backticked text — identifiers, paths, commands, flags — is a technical name: count it
  as one word (8.6) and never rewrite it. Code fences, mermaid, tables, HTML comments
  and front matter are out of scope; headings are titles (8.6).
- A sentence wholly in parentheses or quotes counts its words (8.5, 8.6).
- Software verbs such as deploy, commit, merge, restart and delete are technical verbs
  (1.12) when the project's dictionary lists them; keep "delete" over strict STE's
  "erase" if the dictionary says so.
- The project dictionary (`docs/arch/ste100.json` → `dictionary`) records each technical
  noun and verb once: one meaning, and the names it must NOT go by (1.11, 9.4).
- STE targets maintenance procedures. Architecture text is mostly descriptive:
  a precise term beats a vague approved word. Never trade accuracy for brevity
  — flag the break and say why it stays.
- Rewrite pattern: who does what → subject + simple present verb + object. "The token
  is refreshed by the worker" → "The worker refreshes the token."
- Issue 9 approves "approximately" and "sufficient"; older material saying otherwise
  is out of date.
