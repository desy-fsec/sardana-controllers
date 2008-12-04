#include <iostream>
#include <ni6602CoTiCtrl.h>
#include <pool/PoolAPI.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		ni6602CoTiController::ni6602CoTiController
// 
// description : 	Constructor of the ni6602CoTiController class
//			It doesn't retrieve properties from the Tango DB;
//			it initializes some private data,
//                      builds a connection to the NI6602 device server 
//			and pings it to check if it is alive
//
//-----------------------------------------------------------------------------

ni6602CoTiController::ni6602CoTiController(const char *inst,vector<Controller::Properties> &prop):CoTiController(inst)
{
  /* search for device name property to initialize DevName */
  for(unsigned long i=0;i<prop.size();i++)    
    {
      if(prop[i].name=="DevName")
	DevName=prop[i].value.string_prop[0];
    }

  /* initialize private data */
  ctr_dev=NULL;
  for(int32_t i=0; i<MAX_CHANNELS ; i++)
    {
      channels[i]=0;
      values.push_back(0);
    }
  twochans=0;
  master_idx=99;
  master_started=0;
  
  /* create a DeviceProxy */
  ctr_dev = Pool_ns::PoolUtil::instance()->get_device(inst_name, DevName);
  
  /* Ping the device to be sure that it is present */
  if(ctr_dev==NULL)
    {
      TangoSys_OMemStream o;
      o << "The PoolAPI didn't provide a valid NI6602 device server" << ends;
      Tango::Except::throw_exception((const char *) "Ctrl_BadPoolAPI",o.str(),(const char *)"ni6602CoTiController::ni6602CoTiController()");
    }
  else 
    ctr_dev->ping();
  ctr_state.state=Tango::ON;
  ctr_state.status="Initialized";
}

//-----------------------------------------------------------------------------
//
// method : 		ni6602CoTiController::~ni6602CoTiController
// 
// description : 	Destructor of the ni6602Controller class
//
//-----------------------------------------------------------------------------

ni6602CoTiController::~ni6602CoTiController()
{
  /* cout << "[ni6602CoTiController] class destructor" << endl;
     if (ctr_dev != NULL)
     delete ctr_dev;
  */
}

//-----------------------------------------------------------------------------
//
// method : 		ni6602CoTiController::AddDevice
// 
// description : 	Register a new counter channel for the controller
//			For now, this means setting channels[idx-1] to 1
//
//-----------------------------------------------------------------------------

void ni6602CoTiController::AddDevice(int32_t idx)
{
  if(idx>0 && idx<=MAX_CHANNELS)
    channels[idx-1]=1;
}

//-----------------------------------------------------------------------------
//
// method : 		ni6602CoTiController::DeleteDevice
// 
// description : 	Unregister a counter channel for the controller
//			For now, this means setting channels[idx-1] to 0
//
//-----------------------------------------------------------------------------

void ni6602CoTiController::DeleteDevice(int32_t idx)
{
  if(idx>0 && idx<=MAX_CHANNELS)
    channels[idx-1]=0;
}

//-----------------------------------------------------------------------------
//
// method : 		ni6602CoTiController::LoadOne(long idx, double new_value)
// 
// description : 	Load master channel (timer) & perpare the other counters for counting.
//
//
//-----------------------------------------------------------------------------

