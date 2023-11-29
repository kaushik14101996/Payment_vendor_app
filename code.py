import pandas as pd
import json
import requests
import streamlit as st
import time
from io import BytesIO
from datetime import timedelta
from st_aggrid import AgGrid
from streamlit_lottie import st_lottie

# Function to load lottie animation from URL
def load_lottieurl(url: str):
  r = requests.get(url)
  if r.status_code != 200:
    return None
  return r.json()

# Function for the login box
def login():
  st.sidebar.title("Enter the username and password")
  username = st.sidebar.text_input("Enter your username")
  password = st.sidebar.text_input("Enter your password", type="password")
  login_button = st.sidebar.button("Login")

  return username, password, login_button

# Credentials
correct_username = "a"
correct_password = "a"

# Function to style the dataframe
def style_dataframe(df):
  # Add borders to the dataframe
  border_style = f'<style>.dataframe {{border: 3px solid #00F;}}</style>'
  st.markdown(border_style, unsafe_allow_html=True)

  # Make headers bold
  header_style = f'<style>.dataframe th {{font-weight: bold;}}</style>'
  st.markdown(header_style, unsafe_allow_html=True)

# Function for user login
def login_check(username, password):
  if username == correct_username and password == correct_password:
    return True
  else:
    return False

# Function to download Excel
def download_excel(dataframes):
  op = BytesIO()
  with pd.ExcelWriter(op, engine='xlsxwriter') as wr:
    for sheet_name, df in dataframes.items():
      if sheet_name == "Pivot_Summary":
        df.to_excel(wr, index=True, sheet_name=sheet_name)
      else:
        df.to_excel(wr, index=False, sheet_name=sheet_name)
  op.seek(0)
  return op.getvalue()

# Function to calculate the next weekday
def calculate_next_weekday(date, target_weekday):
  days_until_target = (target_weekday - date.weekday() + 7) % 7
  return date + timedelta(days=days_until_target)

# Main function
def main():
  st.set_page_config(
    page_title="Vendor Payment Automation",
    layout="wide",
    page_icon="🧊",
  )

  st.markdown("""
    <script>
      document.addEventListener('hideSidebar', function() {
        document.querySelector('.sidebar').style.display = 'none';
      });
    </script>
  """, unsafe_allow_html=True)

  st.markdown('<h2 style="text-align: center; font-size: 45px; font-weight: bold;">Vendor Payment Automation</h2>', unsafe_allow_html=True)
  st.title("")

  # Load Lottie animation
  lottie_hello = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_M9p23l.json")
  st_lottie(
            lottie_hello,
            speed=1,
            reverse=False,
            loop=True,
            quality="low",  # medium ; high
            height=200,
            width=200,
            key=None,
           )

  # Perform data processing and display results if logged in
  username, password, login_button = login()
