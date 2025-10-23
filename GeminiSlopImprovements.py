import asyncio
import evdev

# The path to the HID gadget device
HID_DEVICE = '/dev/hidg0'

def change_report(report_arr, device_id, event_code, event_value):
    """
    Updates the report bytearray based on an event.
    This is mostly your original logic, but cleaned up slightly.
    """
    # Determine if this is the left (0) or right (1) tablet
    tablet_index = 0 if device_id == 'left' else 1
    
    # --- AXIS EVENTS ---
    if event_code == evdev.ecodes.ABS_X:
        # Map tablet X range (e.g., 0-33020) to joystick 16-bit range (0-65535)
        val = round(event_value * 65535 / 33020)
        report_arr[2 + tablet_index*6], report_arr[3 + tablet_index*6] = val.to_bytes(2, 'little')
    elif event_code == evdev.ecodes.ABS_Y:
        # Map tablet Y range (e.g., 0-20320) to joystick 16-bit range (0-65535)
        val = round(event_value * 65535 / 20320)
        report_arr[4 + tablet_index*6], report_arr[5 + tablet_index*6] = val.to_bytes(2, 'little')
    
    # --- BUTTON EVENTS ---
    # We use a mapping to make this cleaner. (button_code: bit_position)
    # Left tablet buttons use bits 0-7, Right tablet uses bits 8-15
    button_map = {
        256: 0,  # Pad 1
        257: 1,  # Pad 2
        258: 2,  # Pad 3
        259: 3,  # Pad 4
        331: 4,  # Pen Stylus 1
        332: 5,  # Pen Stylus 2
        320: 6,  # Pen In-Range
        330: 7,  # Pen Touch
    }
    
    if event_code in button_map:
        bit_pos = button_map[event_code] + (tablet_index * 8)
        button_byte_index = bit_pos // 8
        bit_in_byte = bit_pos % 8

        if event_value == 1: # Key down
            report_arr[button_byte_index] |= (1 << bit_in_byte)
        elif event_value == 0: # Key up
            report_arr[button_byte_index] &= ~(1 << bit_in_byte)

    return report_arr


async def event_reader(device, device_id, queue):
    """PRODUCER: Reads events from a device and puts them in the queue."""
    try:
        async for event in device.async_read_loop():
            # We only care about absolute axis and key events
            if event.type in (evdev.ecodes.EV_ABS, evdev.ecodes.EV_KEY):
                await queue.put((device_id, event.code, event.value))
    except Exception as e:
        print(f"Error reading from {device.name} ({device_id}): {e}")


async def report_sender(hid_file, queue):
    """CONSUMER: Reads events from queue, updates state, and sends reports."""
    # This is the single source of truth for the joystick state.
    # [Buttons Byte 0][Buttons Byte 1][LX L][LX H][LY L][LY H][LZ L][LZ H] [RX L]...
    report = bytearray(14)

    while True:
        # Wait for the first event to arrive
        device_id, code, value = await queue.get()

        # Update the report based on this event
        report = change_report(report, device_id, code, value)

        # Process any other events that have already arrived in the queue
        # This prevents sending a separate report for every single event in a burst
        while not queue.empty():
            device_id, code, value = queue.get_nowait()
            report = change_report(report, device_id, code, value)
        
        # Now, send the single, updated report
        try:
            hid_file.write(report)
            hid_file.flush() # Ensure the OS sends the report immediately
        except BlockingIOError:
            # This is normal if the host PC isn't ready to read. Just ignore and continue.
            pass


def main():
    """Main function to find devices and start the loops."""
    # --- Find and Grab Devices ---
    # This part is crucial. The physical paths might change if you plug
    # them into different USB ports. A more robust solution might involve
    # checking serial numbers, but this is fine for a fixed setup.
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    
    pen1, pad1, pen2, pad2 = None, None, None, None
    
    for device in devices:
        # --- NOTE: Adjust these physical paths if needed! ---
        if "usb-0000:01:00.0-1.1/input0" in device.phys:
            if "Pen" in device.name: pen1 = device
            if "Pad" in device.name: pad1 = device
        elif "usb-0000:01:00.0-1.2/input0" in device.phys:
            if "Pen" in device.name: pen2 = device
            if "Pad" in device.name: pad2 = device

    if not all((pen1, pad1, pen2, pad2)):
        print("Error: Not all tablet devices were found. Check physical paths.")
        return

    pen1.grab()
    pad1.grab()
    pen2.grab()
    pad2.grab()
    print("All four tablet devices found and grabbed.")

    # --- Start the async tasks ---
    loop = asyncio.get_event_loop()
    event_queue = asyncio.Queue()

    try:
        # Open the HID device file ONCE and keep it open.
        with open(HID_DEVICE, 'rb+') as hidg:
            # Create tasks for reading from each tablet input
            asyncio.ensure_future(event_reader(pen1, 'left', event_queue))
            asyncio.ensure_future(event_reader(pad1, 'left', event_queue))
            asyncio.ensure_future(event_reader(pen2, 'right', event_queue))
            asyncio.ensure_future(event_reader(pad2, 'right', event_queue))

            # Create the single task for sending reports
            asyncio.ensure_future(report_sender(hidg, event_queue))

            loop.run_forever()

    except KeyboardInterrupt:
        print("Stopping.")
    finally:
        loop.close()


if __name__ == "__main__":
    main()