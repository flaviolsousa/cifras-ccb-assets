# Util

```sh
# dependency
sudo apt install -y python3 python3-pip python3-venv
```

```sh
# create venv
cd py-scripts
python3 -m venv .venv

# activate
source .venv/bin/activate

# freeze
pip freeze > requirements.txt

# install
pip install -r requirements.txt
```
