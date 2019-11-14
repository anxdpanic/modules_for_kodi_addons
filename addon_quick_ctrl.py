# -*- coding: utf-8 -*-
"""

    Copyright (C) 2019 anxdpanic

    SPDX-License-Identifier: GPL-3.0-or-later

    Script to disable/enable/restart one of the user specified add-ons from a select
    dialog within Kodi

    Usage:
        - Place this script in the ../userdata/ folder
        - Add your add-ons to the ADDON_IDS list below
        - Create a key map to run this script

            ../userdata/keymaps/addon_quick_ctrl.xml
            <keymap>
                <global>
                    <keyboard>
                        <f1 mod="ctrl,alt">RunScript("special://userdata/addon_quick_ctrl.py")</f1>
                    </keyboard>
                </global>
            </keymap>

"""

import json
import sys

import xbmc  # pylint: disable=import-error
import xbmcaddon  # pylint: disable=import-error
import xbmcgui  # pylint: disable=import-error
import xbmcvfs  # pylint: disable=import-error

ADDON_IDS = []

'''
ADDON_IDS = ['plugin.video.youtube', 'plugin.video.twitch', 'plugin.video.playthis',
             'script.module.python.twitch', 'plugin.video.composite_for_plex',
             'plugin.script.testing', 'context.youtube.download', 'script.trakttokodi.libconn',
             'script.trakttokodi.embycon', 'service.xbmc.versioncheck', 'script.module.youtube.dl']
'''

KODI_VERSION_MAJOR = int(xbmc.getInfoLabel('System.BuildVersion')[0:2])


def addon_status(addon_id):
    """ Check if add-on is enabled/disabled via JSONRPC

    :param addon_id: id of the add-on to check
    :type addon_id: str
    :return: whether the add-on is enabled or not
    :rtype: bool
    """
    request = {
        "jsonrpc": "2.0",
        "method": "Addons.GetAddonDetails",
        "id": 1,
        "params": {
            "addonid": "%s" % addon_id,
            "properties": ["enabled"]
        }
    }
    response = xbmc.executeJSONRPC(json.dumps(request))
    response = json.loads(response)
    try:
        is_enabled = response['result']['addon']['enabled'] is True
        xbmc.log('[aqc] %s is %s' %
                 (addon_id, 'enabled' if is_enabled else 'disabled'), xbmc.LOGDEBUG)
        return is_enabled
    except KeyError:
        xbmc.log('[aqc] addon_status received an unexpected response', xbmc.LOGERROR)
        return False


def disable_addon(addon_id):
    """ Disable an add-on via JSONRPC

    :param addon_id: id of the add-on to disable
    :type addon_id: str
    :return: whether add-on was disabled successfully
    :rtype: bool
    """
    request = {
        "jsonrpc": "2.0",
        "method": "Addons.SetAddonEnabled",
        "params": {
            "addonid": "%s" % addon_id,
            "enabled": False
        },
        "id": 1
    }

    xbmc.log('[aqc] disabling %s' % addon_id, xbmc.LOGDEBUG)
    response = xbmc.executeJSONRPC(json.dumps(request))
    response = json.loads(response)
    try:
        return response['result'] == 'OK'
    except KeyError:
        xbmc.log('[aqc] disable_addon received an unexpected response', xbmc.LOGERROR)
        return False


def enable_addon(addon_id):
    """ Enable an add-on via JSONRPC

    :param addon_id: id of the add-on to enable
    :type addon_id: str
    :return: whether add-on was enabled successfully
    :rtype: bool
    """
    request = {
        "jsonrpc": "2.0",
        "method": "Addons.SetAddonEnabled",
        "params": {
            "addonid": "%s" % addon_id,
            "enabled": True
        },
        "id": 1
    }

    xbmc.log('[aqc] enabling %s' % addon_id, xbmc.LOGDEBUG)

    response = xbmc.executeJSONRPC(json.dumps(request))
    response = json.loads(response)
    try:
        return response['result'] == 'OK'
    except KeyError:
        xbmc.log('[aqc] enable_addon received an unexpected response', xbmc.LOGERROR)
        return False


