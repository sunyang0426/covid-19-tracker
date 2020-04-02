import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
import plotly.graph_objects as go
import plotly.express as px
from dash.dependencies import Input, Output

import pandas as pd

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
external_stylesheets = ['https://codepen.io/amyoshino/pen/jzXypZ.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server 

app.title = 'COVID-19 Dashboard'

# ----------------- Styling ------------------------------------------------

colors = {
    'background': '#222222',
    'text': '#DCDCDC',
    'grid': "#434343",
    'line': '#72bcd4',
    'bar': '#FFB266',
}

stats_charts_style = dict(
	plot_bgcolor =  colors['background'],
	paper_bgcolor = colors['background'],
	font = {'color': colors['text']},
	margin = {'l':90, 'b':40, 't':10, 'r':40}

)

tabs_styles = {'height': '44px', 'padding-left': 20, 'padding-right': 120}

tab_style = {
	'borderBottom': '1px solid #d6d6d6',
	'padding': '6px',
	'fontWeight': 'bold',
	'backgroundColor': '#222222',
	'color': '#DCDCDC'
}

tab_selected_style = {
	'borderTop': '1px solid #d6d6d6',
	'borderBottom': '1px solid #d6d6d6',
	'backgroundColor': '#4682B4',
	'color': 'white',
	'padding': '6px'
}

indicator_style = {
	'backgroundColor': colors['line'],
	'display':'inline-block',
	'height': 130,
	'width': 180,
	'textAlign': 'center',
	'margin-right': 30,
	'color': colors['text'],
	'fontWeight': 'bold',

}




# ----------------- Part One Data Preparation -----------------------------------------------

# import the data 
SPREADSHEET_ID = '1D6okqtBS3S2NRC7GFVHzaZ67DuTw7LX49-fqSLwJyeo'
RANGE_NAME = 'Cases'
url = 'https://docs.google.com/spreadsheets/d/{0}/gviz/tq?tqx=out:csv&sheet={1}'.format(SPREADSHEET_ID, RANGE_NAME)
df = pd.read_csv(url)
# Change datatype of some columns
df.provincial_case_id = df.provincial_case_id.astype('object')
df.travel_yn = df.travel_yn.astype('bool')
# Define the date and time format and conver the 'date_report' column to datetime type
df['date_report'] = pd.to_datetime(df['date_report']).dt.strftime('%d/%m/%Y')
df['date_report'] = pd.to_datetime(df['date_report'])
# data for all canada's cumulative case
dff = df.copy()
dff = dff.set_index('date_report')

# draw the map
province_case = pd.DataFrame(df.province.value_counts()).reset_index().\
rename(columns={'index':'province', 'province':'cases'})

geo = {'Quebec': [53, -70],
      'Ontario': [50, -85],
      'BC': [53.72669, -127.647621],
      'Alberta': [55, -115],
      'Nova Scotia': [45, -63], 
      'NL': [53, -60],
      'Saskatchewan': [55, -106],
      'New Brunswick': [46.498390, -66.159668],
      'PEI': [46.25, -63],
      'Yukon': [64, -135],
      'NWT': [64.2667, -119.1833], 
      'Manitoba': [53.76086, -98.813873]}

geo_df = pd.DataFrame(geo).transpose().reset_index().\
rename(columns = {'index':'province', 0:'lat', 1: 'lon'})

province_case = pd.merge(province_case, geo_df)

token = 'pk.eyJ1Ijoic3VueWFuZzA0MjYiLCJhIjoiY2s4MHV0MWNkMDRpcTNmcHFmOWhwaWoxZiJ9.hIMx3CyEx3erYGxBjnLX9Q'

fig = px.scatter_mapbox(province_case, 
                        lon = 'lon', lat = 'lat', 
                        hover_name = 'province',
                        size = 'cases', size_max = 45,
                        color_discrete_sequence = ['#72bcd4'], 
                        width = 500, height = 500,
                        )

fig.update_layout(mapbox = {'accesstoken': token, 
                           'center': {'lon': -100.3467712, 'lat':60.1303673},
                            'zoom': 1.85},
                 mapbox_style ='dark', paper_bgcolor = colors['background'],
                 margin = {'l': 10, 'r': 10, 't':10, 'b':10})

## data for the canada line chart
canada = pd.DataFrame(dff.index.value_counts()).reset_index()
canada = canada.set_index('index')
canada = canada.resample('d').sum().fillna(0)
canada['cumu'] = canada['date_report'].cumsum()

# generate the canada chart

# import dataframes for other stats
RANGE_NAME_1 = 'Mortality'
RANGE_NAME_2 = 'Recovered'
RANGE_NAME_3 = 'Testing'

url_1 = 'https://docs.google.com/spreadsheets/d/{0}/gviz/tq?tqx=out:csv&sheet={1}'.format(SPREADSHEET_ID, RANGE_NAME_1)
url_2 = 'https://docs.google.com/spreadsheets/d/{0}/gviz/tq?tqx=out:csv&sheet={1}'.format(SPREADSHEET_ID, RANGE_NAME_2)
url_3 = 'https://docs.google.com/spreadsheets/d/{0}/gviz/tq?tqx=out:csv&sheet={1}'.format(SPREADSHEET_ID, RANGE_NAME_3)

mortality = pd.read_csv(url_1)
recovered = pd.read_csv(url_2)
testing = pd.read_csv(url_3)

def rename_first_column(dataframe):
    dataframe = dataframe.rename(columns={dataframe.columns[0]: 'id'})
    return dataframe

testing = rename_first_column(testing)
mortailty = rename_first_column(mortality)
recovered = rename_first_column(recovered)

# ------------------------ Prepare data for the Sankey diagram --------------
sankey_df = pd.read_csv('sankey_df.csv')

# A function to generate Sankey diagram. 
# Credit to https://medium.com/kenlok/how-to-create-sankey-diagrams-from-dataframes-in-python-e221c1b4d6b0
def genSankey(df,cat_cols=[],value_cols=''):
    labelList = []
    for catCol in cat_cols:
        labelListTemp =  list(set(df[catCol].values))
        labelList = labelList + labelListTemp
    # transform df into a source-target pair
    for i in range(len(cat_cols)-1):
        if i==0:
            sourceTargetDf = df[[cat_cols[i],cat_cols[i+1],value_cols]]
            sourceTargetDf.columns = ['source','target','count']
        else:
            tempDf = df[[cat_cols[i],cat_cols[i+1],value_cols]]
            tempDf.columns = ['source','target','count']
            sourceTargetDf = pd.concat([sourceTargetDf,tempDf])
        sourceTargetDf = sourceTargetDf.groupby(['source','target']).agg({'count':'sum'}).reset_index()       
    # add index for source-target pair
    sourceTargetDf['sourceID'] = sourceTargetDf['source'].apply(lambda x: labelList.index(x))
    sourceTargetDf['targetID'] = sourceTargetDf['target'].apply(lambda x: labelList.index(x))    
    # creating the sankey diagram
    data = dict(
        type='sankey',
        valueformat = '.f',
        node = dict(
          pad = 10,
          thickness = 30,
          line = dict(
            color = "black",
            width = 0.5
          ),
          label = labelList,
          color = colors['line']
        ),
        link = dict(
          source = sourceTargetDf['sourceID'],
          target = sourceTargetDf['targetID'],
          value = sourceTargetDf['count'],

        )
      )
    
    layout =  dict(
        font = dict(
          size = 10
        ),     
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        height = 450, 
        margin = {'l':50, 'b':40, 't':30, 'r':50}
    )
       
    fig = go.Figure(data = [go.Sankey(data)], layout = layout)
    return fig






# --------------- Part Two. App layout ---------------------

app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[
	# Headline
    html.H1(
        children='Tracking COVID-19 in Canada',
        style={
            'textAlign': 'center',
            'color': colors['text'],
            'padding-top': 30,
        }
    ),
 #    # Dashboard Intro
    html.Div(children=[
    	html.P("This dashboard tracks the number and distribution of COVID-19 cases in Canada in real-time. \
    		Data used for this project is a publicly available dataset collected by ", 
    		style = {'display': 'inline'}),
    	html.A('COVID-19 Canada Open Data Working Group', href = 'https://github.com/ishaberry/Covid19Canada', 
    		target = '_blank',
    		style = {'display': 'inline'}),
    	html.P(". This dashboard allows a user to filter cumulative cases and daily \
    		increase in a province or territory.", style = {'display': 'inline'}),
    	html.P(df.columns[0].split('Please')[0]),

    	], 

    	style={ 'textAlign': 'left',
			        'color': colors['text'],
			        'padding-left': 70,
			        'padding-right': 70}
	    ),

    # indicators
    html.Div([
    	html.Div([html.H3(df.shape[0]), 
    			  html.H5('Confirmed')], 
    			  style = indicator_style, 
    			  className = 'three columns'),
    	html.Div([html.H3(mortailty.shape[0]),
    			  html.H5('Deaths')], 
    			  style = indicator_style, 
    			  className = 'three columns'),
    	html.Div([html.H3(recovered.groupby('province').cumulative_recovered.max().sum()),
    			  html.H5('Recovered')], 
    			  style = indicator_style, 
    			  className = 'three columns'),
    	html.Div([html.H3(testing.groupby('province').cumulative_testing.max().sum()),
    			  html.H5('Testing')], 
    			  style = indicator_style, 
    			  className = 'three columns'),

    	], className = 'row', style = {'margin-top': 30, 'padding-left': 150}),


    # Overview of the country (map and line chart)
    html.Div([

    	# line chart
    	html.Div([
    		# selector
    		html.Div([
	    		dcc.RadioItems(
	    			id = 'scale-type',
	    			options = [{'label': i, 'value': i} for i in ['Linear', 'Log']],
	    			value = 'Log',
	    			labelStyle = {'display': 'inline-block'},
	    			style = {'background': colors['background'], 
	    					'color': colors['text'], 
	    					'padding-top': 40,
	    					'padding-left': 70,}
	    			)
    		  ]),
    		# the chart
    		html.Div([
	    		dcc.Graph(
	    			id = 'canada-line',
	    			)
    		  ])
    		], className = 'six columns'),

    	# map
    	html.Div([
    		html.Div([
	    		dcc.Graph(
	    			id = 'canada-map',
	    			figure = fig,
	    			)]),
    		], className = 'six columns')
	    ], className = 'row', style = {'padding-top': 50}), # end of country overview



 #    # curve by province
    html.Div([
 #    	# selectors + line chart
    	html.Div([
    		# selector Dropdown
    		html.Div([
    			html.P(children = 'Choose a province from the dropdown menu', 
    				style = {'backgroundColor': colors['background'],
    						'color': colors['text']}),

    			dcc.Dropdown(
    				id = 'province-select',
    				options = [ 
    						
    							{'label': i, 'value': i} for i in df['province'].unique()

    							],
    				value = 'Ontario',
    				),
    			], style = { 'padding-left': 70, 'padding-right': 100}),
    		# selector RadioItems
    		html.Div([
    			html.P(children = 'Choose a calculation type',
    				style = {'backgroundColor': colors['background'],
    						'color': colors['text'],
    						'marging-left': '15'}),

    			dcc.RadioItems(
    				id = 'calculation-type',
    				options = [{'label':i, 'value':i} for i in ['Cumulative Cases', 'New Cases']],
    				value = 'Cumulative Cases',
    				labelStyle = {'display': 'inline-block'},
    				style = {'background': colors['background'], 'color': colors['text']}
    				)
    			], style = { 'padding-left': 70, 'padding-top': 30}),
    		# line chart
    		html.Div([
    			html.Div([
    				dcc.Graph(id = 'line-by-province'),
    				],),

    		], style = {'backgroundColor': colors['background']}), 

    	], className = 'seven columns'), # end of selectors + line charts

 #    		# table
		html.Div([
			html.P('Distribution of cases in regions of a province/ territory',
				style = {'color': colors['text'], 'padding-bottom': 20}),
			html.Div(id = 'datatable'),
			], className = 'five columns', style={'margin-top': 100}),


    ], className = 'row', style = {'margin-top': 70}), # end of province div



    # other stats
    html.Div([
    	# the tab selector
    	dcc.Tabs(
    		id = 'stats-tab',
    		value = 'mortality-tab',
    		children = [
    					dcc.Tab(label = 'Mortality', value = 'mortality-tab', 
    						style = tab_style, selected_style = tab_selected_style),
    					dcc.Tab(label = 'Recovered', value = 'recover-tab',
    						style = tab_style, selected_style = tab_selected_style),
    					dcc.Tab(label = 'Testing', value = 'testing-tab',
    						style = tab_style, selected_style = tab_selected_style)
    					],
    		style = tabs_styles,),

    	dcc.Graph(id = 'other-stats'),
    	], style = {'margin-top': 70}),

    # sankey diagram
    html.Div([
        html.Div(children = ['At this moment, more than half of COVID-19 cases in Canada related to community transmission. \
            But at the early stage of the outbreak, the majority were due to traveling. \
            The lack of a universal reporting format among provinces and territories makes it hard to have \
            a clear picture of how human migration across borders initiated the spread within Canada. \
            Less than 10 percent of cases reported by governments indicating whether there was a travel history \
            and even a smaller fraction of reported cases indicating where this patient had traveled to. \
            The data is not perfect. However, the graphic below can still try to visualize where the early \
            waves of cases came from.'],
                    style={ 'textAlign': 'left',
                                'color': colors['text'],
                                'padding-left': 70,
                                'padding-right': 70,
                                'padding-top': 70}
            ),

    	dcc.Graph(
    		id = 'sankey',
    		figure = genSankey(sankey_df, cat_cols = ['from', 'to'], value_cols = 'count'),
    		)
    	]),

    # credits
    html.Div([
    	html.P('Developed by Yang Sun'),
    	html.A('DataLabTo', href = 'http://www.datalabto.ca/about/', target = '_blank',),
    	html.Br(),
    	html.A('Contact', href = 'mailto:sun.yang.ys57f@gmail.com'),
    	], className = "twelve columns", 
    	   style = {'fontSize': 15, 'padding-bottom': 30, 'padding-top': 30,
    	   			'textAlign': 'center', 
    	   			'backgroundColor': colors['background'],
    	   			'color': colors['text'],}),

]) # end of global div


