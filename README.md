# Uniswap trades parser

Looks up the most liquid pools for a specified token and gets all the swaps within a given time period and prints out a .csv files containing relevant information.

**Warning:** this script is not optimized for speed and the resulting .csv files can be very
large when parsing large periods of time.

## Requirements

1. [Install Brownie](https://eth-brownie.readthedocs.io/en/stable/install.html) & [Ganache-CLI](https://github.com/trufflesuite/ganache-cli), if you haven't already.

2. Sign up for [Alchemy](https://alchemy.com/) , create a free account and an application.

Get the API URL that includes your key and note it down: 

```https://eth-mainnet.alchemyapi.io/v2/<YOUR-KEY>```

3. Sign up for [Etherscan](www.etherscan.io) and generate an API key. This is required for fetching source codes of the mainnet contracts we will be interacting with. Store the API key in the `ETHERSCAN_TOKEN` environment variable.

```bash
export ETHERSCAN_TOKEN=YourApiToken
```

## Installing

```bash
git clone https://github.com/thegismar/farmtrades
cd farmtrades
```

Following assumes you're running *nix and python/pip 3.8 as python3/pip3 and an alchemy (free) subscription as well as an etherscan api


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

3. Install brownie network

 ```bash
brownie networks add Ethereum alchemy host=<URL FROM YOUR ALCHEMY APP> explorer="https://api.etherscan.io/api" chainid=1
```

4. Make sure the network is listed and correct:

 ```bash
brownie networks list true
```

It should show your added network with id=alchemy and all the parameters.

4. Run tests

 ```bash
pytest test.py
```

5. Run script

```bash
python3 main.py [-h] [-l LENGTH] [-t TOKEN] [-i IFARM] [-b BUFFER]
```
```
usage: main.py [-h] [-l LENGTH] [-t TOKEN] [-i IFARM] [-b BUFFER]

Simple script that looks up uniswap trades for a given token and dumps relevant data into a .csv file

optional arguments:
  -h, --help            show this help message and exit
  -l LENGTH, --length LENGTH
                        Historic lookup for trades in days.
  -t TOKEN, --token TOKEN
                        Token address.
  -i IFARM, --ifarm IFARM
                        Custom flag for calculating iFARM reward price
  -b BUFFER, --buffer BUFFER
                        Buffer between queries.
```
