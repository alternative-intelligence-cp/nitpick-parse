# meta/roadmap/0.0/0.0.1a_tools/facts.sh -- re-derives `0.0.1a.md` §1, block 0b. Sourced after `../tools/env.sh`.
# Writes only under `$A/facts`, and removes it. Reads the compiler's tree with `git show` alone, and GitHub's record of
# the LLVM release with `gh api`, which downloads nothing.
F=$A/facts
rm -rf "${F:?}"; mkdir -p "$F"
T1=$REPO/meta/roadmap/0.0/0.0.1a_tools
TL=$REPO/meta/roadmap/0.0/tools
d=$F/tree; git clone -q --shared "$REPO" "$d"
for s in 1 2; do python3 -B "$TL/apply.py" "$d" 0.0.1a $s > /dev/null; done
env_of() { python3 -B -c 'import sys, yaml; print(yaml.safe_load(open(sys.argv[1]))["env"].get(sys.argv[2], "none"))' "$1" "$2"; }
llvm_key() { python3 -B -c 'import sys, yaml; print([s for s in yaml.safe_load(open(sys.argv[1]))["jobs"]["build"]["steps"] if s.get("id") == "llvm-cache"][0]["with"]["key"])' "$1"; }

# §1.1 -- the tree it starts from
ci=$REPO/.github/workflows/ci.yml
echo "§1.1 ci.yml pins the compiler at $(env_of "$ci" NITPICK_COMMIT), its emission at $(env_of "$ci" NPKC_LL_BYTES) B / $(env_of "$ci" NPKC_LL_SHA256 | cut -c1-8)…; LLVM_TARBALL_SHA256: $(env_of "$ci" LLVM_TARBALL_SHA256)"
echo "§1.1 its install step pipes the download into tar: $(grep -cF '| tar -xJ' "$ci") line(s); its LLVM cache key: $(llvm_key "$ci")"
python3 -B "$T1/dates.py" "$REPO" > "$F/dates0"
echo "§1.1 0.0.0's notes: $(grep -c '^(STALE) ' "$F/dates0") at their drafting date, $(grep -c '^(note) meta/' "$F/dates0") at 2026-10-17; decision sites: $(grep -c '^(site) meta' "$F/dates0"), $(grep -c '^(site)   beneath it, line NOT FOUND' "$F/dates0") with no note beneath"

# §1.2 -- the two pins: what moved between them that this plan reads
for p in nitpick.toml src/frontend/keywords.npk src/prelude/prelude.npk bootstrap/harness/quickemit.py runtime/npkrt.ll; do
  git -C "$NPK_TREE" diff --quiet "$OLD_PIN" "$PIN" -- "$p" && echo "§1.2 $p: byte-identical at $OLD_PIN and $PIN" || echo "§1.2 $p: DIFFERS between $OLD_PIN and $PIN"
done
echo "§1.2 npkrt.o, by each pin's SHA256SUMS: $(grep -h ' npkrt.o$' "$WB/.internal/toolchain/$OLD_PIN/SHA256SUMS" "$WB/.internal/toolchain/$PIN/SHA256SUMS" | cut -c1-16 | uniq | wc -l) digest(s), $(grep -h ' npkrt.o$' "$WB/.internal/toolchain/$PIN/SHA256SUMS" | cut -c1-8)…"
for k in llvm triple datalayout llc-flags llc-opt-flags opt-flags lld-flags; do
  pin=$(git -C "$NPK_TREE" show $PIN:nitpick.toml | grep -E "^$k +=" | sed -E 's/ +/ /g')
  ours=$(grep -E "^$k +=" "$d/nitpick.toml" | sed -E 's/ +/ /g')
  [ "$pin" = "$ours" ] && echo "§1.2 $k: the same as the compiler's at $PIN" || echo "§1.2 $k: DIFFERS -- $PIN [$pin] ours [$ours]"
done
echo "§1.2 the compiler's sitenorm.py at $PIN: $(git -C "$NPK_TREE" cat-file -e "$PIN:meta/roadmap/1.6/tools/sitenorm.py" 2>/dev/null && echo "$(git -C "$NPK_TREE" show "$PIN:meta/roadmap/1.6/tools/sitenorm.py" | grep -c 'landing 126') line(s) naming landing 126" || echo absent)"

# §1.3 -- CI's rows as step 1 writes them, against the compiler and notice 140's npkc.ll row in the pin's notes
ci1=$d/.github/workflows/ci.yml
row=$(grep -E '^ +npkc\.ll +[0-9a-f]{64} +[0-9]+ B' "$WB/.internal/toolchain/$PIN/PIN.md")
echo "§1.3 NITPICK_COMMIT: $(env_of "$ci1" NITPICK_COMMIT); the compiler clone's $PIN: $(git -C "$NPK_TREE" rev-parse --verify -q "$PIN^{commit}")"
echo "§1.3 notice 140's npkc.ll row, PIN.md: $(echo "$row" | awk '{print $3 " B / " $2}')"
echo "§1.3 NPKC_LL_BYTES / NPKC_LL_SHA256:  $(env_of "$ci1" NPKC_LL_BYTES) B / $(env_of "$ci1" NPKC_LL_SHA256)"