# ------------ Part Three. Callbacks --------------------
@app.callback(
	Output('canada-line', 'figure'),
	[Input('scale-type', 'value')]
	)
def canada_line_update(yaxis_type):

	return{

		'data': [dict(x = canada.index, 
				y = canada.cumu, 
				type = 'line', 
				name = 'Cumulative cases',
				marker = {'color': colors['line']}),
				dict(x = canada.index, 
					y = canada.date_report, 
					type = 'bar', 
					name = 'New confirmed',
					marker = {'color': colors['bar']})],
		'layout': dict(
			plot_bgcolor = colors['background'],
			paper_bgcolor = colors['background'],
			font = dict(color = colors['text']),
			xaxis = {'gridcolor': colors['grid'], 'gridwidth': 0.05},
			yaxis = {'gridcolor': colors['grid'], 'gridwidth': 0.05,
					'title': 'No. of cases',
					'type': 'linear' if yaxis_type == 'Linear' else 'log'},
	 	    legend={ 'x':0, 'y':1},
	 	    margin = {'l':90, 'b':40, 't':10, 'r':40}
			)

		}



@app.callback(
	Output('line-by-province', 'figure'),
	[Input('province-select', 'value'),
	Input('calculation-type', 'value')]
	)
def update_line_chart(province, calculation_type):
	df_province = pd.DataFrame(dff[dff.province == province].index.value_counts()).reset_index()
	df_province = df_province.set_index('index')
	df_province = df_province.resample('d').sum().fillna(0)
	df_province['cumu'] = df_province['date_report'].cumsum()

	if calculation_type == 'New Cases':
		return {

			'data':[dict(
				x = df_province.index,
				y = df_province.date_report,
				type = 'bar',
				marker = {'color': colors['bar']}
				)
			],
			'layout': dict(
				yaxis = {'title': 'No. of new cases'},
				plot_bgcolor =  colors['background'],
				paper_bgcolor = colors['background'],
				font = {'color': colors['text']},
				margin = {'l':90, 'b':40, 't':10, 'r':40}

				)
		}
	else: 
		return {

			'data':[dict(
				x = df_province.index,
				y = df_province.cumu,
				tpye = 'line',
				marker = {'color': colors['line']}
				)
			],
			'layout': dict(
				yaxis = {'title': 'No. of cumulative cases'},
				plot_bgcolor =  colors['background'],
				paper_bgcolor = colors['background'],
				font = {'color': colors['text']},
				margin = {'l':90, 'b':40, 't':10, 'r':40}
				)
		}



