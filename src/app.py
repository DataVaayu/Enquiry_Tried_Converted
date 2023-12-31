## Getting the credentials, reading the sheets and creating three dataframes

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '1GTApxk_-pGgoPxXbhR0rSz_E9YuaB93kj8MjRzEuUOc'
SHEET_NAME_ENQUIRY = '2023!A:AC'
SHEET_NAME_TOTAL_STOCK = "Total Stock!A:M"
SHEET_NAME_PRODUCT_MASTER = "Company Product Master!A:T"
DSR_Kolkata = "DSR Kolkata!A:P"
DSR_Delhi = "DSR Delhi!A:P"



"""Shows basic usage of the Sheets API.
Prints values from a sample spreadsheet.
"""
creds = None
# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

try:
    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API to get enquiry sheet
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=SHEET_NAME_ENQUIRY).execute()
    values = result.get('values', [])
    
    # __getting the total stock
    result_stock = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=SHEET_NAME_TOTAL_STOCK).execute()
    values_stock = result_stock.get('values', [])
    
    # __getting the Product Master
    result_product_master = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=SHEET_NAME_PRODUCT_MASTER).execute()
    values_product_master = result_product_master.get('values', [])
    
    # 2. Call the Sheets dsr kolkata data
    sheet = service.spreadsheets()
    result_dsr_kolkata = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=DSR_Kolkata).execute()
    values_dsr_kolkata = result_dsr_kolkata.get('values', [])
    
    # 3. Call the Sheets API to get dsr delhi data
    sheet = service.spreadsheets()
    result_dsr_delhi = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=DSR_Delhi).execute()
    values_dsr_delhi = result_dsr_delhi.get('values', [])

    if not values:
        print('No data found.')
        
    # creating the dataframe by reading enquiry sheet
    df_enquiry = pd.DataFrame.from_records(values)
    
    # creating the dataframe by reading stock
    df_stock = pd.DataFrame.from_records(values_stock)
    
    # creating the dataframe by reading product master
    df_product_master = pd.DataFrame.from_records(values_product_master)
    
    # Creating the dataframes for DSR Kolkata and Delhi
    df_dsr_kolkata = pd.DataFrame.from_records(values_dsr_kolkata)
    df_dsr_delhi = pd.DataFrame.from_records(values_dsr_delhi)
    
    

except HttpError as err:
    print(err)

    
# __________________________________Sizing the dataframes_________________________________________________________________
    
# Setting the column names to the first rows that appear in the dataframes

dataframes=[df_enquiry,df_stock,df_product_master,df_dsr_kolkata,df_dsr_delhi]

for i in dataframes:
    i.columns=i.loc[0]
    i.drop(0,axis=0,inplace=True)

# _____________________________Filtering the stock dataframe to stock of Osaa Only _______________________________________

df_stock=df_stock[(df_stock["Location Type"]=='STORE')&(df_stock["Brand"]=="OSAA BY ADARSH")].copy()
df_stock=df_stock[df_stock["Location Name"].isin(["Delhi Store New","Showroom","WAREHOUSE 1","WAREHOUSE 2","SALE PCS","CANDY WAREHOUSE","Warehouse"])]

# _____________________________________________Stripping the Tried Not Tried Column__________________________________________

df_enquiry["Tried / Not Tried"] = df_enquiry["Tried / Not Tried"].apply(lambda x: str(x).strip())

# _________________________________________________________________________________________________________________________

# RENAMING THE DATE COLUMN IN THE ENQUIRY SHEET

df_enquiry.rename(columns={"DATE":"Date"},inplace=True)

# ________________________________________ Cleaning the enquiry sheet Category Data __________________________

# print(df_enquiry["Category"].unique())

df_enquiry["Category"]=df_enquiry["Category"].astype(str)

# df_enquiry["Category"]=df_enquiry["Category"].apply(lambda x: x.replace("","no data"))

df_enquiry["Category"]=df_enquiry["Category"].apply(lambda x: x.replace("Miscellaneous","MISCELLANEOUS"))
df_enquiry["Category"]=df_enquiry["Category"].apply(lambda x: x.replace("Lehenga","LEHANGA"))
df_enquiry["Category"]=df_enquiry["Category"].apply(lambda x: x.replace("Saree","SAREE"))
df_enquiry["Category"]=df_enquiry["Category"].apply(lambda x: x.replace("Jacket","JACKET"))
df_enquiry["Category"]=df_enquiry["Category"].apply(lambda x: x.replace("Suit","SUIT"))
df_enquiry["Category"]=df_enquiry["Category"].apply(lambda x: x.replace("Top Skirt","TOP SKIRT"))
df_enquiry["Category"]=df_enquiry["Category"].apply(lambda x: x.replace("SUIT","SUIT"))


df_enquiry["Category"]=df_enquiry["Category"].apply(lambda x: x.upper())


# _________________________ Transforming the Price Columns __________________________________________

df_enquiry["Price Bracket"].replace("","no data",inplace=True)
df_enquiry["Price Bracket"].replace("no data","No Data",inplace=True)

#df_enquiry["Price Bracket"].unique()

df_product_master["Price"]=df_product_master["Price"].astype("int")

df_stock["MRP"].replace("",00000,inplace=True)
df_stock['MRP']=df_stock['MRP'].astype(int)


# ____________________________ ________________________________________________________________________

# making the lower price limit and the upper price limit from the price bracket column

