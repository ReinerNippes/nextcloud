#!/usr/bin/env bash
set -euo pipefail

# Cross-distribution matrix test for Hetzner stacks:
# - pulumi up
# - ansible playbook
# - pulumi destroy
# with separate logs per stack.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/.logs/matrix"

DEFAULT_STACKS=(
  debian12
  debian13
  ubuntu2404
  alma10
  rocky10
  centos10
)

if [[ -n "${STACKS:-}" ]]; then
  # Accept comma- or space-separated list, e.g. STACKS="alma10,fedora43".
  stack_input="${STACKS//,/ }"
  read -r -a STACK_LIST <<< "${stack_input}"
else
  STACK_LIST=("${DEFAULT_STACKS[@]}")
fi

mkdir -p "${LOG_DIR}"

cd "${ROOT_DIR}"
source cloud-stuff/.venv/bin/activate

echo "Running stacks: ${STACK_LIST[*]}"

for stack in "${STACK_LIST[@]}"; do
  echo "=== STACK: ${stack} ==="
  ts="$(date +%Y%m%d-%H%M%S)"

  # Read HCLOUD_TOKEN from stack config (needed by dynamic inventory)
  export HCLOUD_TOKEN="$(cd cloud-stuff && pulumi config get hetzner:token --stack "${stack}")"

  pulumi_log="${LOG_DIR}/${stack}-${ts}-pulumi-up.log"
  ansible_log="${LOG_DIR}/${stack}-${ts}-ansible.log"
  destroy_log="${LOG_DIR}/${stack}-${ts}-pulumi-destroy.log"

  (
    cd cloud-stuff
    pulumi up --yes --stack "${stack}"
  ) 2>&1 | tee "${pulumi_log}"
  up_rc=${PIPESTATUS[0]}

  if [[ ${up_rc} -eq 0 ]]; then
    ./nextcloud.yml -i "hetzner-inventory-dynamic.${stack}.hcloud.yml" \
      2>&1 | tee "${ansible_log}"
    ansible_rc=${PIPESTATUS[0]}
  else
    ansible_rc=99
  fi

  (
    cd cloud-stuff
    pulumi destroy --yes --stack "${stack}"
  ) 2>&1 | tee "${destroy_log}"
  destroy_rc=${PIPESTATUS[0]}

  if [[ ${up_rc} -ne 0 || ${ansible_rc} -ne 0 || ${destroy_rc} -ne 0 ]]; then
    echo "Failure in stack ${stack}"
    echo "pulumi up log:      ${pulumi_log}"
    echo "ansible log:        ${ansible_log}"
    echo "pulumi destroy log: ${destroy_log}"
    exit 1
  fi
done

echo "All stacks completed successfully. Logs: ${LOG_DIR}"
