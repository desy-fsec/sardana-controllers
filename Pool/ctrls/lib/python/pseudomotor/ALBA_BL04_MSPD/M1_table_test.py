import PyTango
import time

f = open("results", "r")
ff = open("differences", "w")
ff.write("mzl_diff    mzr_diff    mzc_diff\n")
results = []

lines = f.readlines()
lines.pop(0)

for line in lines:
    results.append(line.split())
    
z = PyTango.DeviceProxy("pm/m1_z_pitch_roll/mot_z")
pitch = PyTango.DeviceProxy("pm/m1_z_pitch_roll/mot_pitch")
roll = PyTango.DeviceProxy("pm/m1_z_pitch_roll/mot_roll")

mzl = PyTango.DeviceProxy("motor/dummymotorctrl/mzl")
mzr = PyTango.DeviceProxy("motor/dummymotorctrl/mzr")
mzc = PyTango.DeviceProxy("motor/dummymotorctrl/mzc")

for line in results:
    z.write_attribute("Position", float(line[0]) * 1000)
    time.sleep(1)
    pitch.write_attribute("Position", float(line[1]) * 1000)
    time.sleep(1)
    roll.write_attribute("Position", float(line[2]) * 1000)
    time.sleep(1)
    
    mzl_pos = mzl.read_attribute("Position").value
    mzr_pos = mzr.read_attribute("Position").value
    mzc_pos = mzc.read_attribute("Position").value
    
    mzl_diff = abs(abs(mzl_pos) - abs(float(line[3])) * 1000)
    mzr_diff = abs(abs(mzr_pos) - abs(float(line[4])) * 1000)
    mzc_diff = abs(abs(mzc_pos) - abs(float(line[5])) * 1000)
    print "%f    %f    %f\n" % (mzl_diff, mzr_diff, mzc_diff) 
    ff.write("%f    %f    %f\n" % (mzl_diff, mzr_diff, mzc_diff))