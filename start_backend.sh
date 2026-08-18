#!/bin/bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20

cd /home/monic/projects/BridgeAI
source venv/bin/activate
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
