#include <LTB_BCM_PseudoCoCtrl.h>
#include <pool/PoolAPI.h>

LTB_BCM_PCs::LTB_BCM_PCs(const char *inst,vector<Controller::Properties> &prop):
PseudoCounterController(inst)
{
  //cout << "[LTB_BCM_PCs] class ctor" << endl;
}

LTB_BCM_PCs::~LTB_BCM_PCs ( )
{
  //cout << "[LTB_BCM_PCs] class dtor" << endl;
}

double LTB_BCM_PCs::e()
{
  //return (ibend() * 0.688901) + 0.235063;
  return ((0.705787 * ibend()) + 0.244807) * (1 + (offset() / 1013));
}

double LTB_BCM_PCs::egap()
{
  return e() / gap();
}

double LTB_BCM_PCs::gap()
{
  return read_device_attribute("pm/lt02_hslit/1","Position");
}

double LTB_BCM_PCs::offset()
{
  return read_device_attribute("pm/lt02_hslit/2","Position");
}

double LTB_BCM_PCs::ibend()
{
  return read_device_attribute("motor/lt01_pc_bend1/1","Position");
}

double LTB_BCM_PCs::read_device_attribute(std::string dev_name, std::string dev_attr)
{
  Tango::DeviceProxy* device = Pool_ns::PoolUtil::instance()->get_device(inst_name,dev_name);
  double value = -1;
  try {
    device->read_attribute(dev_attr) >> value;
  } catch (...) {
    cout << "[LTB_BCM_PCs]: Some exception found reading " << dev_name << "/" << dev_attr << endl;
    //throw;
  }
  return value;
}

double LTB_BCM_PCs::Calc(int32_t index,vector<double> &counter_values)
{
  double bcm1 = counter_values[0];
  double bcm2 = counter_values[1];

  double real1_bcm1;
  double real1_bcm2;
  double real2_bcm1;
  double real2_bcm2;
  double real3_bcm1;
  double real3_bcm2;
  cout << "[LTB_BCM_PCs]: Calculating for index" << index << endl;
  switch (index) {
  case 1:
    cout << "[LTB_BCM_PCs]: WORK AROUND BECAUSE BCM1 AND BCM2 ARE NOT CORRECT" << endl;
    cout << "[LTB_BCM_PCs]: IN bcm1:" << bcm1 << " bcm2:" << bcm2 << " cr:" << bcm2/bcm1<< endl;
    real1_bcm1 = read_device_attribute("expchan/ltb_bcmzerod/1","CumulatedValue");
    real1_bcm2 = read_device_attribute("expchan/ltb_bcmzerod/2","CumulatedValue");
    cout << "[LTB_BCM_PCs]: REAL bcm1:" << real1_bcm1 << " bcm2:" << real1_bcm2 << " cr:" << bcm2/bcm1<< endl;
    //     cr = bcm2/bcm1
    return real1_bcm2 / real1_bcm1;
    break;
  case 2:
    cout << "[LTB_BCM_PCs]: WORK AROUND BECAUSE BCM1 AND BCM2 ARE NOT CORRECT" << endl;
    cout << "[LTB_BCM_PCs]: IN bcm1:" << bcm1 << " bcm2:" << bcm2 << " cr:" << bcm2/bcm1<< endl;
    real2_bcm1 = read_device_attribute("expchan/ltb_bcmzerod/1","CumulatedValue");
    real2_bcm2 = read_device_attribute("expchan/ltb_bcmzerod/2","CumulatedValue");
    cout << "[LTB_BCM_PCs]: REAL bcm1:" << real2_bcm1 << " bcm2:" << real2_bcm2 << " cr:" << bcm2/bcm1<< endl;
    //     crgap = cr / gap
    return (real2_bcm2 / real2_bcm1) / gap();
    break;
  case 3:
    //     E = ((ibend * 0.705787) + 0.244807 ) * (1 + (offset / 1013)
    return e();
    break;
  case 4:
    //     egap = e / gap
    return egap();
    break;
  case 5:
    //     gap
    return gap();
    break;
  case 6:
    //     offset
    return offset();
    break;
  case 7:
    //     ibend
    return ibend();
    break;
  case 8:
    //     crnorm = (bcm2 / bcm1) / ((gap / 1013) * E)
    real3_bcm1 = read_device_attribute("expchan/ltb_bcmzerod/1","CumulatedValue");
    real3_bcm2 = read_device_attribute("expchan/ltb_bcmzerod/2","CumulatedValue");
    //return (real3_bcm2 / real3_bcm1) / ((gap()/1000.0) * e());
    return (real3_bcm2 / real3_bcm1) / ((gap() / 1013.0) * e());
    break;
  }
  return -1;
}


//
//===============================================================================================
//

const char *PseudoCounter_Ctrl_class_name[] = { "LTB_BCM_PCs", NULL };

const char *LTB_BCM_PCs_doc = "This is the C++ pseudo counter controller for a LTB BCM scans";
const char *LTB_BCM_PCs_gender = "PseudoCounter";
const char *LTB_BCM_PCs_model = "LTB_BCM_PCs";
const char *LTB_BCM_PCs_image = "dummy_com.png";
const char *LTB_BCM_PCs_organization = "CELLS - ALBA";
const char *LTB_BCM_PCs_logo = "ALBA_logo.png";

Controller::ExtraAttrInfo LTB_BCM_PCs_ctrl_extra_attributes[] = { NULL };

Controller::PropInfo LTB_BCM_PCs_class_prop[] = { NULL };

//const char *LTB_BCM_PCs_counter_roles[] = { "bcm1", "bcm2", "mot_gap", "mot_offset", "mot_ibend", NULL };
const char *LTB_BCM_PCs_counter_roles[] = { "bcm1", "bcm2", NULL };
const char *LTB_BCM_PCs_pseudo_counter_roles[] = {
  "cr", "crgap", "e", "egap", "gap", "offset", "ibend", "crnorm", NULL };

long LTB_BCM_PCs_MaxDevice = 8; // should be the pseudo counter role #

extern "C"
{
  Controller *_create_LTB_BCM_PCs(const char *inst,vector<Controller::Properties> &prop)
  {
    return new LTB_BCM_PCs(inst,prop);
  }
}
