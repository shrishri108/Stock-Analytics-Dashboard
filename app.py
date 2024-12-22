import yfinance as yf
import streamlit as st
import pandas as pd
import requests_cache
import datetime
import plotly.express as px
from streamlit_extras import add_vertical_space as avs
from babel.numbers import format_currency
import sqlite3
# from alpha_vantage.timeseries import TimeSeries

def format_numbers(number):
    if 'N/A' in str(number):
        return 'N/A'
    
    number=float(number)
    formatted_number = format_currency(number, 'INR', locale='en_IN')
    return formatted_number

def fetch_ticker_data(ticker_name):
    if len(ticker_name)==0:
        st.error('Enter correct ticker.')
        return
    session = requests_cache.CachedSession('yfinance.cache')
    session.headers['User-agent'] = 'my-program/1.0'
    ticker = yf.Ticker(ticker_name, session=session)
    return ticker

def get_balance_sheet(ticker):

    balance_sheet=pd.DataFrame(ticker.balance_sheet)
    balance_sheet=balance_sheet.fillna('N/A')
    balance_sheet=balance_sheet.map(format_numbers)

    # List of asset-related keywords
    assets_keywords = [
        'Total Assets', 'Total Non Current Assets', 'Other Non Current Assets', 
        'Investments And Advances', 'Long Term Equity Investment', 
        'Goodwill And Other Intangible Assets', 'Other Intangible Assets', 
        'Goodwill', 'Net PPE', 'Accumulated Depreciation', 'Gross PPE', 
        'Leases', 'Other Properties', 'Machinery Furniture Equipment', 
        'Buildings And Improvements', 'Land And Improvements', 'Properties', 
        'Current Assets', 'Other Current Assets', 'Hedging Assets Current', 
        'Inventory', 'Finished Goods', 'Work In Process', 'Raw Materials', 
        'Receivables', 'Accounts Receivable', 'Allowance For Doubtful Accounts Receivable', 
        'Gross Accounts Receivable', 'Cash Cash Equivalents And Short Term Investments', 
        'Other Short Term Investments', 'Cash And Cash Equivalents', 'Cash Equivalents', 'Cash Financial'
    ]

    # List of liability-related keywords
    liabilities_keywords = [
        'Ordinary Shares Number', 'Share Issued', 'Net Debt', 'Total Debt',
        'Tangible Book Value', 'Invested Capital', 'Working Capital', 
        'Net Tangible Assets', 'Capital Lease Obligations', 'Common Stock Equity', 
        'Total Capitalization', 'Total Equity Gross Minority Interest', 'Stockholders Equity', 
        'Gains Losses Not Affecting Retained Earnings', 'Other Equity Adjustments', 'Retained Earnings', 
        'Capital Stock', 'Common Stock', 'Total Liabilities Net Minority Interest', 
        'Total Non Current Liabilities Net Minority Interest', 'Other Non Current Liabilities', 
        'Tradeand Other Payables Non Current', 'Non Current Deferred Liabilities', 
        'Non Current Deferred Revenue', 'Non Current Deferred Taxes Liabilities', 
        'Long Term Debt And Capital Lease Obligation', 'Long Term Capital Lease Obligation', 
        'Long Term Debt', 'Current Liabilities', 'Other Current Liabilities', 
        'Current Deferred Liabilities', 'Current Deferred Revenue', 'Current Debt And Capital Lease Obligation', 
        'Current Debt', 'Pensionand Other Post Retirement Benefit Plans Current', 'Payables And Accrued Expenses', 
        'Payables', 'Total Tax Payable', 'Income Tax Payable', 'Accounts Payable'
    ]


    # Function to apply styles based on assets/liabilities
    def style_balance_sheet(row):
        if any(keyword in row.name for keyword in assets_keywords):
            return ['background-color: green; color: white'] * len(row)  # Green for assets
        elif any(keyword in row.name for keyword in liabilities_keywords):
            return ['background-color: red; color: white'] * len(row)  # Red for liabilities
        else:
            return [''] * len(row)  # No style for other rows

    # Apply the style function to the DataFrame
    styled_balance_sheet = balance_sheet.style.apply(style_balance_sheet, axis=1)

    return styled_balance_sheet


def print_chart(ticker,symbol,tf):
    price=ticker.history(period=tf)
    price['Date']=price.index
    price['Date']=pd.to_datetime(price['Date'])

    fig=px.line(price,x='Date',y='Close')
    min_y=price['Close'].min()-10
    max_y=price['Close'].max()+10
    st.write(min_y,max_y)
    fig.update_layout(yaxis=dict(range=[min_y,max_y]))
    st.plotly_chart(fig)
    return


def render_financials(ticker):
    st.subheader('Financials')
    # Streamlit layout for buttons on the left
    col1, col2 = st.columns([1, 3])

    # Buttons in the first column (left side)
    with col1:
        button1 = st.button('Balance Sheet')
        button2 = st.button('Income Statement')
        button3 = st.button('Cash Flow')

    # Display corresponding DataFrame on the right side based on the button clicked
    with col2:
        if button1:
            # st.write("Balance Sheet")
            balance_sheet=ticker.balance_sheet
            st.dataframe(balance_sheet)
        elif button2:
            # st.write("Income Statement")
            income_statement=ticker.income_stmt
            st.dataframe(income_statement)
        elif button3:
            # st.write("Cash Flow")
            cash_flow=ticker.cash_flow
            st.dataframe(cash_flow)
        else:
            # st.write("Balance Sheet")
            balance_sheet=ticker.balance_sheet
            st.dataframe(balance_sheet)

