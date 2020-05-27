# Copyright 2016-2020 The Van Valen Lab at the California Institute of
# Technology (Caltech), with support from the Paul Allen Family Foundation,
# Google, & National Institutes of Health (NIH) under Grant U24CA224309-01.
# All rights reserved.
#
# Licensed under a modified Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.github.com/vanvalenlab/kiosk-redis-consumer/LICENSE
#
# The Work provided may be used for non-commercial academic purposes only.
# For any other use of the Work, including commercial use, please contact:
# vanvalenlab@gmail.com
#
# Neither the name of Caltech nor the names of its contributors may be used
# to endorse or promote products derived from this software without specific
# prior written permission.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""ImageFileConsumer class for consuming image segmentation jobs."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import timeit

import numpy as np

from redis_consumer.consumers import TensorFlowServingConsumer
from redis_consumer import utils
from redis_consumer import settings


class ImageFileConsumer(TensorFlowServingConsumer):
    """Consumes image files and uploads the results"""

    def is_valid_hash(self, redis_hash):
        if redis_hash is None:
            return False

        fname = str(self.redis.hget(redis_hash, 'input_file_name'))
        return not fname.lower().endswith('.zip')

    def _get_processing_function(self, process_type, function_name):
        """Based on the function category and name, return the function"""
        clean = lambda x: str(x).lower()
        # first, verify the route parameters
        name = clean(function_name)
        cat = clean(process_type)
        if cat not in settings.PROCESSING_FUNCTIONS:
            raise ValueError('Processing functions are either "pre" or "post" '
                             'processing.  Got %s.' % cat)

        if name not in settings.PROCESSING_FUNCTIONS[cat]:
            raise ValueError('"%s" is not a valid %s-processing function'
                             % (name, cat))
        return settings.PROCESSING_FUNCTIONS[cat][name]

    def process(self, image, key, process_type):
        start = timeit.default_timer()
        if not key:
            return image

        f = self._get_processing_function(process_type, key)

        if key == 'retinanet-semantic':
            # image[:-1] is targeted at a two semantic head panoptic model
            # TODO This may need to be modified and generalized in the future
            results = f(image[:-1])
        elif key == 'retinanet':
            results = f(image, self._rawshape[0], self._rawshape[1])
        else:
            results = f(image)

        if results.shape[0] == 1:
            results = np.squeeze(results, axis=0)

        finished = timeit.default_timer() - start

        self.update_key(self._redis_hash, {
            '{}process_time'.format(process_type): finished
        })

        self.logger.debug('%s-processed key %s (model %s:%s, preprocessing: %s,'
                          ' postprocessing: %s) in %s seconds.',
                          process_type.capitalize(), self._redis_hash,
                          self._redis_values.get('model_name'),
                          self._redis_values.get('model_version'),
                          self._redis_values.get('preprocess_function'),
                          self._redis_values.get('postprocess_function'),
                          finished)

        return results

    def detect_scale(self, image):
        start = timeit.default_timer()

        if not settings.SCALE_DETECT_ENABLED:
            self.logger.debug('Scale detection disabled. Scale set to 1.')
            return 1

        model_name, model_version = settings.SCALE_DETECT_MODEL.split(':')

        scales = self.predict(image, model_name, model_version,
                              untile=False)

        detected_scale = np.mean(scales)

        error_rate = .01  # error rate is ~1% for current model.
        if abs(detected_scale - 1) < error_rate:
            detected_scale = 1

        self.logger.debug('Scale %s detected in %s seconds',
                          detected_scale, timeit.default_timer() - start)
        return detected_scale

    def detect_label(self, image):
        start = timeit.default_timer()

        if not settings.LABEL_DETECT_ENABLED:
            self.logger.debug('Label detection disabled. Label set to None.')
            return None

        model_name, model_version = settings.LABEL_DETECT_MODEL.split(':')

        labels = self.predict(image, model_name, model_version,
                              untile=False)

        labels = np.array(labels)
        vote = labels.sum(axis=0)
        maj = vote.max()

        detected = np.where(vote == maj)[-1][0]

        self.logger.debug('Label %s detected in %s seconds.',
                          detected, timeit.default_timer() - start)
        return detected

    def preprocess(self, image, keys):
        """Wrapper for _process_image but can only call with type="pre".

        Args:
            image: numpy array of image data
            keys: list of function names to apply to the image
            streaming: boolean. if True, streams data in multiple requests

        Returns:
            pre-processed image data
        """
        pre = None
        for key in keys:
            x = pre if pre else image
            pre = self.process(x, key, 'pre')
        return pre

    def postprocess(self, image, keys):
        """Wrapper for _process_image but can only call with type="post".

        Args:
            image: numpy array of image data
            keys: list of function names to apply to the image
            streaming: boolean. if True, streams data in multiple requests

        Returns:
            post-processed image data
        """
        post = None
        for key in keys:
            x = post if post else image
            post = self.process(x, key, 'post')
        return post

    def _consume(self, redis_hash):
        start = timeit.default_timer()
        hvals = self.redis.hgetall(redis_hash)
        # hold on to the redis hash/values for logging purposes
        self._redis_hash = redis_hash
        self._redis_values = hvals

        if hvals.get('status') in self.finished_statuses:
            self.logger.warning('Found completed hash `%s` with status %s.',
                                redis_hash, hvals.get('status'))
            return hvals.get('status')

        self.logger.debug('Found hash to process `%s` with status `%s`.',
                          redis_hash, hvals.get('status'))

        self.update_key(redis_hash, {
            'status': 'started',
            'identity_started': self.name,
        })

        # Overridden with LABEL_DETECT_ENABLED
        model_name = hvals.get('model_name')
        model_version = hvals.get('model_version')

        _ = timeit.default_timer()

        with utils.get_tempdir() as tempdir:
            fname = self.storage.download(hvals.get('input_file_name'), tempdir)
            image = utils.get_image(fname)

        # Pre-process data before sending to the model
        self.update_key(redis_hash, {
            'status': 'pre-processing',
            'download_time': timeit.default_timer() - _,
        })

        # Calculate scale of image and rescale
        scale = hvals.get('scale', '')
        if not scale:
            # Detect scale of image
            scale = self.detect_scale(image)
            self.logger.debug('Image scale detected: %s', scale)
            self.update_key(redis_hash, {'scale': scale})
        else:
            scale = float(scale)
            self.logger.debug('Image scale already calculated: %s', scale)

        image = utils.rescale(image, scale)

        # Save shape value for postprocessing purposes
        # TODO this is a big janky
        self._rawshape = image.shape
        label = None
        if settings.LABEL_DETECT_ENABLED and model_name and model_version:
            self.logger.warning('Label Detection is enabled, but the model'
                                ' %s:%s was specified in Redis.',
                                model_name, model_version)

        elif settings.LABEL_DETECT_ENABLED:
            # Detect image label type
            label = hvals.get('label', '')
            if not label:
                label = self.detect_label(image)
                self.logger.debug('Image label detected: %s', label)
                self.update_key(redis_hash, {'label': str(label)})
            else:
                label = int(label)
                self.logger.debug('Image label already calculated: %s', label)

            # Grap appropriate model
            model_name, model_version = utils._pick_model(label)

        pre_funcs = hvals.get('preprocess_function', '').split(',')
        image = self.preprocess(image, pre_funcs)

        # Send data to the model
        self.update_key(redis_hash, {'status': 'predicting'})

        image = self.predict(image, model_name, model_version)

        # Post-process model results
        self.update_key(redis_hash, {'status': 'post-processing'})

        if settings.LABEL_DETECT_ENABLED and label is not None:
            post_funcs = utils._pick_postprocess(label).split(',')
        else:
            post_funcs = hvals.get('postprocess_function', '').split(',')

        image = self.postprocess(image, post_funcs)

        # Save the post-processed results to a file
        _ = timeit.default_timer()
        self.update_key(redis_hash, {'status': 'saving-results'})

        with utils.get_tempdir() as tempdir:
            # Save each result channel as an image file
            save_name = hvals.get('original_name', fname)
            subdir = os.path.dirname(save_name.replace(tempdir, ''))
            name = os.path.splitext(os.path.basename(save_name))[0]

            # Rescale image to original size before sending back to user
            if isinstance(image, list):
                outpaths = []
                for i in image:
                    outpaths.extend(utils.save_numpy_array(
                        utils.rescale(i, 1 / scale), name=name,
                        subdir=subdir, output_dir=tempdir))
            else:
                outpaths = utils.save_numpy_array(
                    utils.rescale(image, 1 / scale), name=name,
                    subdir=subdir, output_dir=tempdir)

            # Save each prediction image as zip file
            zip_file = utils.zip_files(outpaths, tempdir)

            # Upload the zip file to cloud storage bucket
            cleaned = zip_file.replace(tempdir, '')
            subdir = os.path.dirname(settings._strip(cleaned))
            subdir = subdir if subdir else None
            dest, output_url = self.storage.upload(zip_file, subdir=subdir)

        # Update redis with the final results
        t = timeit.default_timer() - start
        self.update_key(redis_hash, {
            'status': self.final_status,
            'output_url': output_url,
            'upload_time': timeit.default_timer() - _,
            'output_file_name': dest,
            'total_jobs': 1,
            'total_time': t,
            'finished_at': self.get_current_timestamp()
        })
        return self.final_status