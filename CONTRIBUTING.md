# Contributing

Thank you for contributing to Weaviate Agent Skills! Here's how to get started.

[1. Getting Started](#getting-started) | [2. Issues](#issues) | [3. Pull Requests](#pull-requests) | [4. Contributing to a Skill](#contributing-to-a-skill) | [5. Creating a New Skill](#creating-a-new-skill)

## Getting Started

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/<your-username>/agent-skills.git
   cd agent-skills
   ```
2. Ensure you have [Python 3.11+](https://www.python.org/) and [uv](https://docs.astral.sh/uv/) installed.
3. Set the required environment variables (`WEAVIATE_URL`, `WEAVIATE_API_KEY`). See the [README](./README.md#configuration) for details.

## Issues

If you find a bug, have a suggestion, or want to propose a new skill or reference, please create an issue.

- Search [existing issues](https://github.com/weaviate/agent-skills/issues) before creating a new one.
- Include a clear description of the problem or suggestion.
- Tag your issue appropriately (e.g., `bug`, `enhancement`, `new-reference`, `new-skill`, `documentation`).

## Pull Requests

We actively welcome pull requests! Here's what to keep in mind:

- If you're fixing an issue, check that no one else has already opened a PR for it. Link your PR to the related issue(s).
- We will try to accept the first viable PR that resolves an issue.
- If you're new, look for issues tagged with [good first issue](https://github.com/weaviate/agent-skills/labels/good%20first%20issue).
- For significant new skills or major changes, please open a [Discussion](https://github.com/orgs/weaviate/discussions/new/choose) first to gather feedback before investing time in implementation.

## Contributing to a Skill

The repo currently has two skills:

| Skill | Path | Description |
|-------|------|-------------|
| **weaviate** | `skills/weaviate/` | Scripts and references for searching, querying, and managing Weaviate collections |
| **weaviate-cookbooks** | `skills/weaviate-cookbooks/` | Implementation guides for building full-stack AI applications with Weaviate |

### Adding a Reference

References are markdown files that provide detailed guidance for a specific operation or pattern.

1. Navigate to `skills/<skill-name>/references/`.
2. Create a new `.md` file with a descriptive name (e.g., `my_feature.md`).
3. Write clear instructions including usage, parameters, examples, and any prerequisites.
4. Link the new reference from the skill's `SKILL.md`.

## Creating a New Skill

Skills follow the [Agent Skills Open Standard](https://agentskills.io/).

### 1. Create the directory structure

```bash
mkdir -p skills/my-skill/references
```

### 2. Create SKILL.md

Every skill needs a `SKILL.md` file with YAML frontmatter:

```markdown
---
name: my-skill
description: Brief description of what this skill does and when to use it.
---

# My Skill

Instructions for agents using this skill.

## References

- [Feature A](references/feature_a.md): Description of feature A.
- [Feature B](references/feature_b.md): Description of feature B.
```

### 3. Add references

Create markdown files in `references/` for each topic, operation, or pattern your skill covers.

## Questions or Feedback?

- Open an Issue for bugs or suggestions
- Start a Discussion for broader topics or proposals
- Check existing Issues and Discussions before creating new ones
