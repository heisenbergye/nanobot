---
name: skill-finder
description: Search and install agent skills from skills.sh marketplace. Use when user asks "how do I do X", "find a skill for X", or wants to extend capabilities.
homepage: https://skills.sh
metadata: {"nanobot":{"emoji":"🔍","requires":{"bins":["npx"]}}}
---

# Skill Finder

Search and install skills from the open agent skills ecosystem at skills.sh.

## When to use

- User asks "how do I do X" where X might have an existing skill
- User says "find a skill for X" or "is there a skill for X"
- User asks "can you do X" where X is a specialized capability
- User wants to extend agent capabilities
- User mentions they wish they had help with a specific domain

## Commands

```bash
npx skills find [query]     # Search for skills
npx skills add <pkg>        # Install a skill
npx skills add <pkg> -g -y  # Install globally, skip prompts
npx skills list             # List project skills
npx skills list -g          # List global skills
npx skills check            # Check for updates
npx skills update           # Update all skills
```

## How to help users

1. **Understand the need**: Identify the domain and specific task
2. **Search**: Run `npx skills find [query]` with relevant keywords
3. **Present options**: Show skill name, install command, and skills.sh link
4. **Install if requested**: Use `npx skills add <pkg> -g -y`

Example response:
```
I found a skill that might help! The "react-best-practices" skill provides
React performance optimization guidelines.

To install: npx skills add vercel-labs/skills@react-best-practices
Learn more: https://skills.sh/vercel-labs/skills/react-best-practices
```

## Common categories

| Category | Search terms |
|----------|-------------|
| Web Dev | react, nextjs, typescript, tailwind |
| Testing | testing, jest, playwright, e2e |
| DevOps | deploy, docker, kubernetes, ci-cd |
| Media | youtube, transcript, video, audio |
| Docs | docs, readme, changelog, api-docs |
| Code Quality | review, lint, refactor, best-practices |

## Tips

- Use specific keywords: "react testing" > "testing"
- Try alternative terms: "deploy" or "deployment" or "ci-cd"
- Check popular sources: `vercel-labs/skills`, `anthropics/skills`

## When no skills found

1. Acknowledge no skill was found
2. Offer to help directly with general capabilities
3. Suggest creating a custom skill: `npx skills init my-skill`

## After install

Remind user to start a new session (`/new`) to load the new skill.
