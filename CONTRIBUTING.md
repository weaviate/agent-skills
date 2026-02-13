# CONTRIBUTING.md

Thank you for contributing to Weaviate Agent Skills! Here's how to get started:

[1. Getting Started](#getting-started) | [2. Issues](#issues) |
[3. Pull Requests](#pull-requests) | [4. Contributing New References](#contributing-new-references) |
[5. Creating a New Skill](#creating-a-new-skill)

## Getting Started

## Issues

If you find a typo, have a suggestion for a new skill/reference, or want to improve
existing skills/references, please create an Issue.

- Please search
  [existing Issues](https://github.com/weaviate/agent-skills/issues) before
  creating a new one.
- Please include a clear description of the problem or suggestion.
- Tag your issue appropriately (e.g., `bug`, `question`, `enhancement`,
  `new-reference`, `new-skill`, `documentation`).

## Pull Requests

We actively welcome your Pull Requests! Here's what to keep in mind:

- If you're fixing an Issue, make sure someone else hasn't already created a PR
  for it. Link your PR to the related Issue(s).
- We will always try to accept the first viable PR that resolves the Issue.
- If you're new, we encourage you to take a look at issues tagged with
  [good first issue](https://github.com/weaviate/agent-skills/labels/good%20first%20issue).
- If you're proposing a significant new skill or major changes, please open a
  [Discussion](https://github.com/orgs/weaviate/discussions/new/choose) first to
  gather feedback before investing time in implementation.

## Contributing New References

To add a reference to an existing skill:

1. Navigate to `skills/{skill-name}/references/`
2. Fill in the frontmatter (title, impact, tags)
3. Write explanation and examples

## Creating a New Skill

Skills follow the [Agent Skills Open Standard](https://agentskills.io/).

### 1. Create the directory structure

```bash
mkdir -p skills/my-skill/references
```

### 2. Create SKILL.md

```yaml
---
name: my-skill
description: Brief description of what this skill does and when to use it.
license: MIT
metadata:
  author: your-org
  version: "1.0.0"
  organization: Your Org
  date: January 2026
  abstract: Detailed description of this skill for the compiled AGENTS.md.
---

# My Skill

Instructions for agents using this skill.

## References

- https://example.com/docs
```

### 3. Create references/your-reference.md

## Questions or Feedback?

- Open an Issue for bugs or suggestions
- Start a Discussion for broader topics or proposals
- Check existing Issues and Discussions before creating new ones
