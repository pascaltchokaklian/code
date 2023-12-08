from django.views import generic
from django.shortcuts import render
import folium
import requests
import pandas as pd
import polyline
from StravaMap.forms import ColForm
from StravaMap.models import Activity, Col_perform, Month_stat, Perform, Region, Segment, User_dashboard, User_var
from StravaMap.models import Col, Country
from StravaMap.models import Col_counter
from StravaMap.models import Strava_user
from StravaMap import cols_tools as ct
from StravaMap.col_dbtools import *
from StravaMap.segments_tools import segment_explorer
from StravaMap.vars import get_map_center
from django.db.models import Max
from django.shortcuts import render , redirect
from django.contrib.auth.models import User
from social_django.models import UserSocialAuth


###################################################################
#   Base Map
###################################################################

def base_map(request):

    user = request.user # Pulls in the Strava User data                
    f_debug_trace("views.py","base_map","user = "+str(user))
    my_strava_user_id = get_strava_user_id(request,user)
                                  
    # Make your map object
    view_region_info =  get_user_data_values(my_strava_user_id)            
    continent = "EUROPE"
    if view_region_info[0] == "AR":
        continent = "SOUTHAMERICA"
    main_map = folium.Map(location=get_map_center(continent), zoom_start = 6) # Create base map

    conn = create_connection('db.sqlite3')    
    
    feature_group_Road = folium.FeatureGroup(name="Route").add_to(main_map)    
    feature_group_Piste = folium.FeatureGroup(name="Piste").add_to(main_map)    
    feature_group_Sentier = folium.FeatureGroup(name="Sentier").add_to(main_map)    
            
    folium.LayerControl().add_to(main_map)

    # Statistiques Mensuelles     
    # compute_all_month_stat(my_strava_user_id)
    
    # Les cols passés
    colOK = cols_effectue(conn,my_strava_user_id )    
    listeOK = []
    for oneCol in colOK:        
        listeOK.append(oneCol[3])   # col_code
        
    # Tous les cols                
    myColsList =  select_all_cols(conn,view_region_info)
                
    # Plot Cols onto Folium Map
    for oneCol in myColsList:
        myCol = ct.PointCol()
        myCol.setPoint(oneCol)
        location = [myCol.lat,myCol.lon]
        colColor = "red"
        if myCol.col_code in listeOK :
            colColor = "green"

        # Surface
        if  myCol.col_type == "R":            
            folium.Marker(location, popup=myCol.name+" ("+str(myCol.alt)+"m)",icon=folium.Icon(color=colColor, icon="flag")).add_to(feature_group_Road)        
        if  myCol.col_type == "P":            
            folium.Marker(location, popup=myCol.name+" ("+str(myCol.alt)+"m)",icon=folium.Icon(color=colColor, icon="flag")).add_to(feature_group_Piste)        
        if  myCol.col_type == "S":            
            folium.Marker(location, popup=myCol.name+" ("+str(myCol.alt)+"m)",icon=folium.Icon(color=colColor, icon="flag")).add_to(feature_group_Sentier)        
        
    
    main_map_html = main_map._repr_html_() # Get HTML for website

    context = {
        "main_map":main_map_html
    }
                                    
    return render(request, 'index.html', context)

###################################################################
#   Connected Map
###################################################################

