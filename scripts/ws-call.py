#!/usr/bin/env python3
import sys, json, asyncio
import websockets

USAGE = """
Usage:
  python scripts/ws-call.py initialize
  python scripts/ws-call.py tools/list
  python scripts/ws-call.py tools/call '<json-params>'

Examples:
  python scripts/ws-call.py initialize
  python scripts/ws-call.py tools/list
  python scripts/ws-call.py tools/call '{"name":"list_integrations","arguments":{"limit":1}}'
  python scripts/ws-call.py tools/call '{"name":"list_integrations_search","arguments":{"terms":["order","customer"],"perPage":100,"maxPages":30}}'
"""

HOST = "ws://127.0.0.1:8080/ws"

async def main():
	if len(sys.argv) < 2:
		print(USAGE)
		sys.exit(1)
	method = sys.argv[1]
	params = {}
	if method == "tools/call":
		if len(sys.argv) < 3:
			print(USAGE)
			sys.exit(1)
		params = json.loads(sys.argv[2])
	elif method == "initialize":
		params = {}
	elif method == "tools/list":
		params = {}
	else:
		print(USAGE)
		sys.exit(1)

	async with websockets.connect(HOST, max_size=None) as ws:
		payload = {"jsonrpc":"2.0","id":1,"method":method,"params":params}
		await ws.send(json.dumps(payload))
		print(await ws.recv())

if __name__ == "__main__":
	asyncio.run(main()) 