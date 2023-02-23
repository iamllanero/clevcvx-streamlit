import streamlit as st
import requests
import json
from millify import millify
from web3 import Web3
from dotenv import load_dotenv
import os

load_dotenv()
WEB3_HTTP_PROVIDER = os.environ['WEB3_HTTP_PROVIDER']

st.set_page_config(
    page_title='CLever CVX Dashboard', 
    page_icon=':moneybag:', 
    layout='wide', 
    initial_sidebar_state='auto', 
    menu_items=None
    )

st.title('CLever CVX Dashboard')

# w3 = Web3(
#     Web3.HTTPProvider(
#         'https://mainnet.infura.io/v3/de9f566ad33b4fa4b553dd6bb9660ac3')
# )
w3 = Web3(Web3.HTTPProvider(WEB3_HTTP_PROVIDER))

CLEVCVX_FURNACE_ADDR = '0xCe4dCc5028588377E279255c0335Effe2d7aB72a'
CLEVCVX_CURVE_ADDR = '0xF9078Fb962A7D13F55d40d49C8AA6472aBD1A5a6'

def load_contract(address):
    with open(f'abi/{address}.json') as f:
        abi = f.read()
    contract = w3.eth.contract(address=address, abi=abi)
    return contract


def get_eth_price():
    eth_price_url = 'https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd'
    response_json = requests.get(eth_price_url)
    response_dict = json.loads(response_json.text)
    price = response_dict['ethereum']['usd']
    return float(price)

def main():

    # Basic stats
    eth_price = get_eth_price()
    col1, col2, col3, col4 = st.columns(4)
    col1.subheader('Ethereum')
    col2.metric('Latest Block', w3.eth.block_number)
    col3.metric('Gas Price', f'{w3.eth.gas_price/1e9:.2f} gwei')
    col4.metric('ETH Price', f'${eth_price:,.2f}')

    # clevCVX Supply
    clevcvx = load_contract('0xf05e58fCeA29ab4dA01A495140B349F8410Ba904')
    clevcvx_total = clevcvx.functions.totalSupply().call()
    clevcvx_in_furnace = (clevcvx.functions
        .balanceOf(CLEVCVX_FURNACE_ADDR)
        .call()
    )
    clevcvx_in_curve = (clevcvx.functions
        .balanceOf(CLEVCVX_CURVE_ADDR)
        .call()
    )

    col5, col6, col7, col8 = st.columns(4)
    col5.subheader('clevCVX Supply')
    col6.metric('Total', millify(clevcvx_total/1e18))
    col7.metric('Furnace', f'{clevcvx_in_furnace/clevcvx_total * 100:.1f}%')
    col8.metric('Curve Pool', f'{clevcvx_in_curve/clevcvx_total * 100:.1f}%')

    # clevCVX/CVX Pool
    cvx = load_contract('0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B')
    cvx_in_curve = cvx.functions.balanceOf(CLEVCVX_CURVE_ADDR).call()

    col9, col10, col11, col12 = st.columns(4)
    col9.subheader('clevCVX/CVX Pool')
    col10.metric('CVX + clevCVX', f'{millify(cvx_in_curve / 1e18)} + {millify(clevcvx_in_curve / 1e18)}')
    col11.metric('CVX %', f'{cvx_in_curve / (cvx_in_curve + clevcvx_in_curve) * 100:.1f}%')
    col12.metric('clevCVX %', f'{clevcvx_in_curve / (cvx_in_curve + clevcvx_in_curve) * 100:.1f}%')

    # Curve and Convex Stats
    crveth_pool = load_contract('0x8301AE4fc9c624d1D396cbDAa1ed877821D7C511')
    crv_price_eth = crveth_pool.functions.price_oracle().call()
    cvxeth_curve_pool = load_contract('0xB576491F1E6e5E62f1d8F26062Ee822B40B0E0d4')
    cvx_price_eth = cvxeth_curve_pool.functions.price_oracle().call()

    col13, col14, col15, col16 = st.columns(4)
    col13.subheader('CRV and CVX')
    col14.metric('CRV Price', f'${crv_price_eth / 1e18 * eth_price:.2f}')
    col15.metric('CVX Price', f'${cvx_price_eth / 1e18 * eth_price:.2f}')
    col16.metric('CVX/CRV Ratio', f'{cvx_price_eth/crv_price_eth:.2f}')

    # CLever CVX
    clever_cvx_locker = load_contract('0x96C68D861aDa016Ed98c30C810879F9df7c64154')
    cvx_in_clever = clever_cvx_locker.functions.totalLockedGlobal().call()
    clever_cvx_furnace = load_contract('0xCe4dCc5028588377E279255c0335Effe2d7aB72a')
    daily_rate = clever_cvx_furnace.functions.rewardInfo().call()[0] * 60 * 60 * 24

    col17, col18, col19, col20 = st.columns(4)
    col17.subheader('CLever CVX')
    col18.metric('CVX Locked', millify(cvx_in_clever / 1e18, precision=2))
    col19.metric('Daily CVX', millify(daily_rate / 1e18, precision=2))


if __name__ == "__main__":
    main()
