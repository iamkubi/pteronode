# pteronode
Script for managing Pterodactyl nodes

Pteronode allows you to create sets of allocations on one, many, or all of 
your IPs and Nodes with a simple command.

## HELP
Run `python pteronode.py --help` for help.  You can find us on Discord too 
at https://discord.gg/q4AeCxgs.

## Installing
Right now you need to clone this repo and install the dependencies and run 
it using Python.

### From source
```shell
git clone https://github.com/iamkubi/pteronode
cd pteronode
pip install -r requirements.txt
python pteronode.py --help
```

### Pre-built
Pre-built executables are available for Linux and Windows on the Release 
pages.  You can use these without any dependencies.

#### Linux
```shell
wget -q https://github.com/iamkubi/pteronode/releases/download/1.0.2/pteronode && chmod u+x ./pteronode
./pteronode --version
# PteroNode 1.0.2
```

#### Windows
```shell
Invoke-WebRequest -Uri https://github.com/iamkubi/pteronode/releases/download/1.0.2/pteronode.exe -OutFile pteronode.exe
.\pteronode.exe --version
# PteroNode 1.0.2
```

## Credentials
There are two ways to specify your panel credentials.  The easiest option is 
to specify a config file.  By default Pteronode will look for a
`.pteronode.yml` file in the current path.  A valid config file looks like 
this:

```shell
> cat .pteronode.yaml
panel: https://panel.test.com
api-key: your-application-api-key-here
```

Alternatively you can use the `--panel` and `--api_key` flags to specify 
them on the command line.

```shell
python pteronode.py --api_key 1234 --panel https://test.com --list_nodes
```

## --list_nodes
This flag allows you to get a quick glance at all of the nodes on your panel.
Especially useful for getting Node IDs to for when you want to add allocations.

```
> python pteronode.py --list_nodes
+----+-------+----------------+----------+--------+------------------+--------+----------------+-------------------+------------------+
| ID |  Name |      FQDN      | Location | Memory | Allocated Memory |  Disk  | Allocated Disk | Total Allocations | Used Allocations |
+----+-------+----------------+----------+--------+------------------+--------+----------------+-------------------+------------------+
| 1  | test1 | test1.test.com |   PDX1   | 62000  |      58000       | 200000 |     163000     |        111        |        23        |
| 2  | test2 | test2.test.com |   US-E   | 63000  |        0         | 350000 |       0        |        101        |        1         |
+----+-------+----------------+----------+--------+------------------+--------+----------------+-------------------+------------------+
```

## --allocations

Great, so I know my node IDs, now let's make some allocations.  By default 
it will create the same set of allocations on every IP on every node on your 
panel.

```
> python pteronode.py --allocations=7777-7800,25565-25665,27015
PteroNode wants to add the following allocations:
+---------+--------------+----------------+---------------------------------------+
| Node ID |  IP Address  |    IP Alias    |              Allocations              |
+---------+--------------+----------------+---------------------------------------+
|    1    | 10.10.10.10  | 123.234.45.678 | ['7777-7800', '25565-25665', '27015'] |
|    2    | 12.34.45.111 |      None      | ['7777-7800', '25565-25665', '27015'] |
+---------+--------------+----------------+---------------------------------------+
Run again with --no_dry_run to take this action.
```

By default, this didn't do anything, it just prints out a table showing you 
what it would create.  Run the same command again with `--no_dry_run` to 
execute the above.

```
> python pteronode.py --allocations=7777-7800,25565-25665,27015 --no_dry_run
PteroNode wants to add the following allocations:
+---------+--------------+----------------+---------------------------------------+
| Node ID |  IP Address  |    IP Alias    |              Allocations              |
+---------+--------------+----------------+---------------------------------------+
|    1    | 10.10.10.10  | 123.234.45.678 | ['7777-7800', '25565-25665', '27015'] |
|    2    | 12.34.45.111 |      None      | ['7777-7800', '25565-25665', '27015'] |
+---------+--------------+----------------+---------------------------------------+
Done!  CACAW!
```

And that's it, it did it!  Specifying any allocations that already exist 
will not cause an error. Those ports will be ignored, and it will create any 
ports from those ranges that do not exist.

## Deleting Allocations

This works similar to the way that adding allocations works, although 
currently it only supports a comma separated list of ports and does not 
support ranges.

```shell
python pteronode.py --allocations=27015,27016,27017,27018 --action=delete
```

## Other flags
There's some more stuff you can do with filters.  You can use `--nodes` to 
specify a list of node IDs so that it will only add allocations on those nodes.

```shell
python pteronode.py --allocations=1234 --nodes=1,2,4
```

You can filter by IP addresses too.

```shell
python pteronode.py --allocations=1234 --ip_addrs=1.1.1.1,8.8.8.8
```

You can combine them too.

```shell
python pteronode.py --allocations=1234 --ip_addrs=1.1.1.1,8.8.8.8 --nodes=1
```

