# -*- coding: utf-8 -*-
"""

    Copyright (C) 2016 anxdpanic

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import xbmc
import xbmcgui
import xbmcaddon


class PropertyStore:
    def __init__(self, addon_id=None):
        self.addon_id = addon_id
        if self.addon_id is None:
            self.addon_id = xbmcaddon.Addon().getAddonInfo('id')
        self.window = xbmcgui.Window(10000)

    def __enter__(self):
        return self

    def get(self, key):
        if self.addon_id not in key:
            key = '%s-%s' % (self.addon_id, key)
        value = self.window.getProperty(key)
        value = self.__coerce_bool(value)
        xbmc.log('%s: PropertyStore returned value |%s| type |%s| for key |%s|' % (self.addon_id, str(value), type(value), key), xbmc.LOGDEBUG)
        return value

    def set(self, key, value):
        if self.addon_id not in key:
            key = '%s-%s' % (self.addon_id, key)
        value = self.__coerce_bool(value, to_string=True)
        xbmc.log('%s: PropertyStore setting key |%s| to value |%s|' % (self.addon_id, key, value), xbmc.LOGDEBUG)
        self.window.setProperty(key, value)

    def __exit__(self, exc_type, exc_val, exc_tb):
        return

    @staticmethod
    def __coerce_bool(value, to_string=False):
        if not to_string:
            temp = value.lower()
            if temp == 'true':
                return True
            elif temp == 'false':
                return False
            elif temp == 'none':
                return None
        elif value is True or value is False or value is None:
            return str(value).lower()
        else:
            return value