for index, row in df_enquiry.iterrows():
    if (row["Price Bracket"]=="No Data") | (row["Price Bracket"]==None):
        pass
    elif "-" in row["Price Bracket"]:
            df_enquiry.loc[index,"Lower Price Limit"]=row["Price Bracket"].split("-")[0]
            df_enquiry.loc[index,"Upper Price Limit"]=row["Price Bracket"].split("-")[-1]
    elif "Under " in row["Price Bracket"]:
            df_enquiry.loc[index,"Lower Price Limit"]=0
            df_enquiry.loc[index,"Upper Price Limit"]=100000
    elif "Above" in row["Price Bracket"]:
            df_enquiry.loc[index,"Lower Price Limit"]=350000
            df_enquiry.loc[index,"Upper Price Limit"]=1000000
    else:
        pass
    
# ________________________________________ Creating Lower Price Limit Column _____________________________

df_enquiry["Lower Price Limit"].replace("None",0,inplace=True)
df_enquiry["Lower Price Limit"].replace("0",0,inplace=True)
df_enquiry["Lower Price Limit"].replace("25k",25000,inplace=True)
df_enquiry["Lower Price Limit"].replace("25K",25000,inplace=True)
df_enquiry["Lower Price Limit"].replace("50k",50000,inplace=True)
df_enquiry["Lower Price Limit"].replace("75k",75000,inplace=True)
df_enquiry["Lower Price Limit"].replace("1L",100000,inplace=True)
df_enquiry["Lower Price Limit"].replace("1.5L",150000,inplace=True)
df_enquiry["Lower Price Limit"].replace("1.75L",175000,inplace=True)
df_enquiry["Lower Price Limit"].replace("2.75L",275000,inplace=True)
df_enquiry["Lower Price Limit"].replace("2L",200000,inplace=True)
df_enquiry["Lower Price Limit"].replace("1.25L",125000,inplace=True)
df_enquiry["Lower Price Limit"].replace("2.5L",250000,inplace=True)
df_enquiry["Lower Price Limit"].replace("3.25L",325000,inplace=True)
df_enquiry["Lower Price Limit"].replace("2.25L",225000,inplace=True)
df_enquiry["Lower Price Limit"].replace("3L",300000,inplace=True)
df_enquiry["Lower Price Limit"].replace(0,0,inplace=True)
df_enquiry["Lower Price Limit"].replace(350000,350000,inplace=True)

# ___________________________ Creating Upper Price Limit Column ____________________________________________

df_enquiry["Upper Price Limit"].replace("None",0,inplace=True)
df_enquiry["Upper Price Limit"].replace("0",0,inplace=True)
df_enquiry["Upper Price Limit"].replace("25k",25000,inplace=True)
df_enquiry["Upper Price Limit"].replace("25K",25000,inplace=True)
df_enquiry["Upper Price Limit"].replace("50k",50000,inplace=True)
df_enquiry["Upper Price Limit"].replace("75k",75000,inplace=True)
df_enquiry["Upper Price Limit"].replace("1L",100000,inplace=True)
df_enquiry["Upper Price Limit"].replace("1.5L",150000,inplace=True)
df_enquiry["Upper Price Limit"].replace("1.75L",175000,inplace=True)
df_enquiry["Upper Price Limit"].replace("2.75L",275000,inplace=True)
df_enquiry["Upper Price Limit"].replace("2L",200000,inplace=True)
df_enquiry["Upper Price Limit"].replace("1.25L",125000,inplace=True)
df_enquiry["Upper Price Limit"].replace("2.5L",250000,inplace=True)
df_enquiry["Upper Price Limit"].replace("3.25L",325000,inplace=True)
df_enquiry["Upper Price Limit"].replace("2.25L",225000,inplace=True)
df_enquiry["Upper Price Limit"].replace("3L",300000,inplace=True)
df_enquiry["Upper Price Limit"].replace("3.5L",350000,inplace=True)
df_enquiry["Upper Price Limit"].replace(0,0,inplace=True)
df_enquiry["Upper Price Limit"].replace(350000,350000,inplace=True)


# ___________________________ Transforming the datatypes of created columns _____________________________

#df_enquiry["Lower Price Limit"].fillna(0,inplace=True)
#df_enquiry["Lower Price Limit"]=df_enquiry["Lower Price Limit"].astype("int")

#df_enquiry["Upper Price Limit"].fillna(0,inplace=True)
#df_enquiry["Upper Price Limit"]=df_enquiry["Lower Price Limit"].astype("int")

# Fill the empty cells with no data value

df_enquiry.fillna("No Data",inplace=True)

# ____________________________Creating the Style Code - Color Column ______________________________________

# Creating for each dataframe

# df_enquiry["Style Code Color"] = df_enquiry["Style Code"] +"-"+ df_enquiry["Color"] # no style code column in enquiry sheet

df_stock["Style Code Color"] = df_stock["Style Code"] +"-"+ df_stock["Color"]

df_product_master["Style Code Color"] = df_product_master["Style Code"] +"-"+ df_product_master["Color"]

# ___________________ Changing the format of the date column in the enquiry sheet ___________________________

df_enquiry["Date"]=df_enquiry["Date"].apply(lambda x: x.strip())
df_enquiry["Date"]=df_enquiry["Date"].apply(lambda x: str(x).replace(".","/"))

#separating the day, month and year

for index,row in df_enquiry.iterrows():
    try:
        df_enquiry.loc[index,"Day"]=row["Date"].split("/")[0]
    except:
        row["Date"]
        
    try:
        df_enquiry.loc[index,"Month"]=row["Date"].split("/")[1]
    except:
        row["Date"]
        
    try:
        df_enquiry.loc[index,"Year"]=row["Date"].split("/")[2]
    except:
        row["Date"]