def connected_map(request):
        
    # Make your map object    
    main_map = folium.Map(location=get_map_center("EUROPE"), zoom_start = 6) # Create base map 
    user = request.user # Pulls in the Strava User data                
    f_debug_trace("views.py","connected_map","user = "+str(user))
    get_strava_user_id(request,user)
    strava_login = user.social_auth.get(provider='strava') # Strava login             
                
    token_type = strava_login.extra_data['token_type'] 
    access_token = strava_login.extra_data['access_token'] # Strava Access token
    refresh_token = strava_login.extra_data['refresh_token'] # Strava Refresh token
    expires = strava_login.extra_data['expires'] 
                
    activites_url = "https://www.strava.com/api/v3/athlete/activities"
    
    myUser_sq = Strava_user.objects.all().filter(strava_user = user)

    if myUser_sq.count() == 0:
        myUser = Strava_user()        
        myUser.last_name = user
        myUser.first_name = user
        myUser.token_type = token_type
        myUser.access_token = access_token
        myUser.refresh_token = refresh_token
        myUser.strava_user = user
        myUser.expire_at = expires
        myUser.strava_user_id = get_strava_user_id(request,user)
        myUser.save()
        f_debug_trace("views.py","connected_map","New User = "+ str(user))
        
    else:
        for oneOk in myUser_sq:
            myUser = oneOk
            myUser.access_token = access_token
            myUser.refresh_token = refresh_token
            myUser.expire_at = expires
            myUser.save()            

    
    my_strava_user_id = get_strava_user_id(request,user)
    my_user_var_sq = User_var.objects.filter(strava_user_id = my_strava_user_id)
    
    if my_user_var_sq.count() == 0:
        my_user_var = User_var()
        my_user_var.strava_user_id = my_strava_user_id
        my_user_var.last_update = datetime.datetime.today().timestamp()
        my_user_var.save() 
                
    # Get activity data
    header = {'Authorization': 'Bearer ' + str(access_token)}
    
    activity_df_list = []

    select_max_act_date = Activity.objects.filter(strava_user_id=my_strava_user_id).aggregate(Max('act_start_date'))
    
    ze_date = select_max_act_date["act_start_date__max"]    

    if ze_date == None: 
        ### First pass, no data in activity
        ########################
        #   Last 100 activities
        ########################

        for n in range(1):  # Change this to be higher if you have more than 100 activities
            param = {'per_page': 100, 'page': n + 1}
            activities_json = requests.get(activites_url, headers=header, params=param).json()
            if not activities_json:
                break

    else:
        ze_epoc = int(ze_date.timestamp())
        un_d_epoc = 86400
        un_jour_avant = ze_epoc - un_d_epoc    
        param = {'after': un_jour_avant , "per_page": 200}
        activities_json = requests.get(activites_url, headers=header, params=param).json()
                                
    activity_df_list.append(pd.json_normalize(activities_json))
    
    # Get Polyline Data
    activities_df = pd.concat(activity_df_list)        

    if len(activities_df)>0: 
    
        activities_df = activities_df.dropna(subset=['map.summary_polyline'])
        
        activities_df['polylines'] = activities_df['map.summary_polyline'].apply(polyline.decode)

        conn = create_connection('db.sqlite3')
        myColsList =  select_all_cols(conn,"00")        
                
        for ligne in range(len(activities_df)):
            AllVisitedCols = []
            myGPSPoints = []        
            strava_id = int(activities_df['id'][ligne])        
            activity_name = activities_df['name'][ligne]              
            act_start_date = activities_df['start_date'][ligne]      
            act_dist = activities_df['distance'][ligne]      
            act_den = activities_df['total_elevation_gain'][ligne]          
            sport_type = activities_df['sport_type'][ligne]
            act_time = int(activities_df['moving_time'][ligne])
            try:
                act_power = activities_df['average_watts'][ligne]
            except:
                act_power=0

            act_status = 1
            strava_user_id = get_strava_user_id(request,user)
            
            ########## Delete / Insert ###############
            # insert activities and col for each one
            ##########################################

            delete_activity(conn,strava_id)
            delete_col_perform(conn,strava_id)

            insert_activity(conn,strava_user_id,strava_id,activity_name,act_start_date, act_dist, act_den,sport_type,act_time,act_power,act_status)                

            for pl in activities_df['polylines'][ligne]:
                if len(pl) > 0: 
                    myPoint = ct.PointGPS()                
                    myPoint = pl                
                    myGPSPoints.append(myPoint)
        
            returnList = ct.getColsVisited(myColsList,myGPSPoints)       
            
            for ligne in returnList:                
                AllVisitedCols.append(ligne)            
                    
            insert_col_perform(conn,strava_id, AllVisitedCols)
            compute_cols_by_act(conn,my_strava_user_id,strava_id)
                        
        # Plot Polylines onto Folium Map
        my_color = 'red'
        for pl in activities_df['polylines']:
            if sport_type == "Run":
                my_color = "Blue"
            if len(pl) > 0: # Ignore polylines with length zero (Thanks Joukesmink for the tip)
                folium.PolyLine(locations=pl, color=my_color).add_to(main_map)                
            
    # Return HTML version of map
    main_map_html = main_map._repr_html_() # Get HTML for website
    context = {
        "main_map":main_map_html
    }

    update_user_var(request.session.get("strava_user_id"),"","",datetime.datetime.now().timestamp())

    # Statistiques Mensuelles     
    compute_all_month_stat(my_strava_user_id)
    # Liste des Cols des l'année
    set_col_count_list_this_year(my_strava_user_id)
                    
    return render(request, 'index.html', context)


