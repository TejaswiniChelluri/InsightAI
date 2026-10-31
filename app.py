import os
import requests
import streamlit as st
import pandas as pd

st.set_page_config(page_title='InsightAI',page_icon='📊',layout='wide')
st.title('📊 InsightAI | Sales Intelligence')
st.caption('Ask about the supplied sales transactions. All financial figures come from read-only database queries.')
API = os.getenv('API_URL','http://127.0.0.1:8000')
examples = ['What is the total revenue?','Which product generated the highest revenue?','What is the monthly revenue trend?','Which region generated the highest sales?','Compare January and February 2026','Show top 5 products by revenue','Which category has the lowest sales?','Compare online and retail sales','What is the average order value?','How many transactions are valid?','Show data quality issues']
selected = st.selectbox('Try an example (or type your own below)', ['']+examples)
question = st.text_input('Your question',value=selected,placeholder='e.g. Show monthly revenue trend')
if st.button('Analyze',type='primary'):
    if not question.strip(): st.warning('Please enter a question.')
    else:
        try:
            response = requests.post(f'{API}/ask',json={'question':question},timeout=20)
            if response.status_code != 200:
                st.error(response.json().get('detail','Request failed'))
            else:
                result = response.json()
                st.success(result['answer'])
                df = pd.DataFrame(result['data'])
                st.subheader('Supporting data')
                st.dataframe(df,use_container_width=True,hide_index=True)
                if result['intent']=='trend' and not df.empty: st.line_chart(df.set_index('label')['revenue'])
                elif result['intent']=='ranking' and not df.empty: st.bar_chart(df.set_index('label')['revenue'])
                st.caption(result['note'] + ' Currency unspecified in source CSV.')
                with st.expander('SQL evidence (read-only)'):
                    st.code(result['sql'],language='sql')
                    st.write('Bound parameters:',result['parameters'])
        except requests.RequestException:
            st.error('Backend unavailable. Start FastAPI using the README instructions.')
