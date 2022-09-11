import argparse
import sys
import yaml

from prettytable import PrettyTable
from pydactyl import PterodactylClient

__version__ = '1.0.2'

parser = argparse.ArgumentParser(prog='PteroNode',
                                 description='Manage your Pterodactyl '
                                             'allocations with ease.')
parser.add_argument('--cacaw', action='store_true', help='CACAW')
parser.add_argument('--api_key',
                    help='Pterodactyl Application API key')
parser.add_argument('--panel',
                    help='URL to Pterodactyl Panel, e.g. https://panel.test.com')
parser.add_argument('--config', default=".pteronode.yaml",
                    help='Specify a file path to a YAML file with panel '
                         'credentials')
parser.add_argument('--no_dry_run', action='store_true',
                    help='Will not make any changes when set to False')
parser.add_argument('--list_nodes', action='store_true',
                    help='Print a list of nodes and their IDs.')
parser.add_argument('--list_ips', action='store_true',
                    help='Print a list of IPs.')
parser.add_argument('--nodes',
                    help='Comma separated list of Pterodactyl Node IDs to '
                         'create allocations on')
parser.add_argument('--allocations',
                    help='List of allocation ranges to add to each node '
                         'listed e.g. \'7777-7800,9443,25565-25585\'')
parser.add_argument('--action', choices=('add', 'delete'), default='add',
                    help='Whether to add or delete the allocations')
parser.add_argument('--ip_addrs', default=None,
                    help=('Comma separated list of IP addresses for the '
                          'allocations.  Ports will only be added on IPs that '
                          'appear in this list.  If not specified ports will '
                          'be added to every IP on the node.'))
parser.add_argument('--version', action='version',
                    version='%(prog)s ' + __version__)

args = parser.parse_args()

CACAW = """
                           <\              _
                            \\          _/{
                     _       \\       _-   -_
                   /{        / `\   _-     - -_
                 _~  =      ( @  \ -        -  -_
               _- -   ~-_   \( =\ \           -  -_
             _~  -       ~_ | 1 :\ \      _-~-_ -  -_
           _-   -          ~  |V: \ \  _-~     ~-_-  -_
        _-~   -            /  | :  \ \            ~-_- -_
     _-~    -   _.._      {   | : _-``               ~- _-_
  _-~   -__..--~    ~-_  {   : \:}
=~__.--~~              ~-_\  :  /
                           \ : /__
                          //`Y'--\\
                         <+       \\
                          \\      WWW

"""


def get_nodes(api):
    response = api.nodes.list_nodes(include='location,allocations')
    nodes = []
    for page in response:
        for node in page.data:
            nodes.append(node['attributes'])
    return nodes


def list_nodes(api):
    nodes = get_nodes(api)
    table = PrettyTable(['ID', 'Name', 'FQDN', 'Location', 'Memory',
                         'Allocated Memory', 'Disk', 'Allocated Disk',
                         'Total Allocations', 'Used Allocations'])

    for node in nodes:
        location = node['relationships']['location']
        if location:
            location = location['attributes']['short']
        else:
            print('No location data found.  Check your API key permissions.')
        allocs = node['relationships']['allocations']['data']
        total_allocs = len(allocs)
        used_allocs = len([a for a in allocs if a['attributes']['assigned']])

        table.add_row([node['id'], node['name'], node['fqdn'],
                       location, node['memory'],
                       node['allocated_resources']['memory'],
                       node['disk'], node['allocated_resources'][
                           'disk'], total_allocs, used_allocs])
    print(table)
    sys.exit(0)


def list_ips(api):
    table = PrettyTable(['Node ID', 'FQDN', 'IP Address', 'IP Alias',
                         'Total Allocations', 'Used Allocations'])

    nodes = get_nodes(api)
    ips = map_ips_from_nodes(nodes)
    for ip, data in ips.items():
        table.add_row(
            [data['node_id'], data['node_fqdn'], ip, data['alias'],
             data['total_allocs'], data['used_allocs']])
    print(table)
    sys.exit(0)


