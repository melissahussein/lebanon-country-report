import matplotlib as mpl
import matplotlib.pyplot as plt
import plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import networkx as nx
from networkx.readwrite import json_graph
import requests
import pickle
import json
import csv


api_url_base = 'https://stat.ripe.net/data/'

#GENERAL FUNCTIONS

#dico contains a dictionary having for key a country code and for value a list of associated AS numbers
# the following functions allows to find the origin country of a certain AS given its number
def get_country_asn(ASnum):
    d=pickle.load( open( "dico.pickle", "rb" ))
    for key,item in d.items():
        if ASnum in item:
            return key


#returns a dictionary with a lebanese AS number as key and its name as value
def leb_AS_name():
    d={}
    l=[]
    with open("ASlb.txt","r") as f:
        for asn in f:
            l=asn.split()
            c="".join(l[1:])
            d[l[0]]=c
    return d

#returns a list of lebanese autonomous systems
def leb_AS():
    d=leb_AS_name()
    l=[]
    for key in d:
        l.append(key[2:])
    return l

#returns a dictionary with a lebanese AS number as key and its sector of activity as value
def leb_AS_sector():
    d={}
    l=[]
    with open("AS_secteurs.txt","r") as f:
        for asn in f:
            l=asn.split()
            c="".join(l[1:])
            d[l[0]]=c
    return d

#returns the name of a lebanese AS knowing its number
def getASname(ASnum):
    d=leb_AS_name()
    return d["AS"+str(ASnum)]

#returns a dictionary having as key a lebanese AS number and as value a list of tuples  
#in the form (AS neighbor number,type:left if client,right if provider)
#also returns a dictionary having as key a lebanese AS number and as value a list of tuples
#in the form(number of IPv4 neighbors,number of IPv6 neighbors)
def get_country_neighbours(country_code, country_asns,time):
    dict_neighbours={}
    dict_counts={}
    for asn in country_asns:
        #print("studying: ", asn)
        api_url = '{}asn-neighbours/data.json?resource={}&starttime={}'.format(api_url_base, asn,time)
        asn_neighbours_json1 = requests.get(api_url)
        if (asn_neighbours_json1.status_code == 200):
            asn_neighbours_json = json.loads(asn_neighbours_json1.content.decode('utf-8'))
            l1=[]
            l2=[]
            for neighbour in asn_neighbours_json['data']['neighbours']:
                neighbour_asn = str(neighbour['asn'])
                neighbour_type=str(neighbour['type'])
                l1.append((neighbour_asn,neighbour_type))
                dict_neighbours[asn]=l1
            neighbour_counts=asn_neighbours_json['data']['neighbour_counts']   
            neighbour_counts_left=neighbour_counts['left']
            neighbour_counts_right=neighbour_counts['right']
            l2.append((neighbour_counts_left,neighbour_counts_right))
            dict_counts[asn]=l2
    print("saving neighbours with connections...")
    pickle_out=open("neighbours_"+time[:4]+".pickle","wb")
    pickle.dump(dict_neighbours, pickle_out)
    pickle_out2=open("neighbours_count_"+time[:4]+".pickle","wb")
    print("saving neighbours with their numbers...")
    pickle.dump(dict_counts, pickle_out2)
    pickle_out2.close()
    print("done for year "+time[:4])
#get_country_neighbours("LB", leb_AS(),"2015-03-01T00:00:00")


#This function counts the number of IP addresses held by each AS
def countIPS(asn,year):
    l=[]
    time=str(year)+"-03-01T00:00:00"
    api_url = '{}routing-status/data.json?resource={}&starttime={}'.format(api_url_base, asn,time)
    asn_neighbours_json1 = requests.get(api_url)
    if (asn_neighbours_json1.status_code == 200):
        asn_neighbours_json = json.loads(asn_neighbours_json1.content.decode('utf-8'))
        number_ipv4=asn_neighbours_json['data']['announced_space']['v4']['ips']
        number_ipv6=asn_neighbours_json['data']['announced_space']['v6']['prefixes']
        l.append(number_ipv4)
        l.append(number_ipv6)
    return l

