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
		ZeroDData *zerod_data_elem = new ZeroDData;
		zerod_data_elem->tango_device = str_vec[l];
		zerod_data_elem->device_available = false;
		zerod_data_elem->proxy = NULL;
		zerod_data.insert(make_pair(index, zerod_data_elem));
		max_device++;
		index++;
	    }
	}
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
    map<int32_t, ZeroDData*>::iterator ite = zerod_data.begin();
    for(;ite != zerod_data.end();ite++)
    {
	if(ite->second->proxy != NULL)
	    delete ite->second->proxy;
	delete ite->second;		
    }		
    zerod_data.clear();
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
    if(idx > max_device){
	TangoSys_OMemStream o;
	o << "The property 'TangoDevices' has no value for index " << idx << ".";
	o << " Please define a valid tango device before adding a new element to this controller"<< ends;
	
	Tango::Except::throw_exception((const char *)"TIP830u20Ctrl_BadIndex",o.str(),
				       (const char *)"TIP830u20Ctrl::AddDevice()");
    }
    if(zerod_data[idx]->device_available == false){
	if(zerod_data[idx]->proxy == NULL)
	    zerod_data[idx]->proxy = new Tango::DeviceProxy(zerod_data[idx]->tango_device);
	try{
	    zerod_data[idx]->proxy->ping();
	    zerod_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
	    zerod_data[idx]->device_available = false;
	}
    }
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
    if(idx > max_device){
	TangoSys_OMemStream o;
	o << "Trying to delete an inexisting element(" << idx << ") from the controller." << ends;
	
	Tango::Except::throw_exception((const char *)"TIP830u20Ctrl_BadIndex",o.str(),
				       (const char *)"TIP830u20Ctrl::DeleteDevice()");
    }	
    
    if(zerod_data[idx]->proxy != NULL){
	delete zerod_data[idx]->proxy;
	zerod_data[idx]->proxy = NULL;  
    }
    zerod_data[idx]->device_available = false;
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
    Tango::DeviceAttribute d_out;
    double returned_val;
    
    if(zerod_data[idx]->proxy == NULL){
	TangoSys_OMemStream o;
	o << "TIP830u20Ctrl Device Proxy for idx " << idx << " is NULL" << ends;	
	Tango::Except::throw_exception((const char *)"TIP830u20Ctrl_BadCtrlPtr",o.str(),
				       (const char *)"TIP830u20Ctrl::ReadOne()");  
    }
    
    if(zerod_data[idx]->device_available == false){
	try{
	    zerod_data[idx]->proxy->ping();
	    zerod_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
	    zerod_data[idx]->device_available = false;
	    TangoSys_OMemStream o;
	    o << "TIP830u20Ctrl Device for idx " << idx << " not available" << ends;	
	    Tango::Except::throw_exception((const char *)"TIP830u20Ctrl_BadCtrlPtr",o.str(),
					   (const char *)"TIP830u20Ctrl::ReadOne()"); 
	}
    }

    d_out = zerod_data[idx]->proxy->read_attribute("Value");
    d_out >> returned_val;
	
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
    
    Tango::DevState state_tmp;
    
    if(zerod_data[idx]->proxy == NULL){
	state_tmp = Tango::FAULT;
	return;
    }
    
    state_tmp = zerod_data[idx]->proxy->state();
    
    ct_info_ptr->state = (int32_t)state_tmp;
    if(state_tmp == Tango::ON){
	ct_info_ptr->status = "ADC is in ON state";
    } else if (state_tmp == Tango::MOVING){
	ct_info_ptr->status = "ADC is busy";
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


Controller::PropInfo TIP830u20Ctrl_class_prop[] = {
    {"RootDeviceName","Root name for tango devices","DevString"}, 
    NULL};

int32_t TIP830u20Ctrl_MaxDevice = 97;

extern "C"
{
	
  Controller *_create_TIP830u20Ctrl(const char *inst,vector<Controller::Properties> &prop)
  {
    return new TIP830u20Ctrl(inst,prop);
  }

}
