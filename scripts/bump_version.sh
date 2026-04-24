#!/usr/bin/env bash
# Usage: bump_version.sh [major|minor|patch]
# Reads the current version from pyproject.toml, increments the requested
# component, and updates pyproject.toml, admin-dashboard/package.json, and
# k8s/base/kustomization.yaml in-place.
# Prints the new version string to stdout.
set -euo pipefail

BUMP=${1:-patch}

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYPROJECT="$REPO_ROOT/pyproject.toml"
PACKAGE_JSON="$REPO_ROOT/admin-dashboard/package.json"
KUSTOMIZATION="$REPO_ROOT/k8s/base/kustomization.yaml"

CURRENT=$(grep '^version = ' "$PYPROJECT" | sed 's/version = "\(.*\)"/\1/')
MAJOR=$(echo "$CURRENT" | cut -d. -f1)
MINOR=$(echo "$CURRENT" | cut -d. -f2)
PATCH=$(echo "$CURRENT" | cut -d. -f3)

case "$BUMP" in
  major)
    MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
  minor)
    MINOR=$((MINOR + 1)); PATCH=0 ;;
  patch)
    PATCH=$((PATCH + 1)) ;;
  *)
    echo "Usage: $0 [major|minor|patch]" >&2; exit 1 ;;
esac

NEW="$MAJOR.$MINOR.$PATCH"

# Portable sed: GNU sed uses -i, BSD/macOS sed requires -i ''
sedi() { sed --version 2>/dev/null | grep -q GNU && sed -i "$@" || sed -i '' "$@"; }

sedi "s/^version = \"$CURRENT\"/version = \"$NEW\"/" "$PYPROJECT"
sedi "s/\"version\": \"$CURRENT\"/\"version\": \"$NEW\"/" "$PACKAGE_JSON"
sedi "s/newTag: \"$CURRENT\"/newTag: \"$NEW\"/g" "$KUSTOMIZATION"

echo "$NEW"
