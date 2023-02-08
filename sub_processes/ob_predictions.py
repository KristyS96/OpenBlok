'''
OpenBlok | sub_processes | ob_predictions.py

Performs predictions on the frames in the queue.
'''

import numpy as np

from bloks.utils import crop_square
from modules import ob_storage

from modeled import location, e2e


redis_db = ob_storage.RedisStorageManager()

location_model = location.LocationInference()
e2e_model = e2e.PartInference()


def run_models():
    '''
    runs models on frames in the queue, stores results in Redis
    '''
    while True:
        preprocessed_frame = redis_db.get_frame("roi")

        new_metadata = {}

        side, top = location_model.get_location(preprocessed_frame)

        new_metadata['side'] = side
        new_metadata['top'] = top

        if 0 not in [side[0], side[1], top[0], top[1]] and top[0] > preprocessed_frame.shape[1]//3:
            top[0] = top[0] - preprocessed_frame.shape[1]//3

            side_crop = crop_square(
                preprocessed_frame[:, :preprocessed_frame.shape[1]//3],
                (side[0], side[1])
            )

            top_crop = crop_square(
                preprocessed_frame[:, preprocessed_frame.shape[1]//3:],
                (top[0], top[1])
            )

            view_concatenated = np.concatenate(
                (side_crop[0], top_crop[0]), axis=1)
            predictions = e2e_model.get_predictions(view_concatenated)

            new_metadata['predictions'] = predictions
            new_metadata['side_crop'] = side_crop
            new_metadata['top_crop'] = top_crop

        redis_db.add_metadata("rotated", preprocessed_frame['uuid'], new_metadata)
