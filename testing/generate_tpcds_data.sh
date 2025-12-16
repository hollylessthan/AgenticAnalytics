#!/bin/bash

# Generate TPC-DS benchmark data
# Usage: ./generate_tpcds_data.sh <scale_factor> [parallel]
# Example: ./generate_tpcds_data.sh 100 4  # 100GB with 4 parallel processes

set -e

SCALE=${1:-1}  # Default 1GB
PARALLEL=${2:-1}  # Default single process
OUTPUT_DIR="$(pwd)/data/tpcds"

echo "🚀 TPC-DS Data Generation"
echo "=========================="
echo "Scale Factor: ${SCALE}GB"
echo "Parallel Jobs: ${PARALLEL}"
echo "Output Directory: ${OUTPUT_DIR}"
echo ""

# Check if tpcds-kit exists
if [ ! -d "../tpcds-kit" ]; then
    echo "📦 Cloning TPC-DS kit..."
    cd ..
    git clone https://github.com/databricks/tpcds-kit.git
    cd tpcds-kit/tools
    
    # Detect OS and compile
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "🔨 Compiling for macOS..."
        make OS=MACOS
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "🔨 Compiling for Linux..."
        make OS=LINUX
    else
        echo "❌ Unsupported OS: $OSTYPE"
        exit 1
    fi
    
    cd ../../testing
fi

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Check if data already exists
if [ -f "${OUTPUT_DIR}/store_sales.dat" ]; then
    echo "⚠️  Data already exists in ${OUTPUT_DIR}"
    read -p "Delete and regenerate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Removing existing data..."
        rm -rf "${OUTPUT_DIR}"/*
    else
        echo "✅ Using existing data"
        exit 0
    fi
fi

# Generate data
echo "⏳ Generating data (this may take a while)..."
echo "   - 1GB scale: ~2 minutes"
echo "   - 10GB scale: ~15 minutes"
echo "   - 100GB scale: ~30 minutes"
echo ""

START_TIME=$(date +%s)

cd ../tpcds-kit/tools

if [ ${PARALLEL} -gt 1 ]; then
    echo "🔄 Running with ${PARALLEL} parallel processes..."
    ./dsdgen -scale ${SCALE} -dir "${OUTPUT_DIR}" -parallel ${PARALLEL} -force
else
    echo "🔄 Running single process..."
    ./dsdgen -scale ${SCALE} -dir "${OUTPUT_DIR}" -force
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

cd ../../testing

echo ""
echo "✅ Data generation complete!"
echo "⏱️  Time taken: ${DURATION} seconds"
echo "📁 Location: ${OUTPUT_DIR}"
echo ""

# Show file sizes
echo "📊 Generated files:"
du -sh "${OUTPUT_DIR}"/*.dat 2>/dev/null | head -10 || echo "No .dat files found"

echo ""
echo "🎯 Next steps:"
echo "   1. Run: python setup_tpcds_duckdb.py --scale ${SCALE}"
echo "   2. Generate RAG docs: python generate_rag_documents.py"
echo "   3. Run tests: python run_performance_tests.py"
