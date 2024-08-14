#!/usr/bin/env python

import os, sys
from typing import List, Set, Optional
from warnings import warn

import psutil
import docker
from docker.models.networks import Network


DOCKER_SOCK = "/var/run/docker.sock"
# Max interfaces stated by output of `mdns-repeater -h`
MAX_INTERFACES = 5

ENV_VAR_HOST_IFS = "MDNSD_HOST_INTERFACES"
ENV_VAR_DOCKER_NETS = "MDNSD_DOCKER_NETWORKS"


def get_host_ifnames() -> List[str]:
    """Returns a List of host interface names"""
    return list(psutil.net_if_addrs().keys())


def validate_ifnames(interfaces: Set[str]) -> Set[str]:
    """Takes a Set of host interface names and returns only the valid ones"""
    valid_interfaces = set()
    host_interfaces = get_host_ifnames()

    for if_name in interfaces:
        if if_name not in host_interfaces:
            warn(f"Interface {if_name} not found on host!\n")
        else:
            valid_interfaces.add(if_name)

    return valid_interfaces


import os


def get_docker_network_by_name(
    net_name: str, networks: List[Network]
) -> Optional[Network]:
    """Retrieve a Docker network by name"""
    for network in networks:
        if network.name == net_name:
            return network
    return None


def resolve_docker_networks(network_names: Set[str]) -> Set[str]:
    """Resolve Docker networks to host interface names"""
    interfaces = set()

    # Initialize Docker client
    client = docker.DockerClient(base_url=f"unix:/{DOCKER_SOCK}")

    # Retrieve all Docker networks
    docker_networks = client.networks.list()

    # Check if no networks were found
    if len(docker_networks) == 0:
        sys.exit("Docker API: No networks found!")

    for name in network_names:
        # Find the Docker network object by name
        network = get_docker_network_by_name(name, docker_networks)

        if isinstance(network, Network):
            mapped_host_if = f"br-{network.short_id}"

            # Log successful match
            print(
                (
                    "Mapping docker network to host interface: "
                    f"{name} -> {mapped_host_if}\n"
                )
            )

            # Add the corresponding bridge interface to the set
            interfaces.add(mapped_host_if)
        else:
            warn(f"{name} not found via Docker API\n")

    return interfaces


def main():
    """Main function to process interfaces and run mdns-repeater."""
    docker_networks = os.environ.get(ENV_VAR_DOCKER_NETS)
    host_interfaces = os.environ.get(ENV_VAR_HOST_IFS)

    if host_interfaces is None:
        warn(
            (
                "No host interfaces provided! You can relay between Docker "
                "networks, but are you sure this is what you want?\n"
            )
        )
        host_interfaces = set()
    else:
        host_interfaces = set(host_interfaces.split())

    if docker_networks is not None:
        if not os.path.exists(DOCKER_SOCK):
            sys.exit(f"Docker socket not mounted at {DOCKER_SOCK}")

        docker_interfaces = resolve_docker_networks(set(docker_networks.split()))

        if not host_interfaces.isdisjoint(docker_interfaces):
            warn(
                (
                    "One or more Docker networks have resolved to an "
                    "interface already provided as a host interface. "
                    "Duplicates will be removed.\n"
                )
            )

        host_interfaces.update(docker_interfaces)
    else:
        warn("No Docker networks provided\n")

    if len(host_interfaces) < 1:
        sys.exit("No valid interfaces provided")

    if len(host_interfaces) > MAX_INTERFACES:
        sys.exit(f"Interfaces provided exceeds maximum of {MAX_INTERFACES} interfaces")

    # Validate that all provided and parsed interfaces actually exist on the host
    print("Validating all interface names\n")
    host_interfaces = validate_ifnames(host_interfaces)

    # Run mdns-repeater in foreground, with any provided cmd args,
    # appended w/ list of host interfaces. os.execvp requires
    # executable to be provided as args[0]
    run_args = ["mdns-repeater", "-f"] + sys.argv[1:] + list(host_interfaces)

    # Everything parsed and validated, let's go!
    print(f"Repeating mDNS traffic across the following interfaces:")
    print(host_interfaces)
    print("\nReady. To. REPEAT! (ノಠ益ಠ)ノ彡┻━┻\n")

    os.execvp("mdns-repeater", run_args)


if __name__ == "__main__":
    main()
