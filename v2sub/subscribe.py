import base64
import json
import os
import sys

import click
import requests

from v2sub import utils

BASE_PATH = os.path.join(os.path.expandvars("$HOME"), ".v2sub")
SUBSCRIBE_CONFIG = os.path.join(BASE_PATH, 'subscribes.json')
SERVER_CONFIG = os.path.join(BASE_PATH, 'servers.json')
DEFAULT_SUBSCRIBE = "default"


def init():
    if not os.path.exists(BASE_PATH):
        os.makedirs(BASE_PATH)
    if not os.path.exists(SUBSCRIBE_CONFIG):
        os.mknod(SUBSCRIBE_CONFIG)
    if not os.path.exists(SERVER_CONFIG):
        os.mknod(SERVER_CONFIG)


def parser_subscribe(url, name=DEFAULT_SUBSCRIBE):
    try:
        resp = requests.get(url)
    except requests.exceptions.ConnectionError as err:
        click.echo("Can't parse the url, please check your network or make"
                   " sure you entered the correct URL!")
        raise err
    server_links = base64.b64decode(resp.content).splitlines()
    servers = []
    for index, server_link in enumerate(server_links):
        server_link = utils.byte2str(server_link).replace("vmess://", "")
        server_node = json.loads(base64.b64decode(server_link))
        servers.append(server_node)
    name_servers = utils.read_as_json(SERVER_CONFIG)
    name_servers.update({name: servers})
    utils.write_to_json(name_servers, SERVER_CONFIG)


def add_subscribe(url, name=DEFAULT_SUBSCRIBE):
    subscribe = utils.read_as_json(SUBSCRIBE_CONFIG)
    subscribe.update({name: url})
    utils.write_to_json(subscribe, SUBSCRIBE_CONFIG)


def list_subscribe():
    subscribe = utils.read_as_json(SUBSCRIBE_CONFIG)
    for name, url in subscribe.items():
        click.echo("\n%s: %s" % (name, url))


def _remove_subscribe(name=DEFAULT_SUBSCRIBE, all_subs=False):
    all_subscribes = utils.read_as_json(SUBSCRIBE_CONFIG)
    if all_subs:
        all_subscribes = dict()
    else:
        all_subscribes.pop(name, None)
    utils.write_to_json(all_subscribes, SUBSCRIBE_CONFIG)


def remove_subscribe(name=DEFAULT_SUBSCRIBE, all_subs=False):
    _remove_subscribe(name=name, all_subs=all_subs)
    _remove_servers(name=name, all_subs=all_subs)


def _update_all_subscribe(subscribes: dict):
    for name, url in subscribes.items():
        parser_subscribe(url, name=name)


def update_subscribe(name=DEFAULT_SUBSCRIBE, all_subs=False):
    all_subscribe = utils.read_as_json(SUBSCRIBE_CONFIG)
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
        click.echo('[' + str(index) + ']' + node['ps'] + '--' + node['add'])


def list_servers(name=DEFAULT_SUBSCRIBE, all_subs=False):
    all_servers = utils.read_as_json(SERVER_CONFIG)
    if not all_servers:
        click.echo("No servers found, please add and update subscribe first!")
        sys.exit()
    if all_subs:
        for name, nodes in all_servers.items():
            _list_server(name, nodes)
    else:
        _list_server(name, all_servers[name])


def _remove_servers(name=DEFAULT_SUBSCRIBE, all_subs=False):
    all_servers = utils.read_as_json(SERVER_CONFIG)
    if all_subs:
        all_servers = dict()
    else:
        all_servers.pop(name, None)
    utils.write_to_json(all_servers, SERVER_CONFIG)


def get_node(index, name=DEFAULT_SUBSCRIBE):
    all_servers = utils.read_as_json(SERVER_CONFIG)
    try:
        run_server = all_servers[name]
    except KeyError:
        click.echo("No subscribe named %s found!" % name)
        sys.exit(1)
    try:
        node = run_server[index]
    except TypeError:
        click.echo("Error index of subscribe %s!" % name)
        sys.exit(1)
    return node