# Replacing the year col values that has only 23 to have 2023
for index,row in df_enquiry.iterrows():
    if (df_enquiry.loc[index,"Year"]==23) | (df_enquiry.loc[index,"Year"]=="23"):
        df_enquiry.loc[index,"Year"]=2023

# congragating the day month and year into one date column
#df_enquiry["Date"]=pd.to_datetime(df_enquiry[["Year","Month","Day"]])

for index,row in df_enquiry.iterrows():
    df_enquiry.loc[index,"Date"] = "-".join([str(row["Year"]),str(row["Month"]),str(row["Day"])])


df_enquiry["Date"]=df_enquiry["Date"].astype('str')
# print(df_enquiry["Date"].shape[0])

# ____________________________ Making the Date Column for DSR Table ______________________________________


# Making the date column for Kolkata DSR

drop_index = df_dsr_kolkata[df_dsr_kolkata["Date2"]=="--"].index
df_dsr_kolkata.drop(index=drop_index,inplace=True)
df_dsr_kolkata["Date2"]=pd.to_datetime(df_dsr_kolkata["Date2"])
df_dsr_kolkata["Date2"]=df_dsr_kolkata["Date2"].astype(str)

# Making the date column for Delhi DSR

drop_index_delhi = df_dsr_delhi[df_dsr_delhi["Date2"]=="--"].index
df_dsr_delhi.drop(index=drop_index_delhi,inplace=True)
df_dsr_delhi["Date2"]=pd.to_datetime(df_dsr_delhi["Date2"])
df_dsr_delhi["Date2"]=df_dsr_delhi["Date2"].astype(str)

# ___________________________ Combining the DSR Tables into One dataframe ________________________________

df_dsr_total = pd.concat([df_dsr_kolkata, df_dsr_delhi],ignore_index=True)

# Removing the commas from the MRP column
df_dsr_total["MRP"] = df_dsr_total["MRP"].apply(lambda x: str(x).replace(",",""))

# replacing the blanks with 0
df_dsr_total["MRP"].replace("","0",inplace=True)

# Changing the datatype of the MRP column
df_dsr_total["MRP"]=df_dsr_total["MRP"].astype(int)

# ___________________________ Creating the Dash App _______________________________________________________

from dash import Dash, dcc, callback, Input, Output, dash_table,html
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
from datetime import date, datetime, timedelta



#df_enquiry['Date']=pd.to_datetime(df_enquiry['Date'])
#df_enquiry = df_enquiry
#df_product_master = 
#df_stock = 

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
#server=app.server

