# meta/roadmap/0.0/0.0.5_tools/facts.sh -- re-derives `0.0.5.md` §1, block 0b. Sourced after `../tools/env.sh`.
# Reads the checkout only; writes nothing.

# §1.1 -- the tree 0.0.4 leaves
echo "§1.1 src/core holds: $(git -C "$REPO" ls-files 'src/core/*.npk' | sed 's|^src/core/||' | tr '\n' ' ')"
echo "§1.1 tests/unit holds: $(git -C "$REPO" ls-files 'tests/unit/*.npk' | wc -l) program(s)"

# §1.2 -- E2-6's sites and E2-10's paragraphs, as the tree stands
echo "§1.2 'examples/' or 'this repository' said of the dogfood consumer: $(cd "$REPO" && grep -n -E 'linter in .?examples/|in this repository rather than a separate one|built \*\*and run\*\* by the harness, so a broken example' meta/roadmap/ROADMAP.md meta/roadmap/0.12/README.md | sed -E 's/^([^:]+:[0-9]+):.*/\1/' | tr '\n' ' ')"
echo "§1.2 counts of open entries copied out of their set: $(cd "$REPO" && grep -n -E 'five measurements|three measurements' meta/roadmap/ROADMAP.md meta/OPEN_QUESTIONS.md | sed -E 's/^([^:]+:[0-9]+):.*/\1/' | tr '\n' ' ')"

# §1.3 -- the research gate (PD-137's), met at cycle 0.0's first dispatch: what the research folder holds, the items
# CURRENCY.md owes, and each digest's date, which cycle 0.1's gate reads (each stale ninety days after its own)
echo "§1.3 meta/research/ holds: $(git -C "$REPO" ls-files meta/research | sed 's|^meta/research/||' | tr '\n' ' ')"
echo "§1.3 CURRENCY.md's research items: $(grep -cE '^[0-9]\. \*\*' "$REPO/meta/research/CURRENCY.md")"
for f in security-defects security-guidance security-vectors; do
  echo "§1.3 $f.md: $(grep -m1 -oE 'As of [0-9]{4}-[0-9]{2}-[0-9]{2}' "$REPO/meta/research/$f.md" 2>/dev/null || echo MISSING)"
done

# §1.4 -- every place outside this folder that names a file in it, the archive's patch's sites
echo "§1.4 outside meta/roadmap/0.0/, naming a file in it: $(cd "$REPO" && git ls-files | grep -v '^meta/roadmap/0\.0/' | xargs grep -n -E 'roadmap/0\.0/|`0\.0/0\.0\.[0-5]\.md' 2>/dev/null | sed -E 's/^([^:]+:[0-9]+):.*/\1/' | tr '\n' ' ')"