#This function saves the number of IP addresses announced by AS number
def ASNwithIP(year):
    d={}
    for asn in leb_AS():
        l=countIPS("AS"+str(asn),year)
        d[str(asn)]=l
    print("saving: amount of address space currently announced by AS number\n left:ipv4, right:ipv6")
    pickle_out=open("address_space_"+str(year)+".pickle","wb")
    pickle.dump(d, pickle_out)   

#ASNwithIP(2020)

#function used for the sake of labeling the interactive graph
def listToString(l):  
    str1 = "<br>"
    s1=""
    for e in l:
        name=get_country_asn(e)
        if name=="LB":
            name=name+" "+str(getASname(e))
        s1=s1+str(e)+"->"+str(name)+str1
    return (s1)


#PLOTTING FUNCTIONS

#Drawing the Lebanese AS graph with the option of choosing which year from 2015 to 2020 to visualize (using plotly)
def drawGraph(startyear,endyear):
    data=[]
    connections=[]
    while startyear<=endyear:
        d=pickle.load(open("neighbours_"+str(startyear)+".pickle", "rb" ))
        allneighbours=[]
        for l in d.values():
            if (l!=[]):
                for t in l:
                 allneighbours.append(t[0])
        nodes=allneighbours+list(d.keys())
        print("all nodes found: local and international ASes")
        G=nx.Graph()
        G.add_nodes_from(list(dict.fromkeys(nodes)))
        pos = nx.spring_layout(G)
        
        for asn in d:
            if (d[asn]!=[]):
                for neighb in d[asn]:
                    G.add_edge(asn,neighb[0])

        #print("NODES: ",G.nodes())
        #print("EDGES: ",G.edges())
        connections.append(len(G.edges()))
        
        edge_x = []
        edge_y = []
        for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.append(x0)
                edge_x.append(x1)
                edge_x.append(None)
                edge_y.append(y0)
                edge_y.append(y1)
                edge_y.append(None)
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            visible=False,
            line=dict(width=1.5, color='#888'),
            hoverinfo='none',
            mode='lines')

        node_xL = []
        node_yL = []
        node_xI = []
        node_yI = []
        for node in G.nodes():
            x, y = pos[node]
            if (node in leb_AS()):
                node_xL.append(x)
                node_yL.append(y)
            else:
                node_xI.append(x)
                node_yI.append(y)

        node_adjacencies_L = []
        node_adjacencies_I = []
        node_text_L=[]
        node_text_I=[]
        for noeud in G.nodes():
            P=[]
            C=[]
            c_L=0
            c_I=0
            if (noeud in leb_AS()):
                name='AS'+str(noeud)+": "+str(getASname(noeud))
                for n in d[noeud]:
                    c_L+=1
                    if (n[1]=="left"):
                        P.append(n[0])
                    else:
                        C.append(n[0])
                node_adjacencies_L.append(c_L)
                if noeud=="42020":
                    node_text_L.append(name+"<br>"+"<br>"+' # of connections: '+str(c_L)+"<br>"+"<br>"+"nb of clients: "+
                                   str(len(C))+"<br>"+"Providers: "+listToString(P))
                else:
                    node_text_L.append(name+"<br>"+"<br>"+' # of connections: '+str(c_L)+"<br>"+"<br>"+"Clients: "+
                                       listToString(C)+"<br>"+"Providers: "+listToString(P))
                    
            else:
                for v in d.values():
                    for t in v:
                        if noeud==t[0]:
                            c_I+=1
                node_adjacencies_I.append(c_I)
                name='AS'+str(noeud)+": "+str(get_country_asn(noeud))
                node_text_I.append(name+"<br>"+"<br>"+' # of connections: '+str(c_I))
                

        node_trace_L= go.Scatter(
                x=node_xL, y=node_yL,
                visible=False,
                mode='markers',
                hoverinfo='text',
                hovertext=node_text_L,
                marker=dict(
                    showscale=True,
                    colorscale='YlGnBu',
                    reversescale=True,
                    color=[],
                    size=15,
                    colorbar=dict(
                        thickness=15,
                        title='Node Connections Lebanese',
                        xanchor='left',
                        titleside='right'
                    ),
                    line_width=2))
        node_trace_L.marker.color = node_adjacencies_L
        node_trace_L.text=node_text_L
        
        node_trace_I= go.Scatter(
                x=node_xI, y=node_yI,
                visible=False,
                mode='markers',
                hoverinfo='text',
                hovertext=node_text_I,
                marker=dict(
                    showscale=True,
                    colorscale='Reds',
                    reversescale=True,
                    color=[],
                    size=20,
                    colorbar=dict(
                        thickness=20,
                        title='Node Connections International',
                        xanchor='right',
                        titleside='right'
                    ),
                    line_width=2))
        
        node_trace_I.marker.color = node_adjacencies_I
        node_trace_I.text=node_text_I
        data.append(edge_trace)
        data.append(node_trace_L)
        data.append(node_trace_I)
        startyear+=1


    updatemenus = list([
            dict(active=6,
                 buttons=list([

                    dict(label = '2015',
                         method = 'update',
                         args = [{'visible': [True, True,True,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False]},
                                 {'title': 'Year 2015'}]),

                    dict(label = '2016',
                         method = 'update',
                         args = [{'visible': [False,False,False,True, True,True,False,False,False,False,False,False,False,False,False,False,False,False]},
                                 {'title': 'Year 2016'}]),

                    dict(label = '2017',
                         method = 'update',
                         args = [{'visible': [False,False,False,False,False,False,True, True,True,False,False,False,False,False,False,False,False,False]},
                                 {'title': 'Year 2017'}]),

                    dict(label = '2018',
                         method = 'update',
                         args = [{'visible': [False,False,False,False,False,False,False,False,False,True, True,True,False,False,False,False,False,False]},
                                 {'title': 'Year 2018'}]),

                    dict(label = '2019',
                         method = 'update',
                         args = [{'visible': [False,False,False,False,False,False,False,False,False,False,False,False,True, True,True,False,False,False]},
                                 {'title': 'Year 2019'}]),

                    dict(label = '2020',
                         method = 'update',
                         args = [{'visible': [False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,True, True,True]},
                                 {'title': 'Year 2020'}])

                    
                ]),
            )
        ])
        
    layout=go.Layout(
                    title='Lebanese AS graph',
                    titlefont_size=25,
                    showlegend=False,
                    hovermode="closest",
                    clickmode="select",
                    margin=dict(b=20,l=5,r=5,t=60),
                    annotations=[ dict(
                       text="choose the year you would like to view the Lebanese AS connectivity for <br> hover your mouse over a node(or simply click on it) for more information",
                       showarrow=False,
                       xref="paper", yref="paper",
                       x=0.005, y=-0.002 ),
                      dict( text="Total number of connections in 2015: "+str(connections[0])+"<br>Total number of connections in 2016: "+str(connections[1])+
                            "<br>Total number of connections in 2017: "+str(connections[2])+"<br>Total number of connections in 2018: "+str(connections[3])+
                            "<br>Total number of connections in 2019: "+str(connections[4])+"<br>Total number of connections in 2020: "+str(connections[5]),
                       showarrow=False,
                       xref="paper", yref="paper",
                       x=-0.002, y=1,bordercolor="black"),

                    ],
                    
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    updatemenus=updatemenus,
                    )
                    
        

    fig = dict(data=data, layout=layout)

    
    plotly.offline.plot(fig, auto_open=True, show_link=False)

