#include <iostream>
#include <c208CoTiCtrl.h>
#include <PoolAPI.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		c208CoTiController::c208CoTiController
// 
// description : 	Constructor of the c208CoTiController class
//			It doesn't retrieve properties from the Tango DB;
//			it initializes some private data,
//                      builds a connection to the C208 device server 
//			and pings it to check if it is alive
//
//-----------------------------------------------------------------------------

c208CoTiController::c208CoTiController(const char *inst,vector<Controller::Properties> &prop):CoTiController(inst)
{
  /* search for device name property to initialize DevName */
  for(unsigned long i=0;i<prop.size();i++)    
    {
      if(prop[i].name=="DevName")
	DevName=prop[i].value.string_prop[0];
      if(prop[i].name=="GhostChannel")
	ghostchan=prop[i].value.long_prop[0];
    }

  /* initialize private data */
  ctr_dev=NULL;
  channels=0;
  for(int i=0; i<MAX_CHANNELS ; i++)
    values.push_back(0);
  if(ghostchan)
    channels|=(1<<(MAX_CHANNELS-1));
  master_idx=0;
  master_started=0;
  
  /* create a DeviceProxy */
  ctr_dev = Pool_ns::PoolUtil::instance()->get_device(inst_name, DevName);
  
  /* Ping the device to be sure that it is present */
  if(ctr_dev==NULL)
    {
      TangoSys_OMemStream o;
      o << "The PoolAPI didn't provide a valid C208 device server" << ends;
      Tango::Except::throw_exception((const char *) "Ctrl_BadPoolAPI",o.str(),(const char *)"c208CoTiController::c208CoTiController()");
    }
  else 
    ctr_dev->ping();
  ctr_state.state=Tango::ON;
  ctr_state.status="Initialized";
}

//-----------------------------------------------------------------------------
//
// method : 		c208CoTiController::~c208CoTiController
// 
// description : 	Destructor of the c208Controller class
//
//-----------------------------------------------------------------------------

c208CoTiController::~c208CoTiController()
{
  /* cout << "[c208CoTiController] class destructor" << endl;
     if (ctr_dev != NULL)
     delete ctr_dev;
  */
}

//-----------------------------------------------------------------------------
//
// method : 		c208CoTiController::AddDevice
// 
// description : 	Register a new counter channel for the controller
//			For now, this means setting channels bit position idx-1 to 1
//
//-----------------------------------------------------------------------------

void c208CoTiController::AddDevice(int32_t idx)
{
  if(idx>0 && idx<=MAX_CHANNELS)
    channels|=(1<<(idx-1));
}

//-----------------------------------------------------------------------------
//
// method : 		c208CoTiController::DeleteDevice
// 
// description : 	Unregister a counter channel for the controller
//			For now, this means setting channels bit position idx-1 to 0
//
//-----------------------------------------------------------------------------

void c208CoTiController::DeleteDevice(int32_t idx)
{
  if(idx>0 && idx<=MAX_CHANNELS)
    channels&=(~(1<<(idx-1)));
}

//-----------------------------------------------------------------------------
//
// method : 		c208CoTiController::LoadOne(long idx, double new_value)
// 
// description : 	Load master channel (timer) & perpare the other counters for counting.
//
//
//-----------------------------------------------------------------------------

void c208CoTiController::LoadOne(int32_t idx, double new_value)
{
  Tango::DeviceData args_in;
  Tango::DeviceAttribute timer("Time",new_value);
  vector<Tango::DevLong> val;
  
  if (ctr_dev != NULL)
    {
      ctr_dev->command_inout("Reset");

      ctr_dev->write_attribute(timer);      

      val.push_back(idx-1);
      if(new_value<0)
	val.push_back(2);    // monitor count
      else
	val.push_back(1);    // timer
      args_in << val;
      ctr_dev->command_inout("ConfigCounter",args_in);
      master_idx=idx;


      for(int i=0;i<MAX_CHANNELS;i++)
	if(i!=(idx-1) && (channels&(1<<i)))
	  {
	    Tango::DeviceData argsin;
	    vector<Tango::DevLong> vals;
	    
	    if(i==(MAX_CHANNELS-1) && ghostchan) /* ghost channel property set */
	      {
		vals.push_back(i);
		vals.push_back(4);
	      }
	    else
	      {
		vals.push_back(i);
		vals.push_back(3);
	      }
	    
	    argsin << vals;
	    ctr_dev->command_inout("ConfigCounter",argsin);
	  }
    }
  else
    {
      TangoSys_OMemStream o;
      
      o << "C208 controller from c208CoTiController/" << get_name() << " is NULL" << ends;
      Tango::Except::throw_exception((const char *)"c208CoTiCtrl_BadCtrlPtr",o.str(),(const char *)"c208CoTiController::LoadOne()");
    }

}

//-----------------------------------------------------------------------------
//
// method : 		c208CoTiController::StartOneCT(long idx)
// 
// description : 	Start counting tasks.
//
// arg(s) : - idx : The counter channel number (starting at 0)
//
//-----------------------------------------------------------------------------
void c208CoTiController::StartOneCT(int32_t idx)
{
  if(idx==master_idx)
    master_started=1;
}

//-----------------------------------------------------------------------------
//
// method : 		c208CoTiController::StartAllCT()
// 
// description : 	Start counting tasks.
//
// arg(s) : - idx : The counter channel number (starting at 0)
//
//-----------------------------------------------------------------------------

