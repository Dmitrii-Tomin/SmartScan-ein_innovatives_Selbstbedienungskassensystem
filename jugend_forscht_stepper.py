from smbus import SMBus

addr = 0x8 # bus address
bus = SMBus(1) # indicates /dev/ic2-1

def move_stepper(speed):

    if speed == 0:
        bus.write_byte(addr, 0x0) # switch it on
    elif speed == 1:
        bus.write_byte(addr, 0x1) # switch it on
    elif speed == 2:
        bus.write_byte(addr, 0x2) # switch it on
    elif speed == 3:
        bus.write_byte(addr, 0x3) # switch it on
