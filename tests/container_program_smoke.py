"""Run inside the actual Bridge container on an internal-only Docker network."""

import asyncio
import os
import platform
from urllib.parse import urlencode

from aiohttp import ClientSession

ACK = b"Start\r\nOK\r\nDone\r\n"
DEVICE = "1234567890ABCDEF"
API = "http://127.0.0.1:8642/api/"
CLOUD = os.environ["SMOKE_CLOUD"]


async def main():
    async with ClientSession() as client:
        for _ in range(50):
            try:
                async with client.get(API + "health") as response:
                    if response.status == 200:
                        break
            except OSError:
                pass
            await asyncio.sleep(.2)
        else:
            raise AssertionError("Bridge did not become healthy")

        async def mode(value):
            async with client.post(CLOUD + "/mode", json={"mode": value}) as response:
                assert response.status == 200

        async def poll(screen, flags="ph", indicator="000", kind="bm_stat"):
            fields = ["0", "12:00", "C", screen, "420", "42", "0", "0", "4", "0",
                      "0", "0", "0", "000", flags, indicator, "0", "0", "0"]
            value = "FW;" + DEVICE + ";1000;" + "X".join(fields) + ";0;0"
            if kind == "rz":
                value = "FW;" + DEVICE + ";1;4\r\n0X1\r\n1X1\r\n2X1\r\n3X1;0;0"
            async with client.post("http://127.0.0.1:8080/braumeister/connect",
                                   data=urlencode({kind: value}),
                                   headers={"Content-Type": "application/x-www-form-urlencoded", "Host": "cloud.invalid"}) as response:
                return response.status, await response.read()

        async def queue(action, expected=202):
            async with client.post(API + "control", json={"device_id": DEVICE, "action": action}) as response:
                assert response.status == expected, (action, response.status, await response.text())

        async def outcome():
            async with client.get(API + "control") as response:
                return (await response.json()).get("result")

        if os.environ.get("SMOKE_RESUME_DISABLED") == "1":
            await mode("ack")
            await poll("2300", "ph", "120")
            await queue("resume_program", 403)
            assert await poll("2300", "ph", "120") == (200, ACK)
            assert await outcome() is None
            print("PASS actual container:", platform.machine(), "program resume remains disabled without the new explicit option")
            return

        await mode("gzip")
        assert await poll("101") == (200, b"\x00\xffSYNTHETIC\r\n")
        await mode("ack")
        assert await poll("101", kind="rz") == (200, ACK)
        transitions = [
            ("select_recipe", "2015", "ph", "000", "2030", "ph", "000", 4),
            ("request_program_pause", "2300", "Ph", "000", "2300", "ph", "120", 1),
            ("resume_program", "2300", "ph", "120", "2300", "Ph", "000", 4),
            ("request_program_pause", "2410", "PH", "000", "2410", "ph", "120", 1),
            ("abort_program", "2410", "ph", "120", "101", "ph", "000", 1),
        ]
        for action, before, flags, indicator, after, target_flags, target_indicator, key in transitions:
            assert await poll(before, flags, indicator) == (200, ACK)
            await queue(action)
            await mode("command")
            assert await poll(before, flags, indicator) == (200, b"Start\r\n$k=2\r\nOK\r\nDone\r\n")
            assert await outcome() == "queued"
            await mode("ack")
            assert await poll(before, flags, indicator) == (200, f"Start\r\n$k={key}\r\nOK\r\nDone\r\n".encode())
            assert await outcome() == "sent"
            assert await poll(before, flags, indicator) == (200, ACK)
            assert await outcome() == "sent"
            assert await poll(after, target_flags, target_indicator) == (200, ACK)
            assert await outcome() == "confirmed"
        await poll("2410", "ph", "120")
        await queue("resume_program", 409)
        await poll("2030")
        await queue("confirm_water_filled", 400)
        await queue("start_delay_up", 400)
        # Malformed acknowledgement isolates cloud failure from local dispatch.
        await mode("bad-encoding")
        assert await poll("101") == (200, ACK)
        async with client.get(API + "status") as response:
            assert (await response.json())["devices"][0]["last_response_source"] == "local"
        assert os.path.exists("/data/recipes.json")
        print("PASS actual container:", platform.machine(), "startup/options, binary gzip forwarding, exact program transitions, cloud priority, no duplicate keys, unsupported actions, fallback distinction, recipe persistence")


if __name__ == "__main__":
    asyncio.run(main())
