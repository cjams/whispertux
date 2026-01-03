#!/bin/bash
# WhisperTux Benchmark Script

BINARY="/home/e/opt/wispr-tux2/whisper.cpp/build/bin/whisper-cli"
MODEL="/home/e/opt/wispr-tux2/whisper.cpp/models/ggml-small.en.bin"
SAMPLE="/home/e/opt/wispr-tux2/whisper.cpp/samples/jfk.wav"

echo "=== WhisperTux Benchmark ==="
echo "Binary: $BINARY"
echo "Model: small.en"
echo "Sample: JFK (11 seconds audio)"
echo ""

for THREADS in 4 8 12 16; do
    echo "Testing with $THREADS threads..."

    # Run 3 times and get average
    TOTAL=0
    for i in 1 2 3; do
        # Extract just the total time (in ms)
        OUTPUT=$($BINARY -m $MODEL -f $SAMPLE --language en --threads $THREADS --no-timestamps --no-prints 2>&1 | grep "total time")
        TIME=$(echo $OUTPUT | grep -oP 'total time = \K[0-9]+')
        echo "  Run $i: ${TIME}ms"
        TOTAL=$((TOTAL + TIME))
    done

    AVG=$((TOTAL / 3))
    echo "  Average: ${AVG}ms ($(echo "scale=2; $AVG/1000" | bc)s)"
    echo ""
done

echo "Benchmark complete!"
