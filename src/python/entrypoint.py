#!/usr/bin/env python

import os
import sys
from pathlib import Path
from warnings import warn
import docker
import psutil

DOCK_SOCK = "unix://var/run/docker.sock"
# Max interfaces stated by output of `mdns-repeater -h`
MAX_INTERFACES = 5


def get_host_interfaces() -> list[str]:
    return list(psutil.net_if_addrs().keys())


def validate_interfaces(interfaces: set[str]) -> set[str]:
    valid_interfaces = set()
    host_interfaces = get_host_interfaces()

    for if_name in interfaces:
        if if_name not in host_interfaces:
            warn(f"Interface {if_name} not found on host")
        else:
            valid_interfaces.add(if_name)

    return valid_interfaces


"""Find the Docker network by name

Given a network name and a list of Docker networks, this function checks
whether the network exists within the list. If it does, the corresponding 
Docker network object is returned. Otherwise, a warning is raised, and 
None is returned.
"""


def get_docker_network_by_name(net_name: str, networks):
    for network in networks:
        if network.name == net_name:
            return network
    return None


def resolve_docker_networks(network_names: set[str]) -> set[str]:
    interfaces = set()

    # Initialize Docker client
    client = docker.DockerClient(base_url=DOCK_SOCK)

    # Retrieve all Docker networks
    docker_networks = client.networks.list()

    # Check if no networks were found
    if len(docker_networks) == 0:
        sys.exit("Docker API: No networks found.")

    for name in network_names:
        # Find the Docker network object by name
        network = get_docker_network_by_name(name, docker_networks)

        if network is not None:
            # Add the corresponding bridge interface to the set
            interfaces.add(f"br-{network.short_id}")
        else:
            warn(f"{name} not found via Docker API")

    return interfaces


def main():
    docker_networks = os.getenv("MDRD_DOCKER_NETWORKS")
    host_interfaces = os.getenv("MDRD_HOST_INTERFACES")

    if host_interfaces is not None:
        host_interfaces = validate_interfaces(set(host_interfaces.split()))

    if docker_networks is not None:
        if not Path(DOCK_SOCK).exists():
            sys.exit(f"Docker socket not mounted at {DOCK_SOCK}")

        docker_interfaces = resolve_docker_networks(set(docker_networks.split()))

        if host_interfaces is not None:
            if not host_interfaces.isdisjoint(docker_interfaces):
                warn((
                    'One or more Docker networks have resolved to an interface '
                    'already provided as a host interface. Check your config!'
                ))
    
            host_interfaces.update(docker_interfaces)

    if host_interfaces is None:
        sys.exit('No valid interfaces provided')
    
    if len(host_interfaces) > MAX_INTERFACES:
        sys.exit(f"Interfaces provided exceeds maximum of {MAX_INTERFACES} interfaces")

    # Everything parsed and validated, LETS GO (ノಠ益ಠ)ノ彡┻━┻
    os.execvp('mdns-repeater', list(host_interfaces))


if __name__ == "__main__":
    main()
