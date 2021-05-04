from typing import List
import pandas as pd
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from dataclasses import dataclass
import time
import datetime
from rich.status import Status
import backoff
import sys
import warnings
from brownie import *
from dotenv import load_dotenv
import os

# not showing warnings, brownie has the tendency to be picky
warnings.simplefilter('ignore')

load_dotenv()
network_name = os.getenv('BROWNIE_NETWORK_NAME')

if not network.is_connected():
    network.connect(network_name)

# init gql
transport = AIOHTTPTransport(url="https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2")
client = Client(transport=transport, fetch_schema_from_transport=True)

s = Status('')

SECONDS_IN_DAY = 60 * 60 * 24


@dataclass()
class Dataset:
    id: str
    hash: str
    block: int
    date: str
    owner: str
    type: str
    coin_name: str
    coin_address: str
    amount: float
    other_coin_name: str
    other_coin_address: str
    other_amount: float
    price: float
    multiplier: float
    finalprice: float
    lp_name: str
    lp_address: str


@dataclass()
class Data:
    elements: List[Dataset]


def grapherr(err):
    s.console.print(f'[red] Connection to the graph interrupted.. Starting over... Sorry ;/ \n '
                    f'(maybe increase TIME_BUFFER?) \n err: {err}')


# this will retry when thegraph is lagging and calls grapherr
@backoff.on_exception(backoff.expo, Exception, max_time=300)
def graph(query, params):
    return client.execute(query, variable_values=params)


def get_pairs(token):
    query = gql(
        """
            query getPairs($tkn: String)
            
            {
                  pairs(first: 100, where: {token0: $tkn, volumeUSD_gt: "0"},
                   orderBy: volumeUSD, orderDirection: desc)
                {
                    id
                    
                    token0
                    {
                        id
                        name
                    }
                    
                    token1
                    {
                        id
                        name
                    }
                }
            }
        
        """
    )
    time.sleep(2)
    params = {'tkn': token}
    result = graph(query, params)
    return result['pairs']


def get_token_price(block, contract, dec1, dec2, ifarm):
    reserves = contract.getReserves(block_identifier=block)

    if ifarm:
        ppfs = ifarm.getPricePerFullShare(block_identifier=block) / 1e18
    else:
        ppfs = 1

    price = float(((reserves[1]) / 10 ** dec2) / (reserves[0] / 10 ** dec1))

    return price, ppfs, price * ppfs


def get_swaps(start_, token_, time_buffer_, ifarm=None):
    if ifarm:
        ifarm = Contract.from_explorer(ifarm)

    # init data_list with empty element
    data_list = Data(elements=[])
    query = gql(
        """
            query getSwaps($pair: String, $ts: BigInt)
       {
            swaps(first: 1000, orderBy: timestamp, orderDirection: asc, 
            where: {pair: $pair,timestamp_gt: $ts})
            
            {
                id
                
                transaction
                {
                    id
                    blockNumber
                }
                
                pair
                {
                token0Price
                token1Price
                }
                
                to 
                sender
                timestamp
                amount0In
                amount1In
                amount0Out
                amount1Out
                amountUSD
           }
           
        }
        """
    )

    # iterate over queries as thegraph limits results to 1000, order ascending by timestamp
    # stop conditions is either reaching current timestamp or not getting an empty list

    init = 'Processing...'
    pair = ''
    work = ''
    now = int(time.time())

    # progress indicator
    s.update(init + pair + work)
    with s:
        s.console.print('Getting pairs..')

        # get the most liquid pairs
        pairs = get_pairs(token_)
        if len(pairs) == 0:
            console.print(f'[red] Did not find any trades for the given time period. Exiting..')
            sys.exit()

        pair_string = ''
        for i in range(len(pairs) - 1):
            pair_string += f"{pairs[i]['id']} "
        s.console.print(f'Pulled pairs: {pair_string}... ')
        for p in pairs:

            s.console.print(f'Parsing pair {p["id"]}...')
            s.update(init)
            ts = start_
            contract = Contract.from_explorer(p['id'])

            token0 = Contract.from_explorer(contract.token0())
            token1 = Contract.from_explorer(contract.token1())

            # needed to correctly calculate the price
            dec_t0 = token0.decimals()
            dec_t1 = token1.decimals()

            # breaks either when the timestamp of the last trade is equal to when the script was run (not likely)
            # or when the resulting list of swaps is 0

            while ts < now:
                params = {'pair': p['id'], 'ts': ts}  # for the graphql query, the pair id and the timestamp
                result = graph(query, params)
                if len(result['swaps']) == 0:
                    break
                time.sleep(time_buffer_)
                # create a single row
                for r in result['swaps']:
                    price_data = get_token_price(int(r['transaction']['blockNumber']), contract, dec_t0, dec_t1, ifarm)
                    ds = Dataset(
                        r['id'],  # id
                        r['transaction']['id'],  # transaction hash
                        r['transaction']['blockNumber'],  # block
                        str(datetime.datetime.fromtimestamp(int(r['timestamp']))),  # date,
                        r['to'],  # owner
                        'buy' if float(r['amount0Out']) > 0 else 'sell',  # trade
                        p['token0']['name'],  # coin0 name
                        p['token0']['id'],  # coin0 addy
                        float(r['amount0In']) + float(r['amount0Out']),  # amount1 (either in(buy) or out(sell)
                        p['token1']['name'],  # coin1 name
                        p['token1']['id'],  # coin1 addy
                        float(r['amount1In']) + float(r['amount1Out']),  # other amounts (either sell/buy)
                        price_data[0],  # price w ithout ppfs
                        price_data[1],  # ppfs
                        price_data[2],  # price times ppfs
                        f"{'i' if ifarm else ''}{p['token0']['name']} / {p['token1']['name']}",  # name of pool
                        p['id'])  # id of pool/pair

                    # add the row to the list and update the timestamp
                    data_list.elements.append(ds)
                    ts = int(r['timestamp'])

                    # progress indicator
                    pair = '  ' + ds.lp_name
                    work = f'   {1 - ((now - ts) / (now - start_)):.2%}'
                    s.update(init + pair + work)

        return data_list


if __name__ == '__main__':
    from rich.console import Console
    import argparse

    parser = argparse.ArgumentParser(
        description='''Simple script that looks up uniswap trades for a given token and dumps relevant data into a
                        .csv file''')
    parser.add_argument('-l', '--length', type=int, default=7, help='Historic lookup for trades in days.')

    parser.add_argument('-t', '--token', type=str, default='0xa0246c9032bc3a600820415ae600c6388619a14d',
                        help='Token address.')
    parser.add_argument('-i', '--ifarm', type=bool, default=False,
                        help='Custom flag for calculating iFARM reward price')
    parser.add_argument('-b', '--buffer', type=int, default=0, help='Buffer between queries.')
    args = parser.parse_args()

    token = args.token
    length_history = args.length
    time_buffer = args.buffer

    console = Console()

    start_time = int(time.time()) - length_history * SECONDS_IN_DAY

    if args.ifarm:
        ifarm_contract = '0x1571eD0bed4D987fe2b498DdBaE7DFA19519F651'
    else:
        ifarm_contract = None

    dl = get_swaps(start_time, token, time_buffer, ifarm_contract)

    df = pd.DataFrame(e for e in dl.elements)
    df.sort_values(by='block', ascending=True, inplace=True, ignore_index=True)

    token_name = dl.elements[0].coin_name

    df.to_csv('data.csv')
    console.rule(f'[green][bold] Done')