app.layout = dbc.Container([
    
    dbc.Row(html.H1("ENQUIRY SHEET ANALYSIS",style={"text-align":"center","background-color":"rgb(207,239,249)","color":"rgb(80,0,0)"}),className="p-5"),
        
    dbc.Row([
        
        dbc.Col([
            
            html.H3("Customer Enquiries"),

            
            html.Label("Select Dates"),
            #dcc.Dropdown(id="date-dropdown",multi=True,options=df_enquiry["Date"].unique(),value=["24/07/2023","25/07/2023","26/07/2023","27/07/2023","28/07/2023","29/07/2023"]),
            
            dcc.DatePickerRange(
                id="date-picker-range",
                calendar_orientation="horizontal",
                day_size=39,
                end_date_placeholder_text="Return",
                first_day_of_week=1,
                reopen_calendar_on_clear=True,
                clearable=True,
                number_of_months_shown=1,
                min_date_allowed=date(2023, 1, 16),
                initial_visible_month=date(2023, 8, 1),
                display_format='MMM Do, YY',
                month_format='MMMM, YYYY',
                minimum_nights=1,
                updatemode='singledate',
                start_date='2023-04-1',
                end_date="2023-08-11",
                
            ),
            dbc.Row([
                dbc.Col([
                    html.Label("Select Parameters for view"),
                    dcc.Dropdown(id="columns-dropdown",multi=True,options=["Point of Enquiry","Category","Color","Price Bracket","Ocassion","Tried / Not Tried","Bought /Did not buy"],value=["Category"]),
                ],width=6),
                dbc.Col([
                    html.Label("Select Store"),
                    dcc.Dropdown(id="store-selector",multi=True,options=["Delhi Store","Kolkata Store"],value=['Delhi Store']),
                ],width=6), 
            ]),   
            
            html.Label(id="row-count-enquiry"),
            dcc.Graph(id="customer-enquiry-analysis"),
        ],width=6),
        
        dbc.Col([
            html.H3("Set Parameters"),
            
            dbc.Row([
                dbc.Col([
                    html.Label("Lower Price Limit *"),
                    dcc.Input(id="lower-price-range",type="number",placeholder="enter number"),
                ],width=6),
                
                dbc.Col([
                    html.Label("Upper Price Limit *"),
                    dcc.Input(id="upper-price-range",type="number",placeholder="enter number"),
                ],width=6),
                
            ]),
            
            dbc.Row([
                
                dbc.Col([
                    html.Label("Choose Category *"),
                    dcc.Dropdown(id="product-category-dropdown",options=df_product_master["Product Name"].unique()),
                ],width=4),
                
                
                dbc.Col([
                    html.Label("Choose Occasion"),
                    dcc.Dropdown(id="occasion-dropdown",options=df_product_master["Occasion"].unique(),multi=True), 
                ],style={"width":4}),
                
                dbc.Col([
                    html.Label("Item Type"),
                    dcc.RadioItems(["NOS","All"],"All",inline=True,id="radioitem-nos")
                ], width=4)
            ]),
            html.H3("Product Master Table"),
            html.Label(id="product-master",style={"offset":"10"}),
            dash_table.DataTable([{"name":i, "id":i} for i in df_product_master[["Style Code","Product Name","Color","Price","NOS"]].columns]
                                 ,page_size=10,id="product-master-table",
                                style_data_conditional=[{
                                    "if":{
                                        'filter_query':"{NOS}='YES'",
                                        'column_id':'Style Code',
                                        
                                    },
                                    'background-color':'tomato',
                                    'color':'white',
                                }]),
            
            
        ],width=4),
        
    ]),
    
    dbc.Row([
        
        dbc.Col([
            html.H3(id="availability-store-heading",style={"font-size":18}),
            html.Label(id="delhi-availability",style={"offset":"10"}),
            dash_table.DataTable([{"data":i,"id":i} for i in df_stock.columns],page_size=10,id="delhi-stock-table",
                                style_data_conditional=[{
                                   "if":{
                                       "filter_query":"{NOS}='YES'",
                                       "column_id":"Style Code",
                                   },
                                    "background-color":"tomato",
                                    "color":"white",

                                }],fill_width=False),
            ],style={"width":3,}),
        
        dbc.Col([
            html.H3(id="availability-osaa-heading",style={"font-size":18}),
            html.Label(id="osaa-availability",style={"offset":"10"}),
            dash_table.DataTable([{"data":i,"id":i} for i in df_stock.columns],page_size=10,id="osaa-stock-table",
                                style_data_conditional=[{
                                   "if":{
                                       "filter_query":"{NOS}='YES'",
                                       "column_id":"Style Code",
                                   },
                                    "background-color":"tomato",
                                    "color":"white",

                                }],fill_width=False),
            ],style={"width":3,"offset":2}),
        
        
    ]),
    
    html.Br(),
    html.Br(),

    # _______________________ Outfit Tried Table ______________________________________________

    dbc.Row([
         html.H3("Outfits Tried",style={"text-align":"center","background-color":"rgb(207,239,249)"}),
         html.Label(id="outfit-tried-table-count"),         
         dash_table.DataTable([{"data":i,"id":i}for i in df_enquiry[["Outfit Tried","Color","Price Bracket","Category"]].columns], page_size=10,id="outfit-tried-table",
                             style_data={"white-space":"normal"}),
    ]),

    # _______________________ Outfit Bought Table Layout _____________________________________

    html.Br(),
    html.Br(),
    dbc.Row([
         html.H3("Outfits Bought",style={"text-align":"center","background-color":"rgb(207,239,249)"}),
         html.Label(id="outfit-bought-table-count"),
         dash_table.DataTable([{"data":i,"id":i}for i in df_enquiry[["Outfit Tried","Color","Price Bracket","Category"]].columns], page_size=10,id="outfit-bought-table",
                             style_data={"white-space":"normal"}),
    ]),

    # __________________________Conversion Tables________________________________________________

    html.Br(),
    html.Br(),
    html.H3("Trial to Conversion of Items in Stock",style={"text-align":"center","background-color":"rgb(207,239,249)"}),
    html.Br(),

    #creating the dropdowns for style code and color - coded in the first call back
    dbc.Row([
         
        dbc.Col([
             html.Label(id="enquiry_delhi"),
        ],width=6),
        
        dbc.Col([
             html.Label(id="enquiry_kolkata"),
        ],width=6),
        
    ]),

    html.Br(),
    
    dbc.Row([
         dbc.Col([
              html.H3("Delhi Conversion",style={"font-size":18}),
              dash_table.DataTable([{"data":i,"id":i} for i in df_stock.columns],page_size=10,id="delhi-conversion-table",
                                   style_data_conditional=[{
                                   "if":{
                                       "filter_query":"{NOS}='YES'",
                                       "column_id":"Style Code",
                                   },
                                    "background-color":"tomato",
                                    "color":"white",

                                }],fill_width=False),
         ],width=6),

         dbc.Col([
              html.H3("Kolkata Conversion",style={"font-size":18}),
              dash_table.DataTable([{"data":i,"id":i} for i in df_stock.columns],page_size=10,id="kolkata-conversion-table",
                                   style_data_conditional=[{
                                   "if":{
                                       "filter_query":"{NOS}='YES'",
                                       "column_id":"Style Code",
                                   },
                                    "background-color":"tomato",
                                    "color":"white",

                                }],fill_width=False),
         ],width=6),  

         html.Br(),    



    ]), 
],className="p-5")


@callback(
    Output("customer-enquiry-analysis","figure"),
    Output("product-master-table","data"),
    Output("delhi-stock-table","data"),
    Output("osaa-stock-table","data"),
    Output("product-master","children"),
    Output("delhi-availability","children"),
    Output("osaa-availability","children"),
    Output("availability-store-heading","children"),
    Output("availability-osaa-heading","children"),
    Output("row-count-enquiry","children"),
    Output("enquiry_delhi","children"),
    Output("enquiry_kolkata","children"),
    #Input("date-dropdown","value"),
    Input("date-picker-range","start_date"),
    Input("date-picker-range","end_date"),
    Input("columns-dropdown","value"),
    Input("upper-price-range","value"),
    Input("lower-price-range","value"),
    Input("product-category-dropdown","value"),
    Input("occasion-dropdown","value"),
    Input("radioitem-nos","value"),
    Input("store-selector","value"),
    
)

