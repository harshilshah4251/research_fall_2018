from sklearn.neighbors import KDTree
import json
import requests
import math
import numpy as np

# ROADS_URL = "https://roads.googleapis.com/v1/snapToRoads"
# API_KEY = "AIzaSyBuqvVlcXTg-Hj9YrE2AW_7DHVgubXTZGM"

#efficiency of building KD tree is O(nlogn)
#efficiency of querying KD tree is O(log n)
  

#Defining variables
with open('jsons/camera-locations-generated.json') as camera_coordinates_file:
    camera_coordinates = [{'id' : camera['id'], 'location' : [camera['longitude'], camera['latitude']]} for camera in json.load(camera_coordinates_file)]
with open('jsons/taxidata-shanghai.json') as taxidata_file:
    taxidata = [{'timestamp' : taxi['timestamp'], 'location' : [taxi['longitude'], taxi['latitude']], 'speed' : taxi['speed'], 'id' : taxi['taxi_id']} for taxi in json.load(taxidata_file)]

#print(json.dumps(camera_coordinates, indent=4))
#print(json.dumps(taxidata, indent=4))
#plot cameras on a spatial graph
camera_coordinates_tree = KDTree([camera['location'] for camera in camera_coordinates], leaf_size = 2)

#add unique taxis to camera stream when detected
camera_taxi_ids_dict = {}
camera_stream = {}
not_detected_taxis = {}



def findPerpendicularDistance(startLocation, endLocation):
    closest_camera_distance, camera_index =  camera_coordinates_tree.query([endLocation], k = 1)
    cam_longitude = camera_coordinates[camera_index[0][0]]["location"][0]
    print(f'{camera_index[0][0]}')
    cam_latitude = camera_coordinates[camera_index[0][0]]["location"][1]
    camera_location = [cam_longitude, cam_latitude] 
    if(endLocation[1] - startLocation[1] != 0):
        slope = (endLocation[0] - startLocation[0]) / (endLocation[1] - startLocation[1])
    else:
        slope = 0
    y_intercept = endLocation[0] - (slope * endLocation[1])
    slope_perpendicular = 0
    if slope == 0:
        slope_perpendicular = 1
    elif slope == 1:
        slope_perpendicular = 0
    else:
        slope_perpendicular = 1/slope

    # print(f'slope {slope}')
    # print(f'slope_per {slope_perpendicular}')
    y_intercept_perpendicular = camera_location[0] - (slope_perpendicular * camera_location[1])

    intersection_x = (y_intercept_perpendicular - y_intercept) / (slope - slope_perpendicular)
    intersection_y = slope * intersection_x + y_intercept

    distance = math.sqrt((camera_location[1] - intersection_x)**2 + (camera_location[0] - intersection_y)**2)


    intersection_point = {
        "perpendicularDistance" : distance,
        "location" : [intersection_y, intersection_x]                  #longitude, latitude                     
    }

    #check if intersection point is in the bounds
    print(f'startlat : {startLocation[1]}')
    print(f'endlat : {endLocation[1]}')
    print(f'startlon : {startLocation[0]}')
    print(f'endlon : {endLocation[0]}')
    
    print(f'intersectionlat : {intersection_x}')
    print(f'intersectionlon : {intersection_y}')


    if intersection_x >= startLocation[1] and intersection_x <= endLocation[1] and intersection_y >= startLocation[0] and intersection_y <= endLocation[1]:
        return intersection_point
    
    return None







def addToCameraStream(taxi, location):
    closest_camera_distance, camera_index =  camera_coordinates_tree.query([location], k = 1)
    print(f'Distance from closest camera : {closest_camera_distance}')
    camera = str(camera_index[0][0])
    if camera not in camera_taxi_ids_dict:
        camera_taxi_ids_dict[camera] = []
    if(round(closest_camera_distance[0][0], 4) <= 5 * 1/1e04):                      #set the range of camera
        
        #print(taxi)
        #check to see if this location is closer to the camera than the previous location
        #print(json.dumps(location, indent=4))
        if camera in camera_stream and taxi["id"] not in camera_taxi_ids_dict[camera]:
            taxi["location"] = location
            taxi["distance_from_cam"] = closest_camera_distance[0][0]
            camera_stream[camera].append(taxi)
            camera_taxi_ids_dict[camera].append(taxi["id"])
        elif taxi["id"] not in camera_taxi_ids_dict[camera]:
            taxi["location"] = location
            taxi["distance_from_cam"] = closest_camera_distance[0][0]
            camera_stream[camera] = [taxi]
            camera_taxi_ids_dict[camera].append(taxi["id"])
        elif taxi["id"] in camera_taxi_ids_dict[camera]:
            last_distance_from_cam = list(filter(lambda detected_taxi : detected_taxi["id"] == taxi["id"], camera_stream[camera]))[0]["distance_from_cam"]
            if closest_camera_distance < last_distance_from_cam:
                taxi["location"] = location
                taxi["distance_from_cam"] = closest_camera_distance[0][0]
                #print(json.dumps(location, indent=4))

        return True
    elif((closest_camera_distance[0][0] > 5* 1e-04) and (taxi["id"] in camera_taxi_ids_dict[camera])):          #marking car as undetected after it leaves the range of the camera
        camera_taxi_ids_dict[camera].remove(taxi["id"])
        return False
    else:
        return False

num_requests = 0
for i, taxi in enumerate(taxidata):
    taxi_detected = addToCameraStream(taxi, taxi["location"])
    print(f'Taxi at {taxi["location"]}, {taxi["timestamp"]} and id {taxi["id"]} detected = {taxi_detected}')
    if(not taxi_detected):
        if(taxi["id"] not in not_detected_taxis):
            not_detected_taxis[taxi["id"]] = {"location" : [taxi["location"]]}
        else:
            last_location = not_detected_taxis[taxi["id"]]["location"][-1]             #getting the last location
            current_location = taxi["location"]
            print(f'Last detected point : {last_location}')
            counter = 0
            intersection_point = findPerpendicularDistance(last_location, current_location)
            if not intersection_point is None:
                print(f'perpendicular distance : {intersection_point["perpendicularDistance"]}')
                

                interpolated_point_detected = addToCameraStream(taxi, intersection_point["location"])
                print(f'Detected : {interpolated_point_detected} ')

                    
                if interpolated_point_detected:
                    del not_detected_taxis[taxi["id"]]
                else:
                    not_detected_taxis[taxi["id"]]["location"].append(taxi["location"])

            else:
                not_detected_taxis[taxi["id"]]["location"].append(taxi["location"])
    elif taxi["id"] in not_detected_taxis and taxi_detected:
        del not_detected_taxis[taxi["id"]]

    print("-"*60)




#print out the result in camera-stream.json
with open('jsons/camera-stream.json', 'w+') as camera_stream_file:
    camera_stream_file.write(json.dumps(camera_stream, indent=4))

dset = {}
print('Camera id : Number of detected vehicles')
for camId in camera_stream:
    if len(camera_stream[camId]) > 1:
        print(f'camera {camId} : {len(camera_stream[camId])}')
    for d in camera_stream[camId]:
        if d['id'] not in dset:
            dset[d['id']] = 1
        else:
            dset[d['id']] += 1
print('*' * 80)
print('Taxi id    : Number of detections')
for id in dset:
    if (dset[id]) > 1:
        print(f'taxi {id} : {dset[id]}')