def map_ips_from_nodes(all_nodes):
    """Creates a mapping of IP address to Node ID and IP Alias.

    {'1.1.1.1': {'node_id': 12, 'alias': '2.2.2.2'},
     '1.2.3.4': {'node_id': 3, 'alias': None}}

    """
    filtered_node_ips = {}
    for node in all_nodes:
        node_ips = {}
        for alloc in node['relationships']['allocations']['data']:
            ip = alloc['attributes']['ip']
            alias = alloc['attributes']['alias']
            port = alloc['attributes']['port']
            alloc_id = alloc['attributes']['id']

            if ip not in node_ips:
                node_ips[ip] = {'node_id': node['id'],
                                'node_fqdn': node['fqdn'], 'alias': alias,
                                'total_allocs': 0, 'used_allocs': 0,
                                'ports': {}}

            if alloc['attributes']['assigned']:
                node_ips[ip]['used_allocs'] += 1
            node_ips[ip]['total_allocs'] += 1
            node_ips[ip]['ports'][port] = alloc_id
        filtered_node_ips.update(node_ips)
    return filtered_node_ips


def modify_allocations(api, nodes_str, ips_str, allocs_str, action, dry_run):
    all_nodes = get_nodes(api)
    node_ips = map_ips_from_nodes(all_nodes)
    allocs = allocs_str.split(',')

    filtered_nodes = []
    if nodes_str:
        nodes_filter = nodes_str.split(',')
        for node in nodes_filter:
            filtered_nodes.extend([n for n in all_nodes if int(n['id']) ==
                                   int(node)])
    else:
        filtered_nodes = all_nodes

    filtered_node_ids = [n['id'] for n in filtered_nodes]
    filtered_ips = []
    if ips_str:
        for ip in ips_str.split(','):
            filtered_ips.extend(
                [k for k, v in node_ips.items() if (k == ip and v['node_id'] in
                                                    filtered_node_ids)])
    else:
        filtered_ips = [k for k, v in node_ips.items() if v['node_id'] in
                        filtered_node_ids]

    table = PrettyTable(
        ['Node ID', 'Node FQDN', 'IP Address', 'IP Alias', 'Allocations'])
    for ip in filtered_ips:
        table.add_row([node_ips[ip]['node_id'], node_ips[ip]['node_fqdn'], ip,
                       node_ips[ip]['alias'], allocs])

    if dry_run:
        print('PteroNode wants to {} the following allocations:'.format(action))
        print(table)
        print('Run again with --no_dry_run to take this action.')
    else:
        print('PteroNode is now modifying the following allocations:')
        print(table)
        if action == 'add':
            for ip in filtered_ips:
                api.nodes.create_allocations(
                    node_ips[ip]['node_id'], ip, allocs, node_ips[ip]['alias'])
        if action == 'delete':
            print('Note: Deleting large number of allocations can cause rate '
                  'limiting issues')
            for ip in filtered_ips:
                for port in allocs:
                    alloc_id = node_ips[ip]['ports'][int(port)]
                    api.nodes.delete_allocation(
                        node_ips[ip]['node_id'], alloc_id)

        print('Done!  CACAW!')


def main(args):
    if args.cacaw:
        print(CACAW)
    try:
        with open(args.config) as f:
            config = yaml.load(f, yaml.Loader)
            url = config['panel']
            key = config['api-key']
    except FileNotFoundError:
        if not args.panel or not args.api_key:
            sys.exit('Could not read credentials from config file and the '
                     '--panel or --api_key flags were missing.')
        url = args.panel
        key = args.api_key

    api = PterodactylClient(url, key)

    if args.list_nodes:
        list_nodes(api)
    if args.list_ips:
        list_ips(api)
    if args.allocations:
        modify_allocations(api, args.nodes, args.ip_addrs, args.allocations,
                           args.action, not args.no_dry_run)


if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