#2015 till 2020 evolution
#drawGraph(2015,2020)

#The following function adds to the diffferent AS sectors txt files (saved by year) the international ASes
def file(year):
    d=pickle.load(open("neighbours_"+str(year)+".pickle", "rb" ))
    allneighbours=[]
    for l in d.values():
        if (l!=[]):
            for t in l:
                 allneighbours.append(t[0])
    print(len(allneighbours))
    nodes=allneighbours+list(d.keys())
    print("all nodes found: local and international ASes")
    for asn in nodes:
            if (asn not in leb_AS()):
                    with open('AS_secteurs_'+str(year)+'.txt','a') as f:
                          f.write("\n"+"AS"+asn+"\t"+"INTERNATIONAL")

#file(2015)
#file(2016)
#file(2017)
#file(2018)
#file(2019)
#file(2020)

#Drawing the Lebanese AS graph (force directed graph) for the years 2015 to 2020 , color coded by sectors of activity
G=nx.DiGraph()
categories={}
def drawGraphSectors(year):
    d=pickle.load(open("neighbours_"+str(year)+".pickle", "rb" ))
    allneighbours=[]
    for l in d.values():
        if (l!=[]):
            for t in l:
                 allneighbours.append(t[0])
    nodes=allneighbours+list(d.keys())
    print("all nodes found: local and international ASes")
    G.add_nodes_from(list(dict.fromkeys(nodes)))
    for asn in nodes:
            print(asn)
            G.node[asn]['cat']=categories["AS"+asn]
            AStype=G.node[asn]['cat']
            if (AStype=="ISP"):
                G.node[asn]['group']=1
                G.node[asn]['color']='blue'
            elif (AStype=="ICT"):
                G.node[asn]['group']=2
                G.node[asn]['color']='slateblue'
            elif (AStype=="DSP"):
                G.node[asn]['group']=3
                G.node[asn]['color']='darkgreen'
            elif (AStype=="BANK"):
                G.node[asn]['group']=4
                G.node[asn]['color']='green'
            elif (AStype=="UNIVERSITY"):
                G.node[asn]['group']=5
                G.node[asn]['color']='orange'
            elif (AStype=="GOVERNMENT"):
                G.node[asn]['group']=6
                G.node[asn]['color']='yellow'
            elif (AStype=="INTERNATIONAL"):
                G.node[asn]['group']=7
                G.node[asn]['color']='red'
            else:
                G.node[asn]['group']=8
                G.node[asn]['color']='purple'
    for asn in d:
        if (d[asn]!=[]):
            for neighb in d[asn]:
                G.add_edge(asn,neighb[0])
               
    nx.draw(G,with_labels=True)
    #plt.show()
    #plt.close()

