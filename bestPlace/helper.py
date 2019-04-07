import pandas as pd

def read_address_csv(fileName):
    houses = pd.read_csv(fileName,delimiter=';')
    return(houses)

def switch_lat_long(list_of_coords):
    return_list_of_coords = []
    for coord in list_of_coords:
       return_list_of_coords.append((coord[1],coord[0]))
    return(return_list_of_coords)

def product_output_df(house):
    average_school_ranking = round(pd.DataFrame(house.school_district_data['rankHistory'])['rankStatewidePercentage'].mean())
    dict_val = pd.DataFrame([{'school_ranking' : average_school_ranking,
                'districtID' : house.school_district_data['districtID'],
                'districtName' : house.school_district_data['districtName']}]).T
    max_duration_from_house = 20
    ind = house.df_travel_distances['duration_x'] < 20
    aa = house.df_travel_distances[ind]
    cc = aa.groupby("destination").head(1)[['destination','total_duration']]
    cc.reset_index()
    travel_df = cc.set_index('destination')
    travel_df = travel_df.reset_index()
    travel_df.set_index('destination')
    travel_df.columns = ['field','values']
    dict_val = dict_val.reset_index()
    dict_val.columns = ['field','values']
    travel_df = travel_df.append(dict_val)
    return(travel_df)