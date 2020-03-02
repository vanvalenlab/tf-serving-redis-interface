# Copyright 2016-2019 The Van Valen Lab at the California Institute of
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
"""DEPRECATED. Please use the "deepell_toolbox" package instead.

Functions for pre- and post-processing image data
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# pylint: disable=W0611

from deepcell_toolbox import normalize
from deepcell_toolbox import mibi
from deepcell_toolbox import watershed
from deepcell_toolbox import pixelwise
from deepcell_toolbox import correct_drift

from deepcell_toolbox.deep_watershed import deep_watershed

from deepcell_toolbox import retinanet_semantic_to_label_image
from deepcell_toolbox import retinanet_to_label_image

del absolute_import
del division
del print_function