@app.callback(
	Output('datatable', 'children'),
	[Input('province-select', 'value')]
	)
def update_datatable(province):
	province_counts = pd.DataFrame(df[df['province'] == province]['health_region'].value_counts()).reset_index().\
					  rename(columns = {'index': 'REGION', 'health_region': 'CONFIRMED CASES'})
	columns = [{'name': i, 'id': i} for i in province_counts.columns]
	data = province_counts.to_dict('records')
	return dt.DataTable(data = data, 
					    columns = columns, 
					    page_size = 10,
					    style_cell = {'backgroundColor': colors['background'], 'color': colors['text']},
					    style_header = {
					    	'fontWeight': 'bold',
					    	'backgroundColor': tab_selected_style['backgroundColor'],
					    })



@app.callback(
	Output('other-stats', 'figure'),
	[Input('stats-tab', 'value')]
	)
def update_stats_graph(tab):
	if tab == 'mortality-tab':
		return {

			'data':[dict(
				x = mortality.province.value_counts().index,
				y = mortality.province.value_counts().values,
				type = 'bar',
				marker = {'color': colors['bar']},
				)
			],
			'layout': stats_charts_style
		}
	if tab == 'recover-tab':
		return {

			'data':[dict(
				x = recovered.groupby('province').cumulative_recovered.max().sort_values(ascending=False).index,
				y = recovered.groupby('province').cumulative_recovered.max().sort_values(ascending=False).values,
				type = 'bar',
				marker = {'color': colors['bar']},
				)
			],
			'layout': stats_charts_style
		}
	else:
		return {

			'data':[dict(
				x = testing.groupby('province').cumulative_testing.max().sort_values(ascending=False).index,
				y = testing.groupby('province').cumulative_testing.max().sort_values(ascending=False).values,
				type = 'bar',
				marker = {'color': colors['bar']},
				)
			],
			'layout': stats_charts_style
		}


if __name__ == '__main__':
    app.run_server(debug=True)