def index(request):

    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_cols = Col.objects.all().count()
    num_cols06 = Col.objects.all().count()

    context = {
        'Nombre de Cols': num_cols,
        'Nombre de Cols (AM)': num_cols06,
    }
    
    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context)

def perf(request):
                   
    return render(request, 'performances.html')

def col_map(request, col_id):

    conn = create_connection('db.sqlite3')
    myColsList =  getCol(conn,col_id)     
    
    
    for oneCol in myColsList:
        myCol = ct.PointCol()
        myCol.setPoint(oneCol)
        col_location = [myCol.lat,myCol.lon]
        colColor = "blue"
        map = folium.Map(col_location, zoom_start=15)
        myPopup = myCol.name+" ("+str(myCol.alt)+"m)"
        folium.Marker(col_location, popup=myPopup,icon=folium.Icon(color=colColor, icon="flag")).add_to(map)      

    map_html = map._repr_html_()
    
    context = {
        "main_map": map_html,
        "col_id" : col_id,        
    }
        
    return render(request, 'index.html', context)

def act_map(request, act_id):

    my_strava_user = request.session.get("strava_user")
    my_strava_user_id = get_strava_user_id(request,my_strava_user)

    f_debug_trace("col_tools.py","act_map","user : "+my_strava_user)
    
    ct.refresh_access_token(my_strava_user)

    user = str(request.user) # Pulls in the Strava User data                
    f_debug_trace("views.py","act_map","user = "+user)
    get_strava_user_id(request,user)

    myActivity_sq = Activity.objects.all().filter(act_id = act_id)    
    access_token = "notFound"
               
    userList = Strava_user.objects.all().filter(strava_user = user)
    for userOne in userList:
            myUser = userOne
            access_token = myUser.access_token                

    f_debug_trace("views.py","act_map","access_token = "+access_token)     
           
    for myActivity in myActivity_sq:            
            strava_id =  myActivity.strava_id
            act_statut = myActivity.act_status

    activites_url = "https://www.strava.com/api/v3//activities/"+str(strava_id)
    
    # Get activity data
    header = {'Authorization': 'Bearer ' + str(access_token)}            
    param = {'id': strava_id}
    
    activities_json = requests.get(activites_url, headers=header, params=param).json()
    activity_df_list = []
       
    activity_df_list.append(pd.json_normalize(activities_json))
    
    # Get Polyline Data
    activities_df = pd.concat(activity_df_list)        
        
    activities_df = activities_df.dropna(subset=['map.summary_polyline'])
    
    activities_df['polylines'] = activities_df['map.summary_polyline'].apply(polyline.decode)
    
    # Centrage de la carte
                       
    centrer_point = ct.map_center(activities_df['polylines'])           

    # Recherche des Segments
    myRectangle = ct.get_map_rectangle(activities_df['polylines'])
    segment_explorer(myRectangle, access_token, strava_id, my_strava_user_id)
                             
    # Zoom
    map_zoom = ct.map_zoom(centrer_point,activities_df['polylines'])    
    
    map = folium.Map(location=centrer_point, zoom_start=map_zoom)
                                               
    #kw = {
    #   "color": "blue",
    #   "line_cap": "round",
    #   "fill": True,
    #   "fill_color": "red",
    #   "weight": 5,
    #   "popup": "Mon rectangle",
    #   "tooltip": "<strong>Click me!</strong>",
    #   }        
    
    #folium.Rectangle(bounds=[[myRectangle[0],myRectangle[1]],[myRectangle[2],myRectangle[3]]],line_join="round",dash_array="5, 5",**kw,).add_to(map)

    ###############################################
    #   Plot Polylines onto Folium Map
    ###############################################

    myGPSPoints = []
    
    for pl in activities_df['polylines']:
        if len(pl) > 0: # Ignore polylines with length zero (Thanks Joukesmink for the tip)
            folium.PolyLine(locations=pl, color='red').add_to(map)                
            myPoint = ct.PointGPS()                
            myPoint = pl                            
            myGPSPoints.append(myPoint)


    ## Col Display
    conn = create_connection('db.sqlite3')
    myColsList =  getColByActivity(conn,strava_id)     
    
    
    for oneCol in myColsList:
        myCol = ct.PointCol()
        myCol.setPoint(oneCol)
        col_location = [myCol.lat,myCol.lon]
        colColor = "blue"        
        mypopup = myCol.name+" ("+str(myCol.alt)+"m)"
        folium.Marker(col_location, popup=mypopup,icon=folium.Icon(color=colColor, icon="flag")).add_to(map)      
        ##### Count Update #####
                   
            
    # Return HTML version of map
    map_html = map._repr_html_() # Get HTML for website
    
    context = {
        "main_map":map_html        
    }

    strava_user = get_strava_user_id(request,my_strava_user)

    ## Check col passed new
    if act_statut == 0:
        recompute_activity(strava_id, activities_df,strava_user)
                    
    return render(request,"base_map.html", context)


