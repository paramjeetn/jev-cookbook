# Contributing to jev-cookbook

Thanks for your interest in contributing! This cookbook is community-maintained and we welcome:

## What We're Looking For

- 🆕 **New use cases** — Found a novel application of Jev? Add an example folder!
- 🐛 **Schema fixes** — TypeSafe updates their API? Help us keep the reference accurate
- 📝 **Pattern docs** — Discovered a composition pattern? Document it!
- 🔧 **Code improvements** — Better error handling, cleaner output, etc.
- 🌍 **Translations** — Help make this accessible in other languages

## How to Contribute

1. Fork the repo
2. Create a feature branch (`git checkout -b add-my-example`)
3. Add your example following the existing folder structure:
   ```
   examples/XX-your-example/
   ├── README.md           # What, why, how to run, sample output
   ├── your_script.py      # Working Python code
   └── payload.json        # Console-ready JSON payload
   ```
4. Ensure your code uses the **correct API schema** (see `reference/api-schema.md`):
   - Choice: `criteria: { "key": "description" }` (NOT `options: [...]`)
   - Score: `criteria: ["level 0", "level 1", ...]` (NOT `min/max`)
5. Test your example (or at least validate the payload in the TypeSafe console)
6. Submit a PR with a clear description

## Code Style

- Python: PEP 8, use `requests` + `python-dotenv`
- Markdown: GitHub Flavored Markdown
- JSON payloads: formatted with 2-space indentation
- State text: realistic and detailed, not placeholder text

## Questions?

Open an issue or reach out on the [TypeSafe Discord](https://typesafe.ai/discord).