#start the main function by opening the corresponding txt file and json file
#the available html files will use the json files to draw the forced directed graph with or without labels)
"""if __name__=="__main__":
    with open('AS_secteurs_2020.txt','r') as csvfile:
        secteur = csv.reader(csvfile, delimiter='\t')
        for row in secteur:
            categories[row[0]]=row[1]
    drawGraphSectors(2020) #change parameter according to the year wanted 
    data = json_graph.node_link_data(G)
    G.nodes(data=True)
    with open('Clustered_Graph_2020.json', 'w') as f:
        json.dump(data, f, indent=4)"""

#These two functions will be used to draw the Pie Diagrams          
def ASN_IPv4():
    labels=[]
    values=[]
    autre=0
    d=pickle.load(open("address_space_"+str(2020)+".pickle", "rb" ))
    for asn in d:
        if d[asn][0]>5000:
            labels.append("AS"+str(asn)+" "+getASname(asn))
            values.append(d[asn][0])
        else:
            autre+=d[asn][0]
    labels.append("Other")
    values.append(autre)
    return labels,values

     
def ASN_IPv6():
    labels=[]
    values=[]
    d=pickle.load(open("address_space_"+str(2020)+".pickle", "rb" ))
    for asn in d:
        if d[asn][1]!=0:
            labels.append("AS"+str(asn)+" "+getASname(asn))
            values.append(d[asn][1])
    labels.append("Other")
    values.append(0)
    return labels,values

