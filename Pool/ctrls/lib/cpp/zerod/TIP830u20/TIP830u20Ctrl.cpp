#include <iostream>
#include <TIP830u20Ctrl.h>
#include <pool/PoolAPI.h>

#include <sys/types.h>
#include <sys/time.h>
#include <unistd.h>
#include <stdlib.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		TIP830u20Ctrl::TIP830u20Ctrl
// 
// description : 	Ctor of the TIP830u20Ctrl class
//					It retrieve some properties from Tango DB, build a 
//					connection to the Simulated controller and ping it
//					to check if it is alive
//
//-----------------------------------------------------------------------------

TIP830u20Ctrl::TIP830u20Ctrl(const char *inst,vector<Controller::Properties> &prop):ZeroDController(inst)
{

  for (unsigned long loop = 0;loop < prop.size();loop++)
    {
      if( prop[loop].name == "DevName" )
	{
	  DevName = prop[loop].value.string_prop[0];
	}
    }
	
  //
  // Create a DeviceProxy on the dgg2 controller and set
  // it in automatic reconnection mode
  //
  adc_ctrl = Pool_ns::PoolUtil::instance()->get_device(inst_name, DevName);
	
  //
  // Ping the device to be sure that it is present
  //
  if(adc_ctrl == NULL)
    {
      TangoSys_OMemStream o;
      o << "The PoolAPI did not provide a valid dgg2 device" << ends;
      Tango::Except::throw_exception((const char *)"TIP830u20Ctrl_BadPoolAPI",o.str(),
				     (const char *)"TIP830u20Ctrl::TIP830u20Ctrl()");
    }
	
  try
    {
      adc_ctrl->ping();
    }
  catch (Tango::DevFailed &e)
    {
      delete adc_ctrl;
      throw;
    }
	
}

//-----------------------------------------------------------------------------
//
// method : 		TIP830u20Ctrl::~TIP830u20Ctrl
// 
// description : 	Dtor of the TIP830u20Ctrl class
//
//-----------------------------------------------------------------------------

TIP830u20Ctrl::~TIP830u20Ctrl()
{
  //cout << "[TIP830u20Ctrl] class dtor" << endl;
  if (adc_ctrl != NULL)
    delete adc_ctrl;
}

//-----------------------------------------------------------------------------
//
// method : 		TIP830u20Ctrl::AddDevice
// 
// description : 	Register a new device for the controller
//					For the simulated controller, this simply means increment
//					motor count
//
//-----------------------------------------------------------------------------

void TIP830u20Ctrl::AddDevice(int32_t idx)
{
  //cout << "[TIP830u20Ctrl] Creating a new Zero D Exp Channel with index " << idx << " on controller TIP830u20Ctrl/" << inst_name << endl;
}

//-----------------------------------------------------------------------------
//
// method : 		TIP830u20Ctrl::DeleteDevice
// 
// description : 	Unregister a new device for the controller
//					For the simulated controller, this simply means decrement
//					motor count
//
//-----------------------------------------------------------------------------

void TIP830u20Ctrl::DeleteDevice(int32_t idx)
{
  //cout << "[TIP830u20Ctrl] Deleting Counter Timer with index " << idx << " on controller TIP830u20Ctrl/" << inst_name  << endl;
}

//-----------------------------------------------------------------------------
//
// method : 		TIP830u20Ctrl::ReadOne
// 
// description : 	Read a counter timer
//
// arg(s) : - idx : The counter timer number (starting at 1)
//
// This method returns the counter timer value
//-----------------------------------------------------------------------------

double TIP830u20Ctrl::ReadOne(int32_t idx)
{
  //cout << "[TIP830u20Ctrl] Getting value for exp channel with index " << idx << " on controller TIP830u20Ctrl/" << endl;
  double returned_val;

  if (adc_ctrl != NULL)
    {
      Tango::DeviceData d_in,d_out;
		
      d_in << (Tango::DevLong)idx;
		
      d_out = adc_ctrl->command_inout("GetAxeValue",d_in);
      d_out >> returned_val;
    }
  else
    {
      TangoSys_OMemStream o;
      o << "TIP830u20Ctrl for controller TIP830u20Ctrl/" << get_name() << " is NULL" << ends;
      Tango::Except::throw_exception((const char *)"TIP830u20ADCCtrl_BadCtrlPtr",o.str(),
				     (const char *)"TIP830u20ADCCtrl::ReadOne()");
    }
	
  return returned_val;
}


//-----------------------------------------------------------------------------
//
// method : 		TIP830u20Ctrl::GetState
// 
// description : 	Get one ADC status.
//
// arg(s) : - idx : The adc number (starting at 1)
//			- ct_info_ptr : Pointer to a struct. which willbe filled with
//							ADC status
//
//-----------------------------------------------------------------------------

void TIP830u20Ctrl::StateOne(int32_t idx, Controller::CtrlState *ct_info_ptr)
{
  //cout << "[TIP830u20Ctrl] Getting state for Exp Channel with index " << idx << " on controller TIP830u20Ctrl/" << inst_name << endl;

  Tango::DevLong state_tmp;
	
  if (adc_ctrl != NULL)
    {
      Tango::DeviceData d_in,d_out;
      d_in << (Tango::DevLong)idx;
      d_out = adc_ctrl->command_inout("GetAxeStatus",d_in);
		
      d_out >> state_tmp;
		
      ct_info_ptr->state = (int32_t)state_tmp;
      if(state_tmp == Tango::ON){
	ct_info_ptr->status = "ADC is in ON state";
      } else if (state_tmp == Tango::MOVING){
	ct_info_ptr->status = "ADC is busy";
      }
		
    }
  else
    {
      TangoSys_OMemStream o;
      o << "TIP830u20ADC Controller for controller TIP830u20Ctrl/" << get_name() << " is NULL" << ends;
				
      Tango::Except::throw_exception((const char *)"TIP830u20ADCCtrl_BadCtrlPtr",o.str(),
				     (const char *)"TIP830u20Ctrl::GetStatus()");
    }
	
}


//-----------------------------------------------------------------------------
//
// method : 		TIP830u20Ctrl::bad_data_type
// 
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void TIP830u20Ctrl::bad_data_type(string &par_name)
{
  TangoSys_OMemStream o;
  o << "A wrong data type has been used to set the parameter " << par_name << ends;

  Tango::Except::throw_exception((const char *)"TIP830u20ADCCtrl_BadParameter",o.str(),
				 (const char *)"TIP830u20Ctrl::SetPar()");
}

//
//===============================================================================================
//

const char *ZeroDExpChannel_Ctrl_class_name[] = {"TIP830u20Ctrl",NULL};

const char *TIP830u20Ctrl_doc = "This is the C++ controller for the TIP830u20Ctrl class";


Controller::PropInfo TIP830u20Ctrl_class_prop[] = {{"DevName","The tango device name of the TIP830u20Ctrl","DevString"},
															
						   NULL};

int32_t TIP830u20Ctrl_MaxDevice = 97;

extern "C"
{
	
  Controller *_create_TIP830u20Ctrl(const char *inst,vector<Controller::Properties> &prop)
  {
    return new TIP830u20Ctrl(inst,prop);
  }

}
