from database import connect

# All queries are predefined, SELECT-only; user input is never interpolated into SQL.
GROUPS = {'product': 'product', 'region': 'region', 'category': 'category', 'channel': 'sales_channel', 'month': "substr(order_date,1,7)"}

def execute(intent, params=None, db_path=None):
    params = params or {}
    conn = connect(db_path)
    try:
        if intent == 'total_revenue':
            sql = 'SELECT COUNT(*) AS transactions, COALESCE(SUM(revenue),0) AS revenue FROM transactions WHERE exclusion_reason IS NULL'
            args = ()
        elif intent == 'transaction_count':
            sql = 'SELECT COUNT(*) AS transactions FROM transactions WHERE exclusion_reason IS NULL'
            args = ()
        elif intent == 'average_order':
            sql = 'SELECT COUNT(*) AS transactions, COALESCE(SUM(revenue),0) AS revenue, ROUND(AVG(revenue),2) AS average_order_value FROM transactions WHERE exclusion_reason IS NULL'
            args = ()
        elif intent in ('ranking', 'trend'):
            group = params.get('group', 'month' if intent == 'trend' else 'product')
            if group not in GROUPS: raise ValueError('Unsupported grouping')
            col = GROUPS[group]
            order = 'label ASC' if intent == 'trend' else ('revenue ASC, label ASC' if params.get('direction') == 'bottom' else 'revenue DESC, label ASC')
            sql = f'SELECT {col} AS label, COUNT(*) AS transactions, ROUND(SUM(revenue),2) AS revenue FROM transactions WHERE exclusion_reason IS NULL GROUP BY {col} ORDER BY {order}'
            limit = params.get('limit')
            if limit is not None:
                if type(limit) is not int or not 1 <= limit <= 100: raise ValueError('Invalid limit')
                sql += ' LIMIT ?'; args = (limit,)
            else: args = ()
        elif intent == 'compare_months':
            months = params.get('months', [])
            if len(months) != 2 or any(not isinstance(m,str) or len(m)!=7 or m[4]!='-' or not m[:4].isdigit() or not m[5:].isdigit() or not 1 <= int(m[5:]) <= 12 for m in months):
                raise ValueError('Specify two months in YYYY-MM format')
            sql = "SELECT substr(order_date,1,7) AS month, COUNT(*) AS transactions, COALESCE(SUM(revenue),0) AS revenue FROM transactions WHERE exclusion_reason IS NULL AND substr(order_date,1,7) IN (?,?) GROUP BY substr(order_date,1,7) ORDER BY month"
            args = tuple(months)
        elif intent == 'compare_channels':
            sql = """
                SELECT sales_channel AS label,
                       COUNT(*) AS transactions,
                       ROUND(SUM(revenue), 2) AS revenue
                FROM transactions
                WHERE exclusion_reason IS NULL
                  AND LOWER(sales_channel) IN ('online', 'retail')
                GROUP BY sales_channel
                ORDER BY sales_channel
            """
            args = ()
        elif intent == 'data_quality':
            sql = "SELECT COALESCE(exclusion_reason,'valid') AS status, COUNT(*) AS records FROM transactions GROUP BY exclusion_reason ORDER BY status"
            args = ()
        else: raise ValueError('Unsupported analysis')
        rows = [dict(r) for r in conn.execute(sql,args).fetchall()]
        if intent == 'compare_months':
            by_month = {r['month']:r for r in rows}
            rows = [by_month.get(m, {'month':m,'transactions':0,'revenue':0}) for m in months]
            a,b = (r['revenue'] for r in rows)
            difference = round(b-a,2)
            percent = round(difference/a*100,2) if a else None
            answer = f'Revenue changed by {difference:,.2f} ({percent:+.2f}%) from {months[0]} to {months[1]}.' if percent is not None else f'Revenue changed by {difference:,.2f}; percentage change is undefined because the first month has zero revenue.'
        elif intent == 'compare_channels':
            channel_data = {
                str(row['label']).lower(): row
                for row in rows
            }

            online = channel_data.get(
                'online',
                {'transactions': 0, 'revenue': 0}
            )
            retail = channel_data.get(
                'retail',
                {'transactions': 0, 'revenue': 0}
            )

            difference = round(
                online['revenue'] - retail['revenue'], 2
            )

            if difference > 0:
                result_text = 'Online sales generated more revenue'
            elif difference < 0:
                result_text = 'Retail sales generated more revenue'
            else:
                result_text = 'Online and Retail generated equal revenue'

            answer = (
                f"{result_text}. "
                f"Online revenue: {online['revenue']:,.2f} "
                f"({online['transactions']} transactions). "
                f"Retail revenue: {retail['revenue']:,.2f} "
                f"({retail['transactions']} transactions). "
                f"Difference (Online - Retail): {difference:,.2f}."
            )
        elif intent == 'total_revenue': answer = f"Total completed valid revenue is {rows[0]['revenue']:,.2f} across {rows[0]['transactions']} transactions."
        elif intent == 'transaction_count': answer = f"There are {rows[0]['transactions']} valid completed transactions."
        elif intent == 'average_order': answer = f"Average transaction value is {rows[0]['average_order_value']:,.2f}." if rows[0]['average_order_value'] is not None else 'No valid transactions available.'
        elif intent == 'data_quality': answer = 'Record counts by validation status are shown below.'
        elif not rows: answer = 'No matching data is available.'
        elif intent == 'trend': answer = 'Monthly completed revenue is shown below, in chronological order.'
        else:
            direction = params.get('direction','top')
            answer = f"{rows[0]['label']} has the {'lowest' if direction == 'bottom' else 'highest'} {params.get('group','product')} revenue: {rows[0]['revenue']:,.2f}."
        return {'intent':intent,'answer':answer,'data':rows,'sql':sql,'parameters':list(args),'note':'Revenue = quantity × unit_price − discount; only valid Completed records included.'}
    finally:
        conn.close()
