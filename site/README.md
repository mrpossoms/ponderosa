# ponderosa / site

This component houses the publicly facing site and web-app. The subdirectory `root` is a stand in for `/` and is designed to  map directly onto a Linux server's directory tree.

## Requirements
* [nginx](https://nginx.org/)
* [GNU make](https://www.gnu.org/software/make/)
* Python (for local dev)

## Usage
For convenience, a Makefile is provided to automate some common tasks for example in a terminal, you can run:

* `make serve` to start a python webserver to test local changes on your own machine.
* `make install` while sshed into a remote webserver with the repo cloned to install the web-app on the server.
