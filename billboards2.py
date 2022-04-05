import pandas as pd
import json
import requests
import time
import sys
import streamlit as st
import datetime as dt


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
        time.sleep(20)
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
def convert_to_dollars(hnt):
        helium_price = sending_request('https://api.helium.io/v1/oracle/prices/current')['price']/100000000
        return str(round(float(hnt)*helium_price,2))
def first_earning(earnings_data):
    formatted_dt = []
    if earnings_data ==None:
        return None
    for d in earnings_data:
        if d['total'] != 0:
            if d['timestamp'] != None:
                formatted_dt.append(dt.datetime.fromisoformat(d['timestamp'][:-1]))
    if len(formatted_dt)==0:
        return None
    first_earned = min(formatted_dt)
    formatted_str = first_earned.strftime("%b") + ' '+ str(first_earned.day) + ' '+ str(first_earned.year)
    return formatted_str
def days_online(earnings_data):
    formatted_dt = []
    if earnings_data ==None:
        return None
    for d in earnings_data:
        if d['total'] != 0:
            if d['timestamp'] != None:
                formatted_dt.append(dt.datetime.fromisoformat(d['timestamp'][:-1]))
    if len(formatted_dt)==0:
        return 0
    first_earned = min(formatted_dt)
    diff =  dt.datetime.now() - first_earned
    return diff.days

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
    d_total['state'] = " "
    d_total['link'] = ''
    d_total['reward scale'] = 0
    d_total['date deployed'] = ''

    d = dict(df.mean(axis =0, numeric_only = True))
    d['name'] = 'AVERAGE'
    d['street'] = " "
    d['status'] = " "
    d['city'] = " "
    d['state']= " "
    d['link']=" "
    d['date deployed']= " "

    df = df.append(d, ignore_index = True)  
    df = df.append(d_total, ignore_index = True)
    return df.loc[:, (df != 0).any(axis=0)]

#start cleaning the data 
account = st.secrets['bill_account']
bill_hot = pd.DataFrame(sending_request('https://api.helium.io/v1/accounts/'+account+'/hotspots'))

bill_hot['city'] = bill_hot.apply(lambda x: format_loc(x['geocode'], 'short_city'),axis=1)
bill_hot['street'] = bill_hot.apply(lambda x: format_loc(x['geocode'], 'short_street'),axis=1)
bill_hot['state'] = bill_hot.apply(lambda x: x['geocode']['short_state'],axis=1)

bill_hot['status'] = bill_hot.apply(lambda x: x['status']['online'], axis=1)
bill_hot['link'] = bill_hot.apply(lambda x: get_link(x['address']), axis=1)
bill_hot['reward scale'] = bill_hot['reward_scale']
bill_hot['name'] = bill_hot.apply(lambda x: x['name'].replace("-"," "),axis=1)

bill_hot['all earnings'] = bill_hot.apply(lambda x: get_all_earnings_data(x['address'],x['timestamp_added']) ,axis=1)
bill_hot['day earnings'] = bill_hot.apply(lambda x: day_earnings(pd.DataFrame(x['all earnings'])), axis=1)
bill_hot['week earnings'] = bill_hot.apply(lambda x: week_earnings(pd.DataFrame(x['all earnings'])), axis=1)
bill_hot['two week earnings'] = bill_hot.apply(lambda x: two_week_earnings(pd.DataFrame(x['all earnings'])), axis=1)
bill_hot['month earnings'] = bill_hot.apply(lambda x: month_earnings(pd.DataFrame(x['all earnings'])), axis=1)
bill_hot['total mined'] = bill_hot.apply(lambda x: total_earnings(pd.DataFrame(x['all earnings'])), axis=1)

bill_hot['date deployed'] = bill_hot.apply(lambda x: first_earning(x['all earnings']), axis=1) 
bill_hot['days online'] = bill_hot.apply(lambda x: days_online(x['all earnings']), axis=1)

new_hotspots = bill_hot[['name','city', 'street','state','status', 'reward scale', 'day earnings','week earnings',
           'month earnings','total mined','date deployed','link']].sort_values(by='total mined', ascending = False)
