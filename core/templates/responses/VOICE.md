# Response Template Voice & Tone Guide

These templates post as `line-sous-chef[bot]`. They should feel like a helpful colleague, not a corporate chatbot.

## Principles

1. **Warm first, informative second.** Text strips out tone-of-voice and facial cues — what reads as "neutral" often lands as cold. Overcorrect toward warm. These are real people who took the time to help.
2. **Slightly playful.** Not comedy, just casual phrasing you'd use chatting with a colleague. "Give it a spin" beats "please verify." Contractions, everyday phrasing, the occasional aside.
3. **Transparent automation.** Disclose the bot clearly but briefly — one short line, then get to the good stuff. Never pretend to be a person.
4. **Concrete and specific.** Pair warmth with real information. Name the version, the workaround command, the specific question. Friendly + vague = hollow; friendly + specific = genuinely helpful.
5. **Acknowledge the person.** Thank them for something specific they did. Specific gratitude reads as genuine; generic platitudes read as automated.
6. **Natural variation.** Vary openers, closings, and phrasing across templates. Repeating the same structure on every issue is the fastest way to sound like a bot.
7. **Close with care.** Even when saying no, be kind and leave the door open.

## Anti-Patterns

| Avoid | Why | Better |
|-------|-----|--------|
| "Thank you for your patience" | Corporate cliche, reads as form letter | Be specific: "Thanks for flagging this — that timeout signal was exactly what we needed" |
| "We apologize for any inconvenience" | Empty formula | Acknowledge directly: "Yeah, 45-min cook phases hitting a 20-min wall — that's rough" |
| "I'm happy to help!" | Peak chatbot | Just be helpful and let it show |
| "Delightful", "amazing", "incredible" | Superlative pile-up screams AI | Plain, warm language |
| "We're looking into this" (alone) | Vague, no substance | Name what's happening: "This landed on main, shipping in the next release" |
| Same opening on every template | Repetitive = robotic | Vary the opener per template |
| "Please don't hesitate to reach out" | Stiff corporate close | "Let us know how it goes" / "Holler if something's still off" |
| Terse one-liners without warmth | Text reads colder than intended | Add a human touch: "Nice find" / "Good question" |

## Good Examples

- "Thanks for flagging this — that 20-min default was definitely too tight for longer tasks. Good catch."
- "This shipped in v0.20.0. Give it a spin and let us know how it holds up!"
- "We'd love to help with this, but could use a bit more detail first."
- "This overlaps with #12, which has a bunch more context. Closing this one in its favor — all the good discussion carries over there."
- "This is actually working as designed, though we totally get why it's surprising. Here's what you can do instead."
- "Appreciate the detailed write-up — made it easy to track down."

## Template Structure

- **Bot identification:** One brief, friendly line at the top (blockquote). Vary it across templates.
- **Body:** Warm and conversational. Contractions. Lead with the most important thing wrapped in genuine warmth.
- **Closing:** End with an inviting next step. Avoid formal sign-offs.
- **Length:** 4-10 lines of body text.
- **Attribution:** `_— line-sous-chef_` (short, unobtrusive)
