import asyncio, evdev

def write_report(report):
    with open('/dev/hidg0', 'rb+') as fd:
        fd.write(report)

    
def bv(byv,bir): #byte value, bit number (1-8). Returns bit state (1/0)
    return(byv%(2**(bir))//(2**(bir-1)))
    
def changeReport(rar,LRv,Lpen,Lpad,ecode,evalue):
    #print(ecode, evalue, sep=' ')
    
    if (LRv == Lpad or LRv == Lpen):
        i=0 #left tablet
    else:
        i=1 #right tablet
    if (ecode==0):
        [rar[3+4*i],rar[2+4*i]]=divmod(round(evalue*65535/33020),256)
        #print(rar[3+4*i],rar[2+4*i])
        #print(evalue)
    elif (ecode==1):
        [rar[5+4*i],rar[4+4*i]]=divmod(round(evalue*65535/20320),256)
    elif (ecode==256): #1
        if(evalue==1 and bv(rar[i],1)==0):
            rar[i]+=1
        elif(evalue==0 and bv(rar[i],1)==1):
            rar[i]-=1
    elif (ecode==257): #2
        if(evalue==1 and bv(rar[i],2)==0):
            rar[i]+=2
        elif(evalue==0 and bv(rar[i],2)==1):
            rar[i]-=2
    elif (ecode==258): #3
        if(evalue==1 and bv(rar[i],3)==0):
            rar[i]+=4
        elif(evalue==0 and bv(rar[i],3)==1):
            rar[i]-=4
    elif (ecode==259): #4
        if(evalue==1 and bv(rar[i],4)==0):
            rar[i]+=8
        elif(evalue==0 and bv(rar[i],4)==1):
            rar[i]-=8
    elif (ecode==331): #5
        if(evalue==1 and bv(rar[i],5)==0):
            rar[i]+=16
        elif(evalue==0 and bv(rar[i],5)==1):
            rar[i]-=16
    elif (ecode==332): #6
        if(evalue==1 and bv(rar[i],6)==0):
            rar[i]+=32
        elif(evalue==0 and bv(rar[i],6)==1):
            rar[i]-=32
    elif (ecode==320): #7
        if(evalue==1 and bv(rar[i],7)==0):
            rar[i]+=64
        elif(evalue==0 and bv(rar[i],7)==1):
            rar[i]-=64
    elif (ecode==330): #8
        if(evalue==1 and bv(rar[i],8)==0):
            rar[i]+=128
        elif(evalue==0 and bv(rar[i],8)==1):
            rar[i]-=128
    return rar

#[0][1][2][3][4][5][6][7][8][9][10][11][12][13]
# B  B  X  X  Y  Y  Z  Z  Rx Rx Ry  Ry  Rz  Rz
def main():
    #list devices
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        if device.phys == "usb-0000:01:00.0-1.1/input0" and device.name == "GAOMON Gaomon Tablet Pen":
            pen1 = evdev.InputDevice(device.path)
            pen1.grab()
        elif device.phys == "usb-0000:01:00.0-1.2/input0" and device.name == "GAOMON Gaomon Tablet Pen":
            pen2 = evdev.InputDevice(device.path)
            pen2.grab()
        elif device.phys == "usb-0000:01:00.0-1.1/input0" and device.name == "GAOMON Gaomon Tablet Pad":
            pad1 = evdev.InputDevice(device.path)
            pad1.grab()
        elif device.phys == "usb-0000:01:00.0-1.2/input0" and device.name == "GAOMON Gaomon Tablet Pad":
            pad2 = evdev.InputDevice(device.path)
            pad2.grab()
            
    ReportArr=bytearray(14)
    async def print_events(device,ReportArr):
        async for event in device.async_read_loop():
            if  event.type == evdev.ecodes.EV_ABS: #event.type == evdev.ecodes.EV_KEY or
                ReportArr=changeReport(ReportArr,device.fd,pen1.fd,pad1.fd,event.code,event.value)
                write_report(ReportArr)
                #print(ReportArr[0],ReportArr[1])
    for device in pen1, pad1, pen2, pad2:
        asyncio.ensure_future(print_events(device,ReportArr))
    loop = asyncio.get_event_loop()
    loop.run_forever()
    

if __name__ == "__main__":
    main()
