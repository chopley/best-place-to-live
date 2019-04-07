import pandas as pd

def read_address_csv(fileName):
    houses = pd.read_csv(fileName,delimiter=';')
    return(houses)

def switch_lat_long(list_of_coords):
    return_list_of_coords = []
    for coord in list_of_coords:
       return_list_of_coords.append((coord[1],coord[0]))
    return(return_list_of_coords)