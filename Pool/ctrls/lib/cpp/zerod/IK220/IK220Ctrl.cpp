#include <iostream>
#include <IK220Ctrl.h>
#include <pool/PoolAPI.h>

#include <sys/types.h>
#include <sys/time.h>
#include <unistd.h>
#include <stdlib.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		IK220Ctrl::IK220Ctrl
// 
// description : 	Ctor of the IK220Ctrl class
//					It retrieve some properties from Tango DB, build a 
//					connection to the IK220 Tango Device controller and ping it
//					to check if it is alive
//
//-----------------------------------------------------------------------------

IK220Ctrl::IK220Ctrl(const char *inst,vector<Controller::Properties> &prop):ZeroDController(inst)
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
// method : 		IK220Ctrl::~IK220Ctrl
// 
// description : 	Dtor of the IK220Ctrl class
//
//-----------------------------------------------------------------------------

IK220Ctrl::~IK220Ctrl()
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
// method : 		IK220Ctrl::AddDevice
// 
// description : 	Register a new device for the controller
//					
//
//-----------------------------------------------------------------------------

void IK220Ctrl::AddDevice(int32_t idx)
{
	//cout << "[IK220Ctrl] Creating a new Zero D Exp Channel with index " << idx << " on controller IK220Ctrl/" << inst_name << endl;
 
    if(idx > max_device){
	TangoSys_OMemStream o;
	o << "The property 'TangoDevices' has no value for index " << idx << ".";
	o << " Please define a valid tango device before adding a new element to this controller"<< ends;
	
	Tango::Except::throw_exception((const char *)"IK220Ctrl_BadIndex",o.str(),
				       (const char *)"IK220Ctrl::AddDevice()");
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
// method : 		IK220Ctrl::DeleteDevice
// 
// description : 	Unregister a new device for the controller
//					For the simulated controller, this simply means decrement
//					motor count
//
//-----------------------------------------------------------------------------

void IK220Ctrl::DeleteDevice(int32_t idx)
{
    //cout << "[IK220Ctrl] Deleting Counter Timer with index " << idx << " on controller IK220Ctrl/" << inst_name  << endl;	
    if(idx > max_device){
	TangoSys_OMemStream o;
	o << "Trying to delete an inexisting element(" << idx << ") from the controller." << ends;
	
	Tango::Except::throw_exception((const char *)"IK220Ctrl_BadIndex",o.str(),
				       (const char *)"IK220Ctrl::DeleteDevice()");
    }	
    
    if(zerod_data[idx]->proxy != NULL){
	delete zerod_data[idx]->proxy;
	zerod_data[idx]->proxy = NULL;  
    }
    zerod_data[idx]->device_available = false;
}

//-----------------------------------------------------------------------------
//
// method : 		IK220Ctrl::ReadOne
// 
// description : 	Read a encoder
//
// arg(s) : - idx : The encoder number (starting at 1)
//
// This method returns the encoder position 
//-----------------------------------------------------------------------------

double IK220Ctrl::ReadOne(int32_t idx)
{
//	cout << "[IK220Ctrl] Getting value for exp channel with index " << idx << " on controller IK220Ctrl/" << endl;

    Tango::DeviceAttribute d_out;
    double returned_val;
    
    if(zerod_data[idx]->proxy == NULL){
	TangoSys_OMemStream o;
	o << "IK220Ctrl Device Proxy for idx " << idx << " is NULL" << ends;	
	Tango::Except::throw_exception((const char *)"IK220Ctrl_BadCtrlPtr",o.str(),
				       (const char *)"IK220Ctrl::ReadOne()");  
    }
    
    if(zerod_data[idx]->device_available == false){
	try{
	    zerod_data[idx]->proxy->ping();
	    zerod_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
	    zerod_data[idx]->device_available = false;
	    TangoSys_OMemStream o;
	    o << "IK220Ctrl Device for idx " << idx << " not available" << ends;	
	    Tango::Except::throw_exception((const char *)"IK220Ctrl_BadCtrlPtr",o.str(),
					   (const char *)"IK220Ctrl::ReadOne()"); 
	}
    }

    d_out = zerod_data[idx]->proxy->read_attribute("Position");
    d_out >> returned_val;
	
    return returned_val;
}


//-----------------------------------------------------------------------------
//
// method : 		IK220Ctrl::GetState
// 
// description : 	Get one Encoder status.
//
// arg(s) : - idx : The encoder number (starting at 1)
//			- ct_info_ptr : Pointer to a struct. which will be filled with
//							Encoder status
//
//-----------------------------------------------------------------------------

void IK220Ctrl::StateOne(int32_t idx, Controller::CtrlState *ct_info_ptr)
{
    //cout << "[IK220Ctrl] Getting state for Exp Channel with index " << idx << " on controller IK220Ctrl/" << inst_name << endl;
    
    Tango::DevState state_tmp;
    
    if(zerod_data[idx]->proxy == NULL){
	state_tmp = Tango::FAULT;
	return;
    }
    
    state_tmp = zerod_data[idx]->proxy->state();
    
    ct_info_ptr->state = (int32_t)state_tmp;
    if(state_tmp == Tango::ON){
	ct_info_ptr->status = "Encoder is in ON state";
    } 
}


//-----------------------------------------------------------------------------
//
// method :             IK220Ctrl::GetExtraAttributePar
// 
// description :        Get a encoder extra attribute parameter.
//
// arg(s) : - idx : The encoder number (starting at 1)
//                      - par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------
                               
  
Controller::CtrlData IK220Ctrl::GetExtraAttributePar(int32_t idx, string &par_name)
{
    Controller::CtrlData par_value;	
    
    Tango::DevLong par_tmp_db;
    Tango::DevLong par_tmp_l;
        
    if(zerod_data[idx]->proxy == NULL){
	TangoSys_OMemStream o;
	o << "IK220Ctrl Device Proxy for idx " << idx << " is NULL" << ends;	
	Tango::Except::throw_exception((const char *)"IK220Ctrl_BadCtrlPtr",o.str(),
				       (const char *)"IK220Ctrl::GetExtraAttributePar()");  
    }
    
    if(zerod_data[idx]->device_available == false){
	try{
	    zerod_data[idx]->proxy->ping();
	    zerod_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
	    zerod_data[idx]->device_available = false;
	    TangoSys_OMemStream o;
	    o << "IK220Ctrl Device for idx " << idx << " not available" << ends;	
	    Tango::Except::throw_exception((const char *)"IK220Ctrl_BadCtrlPtr",o.str(),
					   (const char *)"IK220Ctrl::GetExtraAttributePar()"); 
	}
    }
    
    Tango::DeviceAttribute d_out;

    if (par_name == "Conversion")
    {
	d_out = zerod_data[idx]->proxy->read_attribute("Conversion");
	d_out >> par_value.db_data;
	par_value.data_type = Controller::DOUBLE;	
    }
    else if (par_name == "Offset")
    {
	d_out = zerod_data[idx]->proxy->read_attribute("Offset");
	d_out >> par_value.db_data;
	par_value.data_type = Controller::DOUBLE;
    }
    else if (par_name == "FlagIgnoreStatus")
    {
	d_out = zerod_data[idx]->proxy->read_attribute("FlagIgnoreStatus");
	d_out >> par_tmp_l;
	par_value.int32_data = (int32_t) par_tmp_l;
	par_value.data_type = Controller::INT32;
    }
    else if (par_name == "StatusPort")
    {
	d_out = zerod_data[idx]->proxy->read_attribute("StatusPort");
	d_out >> par_tmp_l;
	par_value.int32_data = (int32_t) par_tmp_l;
	par_value.data_type = Controller::INT32;
    }
    else if ( (par_name == "Calibrate") || (par_name == "CancelReference") || (par_name == "DoReference") || (par_name == "InitEncoder") || (par_name == "SetCorrectionOffOn") )
    {
	TangoSys_OMemStream o;
	o << "Extra attribute " << par_name << " is actually a command. Write to execute it/" << get_name() << ends;
	
	Tango::Except::throw_exception((const char *)"Ctrl_BadCtrlPtr",o.str(),
				       (const char *)"IK220Ctrl::GetExtraAttributePar()");
    }
    else
    {
	TangoSys_OMemStream o;
	o << "Extra attribute " << par_name << " is unknown for controller IK220Ctrl/" << get_name() << ends;
	
	Tango::Except::throw_exception((const char *)"Ctrl_BadCtrlPtr",o.str(),
				       (const char *)"IK220Ctrl::GetExtraAttributePar()");
    }
    
    return par_value;
}



//-----------------------------------------------------------------------------
//
// method : 		IK220Ctrl::SetExtraAttributePar
// 
// description : 	Set a encoder extra attribute parameter.
//
// arg(s) : - idx : The encoder number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void IK220Ctrl::SetExtraAttributePar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{    
    Tango::DeviceData d_in;
    
    if(zerod_data[idx]->proxy == NULL){
	TangoSys_OMemStream o;
	o << "IK220Ctrl Device Proxy for idx " << idx << " is NULL" << ends;	
	Tango::Except::throw_exception((const char *)"IK220Ctrl_BadCtrlPtr",o.str(),
				       (const char *)"IK220Ctrl::SetExtraAttributePar()");  
    }
    
    if(zerod_data[idx]->device_available == false){
	try{
	    zerod_data[idx]->proxy->ping();
	    zerod_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
	    zerod_data[idx]->device_available = false;
	    TangoSys_OMemStream o;
	    o << "IK220Ctrl Device for idx " << idx << " not available" << ends;	
	    Tango::Except::throw_exception((const char *)"IK220Ctrl_BadCtrlPtr",o.str(),
					   (const char *)"IK220Ctrl::SetExtraAttributePar()"); 
	}
    }
    
    if (par_name == "Conversion")
    {
	Tango::DeviceAttribute da_con("Conversion",new_value.db_data );
	if (new_value.data_type == Controller::DOUBLE)
	    zerod_data[idx]->proxy->write_attribute(da_con);
	else
	    bad_data_type(par_name);
    } 
    else if (par_name == "Offset")
    {
	Tango::DeviceAttribute da_off("Offset",new_value.db_data );
	if (new_value.data_type == Controller::DOUBLE)
	    zerod_data[idx]->proxy->write_attribute(da_off);
	else
	    bad_data_type(par_name);
    }
    else if (par_name == "Calibrate")
    {
	if (new_value.data_type == Controller::DOUBLE){
	    d_in << new_value.db_data;
	    zerod_data[idx]->proxy->command_inout("Calibrate", d_in);
	}
	else
	    bad_data_type(par_name);
    }
    else if (par_name == "FlagIgnoreStatus")
    {
	Tango::DeviceAttribute da_fis("FlagIgnoreStatus",(Tango::DevLong)new_value.int32_data );
	if (new_value.data_type == Controller::INT32)
	    zerod_data[idx]->proxy->write_attribute(da_fis);
	else
	    bad_data_type(par_name);
	
    }
    else if (par_name == "StatusPort")
    {
	Tango::DeviceAttribute da_sp("StatusPort",(Tango::DevLong)new_value.int32_data );
	if (new_value.data_type == Controller::INT32)
	    zerod_data[idx]->proxy->write_attribute(da_sp);
	else
	    bad_data_type(par_name);
	
    }
    else if (par_name == "CancelReference")
    {
	zerod_data[idx]->proxy->command_inout("CancelReference");
    }
    else if (par_name == "DoReference")
    {
	zerod_data[idx]->proxy->command_inout("DoReference");
    }
    else if (par_name == "InitEncoder")
    {
	zerod_data[idx]->proxy->command_inout("InitEncoder");
    }
    else if (par_name == "SetCorrectionOffOn")
    {
	if (new_value.data_type == Controller::INT32){
	    d_in << (Tango::DevLong)new_value.int32_data;
	    zerod_data[idx]->proxy->command_inout("CorrectionOffOn", d_in);
	}
	else
	    bad_data_type(par_name);
    }
    else
    {
	TangoSys_OMemStream o;
	o << "Extra attribute " << par_name << " is unknown for controller IK220Ctrl/" << get_name() << ends;
	
	Tango::Except::throw_exception((const char *)"IK220Ctrl_BadCtrlPtr",o.str(),
				       (const char *)"IK220Ctrl::SetExtraAttributePar()");
    }
}

//-----------------------------------------------------------------------------
//
// method : 		IK220Ctrl::bad_data_type
// 
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void IK220Ctrl::bad_data_type(string &par_name)
{
	TangoSys_OMemStream o;
	o << "A wrong data type has been used to set the parameter " << par_name << ends;

	Tango::Except::throw_exception((const char *)"IK220Ctrl_BadParameter",o.str(),
			       			   	   (const char *)"IK220Ctrl::SetPar()");
}

//
//===============================================================================================
//

const char *ZeroDExpChannel_Ctrl_class_name[] = {"IK220Ctrl",NULL};

const char *IK220Ctrl_doc = "This is the C++ controller for the IK220Ctrl class";


Controller::PropInfo IK220Ctrl_class_prop[] = {
    {"RootDeviceName","Root name for tango devices","DevString"}, 
    NULL};

Controller::ExtraAttrInfo IK220Ctrl_ctrl_extra_attributes[] = {{"Conversion","DevDouble","Read_Write"},
							       {"Calibrate","DevDouble","Read_Write"},
							       {"Offset","DevDouble","Read_Write"},
							       {"FlagIgnoreStatus","DevLong","Read_Write"},
							       {"StatusPort","DevLong","Read"},
							       {"CancelReference","DevLong","Read_Write"},
							       {"DoReference","DevLong","Read_Write"},
							       {"InitEncoder","DevLong","Read_Write"},
							       {"SetCorrectionOffOn","DevLong","Read_Write"},
							       NULL};


int32_t IK220Ctrl_MaxDevice = 97;

extern "C"
{
	
Controller *_create_IK220Ctrl(const char *inst,vector<Controller::Properties> &prop)
{
	return new IK220Ctrl(inst,prop);
}

}
