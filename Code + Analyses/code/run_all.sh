#!/bin/bash
# run_all.sh — Volledige testsuite voor NP-Hard Pac-Man benchmarking.
#
# Runt elk model op alle levels van Serie 1, 2 en 3 (levels 0-17).
# Serie 4 (wager level, index 18) wordt overgeslagen.
#
# Gebruik:
#   chmod +x run_all.sh
#   ./run_all.sh                        # alle modellen, alle levels
#   ./run_all.sh deepseek-chat          # alleen DeepSeek
#   ./run_all.sh deepseek-chat claude   # DeepSeek + Claude
#
# Output:
#   - JSON-logs per run in logs/
#   - Terminal-output per model in logs/terminal/<model>.txt
#
# Achtergrond draaien (sluit terminal gerust):
#   nohup ./run_all.sh > logs/terminal/run_all.txt 2>&1 &

set -euo pipefail

# ── Configuratie ───────────────────────────────────────────────────────────────
RUNS=5           # aantal runs per level per model
LEVELS=(0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17)  # Serie 1-3, geen wager
LOG_DIR="logs"
TERMINAL_DIR="logs/terminal"

ALL_MODELS=(
    "claude-opus-4-7"
    "gpt-5.4"
    "deepseek-chat"
    "gemini-2.5-pro"
    "kimi-k2.6"
)

# Als argumenten meegegeven: gebruik die als modellen
if [ $# -gt 0 ]; then
    ALL_MODELS=("$@")
fi

# ── Setup ──────────────────────────────────────────────────────────────────────
mkdir -p "$LOG_DIR" "$TERMINAL_DIR"

echo "========================================================"
echo "  NP-Hard Pac-Man — Volledige testsuite"
echo "  Modellen : ${ALL_MODELS[*]}"
echo "  Levels   : ${#LEVELS[@]} (Serie 1-3)"
echo "  Runs/lvl : $RUNS"
echo "  Gestart  : $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================================"

TOTAL_RUNS=$(( ${#ALL_MODELS[@]} * ${#LEVELS[@]} * RUNS ))
echo "  Totaal te draaien runs: $TOTAL_RUNS"
echo ""

COMPLETED=0
FAILED=0

# ── Hoofd-loop ─────────────────────────────────────────────────────────────────
for MODEL in "${ALL_MODELS[@]}"; do
    MODEL_LOG="$TERMINAL_DIR/${MODEL}.txt"
    echo "--------------------------------------------------------"
    echo "  Model: $MODEL"
    echo "  Log  : $MODEL_LOG"
    echo "--------------------------------------------------------"

    # Leeg model-logbestand aan het begin van dit model
    echo "Model: $MODEL  |  Gestart: $(date '+%Y-%m-%d %H:%M:%S')" > "$MODEL_LOG"

    for LEVEL_IDX in "${LEVELS[@]}"; do
        echo "  [$(date '+%H:%M:%S')] Level index $LEVEL_IDX — $RUNS runs..."

        # Runs 1 t/m RUNS voor dit level
        for RUN in $(seq 1 $RUNS); do
            echo -n "    Run $RUN/$RUNS... "

            # Voer de run uit; vang fouten op zonder het script te stoppen
            if python api_runner.py \
                --model "$MODEL" \
                --level "$LEVEL_IDX" \
                --runs 1 \
                >> "$MODEL_LOG" 2>&1; then
                echo "klaar"
                COMPLETED=$(( COMPLETED + 1 ))
            else
                echo "FOUT (zie $MODEL_LOG)"
                FAILED=$(( FAILED + 1 ))
            fi

            # Korte pauze tussen runs om rate limits te vermijden
            sleep 1
        done
    done

    echo "  Model $MODEL klaar: $(date '+%H:%M:%S')"
    echo ""
done

# ── Eindstats ──────────────────────────────────────────────────────────────────
echo "========================================================"
echo "  KLAAR — $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Geslaagd : $COMPLETED / $TOTAL_RUNS"
echo "  Mislukt  : $FAILED"
echo "========================================================"

# Draai analyze_logs.py als alles klaar is
if [ -f "analyze_logs.py" ]; then
    echo ""
    echo "  Cognitieve flexibiliteitsanalyse:"
    python analyze_logs.py
fi
