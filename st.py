import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import numpy as np
import os

import time
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
load_dotenv()

headers = {
        'Accept': os.getenv('ACCEPT'),
        'Authorization': os.getenv('AUTHORIZATION'),
        'X-GitHub-Api-Version': os.getenv('GITHUB_API_VERSION'),
}

def github_json_parse(parse, repo_name, start_date, end_date):
    result_dic = {}
    result_dic[repo_name] = -1
    result = []
    for con_num in range(len(parse)):
            contributor = parse[con_num]['author']['login']
            data = parse[con_num]['weeks']
            result_dic[contributor] = 0
            
            for item in data:
                if item['c'] != 0:
                    item['w'] = datetime.utcfromtimestamp(item['w']).strftime('%y%m%d')
                    if start_date <= int(item['w']) <= end_date : ##yymmdd
                        result_dic[contributor] = result_dic[contributor] + int(item['c'])
    result.append(result_dic)
    return result

def github_json_parse2(result_dic, result, parse, repo_name, start_date, end_date):
    result_dic[repo_name] = -1
    for con_num in range(len(parse)):
            contributor = parse[con_num]['author']['login']
            data = parse[con_num]['weeks']
            result_dic[contributor] = 0
        
            for item in data:
                if item['c'] != 0:
                    item['w'] = datetime.utcfromtimestamp(item['w']).strftime('%y%m%d')
                    if start_date <= int(item['w']) <= end_date : ##yymmdd
                        result_dic[contributor] = result_dic[contributor] + int(item['c'])
    result.append(result_dic)
    return result

def specific_repo(org, repo_name, start_date_input, end_date_input, headers):

    start_date = int(start_date_input.replace("-", ""))
    end_date = int(end_date_input.replace("-", ""))
    
    url = 'https://api.github.com/repos/'+str(org)+'/'+str(repo_name)+'/stats/contributors'
    r = requests.get(url, headers=headers)
    parse = json.loads(r.text)
    if start_date < end_date:
        original = github_json_parse(parse, repo_name, start_date, end_date)
    else:
        raise Exception("wrong date") 
    data_dict = original[0]
    filtered_data = {k: v for k, v in data_dict.items() if v != -1}
    data = {'Categories': list(filtered_data.keys())}
    for category in data['Categories']:
        data[category] = [0 if cat != category else val for cat, val in filtered_data.items()]

    df = pd.DataFrame(data)
    df = df.set_index('Categories')
    return chart_placeholder.bar_chart(df.sum(axis=1), width=0.01)  # Aggregates the sum of all categories for each item
#########################################################    

def get_repo(org, headers):
    r = requests.get('https://api.github.com/orgs/'+str(org)+'/repos', headers=headers)
    parse = json.loads(r.text)
    repo_name_list = []
    for i in (parse):
        repo_name_list.append(i['html_url'].split('/')[-1])
    return repo_name_list
#########################################################

def fetch_repo_contributors(org, repo_name, headers, start_date, end_date, result):
    url = f'https://api.github.com/repos/{org}/{repo_name}/stats/contributors'
    r = requests.get(url, headers=headers)
    parse = json.loads(r.text)
    result_dic = {}
    if start_date < end_date:
        github_json_parse2(result_dic, result, parse, repo_name, start_date, end_date)
    else:
        print('wrong date')

def overall(org, start_date_input, end_date_input, headers):

    r = requests.get(f'https://api.github.com/orgs/{org}/members', headers=headers)
    parse = json.loads(r.text)
    user_name_list = {i['login']: 0 for i in parse}

    repo_name_list = get_repo(org, headers)

    start_date = int(start_date_input.replace("-", ""))
    end_date = int(end_date_input.replace("-", ""))

    result = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_repo = {executor.submit(fetch_repo_contributors, org, repo_name, headers, start_date, end_date, result): repo_name for repo_name in repo_name_list}
        for future in as_completed(future_to_repo):
            repo_name = future_to_repo[future]
            try:
                data = future.result()
            except Exception as exc:
                print(f'{repo_name} generated an exception: {exc}')

    for result_dic in result:
        for user, contributions in result_dic.items():
            if user in user_name_list:
                user_name_list[user] += contributions

    filtered_data = {k: v for k, v in user_name_list.items() if v != -1}

    df = pd.DataFrame.from_dict(filtered_data, orient='index', columns=['Contributions'])

    return chart_placeholder.bar_chart(df.sum(axis=1), width=0.01)
############################################################

st.title('Infoteam Tracker')
org = os.getenv('ORG')

name_list = ['Overall'] + get_repo(org, headers)

selection = st.selectbox('Select Repository view:', name_list)

with st.form(key='date_range_form'):
    start_date = st.date_input("Start Date", value=datetime(2022, 1, 1), min_value=datetime(2000, 1, 1), max_value=datetime.now())
    end_date = st.date_input("End Date", value=datetime(2024, 2, 18), min_value=datetime(2000, 1, 1), max_value=datetime.today())
    submit_button = st.form_submit_button(label='Submit')

chart_placeholder = st.empty()

if submit_button:
    if start_date < end_date:
        start_date_str = start_date.strftime('%y-%m-%d')
        end_date_str = end_date.strftime('%y-%m-%d')

        if selection == 'Overall':
            overall(org, start_date_str, end_date_str, headers)
        else:
            specific_repo(org, selection, start_date_str, end_date_str, headers)
    else:
        st.error("Error: End date must be after start date.")