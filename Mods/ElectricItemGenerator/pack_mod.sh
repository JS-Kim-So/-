#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
MOD_DIR="${ROOT_DIR}/ElectricItemGenerator"
OUTPUT_DIR="${ROOT_DIR}"
ZIP_NAME="ElectricItemGenerator.zip"

if [[ ! -d "${MOD_DIR}" ]]; then
  echo "Mod folder not found: ${MOD_DIR}" >&2
  exit 1
fi

cd "${ROOT_DIR}"
rm -f "${OUTPUT_DIR}/${ZIP_NAME}"
zip -r "${OUTPUT_DIR}/${ZIP_NAME}" "ElectricItemGenerator" >/dev/null
echo "Created ${OUTPUT_DIR}/${ZIP_NAME}"
