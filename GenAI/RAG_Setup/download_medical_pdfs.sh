#!/bin/bash
# download_medical_pdfs.sh
# Run with: bash download_medical_pdfs.sh  (NOT sh)

BUCKET="aib_raw_pdfs"
PREFIX="pdfs"
TMP_DIR="/tmp/rag_pdfs"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"

mkdir -p "$TMP_DIR"
SUCCESS=0
FAILED=0

echo "========================================================="
echo "Downloading medical PDFs → gs://$BUCKET/$PREFIX/"
echo "========================================================="

download_and_upload() {
  local FILENAME="$1"
  local URL="$2"
  local LOCAL="$TMP_DIR/$FILENAME"

  echo ""
  echo "→ $FILENAME"

  wget -q --user-agent="$UA" -O "$LOCAL" "$URL"

  # Check it's actually a PDF, not an HTML error page
  HEADER=$(head -c 5 "$LOCAL" 2>/dev/null)
  if [ "$HEADER" = "%PDF-" ]; then
    SIZE=$(du -sh "$LOCAL" | cut -f1)
    echo "  ✓ Downloaded ($SIZE)"
    gsutil cp "$LOCAL" "gs://$BUCKET/$PREFIX/$FILENAME"
    echo "  ✓ Uploaded to gs://$BUCKET/$PREFIX/$FILENAME"
    SUCCESS=$((SUCCESS + 1))
  else
    echo "  ✗ Not a valid PDF (likely HTML redirect). See manual instructions below."
    FAILED=$((FAILED + 1))
  fi

  rm -f "$LOCAL"
}

# 1. WHO Essential Medicines 23rd Edition (2023) — reliable direct PDF
download_and_upload \
  "01_who_essential_medicines_2023.pdf" \
  "https://iris.who.int/bitstream/handle/10665/371090/WHO-MHP-HPS-EML-2023.02-eng.pdf?sequence=1&isAllowed=y"

# 2. NIH COVID-19 Treatment Guidelines
download_and_upload \
  "02_nih_covid19_treatment_guidelines.pdf" \
  "https://www.ncbi.nlm.nih.gov/books/NBK570371/pdf/Bookshelf_NBK570371.pdf"

# 3. NIH Drug Information Portal — Metformin monograph
download_and_upload \
  "03_metformin_monograph.pdf" \
  "https://www.ncbi.nlm.nih.gov/books/NBK279014/pdf/Bookshelf_NBK279014.pdf"

# 4. NIH StatPearls — Pharmacology Overview (open access)
download_and_upload \
  "04_nih_pharmacology_overview.pdf" \
  "https://www.ncbi.nlm.nih.gov/books/NBK554495/pdf/Bookshelf_NBK554495.pdf"

echo ""
echo "========================================================="
echo "Done — success: $SUCCESS  failed: $FAILED"
echo ""
gsutil ls "gs://$BUCKET/$PREFIX/"
echo "========================================================="

cat << 'MANUAL'

── IF ANY DOWNLOAD FAILED — manual steps ────────────────────────────
Download in your browser and upload via gsutil:

  gsutil cp /path/to/file.pdf gs://aib_raw_pdfs/pdfs/filename.pdf

FDA labels (browser download required — they block bots):
  https://www.accessdata.fda.gov/drugsatfda_docs/label/2024/761248s000lbl.pdf
  https://www.accessdata.fda.gov/drugsatfda_docs/label/2024/761069s045lbl.pdf
─────────────────────────────────────────────────────────────────────
MANUAL