#the following function is equivalent to drawGraph but plots only lebanese ASes with other 5000 IPv4 addresses
def drawMinGraph(startyear,endyear):

    data=[]
    connections=[]
    while startyear<=endyear:
        allneighbours=[]
        lbnodes=[]
        nodes=[]
        d=pickle.load(open("neighbours_"+str(startyear)+".pickle", "rb" ))
        d2=pickle.load(open("address_space_"+str(startyear)+".pickle", "rb" ))

        for asn in d2:
            if d2[asn][0]>5000:
                lbnodes.append(asn)
        for asn in d:
            if asn in lbnodes:
                if d[asn]!=[]:
                    for t in d[asn]:
                         allneighbours.append(t[0])        
        nodes=allneighbours+lbnodes
        print("all nodes found: local and international ASes")
        G=nx.Graph()
        G.add_nodes_from(list(dict.fromkeys(nodes)))
        pos = nx.spring_layout(G)
        
        for asn in d:
            if (d[asn]!=[] and d2[asn][0]>5000):
                for neighb in d[asn]:
                    G.add_edge(asn,neighb[0])

        #print("NODES: ",G.nodes())
        #print("EDGES: ",G.edges())
        connections.append(len(G.edges()))
        
        edge_x = []
        edge_y = []
        for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.append(x0)
                edge_x.append(x1)
                edge_x.append(None)
                edge_y.append(y0)
                edge_y.append(y1)
                edge_y.append(None)
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            visible=False,
            line=dict(width=1.5, color='#888'),
            hoverinfo='none',
            mode='lines')

        node_xL = []
        node_yL = []
        node_xI = []
        node_yI = []
        for node in G.nodes():
            x, y = pos[node]
            if (node in leb_AS()):
                node_xL.append(x)
                node_yL.append(y)
            else:
                node_xI.append(x)
                node_yI.append(y)

        node_adjacencies_L = []
        node_adjacencies_I = []
        node_text_L=[]
        node_text_I=[]
        for noeud in G.nodes():
            P=[]
            C=[]
            c_L=0
            c_I=0
            if (noeud in lbnodes):
                name='AS'+str(noeud)+": "+str(getASname(noeud))
                if noeud in d:
                    for n in d[noeud]:
                        c_L+=1
                        if (n[1]=="left"):
                            P.append(n[0])
                        else:
                            C.append(n[0])
                    node_adjacencies_L.append(c_L)
                    if noeud=="42020":
                        node_text_L.append(name+"<br>"+"<br>"+' # of connections: '+str(c_L)+"<br>"+"<br>"+"nb of clients: "+
                                       str(len(C))+"<br>"+"Providers: "+listToString(P))
                    else:
                        node_text_L.append(name+"<br>"+"<br>"+' # of connections: '+str(c_L)+"<br>"+"<br>"+"Clients: "+
                                           listToString(C)+"<br>"+"Providers: "+listToString(P))
                    
            elif (noeud not in leb_AS()):
                for v in d.values():
                    for t in v:
                        if noeud==t[0]:
                            c_I+=1
                node_adjacencies_I.append(c_I)
                name='AS'+str(noeud)+": "+str(get_country_asn(noeud))
                node_text_I.append(name+"<br>"+"<br>"+' # of connections: '+str(c_I))
                

        node_trace_L= go.Scatter(
                x=node_xL, y=node_yL,
                visible=False,
                mode='markers',
                hoverinfo='text',
                hovertext=node_text_L,
                marker=dict(
                    showscale=True,
                    colorscale='YlGnBu',
                    reversescale=True,
                    color=[],
                    size=15,
                    colorbar=dict(
                        thickness=15,
                        title='Node Connections Lebanese',
                        xanchor='left',
                        titleside='right'
                    ),
                    line_width=2))
        node_trace_L.marker.color = node_adjacencies_L
        node_trace_L.text=node_text_L
        
        node_trace_I= go.Scatter(
                x=node_xI, y=node_yI,
                visible=False,
                mode='markers',
                hoverinfo='text',
                hovertext=node_text_I,
                marker=dict(
                    showscale=True,
                    colorscale='Reds',
                    reversescale=True,
                    color=[],
                    size=20,
                    colorbar=dict(
                        thickness=20,
                        title='Node Connections International',
                        xanchor='right',
                        titleside='right'
                    ),
                    line_width=2))
        
        node_trace_I.marker.color = node_adjacencies_I
        node_trace_I.text=node_text_I
        data.append(edge_trace)
        data.append(node_trace_L)
        data.append(node_trace_I)
        startyear+=1


    updatemenus = list([
            dict(active=6,
                 buttons=list([

                    dict(label = '2015',
                         method = 'update',
                         args = [{'visible': [True, True,True,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False]},
                                 {'title': 'Year 2015'}]),

                    dict(label = '2016',
                         method = 'update',
                         args = [{'visible': [False,False,False,True, True,True,False,False,False,False,False,False,False,False,False,False,False,False]},
                                 {'title': 'Year 2016'}]),

                    dict(label = '2017',
                         method = 'update',
                         args = [{'visible': [False,False,False,False,False,False,True, True,True,False,False,False,False,False,False,False,False,False]},
                                 {'title': 'Year 2017'}]),

                    dict(label = '2018',
                         method = 'update',
                         args = [{'visible': [False,False,False,False,False,False,False,False,False,True, True,True,False,False,False,False,False,False]},
                                 {'title': 'Year 2018'}]),

                    dict(label = '2019',
                         method = 'update',
                         args = [{'visible': [False,False,False,False,False,False,False,False,False,False,False,False,True, True,True,False,False,False]},
                                 {'title': 'Year 2019'}]),

                    dict(label = '2020',
                         method = 'update',
                         args = [{'visible': [False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,True, True,True]},
                                 {'title': 'Year 2020'}])

                    
                ]),
            )
        ])
        
    layout=go.Layout(
                    title='Lebanese AS graph',
                    titlefont_size=25,
                    showlegend=False,
                    hovermode="closest",
                    clickmode="select",
                    margin=dict(b=20,l=5,r=5,t=60),
                    annotations=[ dict(
                       text="choose the year you would like to view the Lebanese AS connectivity for <br> hover your mouse over a node(or simply click on it) for more information",
                       showarrow=False,
                       xref="paper", yref="paper",
                       x=0.005, y=-0.002 ),
                      dict( text="Total number of connections in 2015: "+str(connections[0])+"<br>Total number of connections in 2016: "+str(connections[1])+
                            "<br>Total number of connections in 2017: "+str(connections[2])+"<br>Total number of connections in 2018: "+str(connections[3])+
                            "<br>Total number of connections in 2019: "+str(connections[4])+"<br>Total number of connections in 2020: "+str(connections[5]),
                       showarrow=False,
                       xref="paper", yref="paper",
                       x=-0.002, y=1,bordercolor="black"),

                    ],
                    
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    updatemenus=updatemenus,
                    )
                    

    fig = dict(data=data, layout=layout)

    
    plotly.offline.plot(fig, auto_open=True, show_link=False)