def act_map_by_col(request,col_id,act_id):      
    return  act_map(request, act_id)

def col_map_by_act(request,act_id,col_id):    
    return  col_map(request, col_id)

##########################################################################

def fActivitiesListView(request, col_code):        
    strava_user_id = request.session.get('strava_user_id') 
    listActivities = Activity.objects.filter(strava_user_id=strava_user_id)
    listActivitiesPassed = Col_perform.objects.filter(col_code = col_code)

    return listActivities
    
##########################################################################    

def fColsListView(request,**kwargs):        

    template = 'cols_list.html' 
            
    code_paysregion = kwargs['pk']        
    
    listeCols = Col.objects.filter(col_code__icontains=code_paysregion).order_by("col_alt")
    country_region = get_country_region(code_paysregion)           
    country_name = get_country_from_code(country_region[0])    
    region_name = get_region_from_code(country_region[0],country_region[1])
    update_user_var(request.session.get("strava_user_id"),country_region[0],country_region[1],0)
            
    return render (request, template, {'col_list':listeCols , 'country':country_name , 'region':region_name })
    
##########################################################################    
    
class ColsListView(generic.ListView):    
    def get_queryset(self):        
        return Col.objects.all().order_by("col_alt")
        
    def get_context_data(self, **kwargs):
        context = super(ColsListView, self).get_context_data(**kwargs)
        context['countries'] = Country.objects.all()
        context['regions'] = Region.objects.all().order_by("region_code")          
        return context
              
class ColsOkListView(generic.ListView):        
    def get_queryset(self):                
        strava_user_id = self.request.session.get('strava_user_id')    
        f_debug_trace("views.py","ColsOkListView","strava_user_id = "+str(strava_user_id))
        qsOk = Col_counter.objects.filter(strava_user_id=strava_user_id).order_by("-col_count")                                                                   
        return qsOk
    
    def get_context_data(self, **kwargs):
        context = super(ColsOkListView, self).get_context_data(**kwargs)
        currentDateTime = datetime.datetime.now()
        date = currentDateTime.date()
        year = date.strftime("%Y")        
        context['annee'] = str(year)
        return context
                
