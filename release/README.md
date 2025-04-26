# Release Instructions

## 1. Create a Release Branch

```bash
# Start from the latest main
git switch main
git pull origin main

# Create a release branch with version in name
git switch -c release/v0.1.X
```

## 2. Make Any Release Preparations

Make any necessary changes for the release (e.g., update documentation, etc.).

```bash
# Make changes and commit them
git add .
git commit -m "Prepare for release v0.1.X"
```

## 3. Push the Release Branch and Create PR

```bash
git push origin release/v0.1.X
```

Then create a PR from the `release/v0.1.X` branch to `main` in GitHub.

## 4. Merge the PR After Review

Once the PR is approved and all CI checks pass, merge it into the main branch.

## 5. Create and Push the Tag

After the PR is merged to `main`:

```bash
git switch main
git pull origin main

# Create release tag
git tag -a v0.1.X -m "Release v0.1.X"

# Push the tag
git push origin v0.1.X
```

The tag push will automatically trigger:

1. The `release` job to build the package using `uv build`
2. The `github-release` job to create a GitHub release with the tag name and release notes