void ni6602CoTiController::LoadOne(int32_t idx, double new_value)
{
  Tango::DeviceData args_in;
  Tango::DeviceAttribute timer("Time",new_value);
  vector<Tango::DevLong> val;
  
  if (ctr_dev != NULL)
    {
      ctr_dev->command_inout("Reset");

      ctr_dev->write_attribute(timer);      

      if(new_value<0)
	{
	  val.push_back(idx-1);
	  val.push_back(8);    // monitor count
	  args_in << val;
	  ctr_dev->command_inout("ConfigCounter",args_in);
	  master_idx=idx;
	}
      else
	if(idx==MAX_CHANNELS)
	  {
	    TangoSys_OMemStream o;
	    
	    o << "NI6602 controller from ni6602CoTiController/" << get_name() << " is NULL" << ends;
	    Tango::Except::throw_exception((const char *)"ni6602CoTiCtrl_BadTimer",o.str(),(const char *)"ni6602CoTiController::LoadOne()");
	  }
	else
	  {
	    Tango::DeviceData args_timer;
	    vector<Tango::DevLong> for_timer;

	    twochans=1;
	    for_timer.push_back(MAX_CHANNELS-1);
	    for_timer.push_back(7);    // generate one pulse
	    args_timer << for_timer;
	    ctr_dev->command_inout("ConfigCounter",args_timer);
	    val.push_back(idx-1);
	    val.push_back(4);    // timing channel
	    args_in << val;	 
	    ctr_dev->command_inout("ConfigCounter",args_in);
	    master_idx=idx;
	  }
      for(int32_t i=0;i<MAX_CHANNELS-1;i++)
	if(i!=master_idx-1 && channels[i])
	  {
	    Tango::DeviceData argsin;
	    vector<Tango::DevLong> vals;
	    
	    vals.push_back(i);
	    vals.push_back(9);
	    argsin << vals;
	    ctr_dev->command_inout("ConfigCounter",argsin);
	  }
      if(twochans==0 && channels[MAX_CHANNELS-1])
	{	 
	  Tango::DeviceData argsin;
	  vector<Tango::DevLong> vals;

	  vals.push_back(MAX_CHANNELS-1);
	  vals.push_back(9);
	  argsin << vals;
	  ctr_dev->command_inout("ConfigCounter",argsin);
	}
    }
  else
    {
      TangoSys_OMemStream o;
      
      o << "NI6602 controller from ni6602CoTiController/" << get_name() << " is NULL" << ends;
      Tango::Except::throw_exception((const char *)"ni6602CoTiCtrl_BadCtrlPtr",o.str(),(const char *)"ni6602CoTiController::LoadOne()");
    }

}

//-----------------------------------------------------------------------------
//
// method : 		ni6602CoTiController::StartOneCT(long idx)
// 
// description : 	Start counting tasks.
//
// arg(s) : - idx : The counter channel number (starting at 0)
//
//-----------------------------------------------------------------------------
void ni6602CoTiController::StartOneCT(int32_t idx)
{
  if(idx==master_idx)
    master_started=1;
}

//-----------------------------------------------------------------------------
//
// method : 		ni6602CoTiController::StartAllCT()
// 
// description : 	Start counting tasks.
//
// arg(s) : - idx : The counter channel number (starting at 0)
//
//-----------------------------------------------------------------------------

void ni6602CoTiController::StartAllCT()
{
  if (ctr_dev != NULL)
    {
      if(master_started)
	{
	  ctr_dev->command_inout("Start");
	  master_started=0;
	}
    }
  else
    {
      TangoSys_OMemStream o;
      
      o << "NI6602 controller from ni6602CoTiController/" << get_name() << " is NULL" << ends;
      Tango::Except::throw_exception((const char *)"ni6602CoTiCtrl_BadCtrlPtr",o.str(),(const char *)"ni6602CoTiController::StartAllCT()");
    }
}

//-----------------------------------------------------------------------------
//
// method : 		ni6602CoTiController::AbortOne
// 
// description : 	Abort counting on a given channel.
//
// arg(s) : - idx : The counter channel number (starting at 1)
//
//-----------------------------------------------------------------------------

void ni6602CoTiController::AbortOne(int32_t idx)
{
  if (ctr_dev != NULL)
    {
      Tango::DeviceData arg_in;
      
      if(channels[idx-1])
	{
	  if(idx==master_idx)
	    {
	      if(twochans)
		{
		  Tango::DeviceData arg_timer;
		  
		  arg_timer << (Tango::DevLong) MAX_CHANNELS-1;
		  ctr_dev->command_inout("AbortTask",arg_timer);
		  twochans=0;
		}
	      master_started=0;
	      master_idx=99;
	    }
	  arg_in << (Tango::DevLong)(idx-1);
	  ctr_dev->command_inout("AbortTask",arg_in);
	  channels[idx-1]=0;
	}
    }
  else
    {
      TangoSys_OMemStream o;
      
      o << "NI6602 controller from ni6602CoTiController/" << get_name() << " is NULL" << ends;
      Tango::Except::throw_exception((const char *)"ni6602CoTiCtrl_BadCtrlPtr",o.str(),(const char *)"ni6602CoTiController::AbortOne()");
    }
}

//-----------------------------------------------------------------------------
//
// method : 		ni6602Controller::ReadAll
// 
// description : 	Read counter channels
//
//
// This method returns the counter/timer values
//-----------------------------------------------------------------------------

void ni6602CoTiController::ReadAll()
{
  if (ctr_dev != NULL)
    {
      (ctr_dev->read_attribute("Counter")) >> values;
    }
  else
    {
      TangoSys_OMemStream o;
      
      o << "Simulated controller for controller ni6602CoTiController/" << get_name() << " is NULL" << ends;
      Tango::Except::throw_exception((const char *)"ni6602Ctrl_BadCtrlPtr",o.str(),(const char *)"ni6602Controller::ReadAll()");
    }
      
}