#2015 till 2020 evolution
#drawMinGraph(2015,2020)

#This function draws two pie diagrams highlighting the distribution of IPv4 addresses and IPv4 prefixes by lebanese ASes
def drawPie():

    labels4,values4=ASN_IPv4()
    labels6,values6=ASN_IPv6()
    # Create subplots: use 'domain' type for Pie subplot
    fig = make_subplots(rows=1, cols=2, specs=[[{'type':'domain'},{'type':'domain'}]])
    fig.add_trace(go.Pie(labels=labels4, values=values4, name="iPv4"),1, 1)
    fig.add_trace(go.Pie(labels=labels6 , values=values6, name="iPv6"),1, 2)


    fig.update_layout(
        title_text="Amount of address space announced by AS number<br><br><br><br>                            IPv4                                                                  IPv6")

    fig.write_html('ASN addressing IPv4_IPv6 2020.html', auto_open=True)

#drawPie()


#returns number of announced prefixes by AS to draw Sankey Diagram
def announcedPrefixes(asn):
    api_url = '{}announced-prefixes/data.json?resource={}'.format(api_url_base, asn)
    asn_pref_json1 = requests.get(api_url)
    if (asn_pref_json1.status_code == 200):
        asn_pref_json = json.loads(asn_pref_json1.content.decode('utf-8'))
        number_prefixes=len(asn_pref_json['data']['prefixes'])
        #return(asn,number_prefixes)
        return number_prefixes
    
