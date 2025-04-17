# install python 3.12.9 # instead I can use a render.yaml
#!/bin/bash

# # Exit immediately if a command exits with a non-zero status
# set -e

# # Install pyenv (if not already installed)
# if ! command -v pyenv &> /dev/null; then
#   curl https://pyenv.run | bash
#   export PATH="$HOME/.pyenv/bin:$PATH"
#   eval "$(pyenv init --path)"
#   eval "$(pyenv init -)"
# fi

# # Install Python 3.12.9 using pyenv
# pyenv install -s 3.12.9

# # Set Python 3.12.9 as the local version
# pyenv local 3.12.9

# # Upgrade pip to the latest version
# pip install --upgrade pip

# Install dependencies from requirements.txt
# pip install -r requirements.txt

poetry install
cd wander_match
