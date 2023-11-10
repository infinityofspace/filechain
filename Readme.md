# Filechain

## About

The project is a simple implementation of a blockchain using sockets, which uses files as block content.
Files can be inserted into and downloaded from the blockchain. It is also possible to check whether the file is in the
blockchain.

Note: The project is a sample implementation of a blockchain with files and is not intended for productive use.

## Installation

Clone the repository:

```commandline
git clone https://github.com/infinityofspace/filechain.git
```

The code requires `Python 3.6+`.

No other requirements or dependencies are needed.

## Usage

All commands have to be executed in the root folder of the project (where this Readme.md file is located).

The module can be used with a structured CLI. There are two different modes: `server` and `client`

### Server

Start the first server with an empty blockchain on `localhost` and port `1230`:

```commandline
python3 -m filechain server localhost 1230
```

Start another server on `localhost` and port `1240` that uses another server to sync the previous filechain (in this
case the other server is our server previously started as first server on `localhost` and port `1230`):

```commandline
python3 -m filechain server localhost 1240 --join localhost 1230
```

Each server notifies other servers known to it if new blocks are added to its own filechain. There is no "root" server,
which manages connections to other servers. Instead, the network of servers is decentralized and changes are propagated
by each server. A detailed description of the protocol can be found in the [Protocol](#protocol) section.

### Client

Send a local file to the server on `localhost` and port `1230` and insert the file into the filechain:

```commandline
python3 -m filechain client localhost 1230 send <path-to-local-file>
```

Get a file from the server on `localhost` and port `1230` by its sha256 hash and save it as a local file:

```commandline
python3 -m filechain client localhost 1230 get <sha256-hash-of-the-file> <path-to-save-the-file>
```

Check if a file exists in the filechain instance on the server on `localhost` and port `1230`:

```commandline
python3 -m filechain client localhost 1230 check <path-to-local-file>
```

The resulting message indicates with "True" or "False" if the file exists in the filechain instance.

### Usage Examples

You can find multiple usage scenarios and all required commands in the following:

#### Upload a file / insert a file into the filechain

First start two filechain server (or more if you want):

`Server 1`:

```commandline
python3 -m filechain server localhost 1240
```

`Server 2`:

```commandline
python3 -m filechain server localhost 1230 --join localhost 1240
```

Now send the sample `test.txt` file to the server and insert the file into the filechain:

```commandline
python3 -m filechain client localhost 1230 send test.txt
```

The successful sending should be indicated by a corresponding message.

#### Check file in filechain

Use the commands from "Upload a file / insert a file into the filechain" section to start a few server and upload
the `text.txt` file.

Now check if the file `test.txt` is in the blockchain instance of `Server 1`:

```commandline
python3 -m filechain client localhost 1230 check test.txt
```

Also check if the file `test.txt` is in the blockchain instance of `Server 2`:

```commandline
python3 -m filechain client localhost 1240 check test.txt
```

Both commands should return "True", because server in the network notify each other about new blocks.

---

Now check if the not inserted file `test2.txt` is in the filechain instance of `Server 1`:

```commandline
python3 -m filechain client localhost 1230 check test2.txt
```

This command should return "False".

#### Get file from the filechain

Use the commands from "Upload a file / insert a file into the filechain" section to start a few server and upload
the `text.txt` file.

Now get the previous inserted file `text.txt` (sha256
hash: `079de97efaa875ef3e72d8063309e554d62df3171978bee8df0ed60989fba1a6`)
from `Server 2` and save it to file `downloaded_file.txt`:

```commandline
python3 -m filechain client localhost 1230 get 079de97efaa875ef3e72d8063309e554d62df3171978bee8df0ed60989fba1a6 downloaded_file.txt
```

(The sha256 hash value of test2.txt is `f1c71b00f2e82e16a90aa4e9ae5e3d7c535d13dfacc46be03fe2bbe20c4a3172`)

## Protocol

The protocol for the exchange of data between server and client or server and server is defined as follows:

After the socket connection is established, the first thing that is sent is the command to be used. This can be one of
these command:

- `INSERT_FILE_CMD`: insert new blocks
- `CONTAINS_FILE_CMD`: check if a file is in the filechain by its sha256 hash
- `GET_FILE_CMD`: get all blocks for a file specified by its sha256 hash
- `NEW_BLOCKS_AVAILABLE_CMD`: notify another server about new blocks in its own blockchain
- `GET_BLOCK_CMD`: get a block by its block hash
- `REGISTER_SERVER_CMD`: get the known server addresses and get the current filechain

After the server command is sent and the server command is supported, the server will respond with an `OK`.

Afterwards, the data is exchanged accordingly via the socket.

At the end the socket is closed from both sides

(The listed commands and response values are only strings, the exact strings can be seen in the class `FilechainServer`
.)

## Data Structure

The chain is internal represented as a dict (the class variable `__chain` of the Blockchain class) with the block hash
as the key and the block as the value. This data structure allows O(1) access by the block hash which is frequently used
when keeping the blockchain synced between server in the network. Representing the blockchain as a list would be behind
a dict at runtime for searching a specific block with O(n).

In addition to the chain dict, there is another internal data structure (the class variable `__files` of the Blockchain
class) that speeds up the check for a file and the receiving all blocks of a file in the blockchain. This variable is a
double nested dict and at the end a list. The first dict has the sha256 file hash as key and the second dict as value.
The second dict contains the content hash of the blocks with the corresponding sha256 file hash. Finally, the list
contains all block hashes of the blocks with the sha256 file hash and the content hash. If a block of the same file is
to be added to the blockchain, then the block hash is appended to the end of this list.

Note: The time complexity of python data structures are listed [here](https://wiki.python.org/moin/TimeComplexity)

A `Block` in the blockchain consists of the following attributes:

- `previous_block_hash`: sha256 hash of the previous block in the blockchain
- `block_hash`: sha256 hash of this block consists of: file_hash | index_all | chunk | index | previous_block_hash
- `file_hash`: sha256 hash of the file to which this block belongs
- `index_all`: total number of blocks for this file
- `index`: block index to determine the order of the chunk data of the file
- `chunk`: 500 byte data of the file
- `content_hash`: sha256 hash of the content of this block consists of: file_hash | index_all | chunk | index

## Pylint adjustments

The following list contains all changes of the rules and a short explanation for this step:

- The max line length was increased from 100 to 120, because the default length is too small and will be reached most of
  the time. Also, the development environment I normally use also uses the value 120, so I am used to this value.

## License

This project is licensed under the MIT License - see the [License](License) file for details.