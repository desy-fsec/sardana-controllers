#include <iostream>
#include <DGG2Ctrl.h>
//#include <signal.h>
//#include <sys/time.h>

#include <pool/PoolAPI.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		DGG2::DGG2
// 
// description : 	Ctor of the DGG2 class
//					It retrieve some properties from Tango DB, build a 
//					connection to the Simulated controller and ping it
//					to check if it is alive
//
//-----------------------------------------------------------------------------

DGG2::DGG2(const char *inst,vector<Controller::Properties> &prop):CoTiController(inst),
nb_ms(0),stop_time_ms(0),remain_ms(0),start_th(0)
{

  for (unsigned long loop = 0;loop < prop.size();loop++)
    {
      if( prop[loop].name == "DevName" )
	{
	  DevName = prop[loop].value.string_prop[0];
	}
    }
  
  //
  // Some data member init
  //
  
  nb_sec = nb_usec = 0;
  
  //
  // Create a DeviceProxy on the dgg2 controller and set
  // it in automatic reconnection mode
  //
  dgg2timer_ctrl = Pool_ns::PoolUtil::instance()->get_device(inst_name, DevName);
  
  //
  // Ping the device to be sure that it is present
  //
  if(dgg2timer_ctrl == NULL)
    {
      TangoSys_OMemStream o;
      o << "The PoolAPI did not provide a valid dgg2 device" << ends;
      Tango::Except::throw_exception((const char *)"DGG2Ctrl_BadPoolAPI",o.str(),
				     (const char *)"DGG2Controller::DGG2Controller()");
    }
  
  try
    {
      dgg2timer_ctrl->ping();
    }
  catch (Tango::DevFailed &e)
    {
      throw;
    }
}
//-----------------------------------------------------------------------------
//
// method : 		DGG2::~DGG2
// 
// description : 	Dtor of the DGG2 class
//
//-----------------------------------------------------------------------------

DGG2::~DGG2()
{
}

//-----------------------------------------------------------------------------
//
// method : 		DGG2::AddDevice
// 
// description : 	Register a new device for the controller
//					For the simulated controller, this simply means increment
//					motor count
//
//-----------------------------------------------------------------------------

void DGG2::AddDevice(int32_t idx)
{
  //cout << "[DGG2] Creating a new Counter Timer with index " << idx << " on controller DGG2/" << inst_name << endl;
  
}

//-----------------------------------------------------------------------------
//
// method : 		DGG2::DeleteDevice
// 
// description : 	Unregister a new device for the controller
//					For the simulated controller, this simply means decrement
//					motor count
//
//-----------------------------------------------------------------------------

void DGG2::DeleteDevice(int32_t idx)
{
  //cout << "[DGG2] Deleting Counter Timer with index " << idx << " on controller DGG2/" << inst_name  << endl;
}

//-----------------------------------------------------------------------------
//
// method : 		DGG2::AbortOne
// 
// description : 	Stop a timer.
//
// arg(s) : - idx : The timer number (starting at 1)
//
//-----------------------------------------------------------------------------

void DGG2::AbortOne(int32_t idx)
{
  //cout << "[DGG2] Aborting one timer with index " << idx << " on controller DGG2/" << inst_name << endl;
  if (dgg2timer_ctrl != NULL)
    {
      Tango::DeviceData d_in;
      d_in << (Tango::DevLong)idx;
      dgg2timer_ctrl->command_inout("Abort",d_in);
    }
  else
    {
      TangoSys_OMemStream o;
      o << "Simulated controller for controller DGG2Ctrl/" << get_name() << " is NULL" << ends;
      
      Tango::Except::throw_exception((const char *)"DGG2Ctrl_BadCtrlPtr",o.str(),
				     (const char *)"DGG2Ctrl::AbortOne()");
    }
  
}

//-----------------------------------------------------------------------------
//
// method : 		DGG2::ReadOne
// 
// description : 	Read a counter timer
//
// arg(s) : - idx : The counter timer number
//
// This method returns the counter timer value
//-----------------------------------------------------------------------------

