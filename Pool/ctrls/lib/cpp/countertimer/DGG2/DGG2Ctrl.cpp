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
  
  //
  // Some data member init
  //
  
  max_device = 0;
  vector<Controller::Properties>::iterator prop_it;
  for (prop_it = prop.begin(); prop_it != prop.end(); ++prop_it){
    if(prop_it->name == "RootDeviceName"){
      Tango::Database *db = new Tango::Database();
      string root_device_name =prop_it->value.string_prop[0];
      string add = "*";
      string name = root_device_name + add;
      Tango::DbDatum db_datum = db->get_device_exported(name);
      vector<string> str_vec;
      db_datum >> str_vec;  
      int index = 1;
      for(unsigned long l = 0; l < str_vec.size(); l++){
	TimerData *timer_data_elem = new TimerData;
	timer_data_elem->tango_device = str_vec[l];
	timer_data_elem->device_available = false;
	timer_data_elem->proxy = NULL;
	timer_data.insert(make_pair(index, timer_data_elem));
	max_device++;
	index++;
      }
    }
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
    map<int32_t, TimerData*>::iterator ite = timer_data.begin();
    for(;ite != timer_data.end();ite++)
    {
	if(ite->second->proxy != NULL)
	    delete ite->second->proxy;
	delete ite->second;		
    }		
    timer_data.clear();
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
 
    if(idx > max_device){
	TangoSys_OMemStream o;
	o << "The property 'TangoDevices' has no value for index " << idx << ".";
	o << " Please define a valid tango device before adding a new element to this controller"<< ends;
	
	Tango::Except::throw_exception((const char *)"DGG2Ctrl_BadIndex",o.str(),
				       (const char *)"DGG2Ctrl::AddDevice()");
    }
    if(timer_data[idx]->device_available == false){
	if(timer_data[idx]->proxy == NULL)
	    timer_data[idx]->proxy = new Tango::DeviceProxy(timer_data[idx]->tango_device);
	try{
	    timer_data[idx]->proxy->ping();
	    timer_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
	    timer_data[idx]->device_available = false;
	}
    } 
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
  if(idx > max_device){
    TangoSys_OMemStream o;
    o << "Trying to delete an inexisting element(" << idx << ") from the controller." << ends;
    
    Tango::Except::throw_exception((const char *)"DGG2Ctrl_BadIndex",o.str(),
				   (const char *)"DGG2Ctrl::DeleteDevice()");
  }	
	
  if(timer_data[idx]->proxy != NULL){
    delete timer_data[idx]->proxy;
    timer_data[idx]->proxy = NULL;  
  }
  timer_data[idx]->device_available = false;
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
  if(timer_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "DGG2Ctrl Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"DGG2Ctrl_BadCtrlPtr",o.str(),
				   (const char *)"DGG2Ctrl::AbortOne()");  
  }
	
  if(timer_data[idx]->device_available == false){
    try{
      timer_data[idx]->proxy->ping();
      timer_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      timer_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "DGG2Ctrl Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"DGG2Ctrl_BadCtrlPtr",o.str(),
				     (const char *)"DGG2Ctrl::AbortOne()"); 
    }
  }

  timer_data[idx]->proxy->command_inout("Stop");
  
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

  Tango::DeviceAttribute d_out;

  double returned_time;
  double sample_time;
  double remaining_time;

  if(timer_data[idx]->proxy == NULL){
      TangoSys_OMemStream o;
      o << "DGG2Ctrl Device Proxy for idx " << idx << " is NULL" << ends;	
      Tango::Except::throw_exception((const char *)"DGG2Ctrl_BadCtrlPtr",o.str(),
				     (const char *)"DGG2Ctrl::ReadOne()");  
  }
  
  if(timer_data[idx]->device_available == false){
      try{
	  timer_data[idx]->proxy->ping();
	  timer_data[idx]->device_available = true;	
      }
      catch(Tango::DevFailed &e){
	  timer_data[idx]->device_available = false;
	  TangoSys_OMemStream o;
	  o << "DGG2Ctrl Device for idx " << idx << " not available" << ends;	
	  Tango::Except::throw_exception((const char *)"DGG2Ctrl_BadCtrlPtr",o.str(),
					 (const char *)"DGG2Ctrl::ReadOne()"); 
      }
  }

  d_out = timer_data[idx]->proxy->read_attribute("SampleTime");
  d_out >> sample_time;

  d_out = timer_data[idx]->proxy->read_attribute("RemainingTime");
  d_out >> remaining_time;
  
  returned_time = sample_time - remaining_time;

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

  Tango::DevState state_tmp;
	   
  if(timer_data[idx]->proxy == NULL){
      state_tmp = Tango::FAULT;
      return;
  }
  
  state_tmp = timer_data[idx]->proxy->state();

  ct_info_ptr->state = (int32_t)state_tmp;
  if(state_tmp == Tango::ON){
      ct_info_ptr->status = "Timer is in ON state";
  } else if (state_tmp == Tango::MOVING){
      ct_info_ptr->status = "Timer is busy";
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
    if(timer_data[idx]->proxy == NULL){
	TangoSys_OMemStream o;
	o << "DGG2Ctrl Device Proxy for idx " << idx << " is NULL" << ends;	
	Tango::Except::throw_exception((const char *)"DGG2Ctrl_BadCtrlPtr",o.str(),
				       (const char *)"DGG2Ctrl::LoadOne()");  
    }
    
    if(timer_data[idx]->device_available == false){
	try{
	    timer_data[idx]->proxy->ping();
	    timer_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
	    timer_data[idx]->device_available = false;
	    TangoSys_OMemStream o;
	    o << "DGG2Ctrl Device for idx " << idx << " not available" << ends;	
	    Tango::Except::throw_exception((const char *)"DGG2Ctrl_BadCtrlPtr",o.str(),
					   (const char *)"DGG2Ctrl::LoadOne()"); 
	}
    }

    Tango::DeviceAttribute da("SampleTime", val);

    timer_data[idx]->proxy->write_attribute(da);

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
    if(timer_data[idx]->proxy == NULL){
	TangoSys_OMemStream o;
	o << "DGG2Ctrl Device Proxy for idx " << idx << " is NULL" << ends;	
	Tango::Except::throw_exception((const char *)"DGG2Ctrl_BadCtrlPtr",o.str(),
				       (const char *)"DGG2Ctrl::StartOneCT()");  
    }
    
    if(timer_data[idx]->device_available == false){
	try{
	    timer_data[idx]->proxy->ping();
	    timer_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
	    timer_data[idx]->device_available = false;
	    TangoSys_OMemStream o;
	    o << "DGG2Ctrl Device for idx " << idx << " not available" << ends;	
	    Tango::Except::throw_exception((const char *)"DGG2Ctrl_BadCtrlPtr",o.str(),
					   (const char *)"DGG2Ctrl::StartOneCT()"); 
	}
    }

    timer_data[idx]->proxy->command_inout("Start");

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

Controller::PropInfo DGG2_class_prop[] = {
    {"RootDeviceName","Root name for tango devices","DevString"}, 
    NULL};

int32_t DGG2_MaxDevice = 97;

extern "C"
{
	
  Controller *_create_DGG2(const char *inst,vector<Controller::Properties> &prop)
  {
    return new DGG2(inst,prop);
  }
}
