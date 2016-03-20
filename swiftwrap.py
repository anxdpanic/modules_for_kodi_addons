# -*- coding: utf-8 -*-
"""
    Super Classed xbmcswift2 Plugin()
        - Based on xbmcswift2 Plugin ( https://raw.githubusercontent.com/jbeluch/xbmcswift2/master/xbmcswift2/plugin.py )

    Super Classed xbmcswift2 ListItem()
        - Based on xbmcswift2 ListItem ( https://raw.githubusercontent.com/jbeluch/xbmcswift2/master/xbmcswift2/listitem.py )

    Allows for is_folder: True/False to be set in ListItem dicts
    Workaround to allow isPlayable == isFolder

    usage:
        from swiftwrap import Plugin
        PLUGIN = Plugin()

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


from xbmcswift2.plugin import Plugin as SwiftPlugin
from xbmcswift2.listitem import ListItem as SwiftListItem


class Plugin(SwiftPlugin):

    def __init__(self, name=None, addon_id=None, filepath=None, info_type=None):
        super(Plugin, self).__init__(name, addon_id, filepath, info_type)

    def _listitemify(self, item):
        # use ListItem() instead of xbmcswift2.listitem ListItem()
        info_type = self.info_type if hasattr(self, 'info_type') else 'video'

        if not hasattr(item, 'as_tuple'):
            if 'info_type' not in item.keys():
                item['info_type'] = info_type
            item = ListItem.from_dict(**item)
        return item


class ListItem(SwiftListItem):

    def __init__(self, label=None, label2=None, icon=None, thumbnail=None, path=None):
        super(ListItem, self).__init__(label, label2, icon, thumbnail, path)

    @classmethod
    def from_dict(cls, label=None, label2=None, icon=None, thumbnail=None,
                  path=None, selected=None, info=None, properties=None,
                  context_menu=None, replace_context_menu=False,
                  is_playable=None, info_type='video', stream_info=None, is_folder=None):
        # add is_folder parameter and set listitem.is_folder if/when appropriate
        listitem = cls(label, label2, icon, thumbnail, path)

        if selected is not None:
            listitem.select(selected)

        if info:
            listitem.set_info(info_type, info)

        if is_playable:
            listitem.set_is_playable(True)

        if is_folder:
            listitem.is_folder = True

        if properties:
            if hasattr(properties, 'items'):
                properties = properties.items()
            for key, val in properties:
                listitem.set_property(key, val)

        if stream_info:
            for stream_type, stream_values in stream_info.items():
                listitem.add_stream_info(stream_type, stream_values)

        if context_menu:
            listitem.add_context_menu_items(context_menu, replace_context_menu)

        return listitem