def update_graph(start_date,end_date,columns_selection,uPriceRange,lPriceRange,productCatDropdown,occasionDropdown,radioNos,storeSelector):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    date_values=[]
    while start_date<=end_date:
        date_values.append(start_date.strftime("%Y-%m-%d"))
        start_date += timedelta(days=1)
    
    # convert the dates in the date_values list into string
    date_values=list(map(str,date_values))

    # print(date_values)
    
    
    df_enquiry_selection = df_enquiry[(df_enquiry["Date"].isin(date_values))] # filtering out the input dates
    df_enquiry_selection = df_enquiry_selection[(df_enquiry_selection["Point of Enquiry"].isin(storeSelector))] # filtering out the entered store
    
    # returning the row count of the figure dataframe
    count_rows = df_enquiry_selection["Point of Enquiry"].shape[0]
    count_rows_string = f"Count: {count_rows}"
       
    fig = px.sunburst(df_enquiry_selection,path=columns_selection,width=400,height=400,)
    fig.update_traces(textinfo="label+percent parent")

    # Modifying the display Label string here since after the loop the storeSelector list is changing

    availability_store_string=f"Availability in {storeSelector}"
    availability_Osaa_string=f"Availability in Osaa Stock but not in {storeSelector}"

    # Changing the Delhi Store Name  and Kolkata store inside StoreSelector to match stock location names

    for i in range(len(storeSelector)):
        if storeSelector[i] =="Delhi Store":
              storeSelector[i]="Delhi Store New"
        elif storeSelector[i]=="Kolkata Store":
             storeSelector.append("Showroom")
             storeSelector.append("WAREHOUSE 2")
             storeSelector.append("WAREHOUSE 1")
             storeSelector.append("Warehouse")
             storeSelector.append("SALE PCS")
        
        
    
  
    # filtering the dataframe according to the price limits
    
    df_product_master_filtered=df_product_master[(df_product_master["Price"]<=uPriceRange)&(df_product_master["Price"]>=lPriceRange)]    #filtering by price range
    
    df_product_master_filtered=df_product_master_filtered[df_product_master_filtered["Product Name"]==productCatDropdown]    #filtering product category
    if radioNos=="NOS":
        df_product_master_filtered=df_product_master_filtered[df_product_master_filtered["NOS"]=="YES"] # filtering out the NOS column
   
    if occasionDropdown:    # filtering by the occasion dropdown
        df_product_master_filtered=df_product_master_filtered[df_product_master_filtered["Occasion"].isin(occasionDropdown)]
        
    df_product_master_filtered.drop_duplicates(subset="Style Code Color",inplace=True)  # dropping duplicate style code color column
    
        
    
    
    # Filtering the store stock dataframe
    
    df_stock_filtered = df_stock[df_stock["Location Name"].isin(storeSelector)]   #filtering by store name
    df_stock_filtered=df_stock_filtered[df_stock_filtered["Category"]==productCatDropdown]   #filtering by product category
    df_stock_filtered=df_stock_filtered[(df_stock_filtered["MRP"]>=lPriceRange) & (df_stock_filtered["MRP"]<=uPriceRange)]    #filtering by price range
    if radioNos=="NOS":
        df_stock_filtered=df_stock_filtered[df_stock_filtered["NOS"]=="YES"]

    if occasionDropdown: # filtering store stock by occasion
         df_stock_filtered=df_stock_filtered[df_stock_filtered["Occasion"].isin(occasionDropdown)]

    df_stock_filtered.drop_duplicates(subset="Style Code Color",inplace=True) # dropping duplicate style code color colummn
    # print(storeSelector)
        
    # Filtering the Osaa stock availability that are not in selected store

    df_stock_filtered_OSAA = df_stock[~df_stock["Location Name"].isin(storeSelector)]
    df_stock_filtered_OSAA=df_stock_filtered_OSAA[df_stock_filtered_OSAA["Category"]==productCatDropdown]   #filtering by product category
    df_stock_filtered_OSAA=df_stock_filtered_OSAA[(df_stock_filtered_OSAA["MRP"]>=lPriceRange) & (df_stock_filtered_OSAA["MRP"]<=uPriceRange)]    #filtering by price range
    df_stock_filtered_OSAA=df_stock_filtered_OSAA[~df_stock_filtered_OSAA["Style Code Color"].isin(df_stock_filtered["Style Code Color"])] # Filtering out the stylecode-color that are in selected store
    
    if radioNos=="NOS":
        df_stock_filtered_OSAA=df_stock_filtered_OSAA[df_stock_filtered_OSAA["NOS"]=="YES"] # filtering out the NOS column

    if occasionDropdown:
         df_stock_filtered_OSAA = df_stock_filtered_OSAA[df_stock_filtered_OSAA["Occasion"].isin(occasionDropdown)]
    
    df_stock_filtered_OSAA.drop_duplicates(subset="Style Code Color",inplace=True)  # dropping duplicate style code color colummn
    
    # calculation of the labels of conversion
    
    df_enquiry_label = df_enquiry[df_enquiry["Date"].isin(date_values)]
    df_enquiry_Kolkata = df_enquiry_label[df_enquiry_label["Point of Enquiry"]=="Kolkata Store"]
    df_enquiry_Delhi = df_enquiry_label[df_enquiry_label["Point of Enquiry"]=="Delhi Store"]

    # filtering the labels according to the category

    df_enquiry_Kolkata=df_enquiry_Kolkata[df_enquiry_Kolkata["Category"]==productCatDropdown]
    df_enquiry_Delhi=df_enquiry_Delhi[df_enquiry_Delhi["Category"]==productCatDropdown]

    # filtering out the upper and lower price limits
    df_enquiry_Kolkata = df_enquiry_Kolkata[(df_enquiry_Kolkata["Lower Price Limit"]>=lPriceRange) & (df_enquiry_Kolkata["Upper Price Limit"]<=uPriceRange)]
    df_enquiry_Delhi = df_enquiry_Delhi[(df_enquiry_Delhi["Lower Price Limit"]>=lPriceRange) & (df_enquiry_Delhi["Upper Price Limit"]>=uPriceRange)]
    
    # for Kolkata
    
    kolkata_enquiry = df_enquiry_Kolkata.shape[0]    
    kolkata_enquiry_tried = df_enquiry_Kolkata[df_enquiry_Kolkata["Tried / Not Tried"]=="Tried"].shape[0]
    kolkata_enquiry_bought = df_enquiry_Kolkata[df_enquiry_Kolkata["Bought /Did not buy"]=="Bought"].shape[0]

    if kolkata_enquiry_tried>0:
        conversion_kolkata = int((kolkata_enquiry_bought/kolkata_enquiry_tried)*100)
    else:
        conversion_kolkata = "0"
    #kolkata_label = f"KOLKATA Enquiries Overall: {kolkata_enquiry}, Tried: {int((kolkata_enquiry_tried/kolkata_enquiry)*100)}%, Bought: {int((kolkata_enquiry_bought/kolkata_enquiry)*100)}%"
    kolkata_label = f"Kolkata enquiries for {productCatDropdown}: {kolkata_enquiry}, Tried: {kolkata_enquiry_tried}, Bought: {kolkata_enquiry_bought}, Conversion: {conversion_kolkata}%"
    

    # for Delhi
    
    delhi_enquiry = df_enquiry_Delhi.shape[0]    
    delhi_enquiry_tried = df_enquiry_Delhi[df_enquiry_Delhi["Tried / Not Tried"]=="Tried"].shape[0]
    delhi_enquiry_bought = df_enquiry_Delhi[df_enquiry_Delhi["Bought /Did not buy"]=="Bought"].shape[0]

    if delhi_enquiry_tried>0:
        conversion_delhi = int((delhi_enquiry_bought/delhi_enquiry_tried)*100)
    else:
        conversion_delhi="0"
    #delhi_label = f"DELHI Enquiries Overall: {delhi_enquiry}, Tried percent: {int((delhi_enquiry_tried/delhi_enquiry)*100)}%, Bought percent: {int((delhi_enquiry_bought/delhi_enquiry)*100)}%"
    delhi_label = f"Delhi enquiries for {productCatDropdown}: {delhi_enquiry}, Tried: {delhi_enquiry_tried}, Bought: {delhi_enquiry_bought}, Conversion: {conversion_delhi}%"
    

    
    # print(uPriceRange,lPriceRange,productCatDropdown,occasionDropdown,radioNos)
    
    return fig,df_product_master_filtered[["Style Code","Product Name","Color","Price","NOS"]].to_dict('records'),df_stock_filtered[["Style Code","Category","MRP","Color","Location Name","NOS"]].to_dict("records"),df_stock_filtered_OSAA[["Style Code","Category","MRP","Color","Location Name","NOS"]].to_dict("records"),df_product_master_filtered.shape[0],df_stock_filtered.shape[0],df_stock_filtered_OSAA.shape[0],availability_store_string,availability_Osaa_string,count_rows_string, delhi_label,kolkata_label   


