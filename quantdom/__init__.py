"""
Copyright © 2017-2019 Constverum <constverum@gmail.com>. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

__title__ = 'Quantdom'
__version__ = '0.1.1'

from .ui import *  # noqa
from .lib import *  # noqa

__all__ = ui.__all__ + lib.__all__ + (__title__, __version__)  # noqa
