from typing import List
import pandas as pd
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport import exceptions
from dataclasses import dataclass
import time
import datetime
from rich.status import Status
import backoff
import sys

# init gql
transport = AIOHTTPTransport(url="https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2")
client = Client(transport=transport, fetch_schema_from_transport=True)

SECONDS_IN_DAY = 60 * 60 * 24
TIME_BUFFER = 5  # wait in seconds between calls to the graph api
FARM_TOKEN = '0xa0246c9032bc3a600820415ae600c6388619a14d'

s = Status('')


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
    lp_name: str
    lp_address: str


@dataclass()
class Data:
    elements: List[Dataset]


# init data_list with empty element
data_list = Data(elements=[])


def grapherr(err):
    s.console.print(f'[red] Connection to the graph interrupted.. Starting over... Sorry ;/ \n '
                    f'(maybe increase TIME_BUFFER?) \n err: {err}')


# this will retry when thegraph is lagging and calls grapherr
@backoff.on_exception(backoff.expo, exceptions.TransportError, max_time=300, on_backoff=grapherr)
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
    result = client.execute(query, variable_values=params)
    return result['pairs']


# this will retry when thegraph is lagging and calls grapherr
@backoff.on_exception(backoff.expo, exceptions.TransportError, max_time=300, on_backoff=grapherr)
def get_swaps(start_, token_):
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
    s.console.print('Starting hard work..')
    with s:
        s.console.print('Getting pairs..')

        # get the most liquid pairs
        pairs = get_pairs(token_)
        s.console.print(f'Pulled pairs: {pairs[0]["id"]}, {pairs[1]["id"]}... ')

        for p in pairs:
            s.console.print(f'Parsing pair {p["id"]}...')
            s.update(init)
            ts = start_

            # breaks either when the timestamp of the last trade is equal to when the script was run (not likely)
            # or when the resulting list of swaps is 0
            while ts < now:
                time.sleep(TIME_BUFFER)
                params = {'pair': p['id'], 'ts': ts}
                result = client.execute(query, variable_values=params)
                if len(result['swaps']) == 0:
                    break
                # create a single row
                for r in result['swaps']:
                    ds = Dataset(
                        r['id'],  # id
                        r['transaction']['id'],  # hash
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

                        # price, amount in dollar divided by the qty of token that were given or taken,
                        # ie that were sold(given) or taken(bought). uniswap gives the USD value

                        float(r['amountUSD']) / ((float(r['amount0In'])) + float(r['amount0Out'])),
                        f"{p['token0']['name']} / {p['token1']['name']}",  # name of pool
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

    token = FARM_TOKEN

    try:
        length_history = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    except ValueError:
        print('Error: argument for number of days must be integer')
        sys.exit()

    start_timestamp = int(time.time()) - length_history * SECONDS_IN_DAY

    dl = get_swaps(start_timestamp, token)
    df = pd.DataFrame(e for e in dl.elements)
    df.sort_values(by='block', ascending=True, inplace=True, ignore_index=True)
    df.to_csv('data.csv')