# _______________________________Callback for the Outfit Tried Table ______________________________________________

@callback(
    Output("outfit-tried-table","data"),
    Output("outfit-tried-table-count","children"),
    #Input("date-dropdown","value"),
    Input("date-picker-range","start_date"),
    Input("date-picker-range","end_date"),
    Input("upper-price-range","value"),
    Input("lower-price-range","value"),
    Input("product-category-dropdown","value"),
    Input("store-selector","value"),
)

def update_triedtable(start_date,end_date,uPriceLimit,lPriceLimit,productCategory,storeSelection):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    date_values=[]
    while start_date<=end_date:
        date_values.append(start_date.strftime("%Y-%m-%d"))
        start_date += timedelta(days=1)

    df_tried=df_enquiry[(df_enquiry["Date"].isin(date_values)) & (df_enquiry["Tried / Not Tried"]=="Tried")]
    
    #replacing the no data in the price columns with 0
    #df_tried["Lower Price Limit"]=df_tried["Lower Price Limit"].replace("No Data",0,inplace=True)
    #df_tried["Upper Price Limit"]=df_tried["Lower Price Limit"].replace("No Data",0,inplace=True)
    
    # cleaning the dataframe of categories and replacing the values
    
    #'', '', '', '', '', '','SUIT', 'JACKET', 'SAREE', 'LEHANGA', 'GOWN', 'SEPARATE', 'WEAR'
    #   '', '', '', ''
    df_tried["Category"].replace("Miscellaneous","MISCELLANEOUS",inplace=True)
    df_tried["Category"].replace("Lehenga","LEHANGA",inplace=True)
    df_tried["Category"].replace("Saree","SAREE",inplace=True)
    df_tried["Category"].replace("Jacket","JACKET",inplace=True)
    df_tried["Category"].replace("Suit","SUIT",inplace=True)
    df_tried["Category"].replace("Top Skirt","TOP SKIRT",inplace=True)
    df_tried["Category"].replace("Gown","GOWN",inplace=True)
    df_tried["Category"].replace("No Data","No Data",inplace=True)
    df_tried["Category"].replace("SUIT","SUIT",inplace=True)
    df_tried["Category"].replace("","No Data",inplace=True)
       
    # print(df_tried.columns)
    # filtering out the price limits
    
    #removing the no data row from the price column
    df_tried=df_tried[~df_tried["Price Bracket"].isin(["No Data"])]
    
       
    
    #converting the price limit columns to int
    df_tried["Lower Price Limit"]=df_tried["Lower Price Limit"].astype(int)
    df_tried["Upper Price Limit"]=df_tried["Upper Price Limit"].astype(int)
    df_tried=df_tried[(df_tried["Lower Price Limit"]>=lPriceLimit) & (df_tried["Upper Price Limit"]<=uPriceLimit)]
    
    #filtering out the category
    df_tried=df_tried[df_tried["Category"]==productCategory]

    # Filtering out the selected store
    df_tried=df_tried[df_tried["Point of Enquiry"].isin(storeSelection)]

    # creating the columns for number of trials and number of boughts
    
    
    df_tried2 = df_tried[["Outfit Tried","Color","Price Bracket","Category","Lower Price Limit","Upper Price Limit","Point of Enquiry"]]
    tried_number = df_tried2.shape[0]    
    
    
    
    return df_tried2.to_dict("records"), tried_number