def AllannouncedPrefixes():
    l=[]
    for asn in leb_AS():
        print("finding number of prefixes announced")
        l.append(announcedPrefixes(asn))
    pickle_out=open("announced_prefixes_by_asn.pickle","wb")
    pickle.dump(l, pickle_out)
    
#AllannouncedPrefixes()

#Plots the Sankey Diagram giving an external view of Lebanon
def drawSankeyDiagram():
    label1= ["US","Other Countries","RU","NG","AO","DE","GB","FR","IT","LU","NL","IQ","NO","CH"]
    label2=["US","Other Countries","RU","NG","AO","DE","GB","FR","IT","LU","NL","IQ","NO","CH"]
    l=[9051,39010,35074,24634,42334,34458,35197,59989,197674,42020,31037,50285,12812,43056,15511,
      48629,60398,51910,13044,59955,206406,210292,15739,56902,56333,51558,203913,34708,56530,
       57937,48335,207445]
    for asn in l:
        label2.append(asn)
        label1.append(getASname(asn))
        
    sources=[0,1,2,1,3,4,1,2,2,5,6,1,0,0,7,8,2,9,5,0,10,10,5,0,2,2,6,0,0,2,0,2,2,10,11,0,0,12,13,0]
    targets=[14,14,15,15,16,16,17,18,19,20,21,21,22,23,23,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,
                    37,38,39,40,41,42,43,44,45,45]
    values=[]
    
    for indice in targets:
        values.append(announcedPrefixes(label2[indice]))
    
    fig = go.Figure(data=[go.Sankey(
        node = dict(
          pad = 25,
          thickness = 20,
          line = dict(color = "black", width = 0.3),
          label = label1,
          color = "light blue"
        ),
        link = dict(
          source = sources,
          target = targets,
          value = values
      ))])

    fig.update_layout(
    title="External View Lebanon",
    font=dict(size = 13, color = 'black'),
    plot_bgcolor='black',
    paper_bgcolor='white')

    fig.write_html('Sankey Diagram.html', auto_open=True)
        
#drawSankeyDiagram()


#Draws a matrix portraying internal lebanese routing
def matrice():
    dg=[21, 67, 96] 
    lg=[41, 128, 185 ]
    w=[253,254,254]
    x=['CYBERIA', 'WAVENET', 'OGERONET-TRIPOLI', 'IncoNet Data Management', 'OGERONET-Jounieh', 'USJ', 'BROADBAND PLUS', 'FARAHNET','AUBNET']
    
    data = [
      [w, lg, lg, lg, lg,lg,lg,dg,lg],
      [lg, w, lg, lg, lg,lg,lg,lg,lg],
      [w,lg, w,lg,lg,lg,lg,lg,lg],
      [lg, lg, lg, w, lg,lg,lg,dg,lg],
      [w,lg, lg, lg, w,lg,lg,lg,lg],
      [lg, lg, lg, lg, lg,w,lg,dg,lg],
      [lg, lg, lg, lg, lg,lg,w,lg,lg],
      [w, lg, lg, dg, lg,lg,dg,w,dg],
      [lg, lg, lg, lg, lg,lg,lg,dg,w]
    ]
    
    fig = go.Figure(go.Image(z=data))
    fig.show()

#matrice()




















    
