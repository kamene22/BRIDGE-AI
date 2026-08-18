#!/bin/bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20
cd /home/monic/projects/BridgeAI/bridge_ai_ui
node --version
npm run dev
