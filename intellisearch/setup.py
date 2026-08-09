"""
 Copyright (c) 2022, Microprodut, inc.
 All rights reserved.
 SPDX-License-Identifier: BSD-3-Clause
 For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
"""

from setuptools import setup, find_namespace_packages
import platform

DEPENDENCY_LINKS = []
if platform.system() == "Windows":
    DEPENDENCY_LINKS.append("https://download.pytorch.org/whl/torch_stable.html")


def fetch_requirements(filename):
    with open(filename) as f:
        return [ln.strip() for ln in f.read().split("\n")]


setup(
    name="microproduct-intellisearch",
    version="1.0.0",
    author="Eskinder Kiros",
    description="INTELLISEARCH - A One-stop AI-empowered search for all your documents",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    keywords="Intelligent Search, Vision-Language, Multimodal, Image Captioning, Generative AI, Deep Learning, Library, Search",
    license="3-Clause BSD",
    packages=find_namespace_packages(include="search.*"),
    install_requires=fetch_requirements("requirements.txt"),
    python_requires=">=3.8.0",
    include_package_data=True,
    dependency_links=DEPENDENCY_LINKS,
    zip_safe=False,
)