def select_dialog(heading, items, use_details=False):
    """ Create a selection dialog

    :param heading: dialog heading
    :type heading: str
    :param items: selection items
    :type items: list of xbmcgui.ListItem or list of str
    :param use_details: whether to use detailed select dialog in Kodi 17+
    :type use_details: bool
    :return: index of user selection
    :rtype: int
    """
    if KODI_VERSION_MAJOR > 16 and use_details:  # use detailed select dialog
        result = xbmcgui.Dialog().select(heading=heading, list=items, useDetails=True)
    else:
        result = xbmcgui.Dialog().select(heading=heading, list=items)
    return result


def main():
    """ Prompt the user to select an add-on to disable/enabled/restart, using the add-on ids
    provided in the ADDON_IDS constant.

    """
    if not ADDON_IDS:
        xbmcgui.Dialog().notification(heading='Add-on Quick Control',
                                      message='No add-ons found, add your add-ons to '
                                              'ADDON_IDS in addon_quick_ctrl.py',
                                      time=15000, sound=False)
        sys.exit(0)

    addons = []
    addon_ids = []
    addon_states = []

    for addon_id in ADDON_IDS:
        addon_id = str(addon_id)
        try:
            addon = xbmcaddon.Addon(addon_id)
            addon_icon = addon.getAddonInfo('icon')
            addon_name = addon.getAddonInfo('name')
            addon_version = addon.getAddonInfo('version')
            label_1 = addon_name
            label_2 = '%s v%s' % (addon_id, addon_version)
            addon_states.append('enabled')
        except RuntimeError:  # add-on is either disabled or not installed
            addon_xml = xbmc.translatePath('special://home/addons/%s/addon.xml' % addon_id)
            if not xbmcvfs.exists(addon_xml):  # if addon.xml exists, add-on is disabled
                xbmc.log('[aqc] %s not found' % addon_id, xbmc.LOGDEBUG)
                continue
            addon_icon = xbmc.translatePath('special://home/addons/%s/icon.png' % addon_id)
            if not xbmcvfs.exists(addon_icon):
                addon_icon = ''
            label_1 = addon_id
            label_2 = 'Disabled'
            addon_states.append('disabled')

        xbmc.log('[aqc] found %s' % addon_id, xbmc.LOGDEBUG)

        if KODI_VERSION_MAJOR > 16:  # create ListItem for detailed select dialog
            list_item = xbmcgui.ListItem(label=label_1, label2=label_2)
            list_item.setArt({'icon': addon_icon, 'thumb': addon_icon})
            addons.append(list_item)
        else:
            addons.append(label_1)
        addon_ids.append(addon_id)
        xbmc.log('[aqc] %s added to the select dialog' % addon_id, xbmc.LOGDEBUG)

    if not addon_ids:
        xbmc.log('[aqc] none of the add-ons are installed', xbmc.LOGERROR)
        xbmcgui.Dialog().notification(heading='Add-on Quick Control',
                                      message='None of the provided add-ons are installed.',
                                      time=15000, sound=False)
        sys.exit(0)

    result = select_dialog('Select an add-on', addons, use_details=True)
    if result == -1:
        xbmc.log('[aqc] user cancelled the add-on select dialog', xbmc.LOGDEBUG)
        sys.exit(0)

    addon_id = addon_ids[result]
    addon_state = addon_states[result]
    xbmc.log('[aqc] user selected %s' % addon_id, xbmc.LOGDEBUG)

    if addon_state == 'enabled' and addon_status(addon_id):
        actions = ['Restart', 'Disable']
        result = select_dialog('Select an action', actions)
        if result == -1:
            xbmc.log('[aqc] user cancelled the action select dialog',
                     xbmc.LOGDEBUG)
            sys.exit(0)

        xbmc.log('[aqc] user selected %s' % actions[result],
                 xbmc.LOGDEBUG)
        disable_addon(addon_id)
        if actions[result] == 'Restart':
            xbmc.sleep(1000)
            enable_addon(addon_id)
        return

    actions = ['Enable']
    result = select_dialog('Select an action', actions)
    if result == -1:
        xbmc.log('[aqc] user cancelled the action select dialog',
                 xbmc.LOGDEBUG)
        sys.exit(0)

    xbmc.log('[aqc] user selected %s' % actions[result],
             xbmc.LOGDEBUG)
    if actions[result] == 'Enable':
        enable_addon(addon_id)
    return


if __name__ == '__main__':
    main()
