from concurrent.futures import ThreadPoolExecutor
import time

# Takes an image file and a list of table ID -> rectangle mappings.
# rectangles are defined by their four vertices.
def get_table_occupations(img, t_id_rect_map):
    return None


# Gets an image from the desired camera.
def get_image(camera_id):
    return None


# SQL script that queries the database for vertices and returns the list of vertices.
def get_trect_map(camera_id):
    return None

# update table samples, and potentially update sql database if a change in the system is detected.
def update_table_samples(tid_occ_list):
    return None

# get camera ids.
def get_camera_ids():
    return None


def process_camera(camera):
    image = get_image(camera)
    tableid_rect_map = get_trect_map(camera)
    tid_occ_list = get_table_occupations(image, tableid_rect_map)
    update_table_samples(tid_occ_list)

while True:
    cameras = get_camera_ids()
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(process_camera, cameras)
    time.sleep(1)

# respond to front end get requests