# ______________________________ Callback for Outfit Bought Table ______________________________

@callback(
    Output("outfit-bought-table","data"),
    Output("outfit-bought-table-count","children"),
    #Input("date-dropdown","value"),
    Input("date-picker-range","start_date"),
    Input("date-picker-range","end_date"),
    Input("upper-price-range","value"),
    Input("lower-price-range","value"),
    Input("product-category-dropdown","value"),
    Input("store-selector","value"),
)

def update_boughttable(start_date,end_date,uPriceLimit,lPriceLimit,productCategory,storeSelection):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    date_values=[]
    while start_date<=end_date:
        date_values.append(start_date.strftime("%Y-%m-%d"))
        start_date += timedelta(days=1)

    # cleaning out the spelling of Lehenga according to the product master column
    df_dsr_total["Silhouette"].replace("LEHENGA","LEHANGA",inplace=True)

    # filtering out the dates for df_bought
    df_bought=df_dsr_total[df_dsr_total["Date2"].isin(date_values)]

    # filtering out the store of df_bought
    for i in range(len(storeSelection)):
        if storeSelection[i]=="Delhi Store":
            storeSelection[i]="Delhi"
        if storeSelection[i]=="Kolkata Store":
            storeSelection[i]="Kolkata"


    df_bought=df_bought[df_bought["Location"].isin(storeSelection)]
    

    # filtering out the price bracket of df_bought

    df_bought=df_bought[(df_bought["MRP"]<=uPriceLimit) & (df_bought["MRP"]>=lPriceLimit)]

    # Filtering out the price bracker for df_bought

    df_bought=df_bought[df_bought["Silhouette"]==productCategory]

    # Final filtering of the columns
    df_bought2=df_bought[["Code","Colour","Colour Type","Silhouette","MRP","Location"]]

    bought_number = df_bought2.shape[0]
       
    
    return df_bought2.to_dict("records"), bought_number

# ______________________________ Callback for Conversion Table ________________________________

@callback(
     Output("delhi-conversion-table","data"),
     Output("kolkata-conversion-table","data"),
     #Input("date-dropdown","value"),
     Input("date-picker-range","start_date"),
     Input("date-picker-range","end_date"),
     Input("upper-price-range","value"),
     Input("lower-price-range","value"),
     Input("product-category-dropdown","value"),   
    
)