//-----------------------------------------------------------------------------
//
// method : 		ni6602Controller::ReadOne
// 
// description : 	Read a counter timer
//
// arg(s) : - idx : The counter/timer number (starting at 1)
//
// This method returns the counter timer value
//-----------------------------------------------------------------------------

double ni6602CoTiController::ReadOne(int32_t idx)
{
  if (ctr_dev == NULL)
    {
      TangoSys_OMemStream o;
      
      o << "NI6602 controller from ni6602CoTiController/" << get_name() << " is NULL" << ends;
      Tango::Except::throw_exception((const char *)"ni6602Ctrl_BadCtrlPtr",o.str(),(const char *)"ni6602Controller::ReadOne()");
    }
  return(values[idx-1]);
}

//-----------------------------------------------------------------------------
//
// method : 		ni6602CoTiController::StateAll
// 
// description : 	Get counter card status.
//
//
//-----------------------------------------------------------------------------

void ni6602CoTiController::StateAll()
{
  if (ctr_dev != NULL)
    {
      ctr_state.state=ctr_dev->state();

      if(ctr_state.state==Tango::STANDBY)
	ctr_state.state=Tango::ON;
      else
	if(ctr_state.state==Tango::RUNNING)
	  ctr_state.state=Tango::MOVING;
	else
	  if(ctr_state.state!=Tango::FAULT)
	    ctr_state.state=Tango::UNKNOWN;
	
      (ctr_dev->command_inout("Status")) >> ctr_state.status;
    }
  else
    {
      TangoSys_OMemStream o;
      o << "Simulated controller for controller ni6602Controller/" << get_name() << " is NULL" << ends;
      
      Tango::Except::throw_exception((const char *)"ni6602Ctrl_BadCtrlPtr",o.str(),
				     (const char *)"ni6602Controller::GetStatus()");
    }
}


//-----------------------------------------------------------------------------
//
// method : 		ni6602CoTiController::StateOne
// 
// description : 	Get counter channel status.
//
// arg(s) : - idx : The counter channel number (starting at 0)
//
//-----------------------------------------------------------------------------

void ni6602CoTiController::StateOne(int32_t idx, Controller::CtrlState *info_ptr)
{
  if (ctr_dev != NULL)
    {
      if(channels[idx-1] || ctr_state.state==Tango::FAULT)
  	{
	  info_ptr->state=ctr_state.state;
	  info_ptr->status.assign(ctr_state.status);
  	}
      else
	{
	  info_ptr->state=Tango::ON;
	  info_ptr->status="Channel not configured for measurement";
	}
    }
  else
    {
      TangoSys_OMemStream o;
      o << "Simulated controller for controller ni6602Controller/" << get_name() << " is NULL" << ends;
      
      Tango::Except::throw_exception((const char *)"ni6602Ctrl_BadCtrlPtr",o.str(),
				     (const char *)"ni6602Controller::GetStatus()");
    }
}

//-----------------------------------------------------------------------------
//
// method : 		ni6602CoTiController::bad_data_type
// 
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void ni6602CoTiController::bad_data_type(string &par_name)
{
	TangoSys_OMemStream o;

	o << "A wrong data type has been used to set the parameter " << par_name << ends;
	Tango::Except::throw_exception((const char *)"ni6602CoTiCtrl_BadParameter",o.str(),(const char *)"ni6602CoTiController::SetPar()");
}

//
//===============================================================================================
//

const char *CounterTimer_Ctrl_class_name[] = {"ni6602CoTiController",NULL};
const char *ni6602CoTiController_doc = "The C++ pool controller for the NI6602 counting card - ni6602CoTiController class";

int32_t ni6602CoTiController_MaxDevice = 8;

/* Controller::ExtraAttrInfo ni6602CoTiController_ctrl_extra_attributes[] = {{"CppCT_extra_1","DevLong","Read"},{"CppCT_extra_2","DevDouble","Read_Write"},NULL}; */

Controller::PropInfo ni6602CoTiController_class_prop[] = {{"DevName","The device server name","DevString",NULL},NULL};
							  			 
extern "C"
{
	
Controller *_create_ni6602CoTiController(const char *inst,vector<Controller::Properties> &prop)
{
	return new ni6602CoTiController(inst,prop);
}


}
