## Set up virtual env and install dependencies required for this repository using this command.

`virtualenv --no-site-packages --distribute .env &&\
    source .env/bin/activate &&\
    pip install -r requirements.txt`



## Running the project

1. Generate camera locations using the available taxi data.
    - Inside of project directory run `python3 camera-locations-generator.py`.
    - This will randomly select a sample of points from the taxi traces and place cameras at those points. The output is stored in [jsons/camera-locations-generated.json](jsons/camera-locations-generated.json).
2. Run [main.py](main.py) which will read taxi traces line by line and map the taxis to the cameras that detected it.
    - Inside of project directory run `python3 main.py`.
    - The output is stored in [jsons/camera-stream.json](jsons/camera-stream.json).
3. Run [plot_on_map.py](plot_on_map.py) which will update the map.html file with camera location and vehicle detection markers.
    - Inside the project directory, run `python3 plot_on_map.py`.