def update_tried_location_tables(start_date,end_date,uPriceRange,lPriceRange,productCategory):
     start_date = pd.to_datetime(start_date)
     end_date = pd.to_datetime(end_date)

     date_values=[]
     while start_date<=end_date:
        date_values.append(start_date.strftime("%Y-%m-%d"))
        start_date += timedelta(days=1)
     
     # filter the data frame according to the dates entered
     df_enquiry_dateSelection = df_enquiry[df_enquiry["Date"].isin(date_values)]
    
     # Filtering the DSR dataframes according to the start and end date
     df_dsr_kolkata_filtered = df_dsr_kolkata[df_dsr_kolkata["Date2"].isin(date_values)]
     df_dsr_delhi_filtered = df_dsr_delhi[df_dsr_delhi["Date2"].isin(date_values)]
    
     # Creating the summary tables for the dress codes in Kolkata
    
     item_summary_kolkata = df_dsr_kolkata_filtered["Code"].value_counts()
     item_summary_kolkata=item_summary_kolkata.reset_index()
     item_summary_kolkata.rename(columns={"index":"Code","Code":"Count"},inplace=True)
     #item_summary_kolkata
    
     # Creating the summary table for dress code in Delhi
        
     item_summary_delhi = df_dsr_delhi_filtered["Code"].value_counts()
     item_summary_delhi=item_summary_delhi.reset_index()
     item_summary_delhi.rename(columns={"index":"Code","Code":"Count"},inplace=True)
     #item_summary_delhi 
        
     # making the dictionary of the item_summary for Kolkata and Delhi

     #item_summary_kolkata_dict = {item_summary_kolkata["Code"][i]:item_summary_kolkata["Count"][i] for i in range(len(item_summary_kolkata["Code"]))}
     #item_summary_delhi_dict = {item_summary_delhi["Code"][i]:item_summary_delhi["Count"][i] for i in range(len(item_summary_delhi["Code"]))}

     # Not working with dictionary
     # Creaating a bought string from the DSR tables

     item_summary_kolkata_string = "".join(i for i in df_dsr_kolkata_filtered["Code"])
     item_summary_delhi_string = "".join(i for i in df_dsr_delhi_filtered["Code"])
     
     # ______________________________________________Table For Delhi ____________________________________________________

     # DELHI STORE WORKOUT FOR THE FIRST DATATABLE

     df_enquiry_dateSelection_Delhi=df_enquiry_dateSelection[df_enquiry_dateSelection["Point of Enquiry"]=="Delhi Store"]

     # query string of outfit tried and outfit bought after doing the two filterations of date and store selection

     tried_string_Delhi = "".join(i for i in df_enquiry_dateSelection_Delhi["Outfit Tried"])
     tried_string_Delhi = tried_string_Delhi.upper()

     bought_string_Delhi = "".join(i for i in df_enquiry_dateSelection_Delhi["Outfit Bought"])
     bought_string_Delhi = bought_string_Delhi.upper()

     # the style code column will have the style codes of the items that are coming from the filteration of the price and category filters
     # this will be basically from the stock data

     df_stock_filtered_Delhi = df_stock[df_stock["Category"]==productCategory]
     df_stock_filtered_Delhi = df_stock_filtered_Delhi[(df_stock_filtered_Delhi["MRP"]>=lPriceRange) & (df_stock_filtered_Delhi["MRP"]<=uPriceRange)]
     df_stock_filtered_Delhi = df_stock_filtered_Delhi[["Category","MRP","Style Code","NOS"]]

     # creating the calculated column that will count the number of items that have been tried

     df_stock_filtered_Delhi["Times Tried"]=0
     df_stock_filtered_Delhi["Times Bought"]=0

     for index,row in df_stock_filtered_Delhi.iterrows():
        df_stock_filtered_Delhi.loc[index,"Times Tried"] = tried_string_Delhi.count(row["Style Code"])
        df_stock_filtered_Delhi.loc[index,"Times Bought"] = item_summary_delhi_string.count(row["Style Code"])

        # if there is one item bought then the tried cannot be zero so it is made to have a value of 1
        if (df_stock_filtered_Delhi.loc[index,"Times Tried"]==0) & (df_stock_filtered_Delhi.loc[index,"Times Bought"]>0):
            df_stock_filtered_Delhi.loc[index,"Times Tried"]=1

     # Creating a columnn for conversion rate of the outfit that has been tried
     df_stock_filtered_Delhi["Conversion %"]=0

     for index,row in df_stock_filtered_Delhi.iterrows():
        if row["Times Tried"]!=0:
            df_stock_filtered_Delhi.loc[index,"Conversion %"] = int((row["Times Bought"]/row["Times Tried"])*100)

     df_stock_filtered_Delhi=df_stock_filtered_Delhi[~df_stock_filtered_Delhi["Times Tried"].isin([0])]
     df_stock_filtered_Delhi.drop_duplicates(subset="Style Code",inplace=True)

     # ____________________________________________________________ Table For Kolkata ______________________________________________

             # KOLKATA STORE WORKOUT FOR THE FIRST DATATABLE

     df_enquiry_dateSelection_Kolkata=df_enquiry_dateSelection[df_enquiry_dateSelection["Point of Enquiry"]=="Kolkata Store"]

     # query string of outfit tried and outfit bought after doing the two filterations of date and store selection

     tried_string_Kolkata = "".join(i for i in df_enquiry_dateSelection_Kolkata["Outfit Tried"])
     tried_string_Kolkata = tried_string_Kolkata.upper()

     bought_string_Kolkata = "".join(i for i in df_enquiry_dateSelection_Kolkata["Outfit Bought"])
     bought_string_Kolkata = bought_string_Kolkata.upper()

     # the style code column will have the style codes of the items that are coming from the filteration of the price and category filters
     # this will be basically from the stock data

     df_stock_filtered_Kolkata = df_stock[df_stock["Category"]==productCategory]
     df_stock_filtered_Kolkata = df_stock_filtered_Kolkata[(df_stock_filtered_Kolkata["MRP"]>=lPriceRange) & (df_stock_filtered_Kolkata["MRP"]<=uPriceRange)]
     df_stock_filtered_Kolkata = df_stock_filtered_Kolkata[["Category","MRP","Style Code","NOS"]]

     # creating the calculated column that will count the number of items that have been tried

     df_stock_filtered_Kolkata["Times Tried"]=0
     df_stock_filtered_Kolkata["Times Bought"]=0

     for index,row in df_stock_filtered_Kolkata.iterrows():
        df_stock_filtered_Kolkata.loc[index,"Times Tried"] = tried_string_Kolkata.count(row["Style Code"])
        df_stock_filtered_Kolkata.loc[index,"Times Bought"] = item_summary_kolkata_string.count(row["Style Code"])

        # If there is one item bought then the tried cannot be zero so it is made to one
        if (df_stock_filtered_Kolkata.loc[index,"Times Tried"]==0) & (df_stock_filtered_Kolkata.loc[index,"Times Bought"]>0):
            df_stock_filtered_Kolkata.loc[index,"Times Tried"]=1

     # Creating a columnn for conversion rate of the outfit that has been tried
     df_stock_filtered_Kolkata["Conversion %"]=0

     for index,row in df_stock_filtered_Kolkata.iterrows():
        if row["Times Tried"]!=0:
            df_stock_filtered_Kolkata.loc[index,"Conversion %"] = int((row["Times Bought"]/row["Times Tried"])*100)

     df_stock_filtered_Kolkata=df_stock_filtered_Kolkata[~df_stock_filtered_Kolkata["Times Tried"].isin([0])]
     df_stock_filtered_Kolkata.drop_duplicates(subset="Style Code",inplace=True)

     return df_stock_filtered_Delhi.to_dict("records"),df_stock_filtered_Kolkata.to_dict("records")

                                                             
# __________________________________________server run ___________________________________________________________________    

if __name__=="__main__":
    app.run(debug=True,port=8023)