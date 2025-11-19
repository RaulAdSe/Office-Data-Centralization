# Contributing

## Workflow

**⚠️ Never push directly to `main`**

All work in feature branches: `feature/<name>`, `fix/<name>`, `docs/<name>`

## Pull Request Process

1. **Update your branch:**
   ```bash
   git checkout main
   git pull origin main
   git checkout your-branch
   git rebase main
   ```

2. **Push and create PR:**
   ```bash
   git push origin feature/your-feature
   # Open PR on GitHub → Add description → Request review
   ```

3. **Wait for approval** - Code owner must approve before merge

## Commit Messages

```
type(scope): description

Examples:
- feat(export): add Presto export
- fix(word): correct LINK fields
- docs: update README
```

## Branch Protection

`main` is protected:
- ✅ Requires PR before merging
- ✅ Requires approval
- ✅ Prevents force pushes
- ✅ Must be up to date

You **cannot** bypass these rules.

---

**Questions?** Open an issue or check [WORKFLOW.md](../docs/WORKFLOW.md)