void c208CoTiController::StartAllCT()
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
      
      o << "C208 controller from c208CoTiController/" << get_name() << " is NULL" << ends;
      Tango::Except::throw_exception((const char *)"c208CoTiCtrl_BadCtrlPtr",o.str(),(const char *)"c208CoTiController::StartAllCT()");
    }
}

//-----------------------------------------------------------------------------
//
// method : 		c208CoTiController::AbortOne
// 
// description : 	Abort counting on a given channel.
//
// arg(s) : - idx : The counter channel number (starting at 1)
//
//-----------------------------------------------------------------------------

void c208CoTiController::AbortOne(int32_t idx)
{
  if (ctr_dev != NULL)
    {
      Tango::DeviceData arg_in;
      
      if(channels&(1<<(idx-1)))
	{
	  arg_in << (idx-1);
	  ctr_dev->command_inout("AbortTask",arg_in);
	  channels&=(~(1<<(idx-1)));
	  if(idx==master_idx)
	    {
	      master_started=0;
	      master_idx=0;
	    }
	}
    }
  else
    {
      TangoSys_OMemStream o;

      o << "C208 controller from c208CoTiController/" << get_name() << " is NULL" << ends;
      Tango::Except::throw_exception((const char *)"c208CoTiCtrl_BadCtrlPtr",o.str(),(const char *)"c208CoTiController::AbortOne()");
    }
}

//-----------------------------------------------------------------------------
//
// method : 		c208Controller::ReadAll
// 
// description : 	Read counter channels
//
//
// This method returns the counter/timer values
//-----------------------------------------------------------------------------

void c208CoTiController::ReadAll()
{
  if (ctr_dev != NULL)
    {
      (ctr_dev->read_attribute("Counter")) >> values;
    }
  else
    {
      TangoSys_OMemStream o;
      
      o << "Simulated controller for controller c208CoTiController/" << get_name() << " is NULL" << ends;
      Tango::Except::throw_exception((const char *)"c208Ctrl_BadCtrlPtr",o.str(),(const char *)"c208Controller::ReadAll()");
    }
      
}

//-----------------------------------------------------------------------------
//
// method : 		c208Controller::ReadOne
// 
// description : 	Read a counter timer
//
// arg(s) : - idx : The counter/timer number (starting at 1)
//
// This method returns the counter timer value
//-----------------------------------------------------------------------------

double c208CoTiController::ReadOne(int32_t idx)
{
  if (ctr_dev == NULL)
    {
      TangoSys_OMemStream o;
      
      o << "C208 controller from c208CoTiController/" << get_name() << " is NULL" << ends;
      Tango::Except::throw_exception((const char *)"c208Ctrl_BadCtrlPtr",o.str(),(const char *)"c208Controller::ReadOne()");
    }
  return(values[idx-1]);
}

//-----------------------------------------------------------------------------
//
// method : 		c208CoTiController::StateAll
// 
// description : 	Get counter card status.
//
//
//-----------------------------------------------------------------------------

void c208CoTiController::StateAll()
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
      o << "Simulated controller for controller c208Controller/" << get_name() << " is NULL" << ends;
      
      Tango::Except::throw_exception((const char *)"c208Ctrl_BadCtrlPtr",o.str(),
				     (const char *)"c208Controller::GetStatus()");
    }
}


//-----------------------------------------------------------------------------
//
// method : 		c208CoTiController::StateOne
// 
// description : 	Get counter channel status.
//
// arg(s) : - idx : The counter channel number (starting at 0)
//
//-----------------------------------------------------------------------------

void c208CoTiController::StateOne(int32_t idx, Controller::CtrlState *info_ptr)
{
  if (ctr_dev != NULL)
    {
      if((channels&(1<<(idx-1))) || ctr_state.state==Tango::FAULT)
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
      o << "Simulated controller for controller c208Controller/" << get_name() << " is NULL" << ends;
      
      Tango::Except::throw_exception((const char *)"c208Ctrl_BadCtrlPtr",o.str(),
				     (const char *)"c208Controller::GetStatus()");
    }
}

//-----------------------------------------------------------------------------
//
// method : 		c208CoTiController::bad_data_type
// 
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void c208CoTiController::bad_data_type(string &par_name)
{
	TangoSys_OMemStream o;

	o << "A wrong data type has been used to set the parameter " << par_name << ends;
	Tango::Except::throw_exception((const char *)"c208CoTiCtrl_BadParameter",o.str(),(const char *)"c208CoTiController::SetPar()");
}

//
//===============================================================================================
//

const char *CounterTimer_Ctrl_class_name[] = {"c208CoTiController",NULL};
const char *c208CoTiController_doc = "The C++ pool controller for the C208 counting card - c208CoTiController class";

int32_t c208CoTiController_MaxDevice = 8;

/* Controller::ExtraAttrInfo c208CoTiController_ctrl_extra_attributes[] = {{"CppCT_extra_1","DevLong","Read"},{"CppCT_extra_2","DevDouble","Read_Write"},NULL}; */

Controller::PropInfo c208CoTiController_class_prop[] = {{"DevName","The device server name","DevString",NULL}, {"GhostChannel","If you want a ghost channel on last channel (no. 8) set this property to 1","DevLong","0"},NULL};

extern "C"
{
	
Controller *_create_c208CoTiController(const char *inst,vector<Controller::Properties> &prop)
{
	return new c208CoTiController(inst, prop);
}


}
