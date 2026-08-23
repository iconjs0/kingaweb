import ipaddress
import socket


def resolve_public_addresses(hostname: str) -> list[str]:
    try:
        records = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as error:
        raise ValueError("Domain could not be resolved") from error
    addresses = sorted({record[4][0] for record in records})
    if not addresses:
        raise ValueError("Domain did not resolve to an address")
    for address in addresses:
        if not ipaddress.ip_address(address).is_global:
            raise ValueError("Domain resolves to a private or reserved network")
    return addresses
