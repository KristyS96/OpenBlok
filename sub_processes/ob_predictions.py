'''
OpenBlok | sub_processes | ob_predictions.py

Performs predictions on the frames in the queue.
'''

import numpy as np

from bloks.utils import crop_square
from modules import ob_storage

from modeled import location, e2e


redis_db = ob_storage.RedisStorageManager()


def run_models():
    '''
    runs models on frames in the queue, stores results in Redis
    '''
    location_model = location.LocationInference()
    e2e_model = e2e.PartInference()

    while True:
        next_ready_frame = redis_db.get_frame("roi")
        preprocessed_frame = next_ready_frame['frame']

        new_metadata = {}

        side, top = location_model.get_location(preprocessed_frame)

        new_metadata['side'] = str(side)
        new_metadata['top'] = str(top)

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
                (side_crop['croppedFrame'], top_crop['croppedFrame']), axis=1)
            predictions = e2e_model.get_predictions(view_concatenated)

            new_metadata['predictions'] = str(predictions)
            new_metadata['side_crop'] = str(side_crop)
            new_metadata['top_crop'] = str(top_crop)

        new_metadata['preprocessed_shape'] = str(list(preprocessed_frame.shape))

        redis_db.move_frame("rotated", "predicted", next_ready_frame['source_frame'])
        redis_db.add_metadata("predicted", next_ready_frame['source_frame'], new_metadata)
