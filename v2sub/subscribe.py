import base64
import json
import os
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError
from v2sub.systemd import SYSTEMD_UNIT

import click

from v2sub import BASE_PATH
from v2sub import DEFAULT_SUBSCRIBE
from v2sub import SERVER_CONFIG
from v2sub import SUBSCRIBE_CONFIG
from v2sub import utils


def init():
    if not os.path.exists(BASE_PATH):
        os.makedirs(BASE_PATH)
    if not os.path.exists(SUBSCRIBE_CONFIG):
        os.mknod(SUBSCRIBE_CONFIG)
    if not os.path.exists(SERVER_CONFIG):
        os.mknod(SERVER_CONFIG)
    if not os.path.exists(SYSTEMD_UNIT):
        os.mknod(SYSTEMD_UNIT)


def add_subscribe(url, name=DEFAULT_SUBSCRIBE):
    subscribe = utils.read_from_json(SUBSCRIBE_CONFIG)
    subscribe.update({name: url})
    utils.write_to_json(subscribe, SUBSCRIBE_CONFIG)
    click.echo("Added subscribe: %s" % url)


def list_subscribe():
    subscribe = utils.read_from_json(SUBSCRIBE_CONFIG)
    click.echo("Subscribes:")
    for name, url in subscribe.items():
        click.echo("%s: %s" % (name, url))


def _remove_subscribe(name=DEFAULT_SUBSCRIBE, all_subs=False):
    all_subscribes = utils.read_from_json(SUBSCRIBE_CONFIG)
    if all_subs:
        all_subscribes.clear()
    else:
        all_subscribes.pop(name, None)
    utils.write_to_json(all_subscribes, SUBSCRIBE_CONFIG)


def _remove_servers(name=DEFAULT_SUBSCRIBE, all_subs=False):
    all_servers = utils.read_from_json(SERVER_CONFIG)
    if all_subs:
        all_servers.clear()
    else:
        all_servers.pop(name, None)
    utils.write_to_json(all_servers, SERVER_CONFIG)


def remove_subscribe(name=DEFAULT_SUBSCRIBE, all_subs=False):
    _remove_subscribe(name=name, all_subs=all_subs)
    _remove_servers(name=name, all_subs=all_subs)
    if all_subs:
        click.echo("Removed all subscribes.")
    else:
        click.echo("Removed subscribe: %s" % name)

def padding_base64(data):
    missing_padding = len(data) % 4
    if missing_padding != 0:
        data += b'='* (4 - missing_padding)
    return data

def parser_subscribe(url, name=DEFAULT_SUBSCRIBE):
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urlopen(req)
    except URLError:
        click.echo("Can't parse the url, please check your network or make"
                   " sure you entered the correct URL!")
        sys.exit(1)
    nodes = base64.b64decode(padding_base64(resp.read())).splitlines()
    servers = []
    for node in nodes:
        # Ignore non-vemss node
        if b"vmess://" not in node:
            continue
        node = utils.byte2str(node).replace("vmess://", "")
        node = utils.byte2str(base64.b64decode(node))
        servers.append(json.loads(node))
    all_servers = utils.read_from_json(SERVER_CONFIG)
    all_servers.update({name: servers})
    utils.write_to_json(all_servers, SERVER_CONFIG)


def _update_all_subscribe(subscribes: dict):
    for name, url in subscribes.items():
        parser_subscribe(url, name=name)


def update_subscribe(name=DEFAULT_SUBSCRIBE, all_subs=False):
    all_subscribe = utils.read_from_json(SUBSCRIBE_CONFIG)
    if all_subs:
        _update_all_subscribe(all_subscribe)
    else:
        try:
            url = all_subscribe[name]
        except KeyError:
            click.echo("No subscribe named %s found!" % name)
            sys.exit(1)
        parser_subscribe(url, name=name)
    list_servers(name=name, all_subs=all_subs)


def _list_server(name, nodes):
    click.echo("=" * 50)
    click.echo("SUBSCRIBE: %s" % name)
    click.echo('=' * 50)
    for index, node in enumerate(nodes, start=1):
        utils.echo_node(index, node)


def list_servers(name=DEFAULT_SUBSCRIBE, all_subs=False):
    all_servers = utils.read_from_json(SERVER_CONFIG)
    if not all_servers:
        click.echo("No servers found, please add and update subscribe first!")
        sys.exit(1)
    if all_subs:
        for name, nodes in all_servers.items():
            _list_server(name, nodes)
    else:
        _list_server(name, all_servers[name])


def get_node(index, name=DEFAULT_SUBSCRIBE):
    all_servers = utils.read_from_json(SERVER_CONFIG)
    try:
        servers = all_servers[name]
    except KeyError:
        click.echo("No subscribe named %s found!" % name)
        sys.exit(1)
    node = servers[index]
    click.echo("switch to node:")
    utils.ping(name=name, index=index, all_servers=all_servers)
    return node


def get_servers(name=DEFAULT_SUBSCRIBE, all_subs=False):
    all_servers = utils.read_from_json(SERVER_CONFIG)
    if not all_servers:
        click.echo("No servers found, please add and update subscribe first!")
        sys.exit(1)
    if all_subs:
        return [node["ps"] for node in [sub for sub in all_servers]]
    else:
        return [node["ps"] for node in all_servers[name]]
