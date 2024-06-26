#!/bin/bash

# Script position
SCRIPT=$(readlink -f "$0")
SCRIPT_PATH=$(dirname "$SCRIPT")

# Color table
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "[${YELLOW}Warning${NC}] This script will install a root service in your distribution that will start at startup. If you want to prevent that from happening, you should not continue this procedure: [Press Space to continue]"
read

# Check Root 
echo -e "[${GREEN}Info${NC}] Root access verification"
if [ "$EUID" -ne 0 ]
    then echo -e "[${RED}Error${NC}] This script needs root access to install some Python dependencies and the service itself"
    exit
fi

# Install python
echo -e "[${GREEN}Info${NC}] Installing Python3"
sudo apt update
sudo apt install python3 -y

# Install python-pip
echo -e "[${GREEN}Info${NC}] Installing Python3-pip"
sudo apt install python3-pip -y

# Install python packages
echo -e "[${GREEN}Info${NC}] Installing Binance connector dependencies"
sudo pip3 install python-binance
sudo pip3 install binance-connector

# Create run.sh file
# Install python
echo -e "[${GREEN}Info${NC}] Creating the running shell file"

FILE_NAME="'${SCRIPT_PATH}/run.sh'"
RUN_FILE="'${SCRIPT_PATH}/src/automatic_invester.py'"
echo -e "#!/bin/bash\n\n/bin/python3 ${RUN_FILE}">run.sh

# Set the execute only priviledges
chmod 111 ${FILE_NAME}