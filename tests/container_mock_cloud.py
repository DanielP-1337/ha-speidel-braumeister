"""Synthetic-only peer for container smoke testing; never contacts a real cloud."""

import gzip

from aiohttp import web

MODE = "ack"


async def set_mode(request):
    global MODE
    MODE = (await request.json())["mode"]
    return web.json_response({"ok": True})


async def reply(request):
    await request.read()
    if MODE == "gzip":
        return web.Response(body=gzip.compress(b"\x00\xffSYNTHETIC\r\n"), headers={"Content-Encoding": "gzip"})
    if MODE == "bad-encoding":
        return web.Response(body=b"invalid", headers={"Content-Encoding": "unsupported-test"})
    if MODE == "command":
        return web.Response(body=b"Start\r\n$k=2\r\nOK\r\nDone\r\n")
    return web.Response(body=b"Start\r\nOK\r\nDone\r\n")


if __name__ == "__main__":
    app = web.Application()
    app.router.add_post("/mode", set_mode)
    app.router.add_route("*", "/braumeister/connect", reply)
    web.run_app(app, host="0.0.0.0", port=18080)