# §1.4 -- the LLVM asset: GitHub's record of it against step 1's pin and the digest step 1 files
gh api repos/llvm/llvm-project/releases/tags/llvmorg-20.1.8 --jq '"\(.immutable) " + (.assets[] | select(.name == "LLVM-20.1.8-Linux-X64.tar.xz") | "\(.id) \(.size) \(.digest)")' > "$F/rel" 2>&1
read -r imm aid size dig < "$F/rel"
echo "§1.4 GitHub's record: asset $aid, $size B, $dig; the release immutable: $imm"
echo "§1.4 LLVM_TARBALL_SHA256: sha256:$(env_of "$ci1" LLVM_TARBALL_SHA256); the digest file names it on $(grep -c "$(env_of "$ci1" LLVM_TARBALL_SHA256)" "$d/meta/research/llvm-release-asset.md") line(s); the LLVM cache key: $(llvm_key "$ci1")"

# §1.5 -- the workflow as step 1 leaves it
python3 -B - "$ci1" "$F" <<'PY'
import os, subprocess, sys, yaml
doc = yaml.safe_load(open(sys.argv[1]))
steps = doc["jobs"]["build"]["steps"]
runs = [s["run"] for s in steps if "run" in s]
bad = 0
for i, r in enumerate(runs):
    p = os.path.join(sys.argv[2], "step%d.sh" % i)
    open(p, "w").write(r)
    bad += subprocess.run(["bash", "-n", p], capture_output=True).returncode != 0
on = doc.get("on", doc.get(True))
print("§1.5 the workflow parses; %d steps; runs-on %s; on %s" % (len(steps), doc["jobs"]["build"]["runs-on"], " ".join(sorted(on))))
print("§1.5 the steps' scripts: %d, and %d that bash -n refuses" % (len(runs), bad))
PY

# §1.6 -- the dated lines as step 2 leaves them
python3 -B "$T1/dates.py" "$d" > "$F/dates2"
echo "§1.6 0.0.0's notes: $(grep -c '^(STALE) ' "$F/dates2") at their drafting date, $(grep -c '^(note) meta/' "$F/dates2") at 2026-10-17; decision sites: $(grep -c '^(site) meta' "$F/dates2"), $(grep -c '^(site)   beneath it, line NOT FOUND' "$F/dates2") with no note beneath"

# §1.7 -- the keyword table and the rulings at the new pin, over every `.npk` of the tree
git -C "$NPK_TREE" show "$PIN:src/frontend/keywords.npk" > "$F/keywords.npk"
echo "§1.7 planted control: $(python3 -B "$TL/names.py" --count "$F/keywords.npk" "$TL/names_planted.txt" | head -1)"
echo "§1.7 clean control: $(python3 -B "$TL/names.py" --count "$F/keywords.npk" "$TL/names_clean.txt" | head -1)"
echo "§1.7 the tree: $(cd "$d" && python3 -B "$TL/names.py" --count "$F/keywords.npk" $(git ls-files '*.npk') | head -1)"
(cd "$d" && python3 -B "$TL/rulings.py" $(git ls-files '*.npk')) | sed 's/^/§1.7 rulings: /'

# §1.8 -- the placeholders, the run's date, and the pointers
python3 -B - "$T1" "$REPO" <<'PY'
import glob, os, re, subprocess, sys
added = lambda raw: [l for l in raw.split("\n") if l.startswith("+") and not l.startswith("+++")]
raws = {os.path.basename(p): open(p, encoding="utf-8").read() for p in sorted(glob.glob(os.path.join(sys.argv[1], "step*.patch")))}
ph = sorted(set(re.findall(r"@@(PD-\d+)@@", "".join(raws.values()))), key=lambda x: int(x[3:]))
dec = sorted(set(re.findall(r"^\+### @@(PD-\d+)@@", "".join(raws.values()), re.M)))
print("§1.8 placeholders in the patches: %s; declared by them: %s" % (" ".join("@@%s@@" % p for p in ph), " ".join(dec) or "none"))
print("§1.8 added lines carrying @@DATE@@, by step: %s" % " ".join("%s %d" % (k[:-6], sum("@@DATE@@" in l for l in added(v))) for k, v in raws.items()))
touched = sorted({m for v in raws.values() for m in re.findall(r"^\+\+\+ b/(\S+)", v, re.M)})
held = [f for f in touched if os.path.isfile(os.path.join(sys.argv[2], f)) and "@@DATE@@" in open(os.path.join(sys.argv[2], f), encoding="utf-8").read()]
print("§1.8 files the patches touch that hold @@DATE@@ as the tree stands: %s" % (" ".join(held) or "none"))
PY
python3 -B "$TL/pointers.py" "$d" "$T1" | sed 's/^§1\.8/§1.8/'

rm -rf "${F:?}"
