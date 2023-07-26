setup:
    python3 -m venv env
    pip install --upgrade pip
    source env/bin/activate
    pip3 install -r requirements.txt

rhinos:
    python3 src/temur_rhinos.py

graph:
    python3 src/graph.py

graph-rhinos:
    python3 src/temur_rhinos.py
    python3 src/graph.py