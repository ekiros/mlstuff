"""
 Copyright (c) 2024, Microproduct, inc.
 All rights reserved.
 SPDX-License-Identifier: BSD-3-Clause
 For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
"""

import os
#import sys

#from data.utilities import *
#from data.audiovideo import *

root_dir = os.path.dirname(os.path.abspath('.'))
repo_root = os.path.join(root_dir, "..")

__all__ = ['utilities.geo_loc', 'utilities.pdf_parser','utilities.text_utils','audiovideo.image_labeling','audiovideo.audio_labeling','audiovideo.video_labeling', 'db.db_utils']