# meta/roadmap/0.0/0.0.1_tools/facts.sh -- re-derives `0.0.1.md` §1, block 0b. Sourced after `../tools/env.sh`.
# Writes only under `$A/facts`, and removes it. Reads the compiler's tree with `git show` alone.
F=$A/facts
rm -rf "${F:?}"; mkdir -p "$F"
T1=$REPO/meta/roadmap/0.0/0.0.1_tools
TL=$REPO/meta/roadmap/0.0/tools
d=$F/tree; git clone -q --shared "$REPO" "$d"
for s in 1 2 3 4 5 6; do python3 -B "$TL/apply.py" "$d" 0.0.1 $s > /dev/null; done

# §1.1 -- the tree it starts from
echo "§1.1 decisions: the highest by value PA-$(grep -o '^### PA-[0-9]*' "$REPO/meta/DECISIONS.md" | cut -d- -f2 | sort -n | tail -1)"
echo "§1.1 src holds: $(git -C "$REPO" ls-files src | grep -c '\.npk$') .npk file(s); harness holds: $(git -C "$REPO" ls-files harness | tr '\n' ' ')"
echo "§1.1 .github exists: $(test -e "$REPO/.github" && echo yes || echo no)"

# §1.2 -- the compiler's manifest rows at the pin, and the patched manifest's
for k in llvm triple datalayout llc-flags llc-opt-flags opt-flags lld-flags; do
  pin=$(git -C "$NPK_TREE" show $PIN:nitpick.toml | grep -E "^$k +=" | sed -E 's/ +/ /g')
  ours=$(grep -E "^$k +=" "$d/nitpick.toml" | sed -E 's/ +/ /g')
  if [ "$pin" = "$ours" ]; then echo "§1.2 $k: the same as the compiler's at the pin"; else echo "§1.2 $k: DIFFERS -- pin [$pin] ours [$ours]"; fi
done
six=$(git -C "$NPK_TREE" show $PIN:meta/specs/BUILD_REFERENCE.md | grep -c 'Six tables')
two=$(git -C "$NPK_TREE" show $PIN:meta/specs/BUILD_REFERENCE.md | grep -oE "manifest carries the same two rows as this one")
echo "§1.2 the compiler's BUILD_REFERENCE.md §1 at the pin: $six line(s) with \"Six tables\"; and \"$two\""
tables=$(grep -oE '^\[[a-z]+\]' "$d/nitpick.toml" | tr '\n' ' ')
ntests=$(grep -c '^\[\[test\]\]' "$d/nitpick.toml")
echo "§1.2 the tables our manifest carries: $tables; and $ntests test entries"

# §1.3 -- every new module compiles as a root, and its name is no keyword
for f in $(cd "$d" && ls src/lib.npk src/*/*.npk); do echo "§1.3 $(cd "$d/$(dirname "$f")" && "$NPKC" "$(basename "$f")" -o /dev/null > "$F/o" 2>&1; echo "$f: npkc $?, $(wc -c < "$F/o") bytes of diagnostics")"; done

# §1.4 -- what the consumer owes: the bill of a root importing the umbrella
echo "§1.4 $(bill "$d/src/lib.npk")"

# §1.5 -- the workflow, read as GitHub reads it: YAML 1.2, where an unquoted hex value can be a number
python3 -B - "$d/.github/workflows/ci.yml" <<'PY'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
# A plain (unquoted) scalar YAML 1.2's core schema reads as a number: an int, or digits with an exponent.
NUM = re.compile(r"^[-+]?(\.[0-9]+|[0-9]+(\.[0-9]*)?)([eE][-+]?[0-9]+)?$")
plain = []
for n, line in enumerate(text.split("\n"), 1):
    m = re.match(r"^\s*(?:- )?([A-Za-z_][\w-]*):\s+([^\s#'\"][^#]*?)\s*$", line)
    if m and NUM.match(m.group(2)):
        plain.append("%s (%s)" % (m.group(1), m.group(2)))
quoted = re.findall(r'^\s*([A-Z0-9_]+): "([^"]*)"', text, re.M)
hexq = [k for k, v in quoted if re.fullmatch(r"[0-9a-f]{7,64}", v)]
print("§1.5 plain values YAML 1.2 reads as numbers: %s -- and none of them a commit or a digest" % (", ".join(plain) or "none"))
print("§1.5 quoted hex values: %s" % ", ".join(hexq))
PY
python3 -B -c "
import yaml, sys
d = yaml.safe_load(open(sys.argv[1]))
steps = d['jobs']['build']['steps']
print('§1.5 the workflow parses; %d steps; runs-on %s; on %s' % (len(steps), d['jobs']['build']['runs-on'], ' '.join(sorted(d[True]))))
" "$d/.github/workflows/ci.yml"
n=0; bad=0
python3 -B -c "
import yaml, sys, os
for i, s in enumerate(yaml.safe_load(open(sys.argv[1]))['jobs']['build']['steps']):
    if 'run' in s:
        open(os.path.join(sys.argv[2], 'run%02d.sh' % i), 'w').write(s['run'])
" "$d/.github/workflows/ci.yml" "$F"
for r in "$F"/run*.sh; do n=$((n+1)); bash -n "$r" || bad=$((bad+1)); done
echo "§1.5 the steps' scripts: $n, and $bad that bash -n refuses"
echo "§1.5 the compiler's bootstrap harness at the pin: $(git -C "$NPK_TREE" show $PIN:bootstrap/harness/quickemit.py > /dev/null 2>&1 && echo 'bootstrap/harness/quickemit.py exists' || echo 'NO quickemit.py')"

# §1.6 -- the shapes, over every `.npk` the patches add
python3 -B "$TL/shapes.py" $(grep -ohE '^\+\+\+ b/.*\.npk$' "$T1"/step*.patch | sed "s|^+++ b/|$d/|") | sed "s|$d/||g"

# §1.7 -- the placeholders
echo "§1.7 placeholders in the patches: $(grep -ohE '@@PD-[0-9]+@@' "$T1"/step*.patch | sort -u | tr '\n' ' ')"

# §1.8 -- every pointer the patches write
python3 -B "$TL/pointers.py" "$d" "$T1" | sed "s|$d/||g"
rm -rf "${F:?}"
