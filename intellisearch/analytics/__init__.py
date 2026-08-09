"""
 Copyright (c) 2024, Microproduct, inc.
 All rights reserved.
 SPDX-License-Identifier: BSD-3-Clause
 For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
 All the analytics modules here: Audio, Video, Text, Image
 See the individual module files for more information.
"""
import os, sys

sys.path.insert(0, os.path.abspath(".."))

#root_dir = os.path.dirname(os.path.abspath('.'))
#repo_root = os.path.join(root_dir, "..")

__all__ = ['audio_analytics','video_analytics', 'image_analytics','text_analytics',
'text_analytics.indexer', 'text_analytics.nl_analytics','text_analytics.analytics_utils']

#from analytics import *