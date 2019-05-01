from gmplot import gmplot
import json
import numpy as np

from bs4 import BeautifulSoup

with open('jsons/camera-locations-generated.json') as camera_coordinates_file:
    camera_coordinates = [{'id' : camera['id'], 'location' : [camera['longitude'], camera['latitude']]} for camera in json.load(camera_coordinates_file)]

with open('jsons/camera-stream.json') as camera_stream_file:
    camera_stream = json.load(camera_stream_file)

with open('jsons/taxidata-shanghai.json') as taxi_data_file:
    taxi_path = json.load(taxi_data_file)





#find mean latitude and longitude to center the map
cam_longitudes = [camera['location'][0] for camera in camera_coordinates]
cam_latitudes = [camera['location'][1] for camera in camera_coordinates]

mean_cam_latitude = np.mean(cam_latitudes)
mean_cam_longitude = np.mean(cam_longitudes)

print(f'mean_cam_latitude : {mean_cam_latitude} \nmean_cam_longitude : {mean_cam_longitude}')

#place map
gmap = gmplot.GoogleMapPlotter(mean_cam_latitude, mean_cam_longitude, 13)


for taxi in taxi_path:
    gmap.scatter([taxi['latitude']], [taxi['longitude']], color='black',  marker = False, size = 1,title=str(taxi['longitude']) + '-' +str(taxi['latitude']))

#plotting sample of cameras and detected points on map
for camera in camera_coordinates:
    cam_latitude, cam_longitude = camera['location'][1], camera['location'][0]
    gmap.marker(cam_latitude, cam_longitude, color='green', title=camera['id'])
    gmap.scatter([cam_latitude], [cam_longitude], color='yellow', marker = False, size=50)
    #only including cameras that detect atleast one vehicle
    if str(camera['id']) in camera_stream:
        detected_vehicles = camera_stream[str(camera['id'])]
        for vehicle in detected_vehicles:
            vehicle_latitude, vehicle_longitude = vehicle['location'][1], vehicle['location'][0]
            #ignoring the car having same location as camera to view cameras properly on the map
            if(vehicle_latitude != cam_latitude and vehicle_longitude != cam_longitude):           
                gmap.marker(vehicle_latitude, vehicle_longitude, color='red', title=vehicle['location'])
        
        

















# # Draw
gmap.draw("map.html")





def insertapikey(fname, apikey):
    """put the google api key in a html file"""
    def putkey(htmltxt, apikey, apistring=None):
        """put the apikey in the htmltxt and return soup"""
        if not apistring:
            apistring = "https://maps.googleapis.com/maps/api/js?key=%s&callback=initMap"
        soup = BeautifulSoup(htmltxt, 'html.parser')
        body = soup.body
        src = apistring % (apikey, )
        tscript = soup.new_tag("script", src=src, async="defer")
        body.insert(-1, tscript)
        return soup
    htmltxt = open(fname, 'r').read()
    soup = putkey(htmltxt, apikey)
    newtxt = soup.prettify()
    open(fname, 'w').write(newtxt)

insertapikey("map.html", "AIzaSyD3Uzwhfn_IRWHfYLS1JhrnNLOj6FhxAao")




