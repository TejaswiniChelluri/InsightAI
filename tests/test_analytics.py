import pytest
from database import initialize, connect
from analytics import execute
from ai_interpreter import fallback, UnsupportedQuestion

@pytest.fixture
def db(tmp_path):
    path = tmp_path/'test.db'
    initialize(path)
    return path

def test_total_revenue(db):
    result = execute('total_revenue',db_path=db)
    assert result['data'][0] == {'transactions':48,'revenue':1439200.0}

def test_top_product(db):
    result = execute('ranking',{'group':'product'},db)
    assert result['data'][0]['label']=='Monitor'
    assert result['data'][0]['revenue']==473000

def test_monthly_trend(db):
    result = execute('trend',db_path=db)
    assert len(result['data'])==6
    assert result['data'][4]['label']=='2026-05'
    assert result['data'][4]['revenue']==318500

def test_top_region(db):
    assert execute('ranking',{'group':'region'},db)['data'][0]['label']=='South'

def test_month_comparison(db):
    result=execute('compare_months',{'months':['2026-01','2026-02']},db)
    assert [r['revenue'] for r in result['data']]==[210250,234600]
    assert '24,350' in result['answer']

def test_excluded_records(db):
    conn=connect(db)
    assert conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]==51
    assert conn.execute('SELECT COUNT(*) FROM transactions WHERE exclusion_reason IS NOT NULL').fetchone()[0]==3
    conn.close()

def test_invalid_question():
    with pytest.raises(UnsupportedQuestion): fallback('What is the weather?')

def test_destructive_question():
    with pytest.raises(UnsupportedQuestion): fallback('DELETE FROM transactions')

def test_month_parser():
    assert fallback('Compare January and February 2026')['params']['months']==['2026-01','2026-02']

def test_zero_base_month(db):
    result=execute('compare_months',{'months':['2026-07','2026-06']},db)
    assert result['data'][0]['revenue']==0
    assert 'undefined' in result['answer']

def test_reject_bad_group(db):
    with pytest.raises(ValueError): execute('ranking',{'group':'sqlite_master'},db)
