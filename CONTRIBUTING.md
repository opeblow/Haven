# Contributing to Haven

Thank you for your interest in contributing to Haven! This document provides
guidelines and information for contributors.

## Development Setup

### Prerequisites
- Python 3.12+
- Node.js 20+
- pnpm 9+
- AWS CLI configured
- uv (Python package manager)

### Getting Started

```bash
# Clone the repository
git clone https://github.com/haven-agent/haven.git
cd haven

# Install dependencies
pnpm install
cd services/agents && uv sync

# Start development
pnpm dev
```

## Branch Naming

- `feature/description` — new features
- `fix/description` — bug fixes
- `docs/description` — documentation changes
- `refactor/description` — code refactoring

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(agents): add batch donation processing
fix(logistics): correct cold chain temperature range
docs(readme): update architecture diagram
```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes following the code style
3. Add tests for new functionality
4. Ensure all checks pass: `pnpm lint && pnpm typecheck && pnpm test`
5. Submit your PR with a clear description

## Code Review Checklist

- [ ] Tests pass
- [ ] No type errors
- [ ] Linting passes
- [ ] Documentation updated (if applicable)
- [ ] Security considerations addressed
- [ ] No secrets or credentials committed

## DCO Sign-off

All contributions must include a Developer Certificate of Origin (DCO) sign-off:

```bash
git commit -s -m "feat: add new feature"
```

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).
