import streamlit as st
import cv2
from PIL import Image
from skimage.metrics import structural_similarity
from skimage.transform import resize
import os
from moralis import evm_api
import requests
import json
import base64
import pandas as pd
import plotly.express as px
from datetime import datetime as dt


def add_bg_from_local(image_file):
    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url(data:image/{"jpg"};base64,{encoded_string.decode()});
        background-size: cover
    }}
    </style>
    """,
    unsafe_allow_html=True
    )


add_bg_from_local('extra_blur.jpg')


def save_uploaded_image(uploaded_img):
    try:
        with open(os.path.join('Uploads', uploaded_img.name), 'wb') as f:
            f.write(uploaded_img.getbuffer())
        return True
    except:
        return False


def structural_sim(img1, img2):
    sim, diff = structural_similarity(img1, img2, full=True)
    return sim


api_key = "RCyfQG6HDAi4RCRdLxz8t6ASemSW2SX8b54HmpzylhsR55PIFYyVcXI0N7sLGoW9"


def get_nft_owner(address, token_id):
    params = {
        "address": address,
        "token_id": token_id,
        "chain": "eth",
        "format": "decimal",
        "normalizeMetadata": True,
    }

    result = evm_api.nft.get_nft_metadata(
        api_key=api_key,
        params=params,
    )

    owner = result['owner_of']
    return owner


def get_collection_stats(contract_address):
    url = f"https://api.nftport.xyz/v0/transactions/stats/{contract_address}?chain=ethereum"

    headers = {
        "accept": "application/json",
        "Authorization": "712a766f-9c20-4cc3-915e-6a6783ab2263"
    }

    response = requests.get(url, headers=headers)

    json_obj = json.loads(response.text)

    stats = json_obj['statistics']

    one_week_sales = int(stats['seven_day_sales'])
    one_week_vol = stats['seven_day_volume']
    one_week_avg_price = stats['seven_day_average_price']

    return one_week_sales, one_week_vol, one_week_avg_price


def get_volume(address, token):
    url = f"https://api.nftport.xyz/v0/transactions/nfts/{address}/{token}?chain=ethereum&page_size=50&type=sale"

    headers = {
        "accept": "application/json",
        "Authorization": "712a766f-9c20-4cc3-915e-6a6783ab2263"
    }

    response = requests.get(url, headers=headers)

    json_obj = json.loads(response.text)

    if json_obj['response'] != 'NOK':
        txn = json_obj['transactions']

        volume_eth = []

        for tran in txn:
            if tran['type'] == 'sale':
                price_details = tran['price_details']
                price = price_details['price']
                volume_eth.append(price)

        if sum(volume_eth) == 0:
            st.write('No Sales found')
        else:
            return volume_eth


def get_sales_history(address, token):
    url = f"https://api.nftport.xyz/v0/transactions/nfts/{address}/{token}?chain=ethereum&page_size=50&type=sale"

    headers = {
        "accept": "application/json",
        "Authorization": "712a766f-9c20-4cc3-915e-6a6783ab2263"
    }

    response = requests.get(url, headers=headers)

    json_obj = json.loads(response.text)

    if json_obj['response'] != 'NOK':
        txn = json_obj['transactions']

        date_prices = []

        for tran in txn:
            if tran['type'] == 'sale':
                price_details = tran['price_details']
                price = price_details['price']
                txn_date = tran['transaction_date'][:10]
                price_date = (txn_date, price)
                date_prices.append(price_date)

        price_df = pd.DataFrame(date_prices, columns=['date', 'price'])

        price_df.sort_values('date', inplace=True)

        return price_df
    else:
        price_df = pd.DataFrame()

        return price_df


def get_floor_price_df(contract_address):
    url = f"https://api.reservoir.tools/collections/sources/v1?collection={contract_address}"

    headers = {
        "accept": "*/*",
        "x-api-key": "demo-api-key"
    }

    response = requests.get(url, headers=headers)
    obj = json.loads(response.text)
    all_data = obj['sources']

    data_list = []

    for i in all_data:
        source = i['sourceDomain']
        on_sale = i['onSaleCount']
        floor_price = i['floorAskPrice']

        data = (source, floor_price, on_sale)
        data_list.append(data)

    df = pd.DataFrame(data_list, columns=['Marketplace', 'Floor Price', 'Listings'])

    return df


def get_wallet_balance(wallet_address):
    params = {
        "address": wallet_address,
        "chain": "eth",
    }

    result = evm_api.balance.get_native_balance(
        api_key=api_key,
        params=params,
    )

    balance = result['balance']
    balance_in_eth = int(balance) / 1000000000000000000

    return balance_in_eth


def is_holder(wallet_address, contract_address):
    url = f"https://eth-mainnet.g.alchemy.com/nft/v2/vDCeg6eSoUKFiNL_d12TowCEW9pdCoMa/isHolderOfCollection?wallet={wallet_address}&contractAddress={contract_address}"

    headers = {"accept": "application/json"}

    response = requests.get(url, headers=headers)

    obj = json.loads(response.text)
    isholder = obj['isHolderOfCollection']

    return isholder


def get_nft_count(wallet_address, contract_address):
    url = f"https://eth-mainnet.g.alchemy.com/nft/v2/vDCeg6eSoUKFiNL_d12TowCEW9pdCoMa/getNFTs?owner={wallet_address}&pageSize=100&contractAddresses[]={contract_address}&withMetadata=false"

    headers = {"accept": "application/json"}

    response = requests.get(url, headers=headers)

    obj = json.loads(response.text)
    total = obj['totalCount']

    return total


def get_total_nfts_owned(wallet_address):
    url = f"https://eth-mainnet.g.alchemy.com/nft/v2/vDCeg6eSoUKFiNL_d12TowCEW9pdCoMa/getNFTs?owner={wallet_address}&pageSize=10&withMetadata=false"

    headers = {"accept": "application/json"}

    response = requests.get(url, headers=headers)

    obj = json.loads(response.text)
    total_nfts = obj['totalCount']

    return total_nfts


def get_holding_days(contract_address, token):
    url = f"https://api.nftport.xyz/v0/transactions/nfts/{contract_address}/{token}?chain=ethereum&page_size=50&type=sale&type=transfer&type=mint"

    headers = {
        "accept": "application/json",
        "Authorization": "712a766f-9c20-4cc3-915e-6a6783ab2263"
    }

    response = requests.get(url, headers=headers)

    obj = json.loads(response.text)
    txn_details = obj['transactions']

    for txn in txn_details:
        if txn['type'] == 'transfer' or txn['type'] == 'sale' or txn['type'] == 'mint':
            txn_date = txn['transaction_date'][:10]
            break

    holding_days = (dt.today() - dt.strptime(txn_date, "%Y-%m-%d")).days

    return txn_date, holding_days


def get_max_holding_days(wallet_address, contract_address):
    url = f"https://eth-mainnet.g.alchemy.com/nft/v2/vDCeg6eSoUKFiNL_d12TowCEW9pdCoMa/getNFTs?owner={wallet_address}&pageSize=100&contractAddresses[]={contract_address}&withMetadata=true"

    headers = {"accept": "application/json"}

    response = requests.get(url, headers=headers)
    obj = json.loads(response.text)
    nfts = obj['ownedNfts']

    nft_nums = []

    for nft in nfts:
        token_uri = nft['tokenUri']
        nft_num = token_uri['raw'].split('/')[-1]
        nft_nums.append(nft_num)

    holding_data = []
    holding_days = []

    for i in nft_nums:
        holding_date, holding_day = get_holding_days(contract_address, i)
        date_day = [holding_date, holding_day]
        holding_days.append(holding_day)
        holding_data.append(date_day)

    max_days = max(holding_days)

    for day in holding_data:
        if max_days == day[1]:
            holder_date_day = day

    return holder_date_day


bayc_address = '0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d'
clonex_address = '0x49cf6f5d44e70224e2e23fdcdd2c053f30ada28b'
doodles_address = '0x8a90cab2b38dba80c64b7734e58ee1db38b8992e'
azuki_address = '0xed5af388653567af2f388e6224dc7c4b3241c544'
mb_address = '0x23581767a106ae21c074b2276d25e5c3e136a68b'
punk_address = '0xb47e3cd837ddf8e4c57f05d70ab865de6e193bbb'
mayc_address = '0x60e4d786628fea6478f785a6d7e704777c86a7c6'
wow_address = '0xe785e82358879f061bc3dcac6f0444462d4b5330'
coolcat_address = '0x1a92f7381b9f03921564a437210bb9396471050c'
pudpen_address = '0xbd3531da5cf5857e7cfaa92426877b022e612cf8'
meebit_address = '0x7bd29408f11d2bfc23c34f18275bbf23bb716bc7'



st.title('JPEG to NFT # Finder')

nft_collections = ['Azuki', 'Moonbirds', 'Doodles', 'BAYC', 'WoW', 'CloneX', 'MAYC', 'Cool Cats', 'Pudgy Penguins', 'CryptoPunks', 'Meebits']

selected_collection = st.selectbox('Select Collection', nft_collections)

uploaded_img = st.file_uploader('Upload Image')

if selected_collection == 'Azuki':
    filenames_azuki = os.listdir('Azuki')

    if uploaded_img is not None:

        if save_uploaded_image(uploaded_img):
            display_img = Image.open(uploaded_img)

            col1, col2 = st.columns(2)
            with col1:
                st.image(display_img, width=200)

            img1 = cv2.imread(os.path.join('Uploads', uploaded_img.name), 0)
            resized_img = resize(img1, (128,128), anti_aliasing=True, preserve_range=True)

            name_scores = []
            scores = []

            for name in filenames_azuki:
                img = cv2.imread(os.path.join('Azuki', name), 0)
                ssim = structural_sim(img, resized_img)

                name_score = (name, ssim)
                scores.append(ssim)

                name_scores.append(name_score)

            max_score = max(scores)
            if max_score < 0.8:
                st.subheader('Please upload a better quality image!')
            else:
                for i in range(len(filenames_azuki)):
                    if name_scores[i][1] == max_score:
                        final_nft = name_scores[i][0][:-4]
                        nft_num = name_scores[i][0].split('#')[1].split('.')[0]

                        opensea_link = f'https://opensea.io/assets/ethereum/{azuki_address}/{nft_num}'
                        rarity_link = f'https://rarity.tools/azuki/view/{nft_num}'
                        owner = get_nft_owner(azuki_address, nft_num)
                        owner_link = f'https://opensea.io/{owner}'

                        with col1:
                            st.subheader(final_nft)
                        with col2:
                            st.subheader("Check on [Opensea](%s)" % opensea_link)
                            st.subheader("Check [Rarity Score](%s)" % rarity_link)

                        st.subheader(f"Owner : [{owner}]({owner_link})")

                        sales, volume, avg_price = get_collection_stats(azuki_address)
                        st.subheader('Azuki Stats (Last 7 Days)')

                        colu1, colu2, colu3 = st.columns(3)

                        with colu1:
                            st.metric('Total Sales', f'{sales}')
                        with colu2:
                            st.metric('Volume', f'{round(volume, 1)} ETH')
                        with colu3:
                            st.metric('Average Selling Price', f'{round(avg_price, 2)} ETH')

                        st.subheader('Azuki Floor Price across Marketplaces')

                        floorprice_df = get_floor_price_df(azuki_address)

                        st.write(floorprice_df)

                        vol_list = get_volume(azuki_address, nft_num)

                        st.subheader(f'{final_nft} Overall Stats')
                        colum1, colum2 = st.columns(2)

                        try:
                            with colum1:
                                st.metric('Total Sales', f'{len(vol_list)}')
                            with colum2:
                                st.metric('Volume Generated', f'{round(sum(vol_list), 2)} ETH')
                        except TypeError:
                            st.write('No Sales Found')

                        sale_history = get_sales_history(azuki_address, nft_num)

                        if sale_history.empty:
                            pass
                        else:
                            fig = px.line(sale_history, x='date', y='price', title='Trade History',
                                          labels=dict(date="Date", price="Price (ETH)"))
                            fig.update_layout(xaxis=dict(showgrid=False),
                                              yaxis=dict(showgrid=False),
                                              title_x=0.5, width=800, height=500,
                                              margin=dict(l=35, b=35, r=35, t=35)
                                              )
                            st.write(fig)

                        st.subheader('More details about the Owner')

                        total_nfts = get_total_nfts_owned(owner)
                        st.write(f'Total NFTs Owned : {total_nfts}')

                        wallet_bal = get_wallet_balance(owner)
                        st.write(f'Wallet Balance : {wallet_bal} ETH')


                        st.subheader('No. of Top NFTs in the Wallet')

                        all_data = []
                        azuki_count = get_nft_count(owner, azuki_address)
                        holder_since = get_max_holding_days(owner, azuki_address)
                        azuki_temp = ['Azuki', azuki_count]
                        azuki_final = azuki_temp + holder_since
                        all_data.append(azuki_final)

                        isholder_clonex = is_holder(owner, clonex_address)
                        isholder_doodles = is_holder(owner, doodles_address)
                        isholder_bayc = is_holder(owner, bayc_address)
                        isholder_mb = is_holder(owner, mb_address)
                        isholder_punk = is_holder(owner, punk_address)
                        isholder_mayc = is_holder(owner, mayc_address)
                        isholder_wow = is_holder(owner, wow_address)
                        isholder_coolcat = is_holder(owner, coolcat_address)

                        if isholder_clonex:
                            clonex_count = get_nft_count(owner, clonex_address)
                            holder_since = get_max_holding_days(owner, clonex_address)
                            clonex_temp = ['CloneX', clonex_count]
                            clonex_final = clonex_temp + holder_since
                            all_data.append(clonex_final)

                        if isholder_doodles:
                            doodles_count = get_nft_count(owner, doodles_address)
                            holder_since = get_max_holding_days(owner, doodles_address)
                            doodles_temp = ['Doodles', doodles_count]
                            doodles_final = doodles_temp + holder_since
                            all_data.append(doodles_final)

                        if isholder_bayc:
                            bayc_count = get_nft_count(owner, bayc_address)
                            holder_since = get_max_holding_days(owner, bayc_address)
                            bayc_temp = ['BAYC', bayc_count]
                            bayc_final = bayc_temp + holder_since
                            all_data.append(bayc_final)

                        if isholder_mb:
                            mb_count = get_nft_count(owner, mb_address)
                            holder_since = get_max_holding_days(owner, mb_address)
                            mb_temp = ['Moonbirds', mb_count]
                            mb_final = mb_temp + holder_since
                            all_data.append(mb_final)

                        if isholder_mayc:
                            mayc_count = get_nft_count(owner, mayc_address)
                            holder_since = get_max_holding_days(owner, mayc_address)
                            mayc_temp = ['MAYC', mayc_count]
                            mayc_final = mayc_temp + holder_since
                            all_data.append(mayc_final)

                        if isholder_wow:
                            wow_count = get_nft_count(owner, wow_address)
                            holder_since = get_max_holding_days(owner, wow_address)
                            wow_temp = ['World of Women', wow_count]
                            wow_final = wow_temp + holder_since
                            all_data.append(wow_final)

                        if isholder_coolcat:
                            coolcat_count = get_nft_count(owner, coolcat_address)
                            holder_since = get_max_holding_days(owner, coolcat_address)
                            coolcat_temp = ['Cool Cats', coolcat_count]
                            coolcat_final = coolcat_temp + holder_since
                            all_data.append(coolcat_final)

                        if isholder_punk:
                            punk_count = get_nft_count(owner, punk_address)
                            punk_temp = ['CryptoPunks', punk_count, '-', '-']
                            all_data.append(punk_temp)

                        holding_df = pd.DataFrame(all_data, columns=['Collection', 'Count', 'Holder Since', 'In Days'])
                        st.write(holding_df)


if selected_collection == 'Doodles':
    filenames_doodles = os.listdir('Doodles')

    if uploaded_img is not None:

        if save_uploaded_image(uploaded_img):
            display_img = Image.open(uploaded_img)

            col1, col2 = st.columns(2)
            with col1:
                st.image(display_img, width=200)

            img1 = cv2.imread(os.path.join('Uploads', uploaded_img.name), 0)
            resized_img = resize(img1, (128, 128), anti_aliasing=True, preserve_range=True)

            name_scores = []
            scores = []

            for name in filenames_doodles:
                img = cv2.imread(os.path.join('Doodles', name), 0)
                ssim = structural_sim(img, resized_img)

                name_score = (name, ssim)
                scores.append(ssim)

                name_scores.append(name_score)

            max_score = max(scores)
            if max_score < 0.8:
                st.subheader('Please upload a better quality image!')
            else:
                for i in range(len(filenames_doodles)):
                    if name_scores[i][1] == max_score:
                        final_nft = name_scores[i][0][:-4]
                        nft_num = name_scores[i][0].split('#')[1].split('.')[0]

                        opensea_link = f'https://opensea.io/assets/ethereum/{doodles_address}/{nft_num}'
                        rarity_link = f'https://rarity.tools/doodles-official/view/{nft_num}'
                        owner = get_nft_owner(doodles_address, nft_num)
                        owner_link = f'https://opensea.io/{owner}'

                        with col1:
                            st.subheader(final_nft)
                        with col2:
                            st.subheader("Check on [Opensea](%s)" % opensea_link)
                            st.subheader("Check [Rarity Score](%s)" % rarity_link)

                        st.subheader(f"Owner : [{owner}]({owner_link})")

                        sales, volume, avg_price = get_collection_stats(doodles_address)
                        st.subheader('Doodles Stats (Last 7 Days)')

                        colu1, colu2, colu3 = st.columns(3)

                        with colu1:
                            st.metric('Total Sales', f'{sales}')
                        with colu2:
                            st.metric('Volume', f'{round(volume, 1)} ETH')
                        with colu3:
                            st.metric('Average Selling Price', f'{round(avg_price, 2)} ETH')

                        st.subheader('Doodles Floor Price across Marketplaces')

                        floorprice_df = get_floor_price_df(doodles_address)

                        st.write(floorprice_df)

                        vol_list = get_volume(doodles_address, nft_num)

                        st.subheader(f'{final_nft} Overall Stats')
                        colum1, colum2 = st.columns(2)

                        try:
                            with colum1:
                                st.metric('Total Sales', f'{len(vol_list)}')
                            with colum2:
                                st.metric('Volume Generated', f'{round(sum(vol_list), 2)} ETH')
                        except TypeError:
                            st.write('No Sales Found')

                        sale_history = get_sales_history(doodles_address, nft_num)

                        if sale_history.empty:
                            pass
                        else:
                            fig = px.line(sale_history, x='date', y='price', title='Trade History',
                                          labels=dict(date="Date", price="Price (ETH)"))
                            fig.update_layout(xaxis=dict(showgrid=False),
                                              yaxis=dict(showgrid=False),
                                              title_x=0.5, width=800, height=500,
                                              margin=dict(l=35, b=35, r=35, t=35)
                                              )
                            st.write(fig)

                        st.subheader('More details about the Owner')

                        total_nfts = get_total_nfts_owned(owner)
                        st.write(f'Total NFTs Owned : {total_nfts}')

                        wallet_bal = get_wallet_balance(owner)
                        st.write(f'Wallet Balance : {wallet_bal} ETH')

                        st.subheader('No. of Top NFTs in the Wallet')

                        all_data = []
                        doodles_count = get_nft_count(owner, doodles_address)
                        holder_since = get_max_holding_days(owner, doodles_address)
                        doodles_temp = ['Doodles', doodles_count]
                        doodles_final = doodles_temp + holder_since
                        all_data.append(doodles_final)

                        isholder_clonex = is_holder(owner, clonex_address)
                        isholder_bayc = is_holder(owner, bayc_address)
                        isholder_azuki = is_holder(owner, azuki_address)
                        isholder_mb = is_holder(owner, mb_address)
                        isholder_punk = is_holder(owner, punk_address)
                        isholder_mayc = is_holder(owner, mayc_address)
                        isholder_wow = is_holder(owner, wow_address)
                        isholder_coolcat = is_holder(owner, coolcat_address)

                        if isholder_clonex:
                            clonex_count = get_nft_count(owner, clonex_address)
                            holder_since = get_max_holding_days(owner, clonex_address)
                            clonex_temp = ['CloneX', clonex_count]
                            clonex_final = clonex_temp + holder_since
                            all_data.append(clonex_final)

                        if isholder_bayc:
                            bayc_count = get_nft_count(owner, bayc_address)
                            holder_since = get_max_holding_days(owner, bayc_address)
                            bayc_temp = ['BAYC', bayc_count]
                            bayc_final = bayc_temp + holder_since
                            all_data.append(bayc_final)

                        if isholder_azuki:
                            azuki_count = get_nft_count(owner, azuki_address)
                            holder_since = get_max_holding_days(owner, azuki_address)
                            azuki_temp = ['Azuki', azuki_count]
                            azuki_final = azuki_temp + holder_since
                            all_data.append(azuki_final)

                        if isholder_mb:
                            mb_count = get_nft_count(owner, mb_address)
                            holder_since = get_max_holding_days(owner, mb_address)
                            mb_temp = ['Moonbirds', mb_count]
                            mb_final = mb_temp + holder_since
                            all_data.append(mb_final)

                        if isholder_mayc:
                            mayc_count = get_nft_count(owner, mayc_address)
                            holder_since = get_max_holding_days(owner, mayc_address)
                            mayc_temp = ['MAYC', mayc_count]
                            mayc_final = mayc_temp + holder_since
                            all_data.append(mayc_final)

                        if isholder_wow:
                            wow_count = get_nft_count(owner, wow_address)
                            holder_since = get_max_holding_days(owner, wow_address)
                            wow_temp = ['World of Women', wow_count]
                            wow_final = wow_temp + holder_since
                            all_data.append(wow_final)

                        if isholder_coolcat:
                            coolcat_count = get_nft_count(owner, coolcat_address)
                            holder_since = get_max_holding_days(owner, coolcat_address)
                            coolcat_temp = ['Cool Cats', coolcat_count]
                            coolcat_final = coolcat_temp + holder_since
                            all_data.append(coolcat_final)

                        if isholder_punk:
                            punk_count = get_nft_count(owner, punk_address)
                            punk_temp = ['CryptoPunks', punk_count, '-', '-']
                            all_data.append(punk_temp)

                        holding_df = pd.DataFrame(all_data, columns=['Collection', 'Count', 'Holder Since', 'In Days'])
                        st.write(holding_df)


if selected_collection == 'Moonbirds':
    filenames_mb = os.listdir('Moonbirds')

    if uploaded_img is not None:

        if save_uploaded_image(uploaded_img):
            display_img = Image.open(uploaded_img)

            col1, col2 = st.columns(2)
            with col1:
                st.image(display_img, width=200)

            img1 = cv2.imread(os.path.join('Uploads', uploaded_img.name), 0)
            resized_img = resize(img1, (128, 128), anti_aliasing=True, preserve_range=True)

            name_scores = []
            scores = []

            for name in filenames_mb:
                img = cv2.imread(os.path.join('Moonbirds', name), 0)
                ssim = structural_sim(img, resized_img)

                name_score = (name, ssim)
                scores.append(ssim)

                name_scores.append(name_score)

            max_score = max(scores)
            if max_score < 0.8:
                st.subheader('Please upload a better quality image!')
            else:
                for i in range(len(filenames_mb)):
                    if name_scores[i][1] == max_score:
                        final_nft = name_scores[i][0][:-4]
                        nft_num = name_scores[i][0].split('#')[1].split('.')[0]

                        opensea_link = f'https://opensea.io/assets/ethereum/{mb_address}/{nft_num}'
                        rarity_link = f'https://rarity.tools/proof-moonbirds/view/{nft_num}'
                        owner = get_nft_owner(mb_address, nft_num)
                        owner_link = f'https://opensea.io/{owner}'

                        with col1:
                            st.subheader(final_nft)
                        with col2:
                            st.subheader("Check on [Opensea](%s)" % opensea_link)
                            st.subheader("Check [Rarity Score](%s)" % rarity_link)

                        st.subheader(f"Owner : [{owner}]({owner_link})")

                        sales, volume, avg_price = get_collection_stats(mb_address)
                        st.subheader('Moonbirds Stats (Last 7 Days)')

                        colu1, colu2, colu3 = st.columns(3)
                        with colu1:
                            st.metric('Total Sales', f'{sales}')
                        with colu2:
                            st.metric('Volume', f'{round(volume, 1)} ETH')
                        with colu3:
                            st.metric('Average Selling Price', f'{round(avg_price, 2)} ETH')

                        st.subheader('Moonbirds Floor Price across Marketplaces')

                        floorprice_df = get_floor_price_df(mb_address)

                        st.write(floorprice_df)

                        vol_list = get_volume(mb_address, nft_num)

                        st.subheader(f'{final_nft} Overall Stats')
                        colum1, colum2 = st.columns(2)

                        try:
                            with colum1:
                                st.metric('Total Sales', f'{len(vol_list)}')
                            with colum2:
                                st.metric('Volume Generated', f'{round(sum(vol_list), 2)} ETH')
                        except TypeError:
                            st.write('No Sales Found')

                        sale_history = get_sales_history(mb_address, nft_num)

                        if sale_history.empty:
                            pass
                        else:
                            fig = px.line(sale_history, x='date', y='price', title='Trade History',
                                          labels=dict(date="Date", price="Price (ETH)"))
                            fig.update_layout(xaxis=dict(showgrid=False),
                                              yaxis=dict(showgrid=False),
                                              title_x=0.5, width=800, height=500,
                                              margin=dict(l=35, b=35, r=35, t=35)
                                              )
                            st.write(fig)

                        st.subheader('More details about the Owner')

                        total_nfts = get_total_nfts_owned(owner)
                        st.write(f'Total NFTs Owned : {total_nfts}')

                        wallet_bal = get_wallet_balance(owner)
                        st.write(f'Wallet Balance : {wallet_bal} ETH')

                        st.subheader('No. of Top NFTs in the Wallet')

                        all_data = []
                        mb_count = get_nft_count(owner, mb_address)
                        holder_since = get_max_holding_days(owner, mb_address)
                        mb_temp = ['Moonbirds', mb_count]
                        mb_final = mb_temp + holder_since
                        all_data.append(mb_final)

                        isholder_clonex = is_holder(owner, clonex_address)
                        isholder_doodles = is_holder(owner, doodles_address)
                        isholder_azuki = is_holder(owner, azuki_address)
                        isholder_bayc = is_holder(owner, bayc_address)
                        isholder_punk = is_holder(owner, punk_address)
                        isholder_mayc = is_holder(owner, mayc_address)
                        isholder_wow = is_holder(owner, wow_address)
                        isholder_coolcat = is_holder(owner, coolcat_address)

                        if isholder_clonex:
                            clonex_count = get_nft_count(owner, clonex_address)
                            holder_since = get_max_holding_days(owner, clonex_address)
                            clonex_temp = ['CloneX', clonex_count]
                            clonex_final = clonex_temp + holder_since
                            all_data.append(clonex_final)

                        if isholder_doodles:
                            doodles_count = get_nft_count(owner, doodles_address)
                            holder_since = get_max_holding_days(owner, doodles_address)
                            doodles_temp = ['Doodles', doodles_count]
                            doodles_final = doodles_temp + holder_since
                            all_data.append(doodles_final)

                        if isholder_azuki:
                            azuki_count = get_nft_count(owner, azuki_address)
                            holder_since = get_max_holding_days(owner, azuki_address)
                            azuki_temp = ['Azuki', azuki_count]
                            azuki_final = azuki_temp + holder_since
                            all_data.append(azuki_final)

                        if isholder_bayc:
                            bayc_count = get_nft_count(owner, bayc_address)
                            holder_since = get_max_holding_days(owner, bayc_address)
                            bayc_temp = ['BAYC', bayc_count]
                            bayc_final = bayc_temp + holder_since
                            all_data.append(bayc_final)

                        if isholder_mayc:
                            mayc_count = get_nft_count(owner, mayc_address)
                            holder_since = get_max_holding_days(owner, mayc_address)
                            mayc_temp = ['MAYC', mayc_count]
                            mayc_final = mayc_temp + holder_since
                            all_data.append(mayc_final)

                        if isholder_wow:
                            wow_count = get_nft_count(owner, wow_address)
                            holder_since = get_max_holding_days(owner, wow_address)
                            wow_temp = ['World of Women', wow_count]
                            wow_final = wow_temp + holder_since
                            all_data.append(wow_final)

                        if isholder_coolcat:
                            coolcat_count = get_nft_count(owner, coolcat_address)
                            holder_since = get_max_holding_days(owner, coolcat_address)
                            coolcat_temp = ['Cool Cats', coolcat_count]
                            coolcat_final = coolcat_temp + holder_since
                            all_data.append(coolcat_final)

                        if isholder_punk:
                            punk_count = get_nft_count(owner, punk_address)
                            punk_temp = ['CryptoPunks', punk_count, '-', '-']
                            all_data.append(punk_temp)

                        holding_df = pd.DataFrame(all_data, columns=['Collection', 'Count', 'Holder Since', 'In Days'])
                        st.write(holding_df)


if selected_collection == 'BAYC':
    filenames_bayc = os.listdir('BAYC')

    if uploaded_img is not None:

        if save_uploaded_image(uploaded_img):
            display_img = Image.open(uploaded_img)

            col1, col2 = st.columns(2)
            with col1:
                st.image(display_img, width=200)

            img1 = cv2.imread(os.path.join('Uploads', uploaded_img.name), 0)
            resized_img = resize(img1, (128, 128), anti_aliasing=True, preserve_range=True)

            name_scores = []
            scores = []

            for name in filenames_bayc:
                img = cv2.imread(os.path.join('BAYC', name), 0)
                ssim = structural_sim(img, resized_img)

                name_score = (name, ssim)
                scores.append(ssim)

                name_scores.append(name_score)

            max_score = max(scores)
            if max_score < 0.8:
                st.subheader('Please upload a better quality image!')
            else:
                for i in range(len(filenames_bayc)):
                    if name_scores[i][1] == max_score:
                        final_nft = name_scores[i][0][:-4]
                        nft_num = name_scores[i][0].split('#')[1].split('.')[0]

                        opensea_link = f'https://opensea.io/assets/ethereum/{bayc_address}/{nft_num}'
                        rarity_link = f'https://rarity.tools/boredapeyachtclub/view/{nft_num}'
                        owner = get_nft_owner(bayc_address, nft_num)
                        owner_link = f'https://opensea.io/{owner}'

                        with col1:
                            st.subheader(final_nft)
                        with col2:
                            st.subheader("Check on [Opensea](%s)" % opensea_link)
                            st.subheader("Check [Rarity Score](%s)" % rarity_link)

                        st.subheader(f"Owner : [{owner}]({owner_link})")

                        sales, volume, avg_price = get_collection_stats(bayc_address)
                        st.subheader('BAYC Collection Stats (Last 7 Days)')

                        colu1, colu2, colu3 = st.columns(3)

                        with colu1:
                            st.metric('Total Sales', f'{sales}')
                        with colu2:
                            st.metric('Volume', f'{round(volume, 1)} ETH')
                        with colu3:
                            st.metric('Average Selling Price', f'{round(avg_price, 2)} ETH')

                        st.subheader('BAYC Floor Price across Marketplaces')

                        floorprice_df = get_floor_price_df(bayc_address)

                        st.write(floorprice_df)

                        vol_list = get_volume(bayc_address, nft_num)

                        st.subheader(f'{final_nft} Overall Stats')
                        colum1, colum2 = st.columns(2)

                        try:
                            with colum1:
                                st.metric('Total Sales', f'{len(vol_list)}')
                            with colum2:
                                st.metric('Volume Generated', f'{round(sum(vol_list), 2)} ETH')
                        except TypeError:
                            st.write('No Sales Found')

                        sale_history = get_sales_history(bayc_address, nft_num)

                        if sale_history.empty:
                            pass
                        else:
                            fig = px.line(sale_history, x='date', y='price', title='Trade History',
                                          labels=dict(date="Date", price="Price (ETH)"))
                            fig.update_layout(xaxis=dict(showgrid=False),
                                              yaxis=dict(showgrid=False),
                                              title_x=0.5, width=800, height=500,
                                              margin=dict(l=35, b=35, r=35, t=35)
                                              )
                            st.write(fig)

                        st.subheader('More details about the Owner')

                        total_nfts = get_total_nfts_owned(owner)
                        st.write(f'Total NFTs Owned : {total_nfts}')

                        wallet_bal = get_wallet_balance(owner)
                        st.write(f'Wallet Balance : {wallet_bal} ETH')


                        st.subheader('No. of Top NFTs in the Wallet')

                        all_data = []
                        bayc_count = get_nft_count(owner, bayc_address)
                        holder_since = get_max_holding_days(owner, bayc_address)
                        bayc_temp = ['BAYC', bayc_count]
                        bayc_final = bayc_temp + holder_since
                        all_data.append(bayc_final)

                        isholder_clonex = is_holder(owner, clonex_address)
                        isholder_doodles = is_holder(owner, doodles_address)
                        isholder_azuki = is_holder(owner, azuki_address)
                        isholder_mb = is_holder(owner, mb_address)
                        isholder_punk = is_holder(owner, punk_address)
                        isholder_mayc = is_holder(owner, mayc_address)
                        isholder_wow = is_holder(owner, wow_address)
                        isholder_coolcat = is_holder(owner, coolcat_address)

                        if isholder_clonex:
                            clonex_count = get_nft_count(owner, clonex_address)
                            holder_since = get_max_holding_days(owner, clonex_address)
                            clonex_temp = ['CloneX', clonex_count]
                            clonex_final = clonex_temp + holder_since
                            all_data.append(clonex_final)

                        if isholder_doodles:
                            doodles_count = get_nft_count(owner, doodles_address)
                            holder_since = get_max_holding_days(owner, doodles_address)
                            doodles_temp = ['Doodles', doodles_count]
                            doodles_final = doodles_temp + holder_since
                            all_data.append(doodles_final)

                        if isholder_azuki:
                            azuki_count = get_nft_count(owner, azuki_address)
                            holder_since = get_max_holding_days(owner, azuki_address)
                            azuki_temp = ['Azuki', azuki_count]
                            azuki_final = azuki_temp + holder_since
                            all_data.append(azuki_final)

                        if isholder_mb:
                            mb_count = get_nft_count(owner, mb_address)
                            holder_since = get_max_holding_days(owner, mb_address)
                            mb_temp = ['Moonbirds', mb_count]
                            mb_final = mb_temp + holder_since
                            all_data.append(mb_final)

                        if isholder_mayc:
                            mayc_count = get_nft_count(owner, mayc_address)
                            holder_since = get_max_holding_days(owner, mayc_address)
                            mayc_temp = ['MAYC', mayc_count]
                            mayc_final = mayc_temp + holder_since
                            all_data.append(mayc_final)

                        if isholder_wow:
                            wow_count = get_nft_count(owner, wow_address)
                            holder_since = get_max_holding_days(owner, wow_address)
                            wow_temp = ['World of Women', wow_count]
                            wow_final = wow_temp + holder_since
                            all_data.append(wow_final)

                        if isholder_coolcat:
                            coolcat_count = get_nft_count(owner, coolcat_address)
                            holder_since = get_max_holding_days(owner, coolcat_address)
                            coolcat_temp = ['Cool Cats', coolcat_count]
                            coolcat_final = coolcat_temp + holder_since
                            all_data.append(coolcat_final)

                        if isholder_punk:
                            punk_count = get_nft_count(owner, punk_address)
                            punk_temp = ['CryptoPunks', punk_count, '-', '-']
                            all_data.append(punk_temp)

                        holding_df = pd.DataFrame(all_data, columns=['Collection', 'Count', 'Holder Since', 'In Days'])
                        st.write(holding_df)


if selected_collection == 'WoW':
    filenames_wow = os.listdir('WoW')

    if uploaded_img is not None:

        if save_uploaded_image(uploaded_img):
            display_img = Image.open(uploaded_img)

            col1, col2 = st.columns(2)
            with col1:
                st.image(display_img, width=200)

            img1 = cv2.imread(os.path.join('Uploads', uploaded_img.name), 0)
            resized_img = resize(img1, (128, 128), anti_aliasing=True, preserve_range=True)

            name_scores = []
            scores = []

            for name in filenames_wow:
                img = cv2.imread(os.path.join('WoW', name), 0)
                ssim = structural_sim(img, resized_img)

                name_score = (name, ssim)
                scores.append(ssim)

                name_scores.append(name_score)

            max_score = max(scores)
            if max_score < 0.8:
                st.subheader('Please upload a better quality image!')
            else:
                for i in range(len(filenames_wow)):
                    if name_scores[i][1] == max_score:
                        final_nft = name_scores[i][0][:-4]
                        nft_num = name_scores[i][0].split('#')[1].split('.')[0]

                        opensea_link = f'https://opensea.io/assets/ethereum/0xe785e82358879f061bc3dcac6f0444462d4b5330/{nft_num}'
                        rarity_link = f'https://rarity.tools/world-of-women-nft/view/{nft_num}'
                        owner = get_nft_owner('0xe785e82358879f061bc3dcac6f0444462d4b5330', nft_num)
                        owner_link = f'https://opensea.io/{owner}'

                        with col1:
                            st.subheader(final_nft)
                        with col2:
                            st.subheader("Check on [Opensea](%s)" % opensea_link)
                            st.subheader("Check [Rarity Score](%s)" % rarity_link)

                        st.subheader(f"Owner : [{owner}]({owner_link})")

                        sales, volume, avg_price = get_collection_stats(wow_address)
                        st.subheader('World of Women Collection Stats (Last 7 Days)')

                        colu1, colu2, colu3 = st.columns(3)

                        with colu1:
                            st.metric('Total Sales', f'{sales}')
                        with colu2:
                            st.metric('Volume', f'{round(volume, 1)} ETH')
                        with colu3:
                            st.metric('Average Selling Price', f'{round(avg_price, 2)} ETH')

                        st.subheader('WoW Floor Price across Marketplaces')

                        floorprice_df = get_floor_price_df(wow_address)

                        st.write(floorprice_df)

                        vol_list = get_volume(wow_address, nft_num)

                        st.subheader(f'{final_nft} Overall Stats')
                        colum1, colum2 = st.columns(2)

                        try:
                            with colum1:
                                st.metric('Total Sales', f'{len(vol_list)}')
                            with colum2:
                                st.metric('Volume Generated', f'{round(sum(vol_list), 2)} ETH')
                        except TypeError:
                            st.write('No Sales Found')

                        sale_history = get_sales_history(wow_address, nft_num)

                        if sale_history.empty:
                            pass
                        else:
                            fig = px.line(sale_history, x='date', y='price', title='Trade History',
                                          labels=dict(date="Date", price="Price (ETH)"))
                            fig.update_layout(xaxis=dict(showgrid=False),
                                              yaxis=dict(showgrid=False),
                                              title_x=0.5, width=800, height=500,
                                              margin=dict(l=35, b=35, r=35, t=35)
                                              )
                            st.write(fig)

                        st.subheader('More details about the Owner')

                        total_nfts = get_total_nfts_owned(owner)
                        st.write(f'Total NFTs Owned : {total_nfts}')

                        wallet_bal = get_wallet_balance(owner)
                        st.write(f'Wallet Balance : {wallet_bal} ETH')

                        st.subheader('No. of Top NFTs in the Wallet')

                        all_data = []
                        wow_count = get_nft_count(owner, wow_address)
                        holder_since = get_max_holding_days(owner, wow_address)
                        wow_temp = ['World of Women', wow_count]
                        wow_final = wow_temp + holder_since
                        all_data.append(wow_final)

                        isholder_clonex = is_holder(owner, clonex_address)
                        isholder_doodles = is_holder(owner, doodles_address)
                        isholder_azuki = is_holder(owner, azuki_address)
                        isholder_mb = is_holder(owner, mb_address)
                        isholder_punk = is_holder(owner, punk_address)
                        isholder_mayc = is_holder(owner, mayc_address)
                        isholder_bayc = is_holder(owner, bayc_address)
                        isholder_coolcat = is_holder(owner, coolcat_address)

                        if isholder_clonex:
                            clonex_count = get_nft_count(owner, clonex_address)
                            holder_since = get_max_holding_days(owner, clonex_address)
                            clonex_temp = ['CloneX', clonex_count]
                            clonex_final = clonex_temp + holder_since
                            all_data.append(clonex_final)

                        if isholder_doodles:
                            doodles_count = get_nft_count(owner, doodles_address)
                            holder_since = get_max_holding_days(owner, doodles_address)
                            doodles_temp = ['Doodles', doodles_count]
                            doodles_final = doodles_temp + holder_since
                            all_data.append(doodles_final)

                        if isholder_azuki:
                            azuki_count = get_nft_count(owner, azuki_address)
                            holder_since = get_max_holding_days(owner, azuki_address)
                            azuki_temp = ['Azuki', azuki_count]
                            azuki_final = azuki_temp + holder_since
                            all_data.append(azuki_final)

                        if isholder_mb:
                            mb_count = get_nft_count(owner, mb_address)
                            holder_since = get_max_holding_days(owner, mb_address)
                            mb_temp = ['Moonbirds', mb_count]
                            mb_final = mb_temp + holder_since
                            all_data.append(mb_final)

                        if isholder_mayc:
                            mayc_count = get_nft_count(owner, mayc_address)
                            holder_since = get_max_holding_days(owner, mayc_address)
                            mayc_temp = ['MAYC', mayc_count]
                            mayc_final = mayc_temp + holder_since
                            all_data.append(mayc_final)

                        if isholder_bayc:
                            bayc_count = get_nft_count(owner, bayc_address)
                            holder_since = get_max_holding_days(owner, bayc_address)
                            bayc_temp = ['BAYC', bayc_count]
                            bayc_final = bayc_temp + holder_since
                            all_data.append(bayc_final)

                        if isholder_coolcat:
                            coolcat_count = get_nft_count(owner, coolcat_address)
                            holder_since = get_max_holding_days(owner, coolcat_address)
                            coolcat_temp = ['Cool Cats', coolcat_count]
                            coolcat_final = coolcat_temp + holder_since
                            all_data.append(coolcat_final)

                        if isholder_punk:
                            punk_count = get_nft_count(owner, punk_address)
                            punk_temp = ['CryptoPunks', punk_count, '-', '-']
                            all_data.append(punk_temp)

                        holding_df = pd.DataFrame(all_data, columns=['Collection', 'Count', 'Holder Since', 'In Days'])
                        st.write(holding_df)


if selected_collection == 'CloneX':
    filenames_clonex = os.listdir('CloneX')

    if uploaded_img is not None:

        if save_uploaded_image(uploaded_img):
            display_img = Image.open(uploaded_img)

            col1, col2 = st.columns(2)
            with col1:
                st.image(display_img, width=200)

            img1 = cv2.imread(os.path.join('Uploads', uploaded_img.name), 0)
            resized_img = resize(img1, (128, 128), anti_aliasing=True, preserve_range=True)

            name_scores = []
            scores = []

            for name in filenames_clonex:
                img = cv2.imread(os.path.join('CloneX', name), 0)
                ssim = structural_sim(img, resized_img)

                name_score = (name, ssim)
                scores.append(ssim)

                name_scores.append(name_score)

            max_score = max(scores)
            if max_score < 0.8:
                st.subheader('Please upload a better quality image!')
            else:
                for i in range(len(filenames_clonex)):
                    if name_scores[i][1] == max_score:
                        final_nft = name_scores[i][0][:-4]
                        nft_num = name_scores[i][0].split(' ')[1].split('.')[0]

                        opensea_link = f'https://opensea.io/assets/ethereum/0x49cf6f5d44e70224e2e23fdcdd2c053f30ada28b/{nft_num}'
                        rarity_link = f'https://rarity.tools/clonex/view/{nft_num}'
                        owner = get_nft_owner('0x49cf6f5d44e70224e2e23fdcdd2c053f30ada28b', nft_num)
                        owner_link = f'https://opensea.io/{owner}'

                        with col1:
                            st.subheader(final_nft)
                        with col2:
                            st.subheader("Check on [Opensea](%s)" % opensea_link)
                            st.subheader("Check [Rarity Score](%s)" % rarity_link)

                        st.subheader(f"Owner : [{owner}]({owner_link})")

                        sales, volume, avg_price = get_collection_stats(clonex_address)
                        st.subheader('CloneX Collection Stats (Last 7 Days)')

                        colu1, colu2, colu3 = st.columns(3)

                        with colu1:
                            st.metric('Total Sales', f'{sales}')
                        with colu2:
                            st.metric('Volume', f'{round(volume, 1)} ETH')
                        with colu3:
                            st.metric('Average Selling Price', f'{round(avg_price, 2)} ETH')

                        st.subheader('CloneX Floor Price across Marketplaces')

                        floorprice_df = get_floor_price_df(clonex_address)

                        st.write(floorprice_df)

                        vol_list = get_volume(clonex_address, nft_num)

                        st.subheader(f'{final_nft} Overall Stats')
                        colum1, colum2 = st.columns(2)

                        try:
                            with colum1:
                                st.metric('Total Sales', f'{len(vol_list)}')
                            with colum2:
                                st.metric('Volume Generated', f'{round(sum(vol_list), 2)} ETH')
                        except TypeError:
                            st.write('No Sales Found')

                        sale_history = get_sales_history(clonex_address, nft_num)

                        if sale_history.empty:
                            pass
                        else:
                            fig = px.line(sale_history, x='date', y='price', title='Trade History',
                                          labels=dict(date="Date", price="Price (ETH)"))
                            fig.update_layout(xaxis=dict(showgrid=False),
                                              yaxis=dict(showgrid=False),
                                              title_x=0.5, width=800, height=500,
                                              margin=dict(l=35, b=35, r=35, t=35)
                                              )
                            st.write(fig)

                        st.subheader('More details about the Owner')

                        total_nfts = get_total_nfts_owned(owner)
                        st.write(f'Total NFTs Owned : {total_nfts}')

                        wallet_bal = get_wallet_balance(owner)
                        st.write(f'Wallet Balance : {wallet_bal} ETH')

                        st.subheader('No. of Top NFTs in the Wallet')

                        all_data = []
                        clonex_count = get_nft_count(owner, clonex_address)
                        holder_since = get_max_holding_days(owner, clonex_address)
                        clonex_temp = ['CloneX', clonex_count]
                        clonex_final = clonex_temp + holder_since
                        all_data.append(clonex_final)

                        isholder_bayc = is_holder(owner, bayc_address)
                        isholder_doodles = is_holder(owner, doodles_address)
                        isholder_azuki = is_holder(owner, azuki_address)
                        isholder_mb = is_holder(owner, mb_address)
                        isholder_punk = is_holder(owner, punk_address)
                        isholder_mayc = is_holder(owner, mayc_address)
                        isholder_wow = is_holder(owner, wow_address)
                        isholder_coolcat = is_holder(owner, coolcat_address)

                        if isholder_bayc:
                            bayc_count = get_nft_count(owner, bayc_address)
                            holder_since = get_max_holding_days(owner, bayc_address)
                            bayc_temp = ['BAYC', bayc_count]
                            bayc_final = bayc_temp + holder_since
                            all_data.append(bayc_final)

                        if isholder_doodles:
                            doodles_count = get_nft_count(owner, doodles_address)
                            holder_since = get_max_holding_days(owner, doodles_address)
                            doodles_temp = ['Doodles', doodles_count]
                            doodles_final = doodles_temp + holder_since
                            all_data.append(doodles_final)

                        if isholder_azuki:
                            azuki_count = get_nft_count(owner, azuki_address)
                            holder_since = get_max_holding_days(owner, azuki_address)
                            azuki_temp = ['Azuki', azuki_count]
                            azuki_final = azuki_temp + holder_since
                            all_data.append(azuki_final)

                        if isholder_mb:
                            mb_count = get_nft_count(owner, mb_address)
                            holder_since = get_max_holding_days(owner, mb_address)
                            mb_temp = ['Moonbirds', mb_count]
                            mb_final = mb_temp + holder_since
                            all_data.append(mb_final)

                        if isholder_mayc:
                            mayc_count = get_nft_count(owner, mayc_address)
                            holder_since = get_max_holding_days(owner, mayc_address)
                            mayc_temp = ['MAYC', mayc_count]
                            mayc_final = mayc_temp + holder_since
                            all_data.append(mayc_final)

                        if isholder_wow:
                            wow_count = get_nft_count(owner, wow_address)
                            holder_since = get_max_holding_days(owner, wow_address)
                            wow_temp = ['World of Women', wow_count]
                            wow_final = wow_temp + holder_since
                            all_data.append(wow_final)

                        if isholder_coolcat:
                            coolcat_count = get_nft_count(owner, coolcat_address)
                            holder_since = get_max_holding_days(owner, coolcat_address)
                            coolcat_temp = ['Cool Cats', coolcat_count]
                            coolcat_final = coolcat_temp + holder_since
                            all_data.append(coolcat_final)

                        if isholder_punk:
                            punk_count = get_nft_count(owner, punk_address)
                            punk_temp = ['CryptoPunks', punk_count, '-', '-']
                            all_data.append(punk_temp)

                        holding_df = pd.DataFrame(all_data, columns=['Collection', 'Count', 'Holder Since', 'In Days'])
                        st.write(holding_df)


if selected_collection == 'MAYC':
    filenames_mayc = os.listdir('MAYC')

    if uploaded_img is not None:

        if save_uploaded_image(uploaded_img):
            display_img = Image.open(uploaded_img)

            col1, col2 = st.columns(2)
            with col1:
                st.image(display_img, width=200)

            img1 = cv2.imread(os.path.join('Uploads', uploaded_img.name), 0)
            resized_img = resize(img1, (128, 128), anti_aliasing=True, preserve_range=True)

            name_scores = []
            scores = []

            for name in filenames_mayc:
                img = cv2.imread(os.path.join('MAYC', name), 0)
                ssim = structural_sim(img, resized_img)

                name_score = (name, ssim)
                scores.append(ssim)

                name_scores.append(name_score)

            max_score = max(scores)
            if max_score < 0.8:
                st.subheader('Please upload a better quality image!')
            else:
                for i in range(len(filenames_mayc)):
                    if name_scores[i][1] == max_score:
                        final_nft = name_scores[i][0][:-4]
                        nft_num = name_scores[i][0].split('#')[1].split('.')[0]

                        opensea_link = f'https://opensea.io/assets/ethereum/0x60e4d786628fea6478f785a6d7e704777c86a7c6/{nft_num}'
                        rarity_link = f'https://rarity.tools/mutant-ape-yacht-club/view/{nft_num}'
                        owner = get_nft_owner('0x60e4d786628fea6478f785a6d7e704777c86a7c6', nft_num)
                        owner_link = f'https://opensea.io/{owner}'

                        with col1:
                            st.subheader(final_nft)
                        with col2:
                            st.subheader("Check on [Opensea](%s)" % opensea_link)
                            st.subheader("Check [Rarity Score](%s)" % rarity_link)

                        st.subheader(f"Owner : [{owner}]({owner_link})")

                        sales, volume, avg_price = get_collection_stats(mayc_address)
                        st.subheader('MAYC Collection Stats (Last 7 Days)')

                        colu1, colu2, colu3 = st.columns(3)

                        with colu1:
                            st.metric('Total Sales', f'{sales}')
                        with colu2:
                            st.metric('Volume', f'{round(volume, 1)} ETH')
                        with colu3:
                            st.metric('Average Selling Price', f'{round(avg_price, 2)} ETH')

                        st.subheader('BAYC Floor Price across Marketplaces')

                        floorprice_df = get_floor_price_df(mayc_address)

                        st.write(floorprice_df)

                        vol_list = get_volume(mayc_address, nft_num)

                        st.subheader(f'{final_nft} Overall Stats')
                        colum1, colum2 = st.columns(2)

                        try:
                            with colum1:
                                st.metric('Total Sales', f'{len(vol_list)}')
                            with colum2:
                                st.metric('Volume Generated', f'{round(sum(vol_list), 2)} ETH')
                        except TypeError:
                            st.write('No Sales Found')

                        sale_history = get_sales_history(mayc_address, nft_num)

                        if sale_history.empty:
                            pass
                        else:
                            fig = px.line(sale_history, x='date', y='price', title='Trade History',
                                          labels=dict(date="Date", price="Price (ETH)"))
                            fig.update_layout(xaxis=dict(showgrid=False),
                                              yaxis=dict(showgrid=False),
                                              title_x=0.5, width=800, height=500,
                                              margin=dict(l=35, b=35, r=35, t=35)
                                              )
                            st.write(fig)

                        st.subheader('More details about the Owner')

                        total_nfts = get_total_nfts_owned(owner)
                        st.write(f'Total NFTs Owned : {total_nfts}')

                        wallet_bal = get_wallet_balance(owner)
                        st.write(f'Wallet Balance : {wallet_bal} ETH')

                        st.subheader('No. of Top NFTs in the Wallet')

                        all_data = []
                        mayc_count = get_nft_count(owner, mayc_address)
                        holder_since = get_max_holding_days(owner, mayc_address)
                        mayc_temp = ['MAYC', mayc_count]
                        mayc_final = mayc_temp + holder_since
                        all_data.append(mayc_final)

                        isholder_clonex = is_holder(owner, clonex_address)
                        isholder_doodles = is_holder(owner, doodles_address)
                        isholder_azuki = is_holder(owner, azuki_address)
                        isholder_mb = is_holder(owner, mb_address)
                        isholder_punk = is_holder(owner, punk_address)
                        isholder_bayc = is_holder(owner, bayc_address)
                        isholder_wow = is_holder(owner, wow_address)
                        isholder_coolcat = is_holder(owner, coolcat_address)

                        if isholder_clonex:
                            clonex_count = get_nft_count(owner, clonex_address)
                            holder_since = get_max_holding_days(owner, clonex_address)
                            clonex_temp = ['CloneX', clonex_count]
                            clonex_final = clonex_temp + holder_since
                            all_data.append(clonex_final)

                        if isholder_doodles:
                            doodles_count = get_nft_count(owner, doodles_address)
                            holder_since = get_max_holding_days(owner, doodles_address)
                            doodles_temp = ['Doodles', doodles_count]
                            doodles_final = doodles_temp + holder_since
                            all_data.append(doodles_final)

                        if isholder_azuki:
                            azuki_count = get_nft_count(owner, azuki_address)
                            holder_since = get_max_holding_days(owner, azuki_address)
                            azuki_temp = ['Azuki', azuki_count]
                            azuki_final = azuki_temp + holder_since
                            all_data.append(azuki_final)

                        if isholder_mb:
                            mb_count = get_nft_count(owner, mb_address)
                            holder_since = get_max_holding_days(owner, mb_address)
                            mb_temp = ['Moonbirds', mb_count]
                            mb_final = mb_temp + holder_since
                            all_data.append(mb_final)

                        if isholder_bayc:
                            bayc_count = get_nft_count(owner, bayc_address)
                            holder_since = get_max_holding_days(owner, bayc_address)
                            bayc_temp = ['BAYC', bayc_count]
                            bayc_final = bayc_temp + holder_since
                            all_data.append(bayc_final)

                        if isholder_wow:
                            wow_count = get_nft_count(owner, wow_address)
                            holder_since = get_max_holding_days(owner, wow_address)
                            wow_temp = ['World of Women', wow_count]
                            wow_final = wow_temp + holder_since
                            all_data.append(wow_final)

                        if isholder_coolcat:
                            coolcat_count = get_nft_count(owner, coolcat_address)
                            holder_since = get_max_holding_days(owner, coolcat_address)
                            coolcat_temp = ['Cool Cats', coolcat_count]
                            coolcat_final = coolcat_temp + holder_since
                            all_data.append(coolcat_final)

                        if isholder_punk:
                            punk_count = get_nft_count(owner, punk_address)
                            punk_temp = ['CryptoPunks', punk_count, '-', '-']
                            all_data.append(punk_temp)

                        holding_df = pd.DataFrame(all_data, columns=['Collection', 'Count', 'Holder Since', 'In Days'])
                        st.write(holding_df)


if selected_collection == 'Cool Cats':
    filenames_cc = os.listdir('Cool Cats')

    if uploaded_img is not None:

        if save_uploaded_image(uploaded_img):
            display_img = Image.open(uploaded_img)

            col1, col2 = st.columns(2)
            with col1:
                st.image(display_img, width=200)

            img1 = cv2.imread(os.path.join('Uploads', uploaded_img.name), 0)
            resized_img = resize(img1, (128, 128), anti_aliasing=True, preserve_range=True)

            name_scores = []
            scores = []

            for name in filenames_cc:
                img = cv2.imread(os.path.join('Cool Cats', name), 0)
                ssim = structural_sim(img, resized_img)

                name_score = (name, ssim)
                scores.append(ssim)

                name_scores.append(name_score)

            max_score = max(scores)
            if max_score < 0.8:
                st.subheader('Please upload a better quality image!')
            else:
                for i in range(len(filenames_cc)):
                    if name_scores[i][1] == max_score:
                        final_nft = name_scores[i][0][:-4]
                        nft_num = name_scores[i][0].split('#')[1].split('.')[0]

                        opensea_link = f'https://opensea.io/assets/ethereum/0x1a92f7381b9f03921564a437210bb9396471050c/{nft_num}'
                        rarity_link = f'https://rarity.tools/cool-cats-nft/view/{nft_num}'
                        owner = get_nft_owner('0x1a92f7381b9f03921564a437210bb9396471050c', nft_num)
                        owner_link = f'https://opensea.io/{owner}'

                        with col1:
                            st.subheader(final_nft)
                        with col2:
                            st.subheader("Check on [Opensea](%s)" % opensea_link)
                            st.subheader("Check [Rarity Score](%s)" % rarity_link)

                        st.subheader(f"Owner : [{owner}]({owner_link})")

                        sales, volume, avg_price = get_collection_stats(coolcat_address)
                        st.subheader('Cool Cats Collection Stats (Last 7 Days)')

                        colu1, colu2, colu3 = st.columns(3)

                        with colu1:
                            st.metric('Total Sales', f'{sales}')
                        with colu2:
                            st.metric('Volume', f'{round(volume, 1)} ETH')
                        with colu3:
                            st.metric('Average Selling Price', f'{round(avg_price, 2)} ETH')

                        st.subheader('Cool Cats Floor Price across Marketplaces')

                        floorprice_df = get_floor_price_df(coolcat_address)

                        st.write(floorprice_df)

                        vol_list = get_volume(coolcat_address, nft_num)

                        st.subheader(f'{final_nft} Overall Stats')
                        colum1, colum2 = st.columns(2)

                        try:
                            with colum1:
                                st.metric('Total Sales', f'{len(vol_list)}')
                            with colum2:
                                st.metric('Volume Generated', f'{round(sum(vol_list), 2)} ETH')
                        except TypeError:
                            st.write('No Sales Found')

                        sale_history = get_sales_history(coolcat_address, nft_num)

                        if sale_history.empty:
                            pass
                        else:
                            fig = px.line(sale_history, x='date', y='price', title='Trade History',
                                          labels=dict(date="Date", price="Price (ETH)"))
                            fig.update_layout(xaxis=dict(showgrid=False),
                                              yaxis=dict(showgrid=False),
                                              title_x=0.5, width=800, height=500,
                                              margin=dict(l=35, b=35, r=35, t=35)
                                              )
                            st.write(fig)

                        st.subheader('More details about the Owner')

                        total_nfts = get_total_nfts_owned(owner)
                        st.write(f'Total NFTs Owned : {total_nfts}')

                        wallet_bal = get_wallet_balance(owner)
                        st.write(f'Wallet Balance : {wallet_bal} ETH')

                        st.subheader('No. of Top NFTs in the Wallet')

                        all_data = []
                        coolcat_count = get_nft_count(owner, coolcat_address)
                        holder_since = get_max_holding_days(owner, coolcat_address)
                        coolcat_temp = ['Cool Cats', coolcat_count]
                        coolcat_final = coolcat_temp + holder_since
                        all_data.append(coolcat_final)

                        isholder_clonex = is_holder(owner, clonex_address)
                        isholder_doodles = is_holder(owner, doodles_address)
                        isholder_azuki = is_holder(owner, azuki_address)
                        isholder_mb = is_holder(owner, mb_address)
                        isholder_punk = is_holder(owner, punk_address)
                        isholder_mayc = is_holder(owner, mayc_address)
                        isholder_wow = is_holder(owner, wow_address)
                        isholder_bayc = is_holder(owner, bayc_address)

                        if isholder_clonex:
                            clonex_count = get_nft_count(owner, clonex_address)
                            holder_since = get_max_holding_days(owner, clonex_address)
                            clonex_temp = ['CloneX', clonex_count]
                            clonex_final = clonex_temp + holder_since
                            all_data.append(clonex_final)

                        if isholder_doodles:
                            doodles_count = get_nft_count(owner, doodles_address)
                            holder_since = get_max_holding_days(owner, doodles_address)
                            doodles_temp = ['Doodles', doodles_count]
                            doodles_final = doodles_temp + holder_since
                            all_data.append(doodles_final)

                        if isholder_azuki:
                            azuki_count = get_nft_count(owner, azuki_address)
                            holder_since = get_max_holding_days(owner, azuki_address)
                            azuki_temp = ['Azuki', azuki_count]
                            azuki_final = azuki_temp + holder_since
                            all_data.append(azuki_final)

                        if isholder_mb:
                            mb_count = get_nft_count(owner, mb_address)
                            holder_since = get_max_holding_days(owner, mb_address)
                            mb_temp = ['Moonbirds', mb_count]
                            mb_final = mb_temp + holder_since
                            all_data.append(mb_final)

                        if isholder_mayc:
                            mayc_count = get_nft_count(owner, mayc_address)
                            holder_since = get_max_holding_days(owner, mayc_address)
                            mayc_temp = ['MAYC', mayc_count]
                            mayc_final = mayc_temp + holder_since
                            all_data.append(mayc_final)

                        if isholder_wow:
                            wow_count = get_nft_count(owner, wow_address)
                            holder_since = get_max_holding_days(owner, wow_address)
                            wow_temp = ['World of Women', wow_count]
                            wow_final = wow_temp + holder_since
                            all_data.append(wow_final)

                        if isholder_bayc:
                            bayc_count = get_nft_count(owner, bayc_address)
                            holder_since = get_max_holding_days(owner, bayc_address)
                            bayc_temp = ['BAYC', bayc_count]
                            bayc_final = bayc_temp + holder_since
                            all_data.append(bayc_final)

                        if isholder_punk:
                            punk_count = get_nft_count(owner, punk_address)
                            punk_temp = ['CryptoPunks', punk_count, '-', '-']
                            all_data.append(punk_temp)

                        holding_df = pd.DataFrame(all_data, columns=['Collection', 'Count', 'Holder Since', 'In Days'])
                        st.write(holding_df)


if selected_collection == 'Pudgy Penguins':
    filenames_pudpen = os.listdir('Pudgy Penguins')

    if uploaded_img is not None:

        if save_uploaded_image(uploaded_img):
            display_img = Image.open(uploaded_img)

            col1, col2 = st.columns(2)
            with col1:
                st.image(display_img, width=200)

            img1 = cv2.imread(os.path.join('Uploads', uploaded_img.name), 0)
            resized_img = resize(img1, (128, 128), anti_aliasing=True, preserve_range=True)

            name_scores = []
            scores = []

            for name in filenames_pudpen:
                img = cv2.imread(os.path.join('Pudgy Penguins', name), 0)
                ssim = structural_sim(img, resized_img)

                name_score = (name, ssim)
                scores.append(ssim)

                name_scores.append(name_score)

            max_score = max(scores)
            if max_score < 0.8:
                st.subheader('Please upload a better quality image!')
            else:
                for i in range(len(filenames_pudpen)):
                    if name_scores[i][1] == max_score:
                        final_nft = name_scores[i][0][:-4]
                        nft_num = name_scores[i][0].split('#')[1].split('.')[0]

                        opensea_link = f'https://opensea.io/assets/ethereum/0xbd3531da5cf5857e7cfaa92426877b022e612cf8/{nft_num}'
                        rarity_link = f'https://rarity.tools/pudgypenguins/view/{nft_num}'
                        owner = get_nft_owner('0xbd3531da5cf5857e7cfaa92426877b022e612cf8', nft_num)
                        owner_link = f'https://opensea.io/{owner}'

                        with col1:
                            st.subheader(final_nft)
                        with col2:
                            st.subheader("Check on [Opensea](%s)" % opensea_link)
                            st.subheader("Check [Rarity Score](%s)" % rarity_link)

                        st.subheader(f"Owner : [{owner}]({owner_link})")

                        sales, volume, avg_price = get_collection_stats(pudpen_address)
                        st.subheader('Pudgy Penguins Collection Stats (Last 7 Days)')

                        colu1, colu2, colu3 = st.columns(3)

                        with colu1:
                            st.metric('Total Sales', f'{sales}')
                        with colu2:
                            st.metric('Volume', f'{round(volume, 1)} ETH')
                        with colu3:
                            st.metric('Average Selling Price', f'{round(avg_price, 2)} ETH')

                        st.subheader('Pudgy Penguins Floor Price across Marketplaces')

                        floorprice_df = get_floor_price_df(pudpen_address)

                        st.write(floorprice_df)

                        vol_list = get_volume(pudpen_address, nft_num)

                        st.subheader(f'{final_nft} Overall Stats')
                        colum1, colum2 = st.columns(2)

                        try:
                            with colum1:
                                st.metric('Total Sales', f'{len(vol_list)}')
                            with colum2:
                                st.metric('Volume Generated', f'{round(sum(vol_list), 2)} ETH')
                        except TypeError:
                            st.write('No Sales Found')

                        sale_history = get_sales_history(pudpen_address, nft_num)

                        if sale_history.empty:
                            pass
                        else:
                            fig = px.line(sale_history, x='date', y='price', title='Trade History',
                                          labels=dict(date="Date", price="Price (ETH)"))
                            fig.update_layout(xaxis=dict(showgrid=False),
                                              yaxis=dict(showgrid=False),
                                              title_x=0.5, width=800, height=500,
                                              margin=dict(l=35, b=35, r=35, t=35)
                                              )
                            st.write(fig)

                        st.subheader('More details about the Owner')

                        total_nfts = get_total_nfts_owned(owner)
                        st.write(f'Total NFTs Owned : {total_nfts}')

                        wallet_bal = get_wallet_balance(owner)
                        st.write(f'Wallet Balance : {wallet_bal} ETH')

                        st.subheader('No. of Top NFTs in the Wallet')

                        all_data = []
                        pudpen_count = get_nft_count(owner, pudpen_address)
                        holder_since = get_max_holding_days(owner, pudpen_address)
                        pudpen_temp = ['Pudgy Penguins', pudpen_count]
                        pudpen_final = pudpen_temp + holder_since
                        all_data.append(pudpen_final)

                        isholder_bayc = is_holder(owner, bayc_address)
                        isholder_clonex = is_holder(owner, clonex_address)
                        isholder_doodles = is_holder(owner, doodles_address)
                        isholder_azuki = is_holder(owner, azuki_address)
                        isholder_mb = is_holder(owner, mb_address)
                        isholder_punk = is_holder(owner, punk_address)
                        isholder_mayc = is_holder(owner, mayc_address)
                        isholder_wow = is_holder(owner, wow_address)
                        isholder_coolcat = is_holder(owner, coolcat_address)

                        if isholder_bayc:
                            bayc_count = get_nft_count(owner, bayc_address)
                            holder_since = get_max_holding_days(owner, bayc_address)
                            bayc_temp = ['BAYC', bayc_count]
                            bayc_final = bayc_temp + holder_since
                            all_data.append(bayc_final)

                        if isholder_clonex:
                            clonex_count = get_nft_count(owner, clonex_address)
                            holder_since = get_max_holding_days(owner, clonex_address)
                            clonex_temp = ['CloneX', clonex_count]
                            clonex_final = clonex_temp + holder_since
                            all_data.append(clonex_final)

                        if isholder_doodles:
                            doodles_count = get_nft_count(owner, doodles_address)
                            holder_since = get_max_holding_days(owner, doodles_address)
                            doodles_temp = ['Doodles', doodles_count]
                            doodles_final = doodles_temp + holder_since
                            all_data.append(doodles_final)

                        if isholder_azuki:
                            azuki_count = get_nft_count(owner, azuki_address)
                            holder_since = get_max_holding_days(owner, azuki_address)
                            azuki_temp = ['Azuki', azuki_count]
                            azuki_final = azuki_temp + holder_since
                            all_data.append(azuki_final)

                        if isholder_mb:
                            mb_count = get_nft_count(owner, mb_address)
                            holder_since = get_max_holding_days(owner, mb_address)
                            mb_temp = ['Moonbirds', mb_count]
                            mb_final = mb_temp + holder_since
                            all_data.append(mb_final)

                        if isholder_mayc:
                            mayc_count = get_nft_count(owner, mayc_address)
                            holder_since = get_max_holding_days(owner, mayc_address)
                            mayc_temp = ['MAYC', mayc_count]
                            mayc_final = mayc_temp + holder_since
                            all_data.append(mayc_final)

                        if isholder_wow:
                            wow_count = get_nft_count(owner, wow_address)
                            holder_since = get_max_holding_days(owner, wow_address)
                            wow_temp = ['World of Women', wow_count]
                            wow_final = wow_temp + holder_since
                            all_data.append(wow_final)

                        if isholder_coolcat:
                            coolcat_count = get_nft_count(owner, coolcat_address)
                            holder_since = get_max_holding_days(owner, coolcat_address)
                            coolcat_temp = ['Cool Cats', coolcat_count]
                            coolcat_final = coolcat_temp + holder_since
                            all_data.append(coolcat_final)

                        if isholder_punk:
                            punk_count = get_nft_count(owner, punk_address)
                            punk_temp = ['CryptoPunks', punk_count, '-', '-']
                            all_data.append(punk_temp)

                        holding_df = pd.DataFrame(all_data, columns=['Collection', 'Count', 'Holder Since', 'In Days'])
                        st.write(holding_df)


if selected_collection == 'CryptoPunks':
    filenames_punk = os.listdir('Punks')

    if uploaded_img is not None:

        if save_uploaded_image(uploaded_img):
            display_img = Image.open(uploaded_img)

            col1, col2 = st.columns(2)
            with col1:
                st.image(display_img, width=200)

            img1 = cv2.imread(os.path.join('Uploads', uploaded_img.name), 0)
            resized_img = resize(img1, (128, 128), anti_aliasing=True, preserve_range=True)

            name_scores = []
            scores = []

            for name in filenames_punk:
                img = cv2.imread(os.path.join('Punks', name), 0)
                ssim = structural_sim(img, resized_img)

                name_score = (name, ssim)
                scores.append(ssim)

                name_scores.append(name_score)

            max_score = max(scores)
            if max_score < 0.8:
                st.subheader('Please upload a better quality image!')
            else:
                for i in range(len(filenames_punk)):
                    if name_scores[i][1] == max_score:
                        final_nft = name_scores[i][0][:-4]
                        nft_num = name_scores[i][0].split('#')[1].split('.')[0]

                        opensea_link = f'https://opensea.io/assets/ethereum/0xb47e3cd837ddf8e4c57f05d70ab865de6e193bbb/{nft_num}'
                        rarity_link = f'https://rarity.tools/cryptopunks/view/{nft_num}'
                        owner = get_nft_owner('0xb47e3cd837ddf8e4c57f05d70ab865de6e193bbb', nft_num)
                        owner_link = f'https://opensea.io/{owner}'

                        with col1:
                            st.subheader(final_nft)
                        with col2:
                            st.subheader("Check on [Opensea](%s)" % opensea_link)
                            st.subheader("Check [Rarity Score](%s)" % rarity_link)

                        st.subheader(f"Owner : [{owner}]({owner_link})")

                        sales, volume, avg_price = get_collection_stats(punk_address)
                        st.subheader('CryptoPunks Collection Stats (Last 7 Days)')

                        colu1, colu2, colu3 = st.columns(3)

                        with colu1:
                            st.metric('Total Sales', f'{sales}')
                        with colu2:
                            st.metric('Volume', f'{round(volume, 1)} ETH')
                        with colu3:
                            st.metric('Average Selling Price', f'{round(avg_price, 2)} ETH')

                        st.subheader('CryptoPunks Floor Price across Marketplaces')

                        floorprice_df = get_floor_price_df(punk_address)

                        st.write(floorprice_df)

                        vol_list = get_volume(punk_address, nft_num)

                        st.subheader(f'{final_nft} Overall Stats')
                        colum1, colum2 = st.columns(2)

                        try:
                            with colum1:
                                st.metric('Total Sales', f'{len(vol_list)}')
                            with colum2:
                                st.metric('Volume Generated', f'{round(sum(vol_list), 2)} ETH')
                        except TypeError:
                            st.write('No Sales Found')

                        sale_history = get_sales_history(punk_address, nft_num)

                        if sale_history.empty:
                            pass
                        else:
                            fig = px.line(sale_history, x='date', y='price', title='Trade History',
                                          labels=dict(date="Date", price="Price (ETH)"))
                            fig.update_layout(xaxis=dict(showgrid=False),
                                              yaxis=dict(showgrid=False),
                                              title_x=0.5, width=800, height=500,
                                              margin=dict(l=35, b=35, r=35, t=35)
                                              )
                            st.write(fig)

                        st.subheader('More details about the Owner')

                        total_nfts = get_total_nfts_owned(owner)
                        st.write(f'Total NFTs Owned : {total_nfts}')

                        wallet_bal = get_wallet_balance(owner)
                        st.write(f'Wallet Balance : {wallet_bal} ETH')

                        st.subheader('No. of Top NFTs in the Wallet')

                        all_data = []
                        punk_count = get_nft_count(owner, punk_address)
                        punk_temp = ['CryptoPunks', punk_count, '-', '-']
                        all_data.append(punk_temp)

                        isholder_clonex = is_holder(owner, clonex_address)
                        isholder_doodles = is_holder(owner, doodles_address)
                        isholder_azuki = is_holder(owner, azuki_address)
                        isholder_mb = is_holder(owner, mb_address)
                        isholder_bayc = is_holder(owner, bayc_address)
                        isholder_mayc = is_holder(owner, mayc_address)
                        isholder_wow = is_holder(owner, wow_address)
                        isholder_coolcat = is_holder(owner, coolcat_address)

                        if isholder_clonex:
                            clonex_count = get_nft_count(owner, clonex_address)
                            holder_since = get_max_holding_days(owner, clonex_address)
                            clonex_temp = ['CloneX', clonex_count]
                            clonex_final = clonex_temp + holder_since
                            all_data.append(clonex_final)

                        if isholder_doodles:
                            doodles_count = get_nft_count(owner, doodles_address)
                            holder_since = get_max_holding_days(owner, doodles_address)
                            doodles_temp = ['Doodles', doodles_count]
                            doodles_final = doodles_temp + holder_since
                            all_data.append(doodles_final)

                        if isholder_azuki:
                            azuki_count = get_nft_count(owner, azuki_address)
                            holder_since = get_max_holding_days(owner, azuki_address)
                            azuki_temp = ['Azuki', azuki_count]
                            azuki_final = azuki_temp + holder_since
                            all_data.append(azuki_final)

                        if isholder_mb:
                            mb_count = get_nft_count(owner, mb_address)
                            holder_since = get_max_holding_days(owner, mb_address)
                            mb_temp = ['Moonbirds', mb_count]
                            mb_final = mb_temp + holder_since
                            all_data.append(mb_final)

                        if isholder_mayc:
                            mayc_count = get_nft_count(owner, mayc_address)
                            holder_since = get_max_holding_days(owner, mayc_address)
                            mayc_temp = ['MAYC', mayc_count]
                            mayc_final = mayc_temp + holder_since
                            all_data.append(mayc_final)

                        if isholder_wow:
                            wow_count = get_nft_count(owner, wow_address)
                            holder_since = get_max_holding_days(owner, wow_address)
                            wow_temp = ['World of Women', wow_count]
                            wow_final = wow_temp + holder_since
                            all_data.append(wow_final)

                        if isholder_coolcat:
                            coolcat_count = get_nft_count(owner, coolcat_address)
                            holder_since = get_max_holding_days(owner, coolcat_address)
                            coolcat_temp = ['Cool Cats', coolcat_count]
                            coolcat_final = coolcat_temp + holder_since
                            all_data.append(coolcat_final)

                        if isholder_bayc:
                            bayc_count = get_nft_count(owner, bayc_address)
                            holder_since = get_max_holding_days(owner, bayc_address)
                            bayc_temp = ['BAYC', bayc_count]
                            bayc_final = bayc_temp + holder_since
                            all_data.append(bayc_final)

                        holding_df = pd.DataFrame(all_data, columns=['Collection', 'Count', 'Holder Since', 'In Days'])
                        st.write(holding_df)


if selected_collection == 'Meebits':
    filenames_meebit = os.listdir('Meebits')

    if uploaded_img is not None:

        if save_uploaded_image(uploaded_img):
            display_img = Image.open(uploaded_img)

            col1, col2 = st.columns(2)
            with col1:
                st.image(display_img, width=200)

            img1 = cv2.imread(os.path.join('Uploads', uploaded_img.name), 0)
            resized_img = resize(img1, (192, 128), anti_aliasing=True, preserve_range=True)

            name_scores = []
            scores = []

            for name in filenames_meebit:
                img = cv2.imread(os.path.join('Meebits', name), 0)
                ssim = structural_sim(img, resized_img)

                name_score = (name, ssim)
                scores.append(ssim)

                name_scores.append(name_score)

            max_score = max(scores)
            if max_score < 0.8:
                st.subheader('Please upload a better quality image!')
            else:
                for i in range(len(filenames_meebit)):
                    if name_scores[i][1] == max_score:
                        final_nft = name_scores[i][0][:-4]
                        nft_num = name_scores[i][0].split('#')[1].split('.')[0]

                        opensea_link = f'https://opensea.io/assets/ethereum/0x7bd29408f11d2bfc23c34f18275bbf23bb716bc7/{nft_num}'
                        rarity_link = f'https://rarity.tools/meebits/view/{nft_num}'
                        owner = get_nft_owner('0x7bd29408f11d2bfc23c34f18275bbf23bb716bc7', nft_num)
                        owner_link = f'https://opensea.io/{owner}'

                        with col1:
                            st.subheader(final_nft)
                        with col2:
                            st.subheader("Check on [Opensea](%s)" % opensea_link)
                            st.subheader("Check [Rarity Score](%s)" % rarity_link)

                        st.subheader(f"Owner : [{owner}]({owner_link})")

                        sales, volume, avg_price = get_collection_stats(meebit_address)
                        st.subheader('Meebits Collection Stats (Last 7 Days)')

                        colu1, colu2, colu3 = st.columns(3)

                        with colu1:
                            st.metric('Total Sales', f'{sales}')
                        with colu2:
                            st.metric('Volume', f'{round(volume, 1)} ETH')
                        with colu3:
                            st.metric('Average Selling Price', f'{round(avg_price, 2)} ETH')

                        st.subheader('BAYC Floor Price across Marketplaces')

                        floorprice_df = get_floor_price_df(meebit_address)

                        st.write(floorprice_df)

                        vol_list = get_volume(meebit_address, nft_num)

                        st.subheader(f'{final_nft} Overall Stats')
                        colum1, colum2 = st.columns(2)

                        try:
                            with colum1:
                                st.metric('Total Sales', f'{len(vol_list)}')
                            with colum2:
                                st.metric('Volume Generated', f'{round(sum(vol_list), 2)} ETH')
                        except TypeError:
                            st.write('No Sales Found')

                        sale_history = get_sales_history(meebit_address, nft_num)

                        if sale_history.empty:
                            pass
                        else:
                            fig = px.line(sale_history, x='date', y='price', title='Trade History',
                                          labels=dict(date="Date", price="Price (ETH)"))
                            fig.update_layout(xaxis=dict(showgrid=False),
                                              yaxis=dict(showgrid=False),
                                              title_x=0.5, width=800, height=500,
                                              margin=dict(l=35, b=35, r=35, t=35)
                                              )
                            st.write(fig)

                        st.subheader('More details about the Owner')

                        total_nfts = get_total_nfts_owned(owner)
                        st.write(f'Total NFTs Owned : {total_nfts}')

                        wallet_bal = get_wallet_balance(owner)
                        st.write(f'Wallet Balance : {wallet_bal} ETH')

                        st.subheader('No. of Top NFTs in the Wallet')

                        all_data = []
                        meebit_count = get_nft_count(owner, meebit_address)
                        holder_since = get_max_holding_days(owner, meebit_address)
                        meebit_temp = ['Meebits', meebit_count]
                        meebit_final = meebit_temp + holder_since
                        all_data.append(meebit_final)

                        isholder_bayc = is_holder(owner, bayc_address)
                        isholder_clonex = is_holder(owner, clonex_address)
                        isholder_doodles = is_holder(owner, doodles_address)
                        isholder_azuki = is_holder(owner, azuki_address)
                        isholder_mb = is_holder(owner, mb_address)
                        isholder_punk = is_holder(owner, punk_address)
                        isholder_mayc = is_holder(owner, mayc_address)
                        isholder_wow = is_holder(owner, wow_address)
                        isholder_coolcat = is_holder(owner, coolcat_address)

                        if isholder_bayc:
                            bayc_count = get_nft_count(owner, bayc_address)
                            holder_since = get_max_holding_days(owner, bayc_address)
                            bayc_temp = ['BAYC', bayc_count]
                            bayc_final = bayc_temp + holder_since
                            all_data.append(bayc_final)

                        if isholder_clonex:
                            clonex_count = get_nft_count(owner, clonex_address)
                            holder_since = get_max_holding_days(owner, clonex_address)
                            clonex_temp = ['CloneX', clonex_count]
                            clonex_final = clonex_temp + holder_since
                            all_data.append(clonex_final)

                        if isholder_doodles:
                            doodles_count = get_nft_count(owner, doodles_address)
                            holder_since = get_max_holding_days(owner, doodles_address)
                            doodles_temp = ['Doodles', doodles_count]
                            doodles_final = doodles_temp + holder_since
                            all_data.append(doodles_final)

                        if isholder_azuki:
                            azuki_count = get_nft_count(owner, azuki_address)
                            holder_since = get_max_holding_days(owner, azuki_address)
                            azuki_temp = ['Azuki', azuki_count]
                            azuki_final = azuki_temp + holder_since
                            all_data.append(azuki_final)

                        if isholder_mb:
                            mb_count = get_nft_count(owner, mb_address)
                            holder_since = get_max_holding_days(owner, mb_address)
                            mb_temp = ['Moonbirds', mb_count]
                            mb_final = mb_temp + holder_since
                            all_data.append(mb_final)

                        if isholder_mayc:
                            mayc_count = get_nft_count(owner, mayc_address)
                            holder_since = get_max_holding_days(owner, mayc_address)
                            mayc_temp = ['MAYC', mayc_count]
                            mayc_final = mayc_temp + holder_since
                            all_data.append(mayc_final)

                        if isholder_wow:
                            wow_count = get_nft_count(owner, wow_address)
                            holder_since = get_max_holding_days(owner, wow_address)
                            wow_temp = ['World of Women', wow_count]
                            wow_final = wow_temp + holder_since
                            all_data.append(wow_final)

                        if isholder_coolcat:
                            coolcat_count = get_nft_count(owner, coolcat_address)
                            holder_since = get_max_holding_days(owner, coolcat_address)
                            coolcat_temp = ['Cool Cats', coolcat_count]
                            coolcat_final = coolcat_temp + holder_since
                            all_data.append(coolcat_final)

                        if isholder_punk:
                            punk_count = get_nft_count(owner, punk_address)
                            punk_temp = ['CryptoPunks', punk_count, '-', '-']
                            all_data.append(punk_temp)

                        holding_df = pd.DataFrame(all_data, columns=['Collection', 'Count', 'Holder Since', 'In Days'])
                        st.write(holding_df)