#   login_box()

  if login_check(username, password):
        st.sidebar.success("Login Successfully")
        st.sidebar.markdown(
        """
        ## Contact Information
        If you encounter any difficulties, please contact:

        - **Name:** Prathmesh Prakash More
        - **Phone Number:** +91-9870225421
        - **Email:** prathmesh.m@quation.in
        """
        )


        
        st.markdown('<h2 style="text-align: center; font-size: 24px; font-weight: bold;">Upload FABL1N File</h2>', unsafe_allow_html=True)
        uploaded_Fabl1n = st.file_uploader(" ", type=["xlsx"])
        # time.sleep(20)
        
        st.markdown('<h2 style="text-align: center; font-size: 24px; font-weight: bold;">Upload ZFI001 File</h2>', unsafe_allow_html=True)
        uploaded_ZFI001 = st.file_uploader("", type=["xlsx"])
        # time.sleep(20)
        
        st.markdown('<h2 style="text-align: center; font-size: 25px; font-weight: bold;">Upload Vendor Master File</h2>', unsafe_allow_html=True)
        uploaded_Master = st.file_uploader("Upload Vendor Master File", type=["xlsx"])
        # time.sleep(20)
        
        
        try:
            if uploaded_Fabl1n and uploaded_ZFI001 and uploaded_Master:
              login_button = st.button("Start Processing")
              if login_button:
    
                fbl1n = pd.read_excel(uploaded_Fabl1n, dtype='object')
                zfi001 = pd.read_excel(uploaded_ZFI001, dtype='object')
                vendors = pd.read_excel(uploaded_Master, dtype='object')

                vendors.dropna(subset=['Vendor Code'], inplace=True)
                vendors['Vendor Code'] = vendors['Vendor Code'].astype('string')

                fbl1n.dropna(subset=['Account'], inplace=True)
                fbl1n['Reference'] = fbl1n['Reference'].astype('string')
                fbl1n['Account'] = fbl1n['Account'].astype(str)
                fbl1n['concat'] = fbl1n['Account'] + fbl1n['Reference']

                zfi001.dropna(subset=['Payment Reason'], inplace=True)
                zfi001['concat'] = zfi001['Vendor'].astype('string') + zfi001['Payment Reason'].astype('string')



                st.subheader("Vendor Data")
                # style_dataframe(vendors)
                AgGrid(vendors, height=400)
                # st.dataframe(vendors, width=800)

                st.subheader("FBL1N Data")
                AgGrid(fbl1n, height=400)

                st.subheader("ZFI001 Data")
                AgGrid(zfi001, height=400)
                

                status_unique = zfi001['Status'].unique()
                st.sidebar.info("Unique Status")
                st.sidebar.write(status_unique)
                # AgGrid(status_unique)

                zfi001 = zfi001[~zfi001['Status'].isin(['AP-Blocked', 'FA-Post', 'AP-Canceled', 'TR-Paid'])]
                duplicate_concat = zfi001[zfi001['concat'].duplicated()]['concat']
                st.sidebar.info("Duplicate 'concat' Values")
                st.sidebar.write(duplicate_concat)
                # AgGrid(duplicate_concat)
                zfi001_1 = zfi001.copy()
                
                zfi001=zfi001[['Payment Reason','Application No','Status','concat']].astype('string')

                working = pd.merge(fbl1n, zfi001, on='concat', how='inner')
                vendors = vendors[['Vendor Code', 'Credit period']]

                working2 = pd.merge(working, vendors, left_on='Account', right_on='Vendor Code', how='left')
                working2['Document Date'] = pd.to_datetime(working2['Document Date'])
                working2['Due date'] = working2['Document Date'] + pd.to_timedelta(working2['Credit period'], unit='D')

                target_weekday = 4
                working2['Due date grouping'] = working2.apply(lambda row: calculate_next_weekday(row['Due date'], target_weekday), axis=1)

                working2.rename(columns={'Application No': 'BPM', 'Status': 'BPM Status'}, inplace=True)
                
                working2.rename(columns={'Application No': 'BPM', 'Status': 'BPM Status'}, inplace=True)
                working2=working2[['Year/month', 'G/L Account', 'Account', 'Company Code', 'Reference','Invoice reference', 'Document Type',
                        'Document Number','Document Date', 'Posting Date', 'Due date','Due date grouping', 'Amount in doc. curr.',
                    'Document currency', 'Amount in local currency', 'Assignment','Withholding tax amnt','W/tax exempt amount','Withhldg tax base amount', 'Text','BPM','BPM Status']]
                working2.head()

                st.subheader("Final Output Data")
                # style_dataframe(working2)
                # st.dataframe(working2, width=800)
                AgGrid(working2, height=400)


                working3 = working2.copy()
                working3['date_column'] = pd.to_datetime(working3['Due date grouping']).dt.strftime('%d-%b')

                Pivot = pd.pivot_table(data=working3, index='Account', columns='date_column',
                                    values='Amount in local currency', aggfunc='sum', fill_value=0, margins=True,
                                    margins_name='Total')
                pivot1=Pivot.reset_index()
                st.subheader("Final Pivot Summary")
                # style_dataframe(Pivot)
                AgGrid(pivot1, height=400)

                # st.dataframe(Pivot, width=800)

                dataframes = {"Output": working2, "Pivot_Summary": Pivot, "Fbl1n": fbl1n, "ZFI001": zfi001_1}
                excel_data = download_excel(dataframes)

                st.download_button("Download Result", data=excel_data, file_name="Result.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except:
            st.write("An error occurred. Please check your data and try again.")
            
  else:
    if username != "" and password != "":
        if username != correct_username or password != correct_password:
            st.sidebar.error("Login failed. Please provide the correct username and password.")    


if __name__ == "__main__":
    main()
    

    
