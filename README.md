# Uniswap trades parser

Looks up the most liquid pools for a specified token and gets all the swaps within a given time period and prints out a .csv files containing relevant information.

**Warning:** this script is not optimized for speed and the resulting .csv files can be very
large when parsing large periods of time. 
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

3. Run tests

 ```bash
pytest test.py
```

3. Run script

```bash
python3 main.py [-h] [-l LENGTH] [-t TOKEN] [-b BUFFER]
```
```
  -h, --help            show this help message and exit
  -l LENGTH, --length LENGTH
                        Historic lookup for trades in days.
  -t TOKEN, --token TOKEN
                        Token address.
  -b BUFFER, --buffer BUFFER
                        Buffer between queries.
```

## Issues

~~- When looking up historic trades for a large period the connection to thegraph sometimes gives out, current 
  implementation shows a brief message and then **starts the entire process over**, which needs to be addressed~~
  
  
- When the swap isn't done by an EOA (ie path goes through multiple pairs, or is done by another dex), owner is set  to the dex and not the buyer/seller  

## ToDo

- Store information in DB instead of .csv

~~- Test cases~~