double DGG2::ReadOne(int32_t idx)
{
  //cout << "[DGG2] Getting Value for timer with index " << idx << " on controller DGG2/" << inst_name << endl;
  double returned_time;
  
  if (dgg2timer_ctrl != NULL)
    {
      Tango::DeviceData d_in,d_out;
      
      d_in << (Tango::DevLong)idx;
      
      d_out = dgg2timer_ctrl->command_inout("GetAxeSampleTime",d_in);
      d_out >> returned_time;
    }
  else
    {
      TangoSys_OMemStream o;
      o << "DGG2Controller for controller DGG2Ctrl/" << get_name() << " is NULL" << ends;
      
      Tango::Except::throw_exception((const char *)"DGG2Ctrl_BadCtrlPtr",o.str(),
				     (const char *)"DGG2Ctrl::ReadOne()");
    }
  return returned_time;
}
//-----------------------------------------------------------------------------
//
// method : 		DGG2::StateOne
// 
// description : 	Get one timer status. Timer status means two things :
//					1 - The Timer state (Tango sense)
//					2 - The timer error message if any
//
// arg(s) : - idx : The timer number
//			- ct_info_ptr : Pointer to a struct. which will be filled with
//							timer status
//
//-----------------------------------------------------------------------------

void DGG2::StateOne(int32_t idx,Controller::CtrlState *ct_info_ptr)
{
  //cout << "[DGG2] Getting state for Timer with index " << idx << " on controller DGG2/" << inst_name << ", thread = " << omni_thread::self()->id() << endl;

  Tango::DevLong state_tmp;
	
  if (dgg2timer_ctrl != NULL)
    {
      Tango::DeviceData d_in,d_out;
      d_in << (Tango::DevLong)idx;
      d_out = dgg2timer_ctrl->command_inout("GetAxeStatus",d_in);

      d_out >> state_tmp;

      ct_info_ptr->state = (int32_t)state_tmp;
      if(state_tmp == Tango::ON){
	ct_info_ptr->status = "Timer is in ON state";
      } else if (state_tmp == Tango::MOVING){
	ct_info_ptr->status = "Timer is busy";
      }
		
    }
  else
    {
      TangoSys_OMemStream o;
      o << "DGG2 Controller for controller DGG2Ctrl/" << get_name() << " is NULL" << ends;
		
      Tango::Except::throw_exception((const char *)"DGG2Ctrl_BadCtrlPtr",o.str(),
				     (const char *)"DGG2Controller::GetStatus()");
    }
	
}

//-----------------------------------------------------------------------------
//
// method : 		DGG2::LoadOne
// 
// description : 	Load a timer counter
//
// arg(s) : - idx : The timer number
//			- val : The timer value
//
//-----------------------------------------------------------------------------

void DGG2::LoadOne(int32_t idx, double val)
{

  if (dgg2timer_ctrl != NULL)
    {
      Tango::DeviceData d_in;

      vector<double> v_db;
      v_db.push_back(val);

      vector<string> v_str;
      convert_stream << (Tango::DevLong)idx;
      v_str.push_back(convert_stream.str());
      convert_stream.str("");
	
      d_in.insert(v_db,v_str);	
				
		
      dgg2timer_ctrl->command_inout("SetAxeSampleTime",d_in);
			
    }
  else
    {
      TangoSys_OMemStream o;
      o << "DGG2Ctrl for controller DGG2Ctrl/" << get_name() << " is NULL" << ends;
		
      Tango::Except::throw_exception((const char *)"DGG2Ctrl_BadCtrlPtr",o.str(),
				     (const char *)"DGG2Ctrl::LoadOne()");
    }
}

//-----------------------------------------------------------------------------
//
// method : 		DGG2::StartOne
// 
// description : 	Start the timer
//
// arg(s) : - idx : The timer number
//
//-----------------------------------------------------------------------------
void DGG2::StartOneCT(int32_t idx)
{

  if (dgg2timer_ctrl != NULL)
    {
      Tango::DeviceData d_in;
      d_in << (Tango::DevLong)idx;
      dgg2timer_ctrl->command_inout("StartAxe",d_in);
    }
  else
    {
      TangoSys_OMemStream o;
      o << "DGG2 controller for controller DGG2Ctrl/" << get_name() << " is NULL" << ends;
		
      Tango::Except::throw_exception((const char *)"DGG2Ctrl_BadCtrlPtr",o.str(),
				     (const char *)"DGG2Ctrl::StartOneCT()");
    }
	

}
	

//
//===============================================================================================
//

const char *CounterTimer_Ctrl_class_name[] = {"DGG2",NULL};
const char *DGG2_doc = "This is the Unix Timer controller class";
const char *DGG2_gender = "Timer";
const char *DGG2_model = "Linux";
const char *DGG2_image = " ";
const char *DGG2_organization = "DESY";
const char *DGG2_logo = " ";

Controller::PropInfo DGG2_class_prop[] = {{"DevName","The tango device name of the DGG2Ctrl","DevString"},
					  NULL};

int32_t DGG2_MaxDevice = 97;

extern "C"
{
	
  Controller *_create_DGG2(const char *inst,vector<Controller::Properties> &prop)
  {
    return new DGG2(inst,prop);
  }
}
