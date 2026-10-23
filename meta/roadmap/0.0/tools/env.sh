# meta/roadmap/0.0/tools/env.sh -- sourced at the top of EVERY command block of cycle 0.0's subcycle plans, because a
# Bash call keeps no variables and no functions from the call before it. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.0/tools/env.sh"
#
# THE PATHS ARE THE CHECKOUT'S: `WB` is the directory above it (the workbench), `NPK_TREE` the compiler beside that,
# `CHECK` the workbench's `skills/check/scripts`, and `check_refs` resolves `CLAUDE.md`'s two links up into the
# workbench, `../BOARD.md` and `../WORKSTREAMS.md` -- so a block run in a relocated copy finds another workbench or
# none (and, without those two files, two `broken-link` findings in every `refs`), and the blocks are run in the
# checkout the dispatch names. `$NPK_TREE` is read with `git show` and `git rev-parse`
# alone. The toolchain is the pin `2e1cb4a`'s from cycle 0.0.1a, the adoption of the libraries' second re-pin (0.0.0
# and 0.0.1 ran at `c9baa9e`, as their records say), whose LLVM, 20.1.8, is the machine's own: `llc`, `opt` and
# `ld.lld` are found on PATH, and every step 0 block prints what each reports -- anything but 20.1.8 is a stop. `$NPKC`
# and `$NPKRT` come from the dispatch's TOOLCHAIN line when it sets them, and from the workbench's copy of the pin when
# it does not; `$NPKC_OLD` and `$NPKRT_OLD`, the kept pin `c9baa9e`'s, the same way, and only 0.0.1a's old-pin leg
# reads them. TMPDIR is this cycle's scratch, `$A/tmp`; every `rm` names its target through `${VAR:?}`; nothing printed
# carries a path above the repository, so no output carries a home directory into a record.
: "${REPO:?set REPO to the REPO line of the dispatch, first}"
REPO=$(realpath "$REPO")
WB=$(realpath "$REPO/..")
NPK_TREE=$(realpath "$WB/../nitpick")
PIN=2e1cb4a
PIN_FULL=2e1cb4adef795488c0530be297e441f923bbe090
OLD_PIN=c9baa9e
OLD_PIN_FULL=c9baa9e91c553d8db2a2a62f09c36b30a984b07f
NPKC=${NPKC:-$WB/.internal/toolchain/$PIN/npkc}
NPKRT=${NPKRT:-$WB/.internal/toolchain/$PIN/npkrt.o}
NPKC_OLD=${NPKC_OLD:-$WB/.internal/toolchain/$OLD_PIN/npkc}
NPKRT_OLD=${NPKRT_OLD:-$WB/.internal/toolchain/$OLD_PIN/npkrt.o}
TOOLS=$REPO/meta/roadmap/0.0/tools
A=$REPO/.internal/w00
CHECK=$WB/skills/check/scripts
mkdir -p "$A/tmp"
TMPDIR=$A/tmp
export NPKC NPKRT NPKC_OLD NPKRT_OLD TMPDIR A TOOLS

# Compile each file as a root from its own directory: `<file>: compiles`, or each diagnostic's code and its site in
# the file, `CODE L:C`, in the order the compiler reports them, and `npkc` exit status beside them.
#     codes <file>...     (a relative file is the repository's)
codes() {
  local f src out rc b
  for f in "$@"; do
    src=$f; [ "${f#/}" = "$f" ] && src="$REPO/$f"
    b=$(basename "$src")
    out=$(cd "$(dirname "$src")" && "$NPKC" "$b" -o /dev/null 2>&1)
    rc=$?
    if [ -z "$out" ] && [ "$rc" = 0 ]; then echo "$b: compiles"; continue; fi
    echo "$b: npkc $rc -- $(printf '%s\n' "$out" | grep -oE '^NITPICK-[A-Z]+-[0-9]+ [^ ]+:[0-9]+:[0-9]+' \
      | sed -E 's|^(NITPICK-[A-Z]+-[0-9]+) [^ ]*:([0-9]+:[0-9]+)$|\1 \2|' | tr '\n' ' ' | sed 's/ $//')"
  done
}

