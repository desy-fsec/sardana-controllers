
import time
import PyTango

bragg_name = 'motor/dcm_pmac_ctrl/1'
energy_name = 'pm/dcm_energy_ctrl/1'
pmac_name = 'bl22/ct/pmaceth-01' 
vcm_pitch_name = 'pm/oh_vcm_z_pitch_roll_ctrl/2' 
crystal_name = 'ioregister/tattr_ior_ctrl/8'

start_energy = 7180
end_energy = 7280
nr_points = 1000
int_time = 0.5

if __name__ == '__main__':

    bragg_motor = PyTango.DeviceProxy(bragg_name)
    energy_motor = PyTango.DeviceProxy(energy_name)
    pmac = PyTango.DeviceProxy(pmac_name)
    vcm_pitch_motor = PyTango.DeviceProxy(vcm_pitch_name)
    crystal_ds = PyTango.DeviceProxy(crystal_name)

    bragg_spu = bragg_motor.read_attribute('step_per_unit').value
    bragg_offset = bragg_motor.read_attribute('offset').value
    vcm_pitch_mrad = vcm_pitch_motor.read_attribute('position').value
    dSi111 = energy_motor.read_attribute('dSi111').value
    offsetSi111 = energy_motor.read_attribute('angularOffsetSi111').value
    dSi311 = energy_motor.read_attribute('dSi311').value
    offsetSi311 = energy_motor.read_attribute('angularOffsetSi311').value
    crystal_value = crystal_ds.read_attribute('value').value
    if crystal_value == 311:
        crystal = 'Si311'
    else:
        crystal = 'Si111'

    pmac_offset = float(pmac.SendCtrlChar("P").split()[0])
    pmac_enc = float(pmac.GetMVariable(101))

    # TODO: adapt to new version

    # print 'Start testing with python lib'
    # t1 = time.time()
    # print  start_energy, end_energy, nr_points, int_time,bragg_spu, bragg_offset, \
    #     pmac_offset, pmac_enc, \
    #                           crystal, vcm_pitch_mrad, dSi111, offsetSi111, \
    #                           dSi311, offsetSi311
    # py_values = py_energy.get_enc_table(start_energy, end_energy, nr_points, int_time,
    #                           bragg_spu, bragg_offset, pmac_offset, pmac_enc,
    #                           crystal, vcm_pitch_mrad, dSi111, offsetSi111,
    #                           dSi311, offsetSi311)
    #
    # print (time.time() -t1) * 1e6, 'us'
    #
    # print 'Start testing with cython lib'
    # t1 = time.time()
    # cy_values = cy_energy.get_enc_table(start_energy, end_energy, nr_points, int_time,
    #                           bragg_spu, bragg_offset, pmac_offset, pmac_enc,
    #                           crystal, vcm_pitch_mrad, dSi111, offsetSi111,
    #                           dSi311, offsetSi311)
    #
    # print (time.time()-t1) * 1e6, 'us'
    #
    # print py_values == cy_values

    
    
