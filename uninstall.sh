#!/bin/bash

# Script position
SCRIPT=$(readlink -f "$0")
SCRIPT_PATH=$(dirname "$SCRIPT")

# Color table
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

RUN_FILE_NAME="${SCRIPT_PATH}/run.sh"
RUN_FILE="\"${SCRIPT_PATH}/src/automatic_invester.py\""

# Check Root 
echo -e "[${GREEN}Info${NC}] Root access verification"
if [ "$EUID" -ne 0 ]
    then echo -e "[${RED}Error${NC}] This script needs root access to uninstall the service module"
    exit
fi

# Stop services
echo -e "[${GREEN}Info${NC}] Stopping services"
sudo systemctl stop binance.service
sudo systemctl disable binance.service

# Remove run file
echo -e "[${GREEN}Info${NC}] Removing run file"
rm "${RUN_FILE_NAME}"

# Remove automatic running services under the same name
echo -e "[${GREEN}Info${NC}] Removing services"
sudo rm /etc/systemd/system/binance.service

# Reset systemctl and reload 
echo -e "[${GREEN}Info${NC}] Reloading Systemctl"
sudo systemctl daemon-reload
sudo systemctl reset-failed

echo -e "[${GREEN}Info${NC}] Success!" 