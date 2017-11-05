"""
Copyright © 2017-2018 Constverum <constverum@gmail.com>. All rights reserved.

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
__package__ = 'quantdom'
__version__ = '0.1a1'
__short_description__ = 'Simple but powerful backtesting framework, that strives to let you focus on modeling financial strategies, portfolio management, and analyzing backtests.'
__author__ = 'Constverum'
__author_email__ = 'constverum@gmail.com'
__url__ = 'https://github.com/constverum/Quantdom'
__license__ = 'Apache License, Version 2.0'
__copyright__ = 'Copyright 2017-2018 Constverum'

# Each of the submodules having an __all__ variable.

from .ui import *  # noqa
from .lib import *  # noqa


__all__ = (
    ui.__all__ +
    lib.__all__ +
    ('__title__', '__package__', '__version__', '__short_description__',
     '__author__', '__author_email__', '__url__', '__license__',
     '__copyright__')
)