new_hotspots = add_total_avg(new_hotspots)
new_hotspots = new_hotspots.round(2)
new_hotspots = new_hotspots.astype('str')
new_hotspots = new_hotspots.set_index('name')


if check_password():
    st.sidebar.write("## Helium Hotspots")
    filt = st.sidebar.selectbox('Filter Online/Offline', ['All', 'Online','Offline'])
    cali = st.sidebar.selectbox('Filter California', ['All','Exclude California'])
    if cali == 'Exclude California':
        new_hotspots = new_hotspots[new_hotspots['state']!= 'CA'].reset_index(drop=True)

    st.write("## Hotspot Rollup")
    all_earnings = round(sending_request('https://api.helium.io/v1/accounts/'+ account +'/rewards/sum?min_time=2021-06-01T00:00:00')['sum']/100000000, 2)
    helium_price = round(sending_request('https://api.helium.io/v1/oracle/prices/current')['price']/100000000,2)

    names = ['Current HNT Price','Total HNT Mined Since Inception','Total $ Earned Since Inception','Total Hotspots Connected to HBP Wallet','Total Online','Average Transmit Scale']
    num_online = len(bill_hot[bill_hot['status']=='online'])
    avg_transmit = bill_hot['reward scale'].mean()
    values = [str(helium_price), str(all_earnings), str(round(helium_price*all_earnings,2)), str(len(bill_hot)),str(num_online), str(round(avg_transmit,2))]

    df = pd.DataFrame(list(zip(names, values)),
                   columns =['', 'current'])
    df = df.set_index('')
    df

    row_names=['24 hour','7 day','14 day','30 day','lifetime']
    columns_names = ['Time','Avg Composite','Avg Online','Aggregate']
    avg_earnings = [str(round(bill_hot['day earnings'].mean(),2)), str(round(bill_hot['week earnings'].mean(),2)),str(round(bill_hot['two week earnings'].mean(),2)),str(round(bill_hot['month earnings'].mean(),2)), str(round(bill_hot['total mined'].mean(),2))]
    
    hots_online_24 = bill_hot[(bill_hot['status']=='online')&(bill_hot['days online']>=1)]
    hots_online_7 = bill_hot[(bill_hot['status']=='online')&(bill_hot['days online']>=7)]
    hots_online_14 = bill_hot[(bill_hot['status']=='online')&(bill_hot['days online']>=14)]
    hots_online_30 = bill_hot[(bill_hot['status']=='online')&(bill_hot['days online']>=30)]

    avg_online_earnings =[str(round(hots_online_24['day earnings'].mean(),2)), str(round(hots_online_7['week earnings'].mean(),2)),str(round(hots_online_14['two week earnings'].mean(),2)),str(round(hots_online_30['month earnings'].mean(),2)), str(round(hots_online_30['total mined'].mean(),2))]    
    
    agg_earnings = [str(round(bill_hot['day earnings'].sum(),2)), str(round(bill_hot['week earnings'].sum(),2)),str(round(bill_hot['two week earnings'].sum(),2)),str(round(bill_hot['month earnings'].sum(),2)), str(round(bill_hot['total mined'].sum(),2))]
    
    earned_df = pd.DataFrame(list(zip(row_names, avg_earnings,avg_online_earnings,agg_earnings )),
                   columns =columns_names)
    earned_df = earned_df.set_index('Time')
    earned_df['Avg Composite $'] = earned_df.apply(lambda x: convert_to_dollars(x['Avg Composite']),axis=1)
    earned_df['Avg Online $'] = earned_df.apply(lambda x: convert_to_dollars(x['Avg Online']),axis=1)
    earned_df['Aggregate $'] = earned_df.apply(lambda x: convert_to_dollars(x['Aggregate']),axis=1)
    earned = earned_df[['Avg Composite','Avg Composite $','Avg Online', 'Avg Online $', 'Aggregate', 'Aggregate $']]
    earned.columns = ['Avg Composite','in $ ','Avg Online', ' in $', 'Aggregate', ' in $ ']
    earned
    
    st.write('## Hotspot Breakdown')
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