# Build each file as a program and run it at -O0 and through `opt -O2`: `npkc`, `llc`, `ld.lld`, the binary -- all
# four, because `npkc` exit 0 is not a module `llc` accepts. A file carrying `// mem-cap-mib: N` runs under that
# address-space cap (`ulimit -v`), as the harness will run it, after a floor program built by the same toolchain
# under the same cap -- the control `PLAYBOOK.md` §9 asks for -- whose exit is printed first.
#     run4 <file>...     (a relative file is the repository's)
run4() {
  local f src b o r0 r2 cap pre
  mkdir -p "$A/run4"
  for f in "$@"; do
    src=$f; [ "${f#/}" = "$f" ] && src="$REPO/$f"
    b=$(basename "$src" .npk); o="$A/run4/$b"
    if ! ( cd "$(dirname "$src")" && "$NPKC" "$(basename "$src")" -o "$o.ll" ) > "$o.npkc" 2>&1; then
      echo "$b: npkc refused -- $(grep -oE '^NITPICK-[A-Z]+-[0-9]+' "$o.npkc" | sort -u | tr '\n' ' ')"; continue
    fi
    if ! llc -O0 -filetype=obj -relocation-model=static "$o.ll" -o "$o.o" 2> "$o.llc"; then
      echo "$b: llc refused -- $(grep -m1 -oE "use of undefined value '[^']+'" "$o.llc")"; continue
    fi
    ld.lld -static "$o.o" "$NPKRT" -o "$o"
    opt -O2 -S "$o.ll" -o "$o.2.ll" && llc -O2 -filetype=obj -relocation-model=static "$o.2.ll" -o "$o.2.o" \
      && ld.lld -static "$o.2.o" "$NPKRT" -o "$o.2"
    cap=$(grep -m1 -oE '^// mem-cap-mib: [0-9]+' "$src" | grep -oE '[0-9]+$')
    if [ -n "$cap" ]; then
      floor_program
      ( ulimit -v $((cap * 1024)); "$A/floor/floor" ); pre="under ${cap} MiB the floor program exits $?; "
      ( ulimit -v $((cap * 1024)); "$o" > /dev/null 2>&1 ); r0=$?
      ( ulimit -v $((cap * 1024)); "$o.2" > /dev/null 2>&1 ); r2=$?
    else
      pre=""; "$o" > /dev/null 2>&1; r0=$?; "$o.2" > /dev/null 2>&1; r2=$?
    fi
    echo "$b: ${pre}-O0 $r0, -O2 $r2"
  done
}

# A program that allocates nothing, built once by the pinned toolchain: the control under an address-space cap.
floor_program() {
  [ -x "$A/floor/floor" ] && return 0
  mkdir -p "$A/floor"
  printf '%s\n' 'mod:floor;' '' 'func:main = int32(cstring[]:_~argv) {' '    exit 0i32;' '};' '' \
    'func:failsafe = int32(Error:e) {' '    pick (e) {' '        (HeapBadRequest)    { exit 91i32; },' \
    '        (HeapOom)           { exit 92i32; },' '        (Unreachable)       { exit 95i32; },' \
    '        (WildLeak)          { exit 96i32; },' '        (StackExhausted)    { exit 106i32; },' \
    '        (MachineFault)      { exit 107i32; },' '        (*)                 { exit 99i32; }' '    }' \
    '    exit 9i32;' '};' > "$A/floor/floor.npk"
  ( cd "$A/floor" && "$NPKC" floor.npk -o floor.ll ) && llc -O0 -filetype=obj -relocation-model=static \
    "$A/floor/floor.ll" -o "$A/floor/floor.o" && ld.lld -static "$A/floor/floor.o" "$NPKRT" -o "$A/floor/floor"
}

# The identities `NITPICK-REACH-003` names for a root that imports <file> and declares no `failsafe` -- what a
# consumer of that module owes (`PLAYBOOK.md` §6, the compiler as the oracle). The root is written in `$A/reach`,
# importing the file by its relative path, compiled, and removed.
#     bill <file>...     (a relative file is the repository's)
bill() {
  local f src d="$A/reach" r
  mkdir -p "$d"; r="$d/zz_reach_root.npk"
  for f in "$@"; do
    src=$f; [ "${f#/}" = "$f" ] && src="$REPO/$f"
    printf 'mod:zz_reach_root;\n\nuse "%s".*;\n\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n' \
      "$(realpath --relative-to="$d" "$src")" > "$r"
    echo "$(basename "$src"): $(cd "$d" && "$NPKC" zz_reach_root.npk -o /dev/null 2>&1 \
      | grep -oE '[0-9]+ identities: [^-]*' | sed 's/ *$//')"
  done
  rm -rf "${d:?}"
}

# The steps' patches applied in order to a throwaway clone of HEAD -- the check that the tree is the one they were
# cut from, before any is applied here. `--shared`, so it costs no object copy; removed after.
#     dryrun <subcycle> <step>...
dryrun() {
  local d="$A/dry" sub=$1 n; shift
  rm -rf "${d:?}"; git clone -q --shared "$REPO" "$d"
  for n in "$@"; do python3 -B "$TOOLS/apply.py" "$d" "$sub" "$n" | sed 's/^/dry run: /'; done
  rm -rf "${d:?}"
}

# The workbench's reference check over the repository, its exit status read on its own line -- never through a pipe.
#     refs
refs() {
  ( cd "$REPO" && python3 -B "$CHECK/check_refs.py" . ) > "$A/refs.out" 2>&1
  echo "check_refs exit $?"
  sed -E 's/  +/ /g' "$A/refs.out"
}

