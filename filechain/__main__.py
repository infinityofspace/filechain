"""
Main entry point for the CLI of the filechain. It parses the arguments and starts a server or client.
"""

import argparse

from filechain.client.client import FilechainClient
from filechain.server.server import FilechainServer

parser = argparse.ArgumentParser(
    description="filechain - files in a blockchain network",
    formatter_class=argparse.RawDescriptionHelpFormatter
)

subparsers = parser.add_subparsers(help="Use the server to host a filechain server of client to connect to a server.")

parser_server = subparsers.add_parser("server", help="Start a filechain server.")
parser_server.set_defaults(func=FilechainServer.start)
parser_server.add_argument("host", help="Hostname where to bind the server.")
parser_server.add_argument("port",
                           help="Port where to bind the server. If not specified the OS will choose a free port.",
                           type=int)
parser_server.add_argument("--join",
                           metavar=("host", "port"),
                           help="Hostname and port of the server which will be used to joint the filechain network.",
                           nargs=2,
                           dest="register_node_addr")
parser_server.add_argument("-c", "--connections", help="Max number of concurrent connections.", type=int, default=20)

parser_client = subparsers.add_parser("client", help="Use the filechain client to connect to a server.",
                                      formatter_class=argparse.RawTextHelpFormatter)
parser_client.add_argument("host", help="Hostname of the server.")
parser_client.add_argument("port", help="Port of the server.", type=int)

client_subparsers = parser_client.add_subparsers(help="Client methods")

parser_client_send = client_subparsers.add_parser("send",
                                                  help="Send a file to the server and insert the file into "
                                                       "the blockchain.")
parser_client_send.set_defaults(func=FilechainClient.send_file)
parser_client_send.add_argument("file_path", help="Path of the file to be sent to the server.")

parser_client_get = client_subparsers.add_parser("get",
                                                 help="Get a file from the blockchain and save it to local file.")
parser_client_get.set_defaults(func=FilechainClient.get_file)
parser_client_get.add_argument("file_hash", help="Hash of the file to get from the server.")
parser_client_get.add_argument("file_path", help="Path where the file should be saved.")

parser_client_check = client_subparsers.add_parser("check", help="Check if a file is in the blockchain.")
parser_client_check.set_defaults(func=FilechainClient.check_file)
parser_client_check.add_argument("file_path", help="Path of the file to be checked on the server.")
parser_client_check.add_argument("--hash", help="Hash of the file to be checked on the server.", type=str,
                                 nargs=1)

args = parser.parse_args()

if not hasattr(args, "func"):
    raise argparse.ArgumentError(None, "No method specified. Please provide a supported method and try again.")

if FilechainServer.__qualname__ in args.func.__qualname__:
    server = FilechainServer(args.host, args.port, args.connections)

    # parse the register_node_addr argument
    if args.register_node_addr:
        args.register_node_addr = (args.register_node_addr[0], int(args.register_node_addr[1]))

    args.func(server, **vars(args))
else:
    client = FilechainClient(args.host, args.port)

    args.func(client, **vars(args))

if __name__ == "__main__":
    pass
