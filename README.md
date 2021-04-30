# FARM Uniswap trades parser

Looks up the most liquid pools for FARM REWARDS Token and gets all the swaps within a given time period

## Installing

Assuming you're running *nix and python/pip v. > 3.8 as python3/pip3

1. Create virtual environment

```bash
python3 -m venv venv
```
2. Install dependencies

```bash
pip3 install -r requirements.txt
```

3. Run script

```bash
python3 main.py [DAYS]
```

- DAYS, given as int is an optional parameter to fetch the trades  since a certain number of days, 
default is 30
