# Reproducing the ADEPT runs in this folder

All commands are run from the repository root unless noted. Total disk used is about
11 GB (venv 2.8 GB, models 3.2 GB, BHL tables 2.7 GB, names index 1.4 GB, OCR pages ~60 MB);
none of it is committed (see `.gitignore`).

```bash
# 1. ADEPT checkout pinned to v1.0.0 (= 8c6cf4e8c5a25ff79a1364bdde3f5c22752e77ab), plus our one patch
git clone https://github.com/NaturalHistoryMuseum/ADEPT.git adept_repro/vendor/ADEPT
git -C adept_repro/vendor/ADEPT checkout 8c6cf4e8c5a25ff79a1364bdde3f5c22752e77ab
git -C adept_repro/vendor/ADEPT apply ../../patches/0001-add-missing-adept-bhl-ocr-stub.patch

# 2. Python 3.11 env from ADEPT's own uv.lock, CPU torch instead of CUDA
cd adept_repro
uv venv --python 3.11 .venv-adept && source .venv-adept/bin/activate
(cd vendor/ADEPT && uv export --frozen --no-hashes --no-emit-project -o /tmp/adept-lock.txt)
grep -vE "^(nvidia-|triton==|torch==)" /tmp/adept-lock.txt > /tmp/adept-cpu.txt
uv pip install --torch-backend cpu "torch==2.10.0"
uv pip install -r /tmp/adept-cpu.txt
uv pip install --no-deps -e vendor/ADEPT
uv pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_trf-3.7.3/en_core_web_trf-3.7.3-py3-none-any.whl  # undeclared dependency
uv pip install duckdb==1.4.1   # only for our index builder
cd ..

# 3. BHL export tables (S3 open data, ~2.75 GB) and ADEPT's names index
mkdir -p adept_repro/.assets/bhl-data
for f in title item page pagename; do
  curl -sS -o adept_repro/.assets/bhl-data/$f.txt.gz https://bhl-open-data.s3.amazonaws.com/data/$f.txt.gz; done
python adept_repro/scripts/build_bhl_names_index.py --data adept_repro/.assets/bhl-data \
  --full adept_repro/.assets/bhl-names-full.parquet \
  --subset adept_repro/vendor/ADEPT/adept/.cache/bhl-names.parquet \
  --taxa "Achillea millefolium" "Leersia hexandra"

# 4. Evaluation reproductions (models download on first use via ADEPT's own code)
python adept_repro/scripts/eval_classifier.py --out adept_repro/outputs/classifier_eval
python adept_repro/scripts/eval_ner.py        --out adept_repro/outputs/ner_eval
python adept_repro/scripts/eval_traits.py     --out adept_repro/outputs/traits_eval

# 5. README examples, with page OCR from S3
python adept_repro/scripts/fetch_s3_ocr.py --taxa "Leersia hexandra"     --log adept_repro/outputs/s3_fetch/leersia_hexandra.csv
python adept_repro/scripts/fetch_s3_ocr.py --taxa "Achillea millefolium" --log adept_repro/outputs/s3_fetch/achillea_millefolium.csv
(cd adept_repro && adept traits --taxa "Leersia hexandra" --group angiosperm > outputs/logs/traits_leersia_default.log 2>&1)
(cd adept_repro && adept descriptions --taxa "Achillea millefolium"       > outputs/logs/descriptions_achillea.log 2>&1)
python adept_repro/scripts/export_run.py ...   # see the docstring; arguments are recorded in each outputs/*/run.json

# 6. PCAS botany pages (BHL item 48989); the committed fetch log doubles as the page list
python adept_repro/scripts/fetch_s3_ocr.py --pages adept_repro/outputs/pcas/s3_fetch_item48989.csv --log /tmp/pcas_fetch.csv
python adept_repro/scripts/run_pcas_pages.py --pages 13793662 13793669 13793689 13793690 13793698 --out adept_repro/outputs/pcas
```