def render_news(ticker,company_name):
    st.subheader('{} in News'.format(company_name))
    in_news=yf.Search(company_name, max_results=5, news_count=5, enable_fuzzy_query=False, session=None, proxy=None, timeout=30, raise_errors=True)
    for item in in_news.news:
        title=item['title']
        publisher=item['publisher']
        date_posted=item['providerPublishTime']
        link=item['link']
        date_posted= datetime.datetime.utcfromtimestamp(date_posted)

        st.markdown('<h5>{0} </h5><h6>{1}</h6><a style="font-size:small;display:inline;" href="{2}">Read Full</a>'.format(publisher,title,link),
                    unsafe_allow_html=True)
        st.markdown('<h7>Posted on : {0}</h7>'.format(date_posted),
                    unsafe_allow_html=True)
        # avs.add_vertical_space(1)
        st.markdown('<hr>', unsafe_allow_html=True) 
        
def get_info_df(ticker):
    exchange=ticker.fast_info['exchange']
    currency=ticker.fast_info['currency']
    market_cap=ticker.fast_info['marketCap']
    year_change=ticker.fast_info['yearChange']
    ltp=ticker.fast_info['lastPrice']
    total_shares=ticker.fast_info['shares']
    info={
        'Exchange':exchange,
        'Currency':currency,
        'Market Cap':market_cap,
        'LTP':ltp,
        'Total Outstanding Shares':total_shares
    }

    info=pd.DataFrame([info])
    info=info.set_index('Exchange')
    return info

def get_financial_df(ticker):

    financial_metrics = {
        "symbol": ticker.info.get('symbol', 'N/A'),
        "Div. Yield": str(round(float(ticker.info.get('dividendYield', 0.0)) * 100, 2)) if ticker.info.get('dividendYield') else 'N/A',
        "Trailing P/E": str(round(float(ticker.info.get('trailingPE', 0.0)), 2)) if ticker.info.get('trailingPE') else 'N/A',
        "Trailing EPS": str(round(float(ticker.info.get('trailingEps', 0.0)), 2)) if ticker.info.get('trailingEps') else 'N/A',
        "Book Value": str(round(float(ticker.info.get('bookValue', 0.0)), 2)) if ticker.info.get('bookValue') else 'N/A',
        "Price/Book": str(round(float(ticker.info.get('priceToBook', 0.0)), 2)) if ticker.info.get('priceToBook') else 'N/A',
        "Current Ratio": str(round(float(ticker.info.get('currentRatio', 0.0)), 2)) if ticker.info.get('currentRatio') else 'N/A',
        "Revenue Growth (%)": str(round(float(ticker.info.get('revenueGrowth', 0.0)) * 100, 2)) if ticker.info.get('revenueGrowth') else 'N/A',
        "Earnings Growth (%)": str(round(float(ticker.info.get('earningsGrowth', 0.0)) * 100, 2)) if ticker.info.get('earningsGrowth') else 'N/A',
        "EBITDA Margin (%)": str(round(float(ticker.info.get('ebitdaMargins', 0.0)) * 100, 2)) if ticker.info.get('ebitdaMargins') else 'N/A',
    }

    # Convert to DataFrame with proper formatting
    financial_metrics_df = pd.DataFrame([financial_metrics])
    financial_metrics_df.set_index('symbol', inplace=True)

    return financial_metrics_df

def deploy_dashboard(ticker):      
    company_name=ticker.info['longName']
    txt=':grey['+company_name+']'
    symbol=ticker.info['symbol']
    st.title(txt)
    col1, col2 = st.columns([1, 3])
    with col1:
        info=get_info_df(ticker)
        st.dataframe(info[['Currency','Market Cap','Total Outstanding Shares','LTP']])
    with col2:
        financial_df=get_financial_df(ticker)
        st.dataframe(financial_df[financial_df.columns.to_list()])

    # with st.expander("Select Date Range"):
    #     start_date = st.date_input('Start Date', value=datetime.date.today() - datetime.timedelta(days=30))
    #     end_date = st.date_input('End Date', value=datetime.date.today())        
        

    buttons = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
    selected_button = '1mo'
    cols = st.columns(len(buttons)+20) 

    with st.container():
        cols = st.columns(len(buttons)) 
        for i, button in enumerate(buttons):
            with cols[i]:
                if st.button(button,use_container_width=True):
                    selected_button = button
                    st.write(selected_button)
        
        print_chart(ticker,symbol,selected_button)
    
    render_financials(ticker)

    render_news(ticker,company_name)

def log_error(e):

    time_stamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    connection=sqlite3.connect('./logs/error_logs.db')
    cursor=connection.cursor()
    cursor.execute('''create table if not exists app_error_logs(
               time_stamp nvarchar(30) not null,
               error_string text not null
               )
               ''')   
    cursor.execute('''
            insert into app_error_logs(time_stamp,error_string) 
            values(?,?)
            ''',(time_stamp,str(e))) 

if __name__ == "__main__":    
    try:
        st.set_page_config(page_title="Stock Analytics Dashboard",
                        layout='wide') 

        st.title("Stock Analytics Dashboard")   
        st.write('Enter Ticker for stock info. Eg. AAPL.')
        st.markdown("Find all availale tickers [here](https://finance.yahoo.com/lookup/)")

        ticker=''

        if 'ticker_name' not in st.session_state:
            st.session_state.ticker_name = 'AAPL'
            ticker=fetch_ticker_data(st.session_state.ticker_name)

        def update_ticker():
            st.session_state.ticker_name = st.session_state.new_ticker_name
            fetch_ticker_data(st.session_state.ticker_name)

        ticker_name=st.text_input('',placeholder='AAPL',key='new_ticker_name',on_change=update_ticker)
        ticker=fetch_ticker_data(st.session_state.ticker_name)

        deploy_dashboard(ticker)
    except Exception as e:
        log_error(e)
        st.error('Something went wrong! Error has been logged.')

#-----------------
