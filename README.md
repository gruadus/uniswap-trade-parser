# FARM Uniswap trades parser

Looks up the most liquid pools for FARM REWARDS Token and gets all the swaps within a given time period and prints out a .csv files containing relevant information.

## Installing

0. Clone repository

```bash
git clone https://github.com/thegismar/farmtrades
cd farmtrades
```


Following assumes you're running *nix and python/pip 3.8 as python3/pip3

1. Create virtual environment

```bash
python3 -m venv venv
```

2. Set virtual environment

```bash
source venv/bin/activate
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

## Issues

- When looking up historic trades for a large period the connection to thegraph sometimes gives out, current 
  implementation shows a brief message and then **starts the entire process over**, which needs to be addressed
  
  
- Trader in some cases is the uniswap router, this needs to be addressed