# A workflow's top-level `env:` rows, read two ways -- as YAML reads them, and by the row pattern the counts use,
# `^  [A-Z][A-Z0-9_]*: `, a capital and then capitals, digits and `_` -- then how many are quoted; and the pattern's
# positive control: each row YAML names, planted unquoted in a copy in turn, must move one row from quoted to
# unquoted. The control takes its rows from YAML, not from the pattern, so a row the pattern misses shows. (Cycle
# 0.0's text round, 2026-10-21: the counts' first pattern, `[A-Z_]+`, could not match `NPKC_LL_SHA256`.)
#     envrows <workflow>
envrows() {
  local ci=$1 row='^  [A-Z][A-Z0-9_]*: ' k names
  names=$(python3 -B -c 'import sys, yaml; print(" ".join(yaml.safe_load(open(sys.argv[1]))["env"]))' "$ci")
  echo "env rows as YAML reads them: $names"
  echo "env rows as the pattern reads them: $(grep -oE "$row" "$ci" | sed -E 's/^  //; s/: $//' | tr '\n' ' ' | sed 's/ $//')"
  echo "quoted: $(grep -cE "$row\"" "$ci") env row(s); unquoted env rows: $(grep -cE "$row[^\"]" "$ci")"
  for k in $names; do
    sed -E "s/^(  $k: )\"(.*)\"\$/\1\2/" "$ci" > "$A/tmp/envrows.yml"
    echo "planted, $k unquoted: quoted $(grep -cE "$row\"" "$A/tmp/envrows.yml"), unquoted $(grep -cE "$row[^\"]" "$A/tmp/envrows.yml")"
  done
  rm -f "${A:?}/tmp/envrows.yml"
}

# `apply.py`'s label checks, each seen to STOP on a mutated copy of this plan's folder: a bare PD-131 in an added line
# of 0.0.4's step 4 (the plan verification of 2026-10-15, its finding 1), and @@PD-144@@ cited in 0.0.4's step 1,
# which step 2 declares (its finding 5); and, planted in 0.0.0's step 1, which carries no label, a number past the
# base -- `PA-` and the base plus 900, made here and named in the output, so no file of the plan writes it -- and
# @@PD-999@@, which no step declares (the second plan verification's finding 6). The copy is applied to no tree --
# the checks stop it before `git apply` runs, and a check that did not would fail on the missing directory instead, a
# different line -- and is removed after.
#     label_mutants
label_mutants() {
  local d="$A/labels" pa
  pa="PA-$(( $(sed -n 's/^base PA-//p' "$TOOLS/decisions.txt") + 900 ))"
  rm -rf "${d:?}"; mkdir -p "$d"; cp -r "$TOOLS/.." "$d/plan"
  sed -i '0,/^+.*@@PD-131@@/s/@@PD-131@@/PD-131/' "$d/plan/0.0.4_tools/step4.patch"
  echo "label mutant, a bare PD-131 in 0.0.4's step 4: $(python3 -B "$d/plan/tools/apply.py" "$d/none" 0.0.4 4 2>&1)"
  cp "$TOOLS/../0.0.4_tools/step4.patch" "$d/plan/0.0.4_tools/step4.patch"
  sed -i '0,/^+.*@@PD-143@@/s/@@PD-143@@/@@PD-143@@, @@PD-144@@/' "$d/plan/0.0.4_tools/step1.patch"
  echo "label mutant, @@PD-144@@ cited in 0.0.4's step 1: $(python3 -B "$d/plan/tools/apply.py" "$d/none" 0.0.4 1 2>&1)"
  cp "$TOOLS/../0.0.4_tools/step1.patch" "$d/plan/0.0.4_tools/step1.patch"
  sed -i "0,/^+\/\/ PROBE 01a/s//+\/\/ $pa PROBE 01a/" "$d/plan/0.0.0_tools/step1.patch"
  echo "label mutant, a number past the base in 0.0.0's step 1: $(python3 -B "$d/plan/tools/apply.py" "$d/none" 0.0.0 1 2>&1 | sed "s/$pa/the base plus 900/")"
  cp "$TOOLS/../0.0.0_tools/step1.patch" "$d/plan/0.0.0_tools/step1.patch"
  sed -i '0,/^+\/\/ PROBE 01a/s//+\/\/ @@PD-999@@ PROBE 01a/' "$d/plan/0.0.0_tools/step1.patch"
  echo "label mutant, a placeholder no step declares in 0.0.0's step 1: $(python3 -B "$d/plan/tools/apply.py" "$d/none" 0.0.0 1 2>&1)"
  rm -rf "${d:?}"
}

# Whether a file's first line is a research digest's heading, `# <topic> — research digest` -- the line by which
# `sweep.py` leaves a digest out of every sweep (its `DIGEST`, after the workbench research skill's §5), so a digest
# filed with another first line would be swept as live text: `first line a digest heading`, or `... NOT ...`.
#     heading <file>
heading() {
  python3 -B -c 'import os, sys; sys.path.insert(0, sys.argv[1]); import sweep
first = open(sys.argv[2], encoding="utf-8").readline() if os.path.isfile(sys.argv[2]) else ""
print("first line %sa digest heading" % ("" if sweep.DIGEST.match(first.rstrip("\n")) else "NOT "))' "$TOOLS" "$1"
}
