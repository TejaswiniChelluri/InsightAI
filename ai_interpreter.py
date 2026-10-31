import json
import os
import re
from datetime import datetime

MONTHS = {name.lower():i for i,name in enumerate(('January','February','March','April','May','June','July','August','September','October','November','December'),1)}

class UnsupportedQuestion(ValueError): pass

def month_tokens(text):
    found = []
    pattern = r'\b(20\d{2})-(0[1-9]|1[0-2])\b|\b(' + '|'.join(MONTHS) + r')\b(?:\s+(20\d{2}))?'
    for m in re.finditer(pattern,text,re.I):
        value = f'{m.group(1)}-{m.group(2)}' if m.group(1) else f'{m.group(4) or 2026}-{MONTHS[m.group(3).lower()]:02d}'
        if value not in found: found.append(value)
    return found

def fallback(question):
    q = question.lower().strip()
    if not q or len(q)>500: raise UnsupportedQuestion('Enter a question of 1–500 characters.')
    if re.search(r'\b(drop|delete|truncate|insert|update|alter|create|attach|pragma)\b',q):
        raise UnsupportedQuestion('Database modification requests are not supported.')
    if any(x in q for x in ('invalid record','data quality','excluded record','missing data')):
        return {'intent':'data_quality'}
    # Compare sales channels when the question mentions Online and Retail.
    if (
        any(word in q for word in ('compare', 'comparison', 'difference', 'versus', ' vs '))
        and 'online' in q
        and 'retail' in q
    ):
        return {'intent': 'compare_channels'}
    if any(x in q for x in ('compare','difference','change between','growth between','versus',' vs ')) or ('revenue' in q and 'from' in q and 'to' in q):
        months = month_tokens(q)
        if len(months)!=2: raise UnsupportedQuestion('Please specify two months, e.g. compare January and February 2026.')
        return {'intent':'compare_months','params':{'months':months}}
    if any(x in q for x in ('average order','average transaction','average sale','average purchase')):
        return {'intent':'average_order'}
    if any(x in q for x in ('how many transaction','number of transaction','transaction count','how many orders','valid completed transaction','completed transaction count','count of valid transaction','number of valid transaction')):
        return {'intent':'transaction_count'}
    if any(x in q for x in ('trend','month wise','month-wise','monthly','by month','each month')):
        return {'intent':'trend','params':{'group':'month'}}
    group = next((g for g,words in [('product',('product','item')),('region',('region','north','south','east','west')),('category',('category','categories')),('channel',('channel','online','retail'))] if any(w in q for w in words)),None)
    if group and any(w in q for w in ('revenue','sales','perform','top','best','highest','lowest','least','worst','rank','generated','earning','selling')):
        direction = 'bottom' if any(w in q for w in ('lowest','least','worst','bottom','minimum')) else 'top'
        limit_match = re.search(r'\b(?:top|bottom|first)\s+(\d+)\b',q)
        params = {'group':group,'direction':direction}
        if limit_match: params['limit'] = int(limit_match.group(1))
        return {'intent':'ranking','params':params}
    if any(x in q for x in ('total revenue','overall revenue','total sales','overall sales','how much money','total earnings','total income','revenue overall')):
        return {'intent':'total_revenue'}
    raise UnsupportedQuestion('Unsupported question. Try total revenue, monthly trend, product/region/category/channel ranking, transaction count, average order, or comparing two months.')

# Optional AI classifier; model returns an intent only, never executable SQL or financial answers.
def interpret(question):
    if not question.strip() or len(question) > 500:
        raise UnsupportedQuestion('Enter a question of 1–500 characters.')
    if re.search(r'\b(drop|delete|truncate|insert|update|alter|create|attach|pragma)\b', question, re.I):
        raise UnsupportedQuestion('Database modification requests are not supported.')
    key = os.getenv('GROQ_API_KEY')
    if not key: return fallback(question)
    try:
        from groq import Groq
        prompt = ('Classify the user question into JSON with keys intent and params. '
                  'Allowed intents: total_revenue, transaction_count, average_order, ranking, trend, compare_months, compare_channels, data_quality, unsupported. '
                  'ranking params: group (product/region/category/channel), direction (top/bottom), optional limit integer 1-100. '
                  'trend params group month. compare_months params months array of two YYYY-MM strings. '
                  'Assume year 2026 for month names. No SQL or answers. Unsupported if outside these analyses. Question: ' + question)
        print("[Groq] Sending question to LLM...")
        completion = Groq(api_key=key).chat.completions.create(model=os.getenv('GROQ_MODEL','openai/gpt-oss-120b'),messages=[{'role':'user','content':prompt}],response_format={'type':'json_object'},temperature=0,max_tokens=200,timeout=8)
        print("[Groq] LLM response received successfully.")
        result = json.loads(completion.choices[0].message.content)
        intent = result.get('intent')
        if intent not in (
            'total_revenue',
            'transaction_count',
            'average_order',
            'ranking',
            'trend',
            'compare_months',
            'compare_channels',
            'data_quality'
        ):raise UnsupportedQuestion('Unsupported question.')
        params = result.get('params') or {}
        if not isinstance(params,dict): raise ValueError('Invalid model parameters')
        if intent == 'ranking' and (params.get('group') not in ('product','region','category','channel') or params.get('direction','top') not in ('top','bottom')): raise ValueError('Invalid ranking intent')
        if intent == 'trend': params = {'group':'month'}
        if intent == 'compare_months' and len(params.get('months',[])) != 2: raise ValueError('Invalid months')
        return {'intent':intent,'params':params}
    except UnsupportedQuestion: raise
    except Exception as exc:
        print(f"[Groq] Error: {type(exc).__name__}: {exc}")
        print("[Groq] Falling back to local interpreter.")
        return fallback(question)
