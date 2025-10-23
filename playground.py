import asyncio, evdev

def main():
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        if device.phys == "usb-0000:01:00.0-1.1/input0" and \
           device.name == "GAOMON Gaomon Tablet Pen":
            pen1 = evdev.InputDevice(device.path)
            print("pen-1-1 ", pen1)
            pen1.grab()
        elif device.phys == "usb-0000:01:00.0-1.1/input0" and \
             device.name == "GAOMON Gaomon Tablet Pad":
            pad1 = evdev.InputDevice(device.path)
            print("pad-1-1 ", pad1)
            pad1.grab()
	
    async def print_events(device):
        async for event in device.async_read_loop():
            print(event.code, event.type, event.value, evdev.categorize(event))

            
    for device in pen1, pad1:
        asyncio.ensure_future(print_events(device))
    loop = asyncio.get_event_loop()
    loop.run_forever()
    
if __name__ == "__main__":
    main()
