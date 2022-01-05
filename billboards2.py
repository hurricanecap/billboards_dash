import pandas as pd
import json
import requests
import time
import sys
import streamlit as st

def check_password():
    """Returns `True` if correct password is entered."""

    # Show text field for password.
    # You can move this anywhere on the page!
    password = st.sidebar.text_input("Password", type="password")
        
    # Check that it matches the stored password.
    if password:
        if password == st.secrets["password"]:
            return True
        else:
            st.sidebar.error("😕 Password incorrect")
    return False
def sending_request(url, cursor=None):
    r = requests.get(url=url, params = {'cursor':cursor}, headers={'user-agent':'dash_v1.ipynb/0.0.1'})
    data = r.json()
    if 'data' in data:
        if 'cursor' in data:
            print(url+'?cursor='+data['cursor'])
            return data['data'] + send_req(url, data['cursor'])

        else:
            return data['data']
    else:
        time.sleep(10)
        sending_request(url, cursor)
def format_loc(loc_dic, key):
    if loc_dic[key] != None:
        return loc_dic[key].title()
    else:
        return None
def get_all_earnings_data(address, timestamp_added):
    url = 'https://api.helium.io/v1/hotspots/'+ address+'/rewards/sum?min_time='+timestamp_added+'&bucket=day'
    data = sending_request(url)
    return data
def day_earnings(earnings):
    if len(earnings)==0:
        return 0
    return earnings['total'][0]
def month_earnings(earnings):
    if len(earnings)==0:
        return 0
    if len(earnings) >= 30:
        return earnings['total'][0:30].sum()
    else:
        return earnings['total'].sum()
def week_earnings(earnings):
    if len(earnings)==0:
        return 0
    if len(earnings) >= 7:
        return earnings['total'][0:7].sum()
    else:
        return earnings['total'].sum()
def two_week_earnings(earnings):
    if len(earnings)==0:
        return 0
    if len(earnings) >= 14:
        return earnings['total'][0:14].sum()
    else:
        return earnings['total'].sum()
def total_earnings(earnings):
    if len(earnings)==0:
        return 0
    return earnings['total'].sum()
def get_link(address):
    return 'https://explorer.helium.com/hotspots/'+ address
def color_status(val):
    color = 'white'
    try:
        if float(val) < 300:
            color = 'tomato'
        elif float(val) < 500 and float(val) > 300:
            color = 'yellow'
    
    except:  
        if val == None:
            color = 'lightsteelblue'
        if val == 'online':
            color = 'lightgreen'
        elif val == 'offline':
            color = 'tomato'
        elif val == ' ':
            color = 'lightsteelblue'
        elif val == '  ':
            color = 'white'
        else:
            color = 'white'
    return f'background-color:{color}'
def add_total_avg(df):   
    d_total = dict(df.sum(axis =0, numeric_only = True))
    d_total['name'] = 'TOTAL'
    d_total['street'] = " "
    d_total['status'] = " "
    d_total['city'] = " "
    #d_total['link'] = ''
    d_total['reward scale'] = 0

    d = dict(df.mean(axis =0, numeric_only = True))
    d['name'] = 'AVERAGE'
    d['street'] = " "
    d['status'] = " "
    d['city'] = " "
    #d['link']=" "

    df = df.append(d, ignore_index = True)  
    df = df.append(d_total, ignore_index = True)
    return df.loc[:, (df != 0).any(axis=0)]

#start cleaning the data 
account = st.secrets['bill_account']
bill_hot = pd.DataFrame(sending_request('https://api.helium.io/v1/accounts/'+account+'/hotspots'))

bill_hot['city'] = bill_hot.apply(lambda x: format_loc(x['geocode'], 'short_city'),axis=1)
bill_hot['street'] = bill_hot.apply(lambda x: format_loc(x['geocode'], 'short_street'),axis=1)
bill_hot['status'] = bill_hot.apply(lambda x: x['status']['online'], axis=1)
#bill_hot['link'] = bill_hot.apply(lambda x: get_link(x['address']), axis=1)
bill_hot['reward scale'] = bill_hot['reward_scale']
bill_hot['name'] = bill_hot.apply(lambda x: x['name'].replace("-"," "),axis=1)

bill_hot['all earnings'] = bill_hot.apply(lambda x: get_all_earnings_data(x['address'],x['timestamp_added']) ,axis=1)
bill_hot['day earnings'] = bill_hot.apply(lambda x: day_earnings(pd.DataFrame(x['all earnings'])), axis=1)
bill_hot['week earnings'] = bill_hot.apply(lambda x: week_earnings(pd.DataFrame(x['all earnings'])), axis=1)
bill_hot['two week earnings'] = bill_hot.apply(lambda x: two_week_earnings(pd.DataFrame(x['all earnings'])), axis=1)
bill_hot['month earnings'] = bill_hot.apply(lambda x: month_earnings(pd.DataFrame(x['all earnings'])), axis=1)
bill_hot['total mined'] = bill_hot.apply(lambda x: total_earnings(pd.DataFrame(x['all earnings'])), axis=1)

new_hotspots = bill_hot[['name','city', 'street','status', 'reward scale', 'day earnings',
           'month earnings','total mined']].sort_values(by='total mined', ascending = False)
new_hotspots = add_total_avg(new_hotspots)
new_hotspots = new_hotspots.round(2)
new_hotspots = new_hotspots.astype('str')
new_hotspots = new_hotspots.set_index('name')


if check_password():
    st.sidebar.write("## Helium Hotspots")
    total_earnings = sending_request('https://api.helium.io/v1/accounts/'+ account +'/rewards/sum?min_time=2021-06-01T00:00:00')['sum']
    helium_price = sending_request('https://api.helium.io/v1/oracle/prices/current')['price']/100000000
    
    earned = pd.DataFrame([{'HNT': str(round(total_earnings/100000000,2)), '$': str(round(total_earnings/100000000*helium_price,2))}, {'HNT': str(round((total_earnings/100000000)/len(bill_hot),2)), '$': str(round(((total_earnings/100000000)/len(bill_hot))*helium_price,2))}])
    earned.index = ['total earnings', 'average earnings']
    earned

    quantiles = bill_hot[['total mined']].quantile(q=[1,.75,.5,.25], axis= 0)
    quantiles.index = ['100%','75%','50%','25%']
    quantiles.columns = ['earnings quartiles']
    quantiles['earnings quartiles'] = quantiles.apply(lambda x: round(x['earnings quartiles'],2), axis = 1)
    quantiles
    
    filt = st.sidebar.selectbox('Filter Online/Offline', ['All', 'Online','Offline'])
    if filt == 'Online':
        filtered = new_hotspots[new_hotspots['status']== 'online']
        hot_data = filtered.style.apply(lambda x: ['background: lightsteelblue' if x.name in ['TOTAL','AVERAGE'] else '' for i in x], axis=1)
        st.table(hot_data.applymap(color_status, subset=['status']).set_precision(2))
    elif filt == 'Offline':
        filtered = new_hotspots[new_hotspots['status']== 'offline']
        hot_data = filtered.style.apply(lambda x: ['background: lightsteelblue' if x.name in ['TOTAL','AVERAGE'] else '' for i in x], axis=1)
        st.table(hot_data.applymap(color_status, subset=['status']).set_precision(2))
    else:
        hot_data = new_hotspots.style.apply(lambda x: ['background: lightsteelblue' if x.name in ['TOTAL','AVERAGE'] else '' for i in x], axis=1)
        st.table(hot_data.applymap(color_status, subset=['status']).set_precision(2))