class Cols06koListView(generic.ListView):        
    def get_queryset(self):                
        strava_user_id = self.request.session.get('strava_user_id')    
        qsOk = Col_counter.objects.filter(strava_user_id=strava_user_id)
        lOk= []

        for oneOk in qsOk:
            lOk.append(oneOk.col_code)

        qsCol =  Col.objects.exclude(col_code__in=lOk)
                                   
        return qsCol.filter(col_code__icontains='FR-06').order_by("col_alt")    
    
class ActivityListView(generic.ListView):        
    def get_queryset(self):                
        strava_user_id = self.request.session.get('strava_user_id')    
        return Activity.objects.filter(strava_user_id=strava_user_id).order_by("-act_start_date")
    
class ActivityDetailView(generic.DetailView):                       
    model = Activity        
                                                                            
class ColsDetailView(generic.DetailView):
	# specify the model to use            
    model = Col    

    def get_context_data(self, **kwargs):
        ### Looking for activities on this col for the context user
        context = super(ColsDetailView, self).get_context_data(**kwargs)
        strava_user_id = self.request.session.get('strava_user_id')            
        le_col = context["object"]        
        listColPerform = le_col.get_activities_passed()        
        liste_activities = []        
        for cp in listColPerform:            
            pk_activity = cp.strava_id
            myActivities= Activity.objects.filter(strava_id = pk_activity)
            for lactivity in myActivities:                                
                if int(strava_user_id) == int(lactivity.strava_user_id):
                    liste_activities.append(lactivity)                            
        context.update({'strava_user_id': strava_user_id})        
        context.update({'activities': liste_activities})        
        f_debug_trace("views.py","ColsDetailView",liste_activities)
        return context
    
       
class User_dashboardView(generic.ListView):	
    def get_queryset(self):                
        strava_user_id = self.request.session.get('strava_user_id')             
        # Delete/Insert        
        User_dashboard.objects.filter(strava_user_id=strava_user_id).delete()
        myUd = User_dashboard()
        myUd.strava_user_id = strava_user_id
        myUd.col_count = 0
        myUd.col2000_count = 0
        myUd.bike_year_km = 0        
        myUd.run_year_km = 0
        myUd.save()
        myQs = User_dashboard.objects.filter(strava_user_id=strava_user_id)
        return myQs
    
class PerformListView(generic.ListView):
    model = Perform     
    def get_queryset(self):                
        strava_user_id = self.request.session.get('strava_user_id')             
        perfList = Perform.objects.filter(strava_user_id=strava_user_id).order_by("-perf_vam")
        return perfList
    
class SegmentListView(generic.ListView):        
    def get_queryset(self):                
        qsOk = Segment.objects.all()
        return qsOk           

class MonthStatListView(generic.ListView):        
    def get_queryset(self):   
        strava_user_id = self.request.session.get('strava_user_id')             
        return Month_stat.objects.filter(strava_user_id=strava_user_id).order_by("-yearmonth")        
    
def new_col_form(request):
    if request.method  == 'POST':         
        form = ColForm(request.POST)
        if form.is_valid():        
            form.save()
            return redirect('../cols/')
        else:
            form = ColForm()
            return render(request , 'new_col.html' , {'form' : form})        
    else:                
        form = ColForm()
        return render(request , 'new_col.html' , {'form' : form})    
    
def get_strava_user_id(request,username):
    f_debug_trace("views.py","get_strava_user_id","username = "+str(username))
    user_id = User.objects.get(username=username).pk        
    uid = UserSocialAuth.objects.get(user_id=user_id).uid        
    request.session['strava_user'] = str(username)
    request.session['strava_user_id'] = uid
    f_debug_trace("views.py","get_strava_user_id","strava_user_id = "+str(uid))

    return uid
    