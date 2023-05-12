# Adaptive Anomaly Detection System for Software Defined Networks

## Tasks ( ⬜ - Not Started, 🟨 - Ongoing, 🟩 - Completed )

🟩 Topology creation with Mininet

🟩 RYU controller stats collection

🟩 Stats sending to Database

🟨 Dataset generation

🟨 WebPage design and integration

🟨 ML models research

⬜ Attack generation

⬜ Integrating ML models with RYU controller

⬜ Final tests


## Environment
1. Ubuntu 20.04 LTS
2. mininet 2.3.0
3. ryu-manager 4.30

## Prerequisites

1. Mininet emulation tool

```
sudo apt-get install mininet
pip3 install mininet
```

2. Python 3

```
sudo apt install python3
```

3. RYU controller

```
pip3 install ryu (OR) sudo apt install python3-ryu
```

4. Other dependencies

```
sudo apt-get install ffmpeg
sudo apt-get install netcat
pip install pymongo
```


## Running the system
1. Run the RYU controller

```
ryu-manager [--verbose] ./path/to/your-app.py
```

2. Run mininet topology file

```
sudo python3 ./path/to/topology-file.py
```

The same is also implemented in BASH file 'run.sh'
