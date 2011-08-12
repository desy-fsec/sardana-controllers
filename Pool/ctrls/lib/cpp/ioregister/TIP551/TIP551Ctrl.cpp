#include <iostream>
#include <TIP551Ctrl.h>
#include <pool/PoolAPI.h>

using namespace std;

// Controller for the DACs: TIP551 and TIP850DAC

//-----------------------------------------------------------------------------
//
// method : 		TIP551Ctrl::TIP551Ctrl
// 
// description : 	Ctor of the TIP551Ctrl class
//					It retrieve some properties from Tango DB, build a 
//					connection to the Simulated controller and ping it
//					to check if it is alive
//
//-----------------------------------------------------------------------------

TIP551Ctrl::TIP551Ctrl(const char *inst, vector<Controller::Properties> &prop):
IORegisterController(inst)
{
    read_nb = 0;
    write_nb = 0;

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
		IORegisterData *ioregister_data_elem = new IORegisterData;
		ioregister_data_elem->tango_device = str_vec[l];
		ioregister_data_elem->device_available = false;
		ioregister_data_elem->proxy = NULL;
		ioregister_data.insert(make_pair(index, ioregister_data_elem));
		max_device++;
		index++;
	    }
	}
    }
	
}

//-----------------------------------------------------------------------------
//
// method : 		TIP551Ctrl::~TIP551Ctrl
// 
// description : 	Dtor of the TIP551Ctrl Controller class
//
//-----------------------------------------------------------------------------

TIP551Ctrl::~TIP551Ctrl()
{	
    map<int32_t, IORegisterData*>::iterator ite = ioregister_data.begin();
    for(;ite != ioregister_data.end();ite++)
    {
	if(ite->second->proxy != NULL)
	    delete ite->second->proxy;
	delete ite->second;		
    }		
    ioregister_data.clear();
}

//-----------------------------------------------------------------------------
//
// method : 		TIP551Ctrl::AddDevice
// 
// description : 	Register a new device for the controller
//					For the simulated controller, this simply means increment
//					motor count
//
//-----------------------------------------------------------------------------

void TIP551Ctrl::AddDevice(int32_t idx)
{
	//cout << "[TIP551] Creating a new IORegister with index " << idx << " on controller TIP551/" << inst_name << endl;
 
    if(idx > max_device){
	TangoSys_OMemStream o;
	o << "The property 'TangoDevices' has no value for index " << idx << ".";
	o << " Please define a valid tango device before adding a new element to this controller"<< ends;
	
	Tango::Except::throw_exception((const char *)"TIP551Ctrl_BadIndex",o.str(),
				       (const char *)"TIP551Ctrl::AddDevice()");
    }
    if(ioregister_data[idx]->device_available == false){
	if(ioregister_data[idx]->proxy == NULL)
	    ioregister_data[idx]->proxy = new Tango::DeviceProxy(ioregister_data[idx]->tango_device);
	try{
	    ioregister_data[idx]->proxy->ping();
	    ioregister_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
	    ioregister_data[idx]->device_available = false;
	}
    } 
}

//-----------------------------------------------------------------------------
//
// method : 		TIP551Ctrl::DeleteDevice
// 
// description : 	Unregister a new device for the controller
//					For the simulated controller, this simply means decrement
//					motor count
//
//-----------------------------------------------------------------------------

void TIP551Ctrl::DeleteDevice(int32_t idx)
{
    //cout << "[TIP551] Deleting IORegister with index " << idx << " on controller TIP551/" << inst_name << endl;	
    if(idx > max_device){
	TangoSys_OMemStream o;
	o << "Trying to delete an inexisting element(" << idx << ") from the controller." << ends;
	
	Tango::Except::throw_exception((const char *)"TIP551Ctrl_BadIndex",o.str(),
				       (const char *)"TIP551Ctrl::DeleteDevice()");
    }	
    
    if(ioregister_data[idx]->proxy != NULL){
	delete ioregister_data[idx]->proxy;
	ioregister_data[idx]->proxy = NULL;  
    }
    ioregister_data[idx]->device_available = false;
}

int32_t TIP551Ctrl::ReadOne(int32_t idx)
{

    Tango::DeviceAttribute d_out;
    Tango::DevDouble read_value;
    
    read_nb++;
    
    if(ioregister_data[idx]->proxy == NULL){
	TangoSys_OMemStream o;
	o << "DGG2Ctrl Device Proxy for idx " << idx << " is NULL" << ends;	
	Tango::Except::throw_exception((const char *)"TIP551Ctrl_BadCtrlPtr",o.str(),
				       (const char *)"TIP551Ctrl::ReadOne()");  
    }
    
    if(ioregister_data[idx]->device_available == false){
	try{
	    ioregister_data[idx]->proxy->ping();
	    ioregister_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
	    ioregister_data[idx]->device_available = false;
	    TangoSys_OMemStream o;
	    o << "TIP551Ctrl Device for idx " << idx << " not available" << ends;	
	    Tango::Except::throw_exception((const char *)"TIP551Ctrl_BadCtrlPtr",o.str(),
					   (const char *)"TIP551Ctrl::ReadOne()"); 
	}
    }

    d_out = ioregister_data[idx]->proxy->read_attribute("Voltage");
    d_out >> read_value;
	
	
    return (int32_t)read_value;
}



void TIP551Ctrl::WriteOne(int32_t idx, int32_t write_value)
{	
    write_nb++;
    
    if(ioregister_data[idx]->proxy == NULL){
	TangoSys_OMemStream o;
	o << "DGG2Ctrl Device Proxy for idx " << idx << " is NULL" << ends;	
	Tango::Except::throw_exception((const char *)"TIP551Ctrl_BadCtrlPtr",o.str(),
				       (const char *)"TIP551Ctrl::ReadOne()");  
    }
    
    if(ioregister_data[idx]->device_available == false){
	try{
	    ioregister_data[idx]->proxy->ping();
	    ioregister_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
	    ioregister_data[idx]->device_available = false;
	    TangoSys_OMemStream o;
	    o << "TIP551Ctrl Device for idx " << idx << " not available" << ends;	
	    Tango::Except::throw_exception((const char *)"TIP551Ctrl_BadCtrlPtr",o.str(),
					   (const char *)"TIP551Ctrl::WriteOne()"); 
	}
    }
	
    Tango::DeviceAttribute da("Voltage", (Tango::DevDouble)write_value);

    ioregister_data[idx]->proxy->write_attribute( da);   
}

//-----------------------------------------------------------------------------
//
// method : 		TIP551Ctrl::GetState
// 
// description : 	Get one motor status. Motor status means two things :
//					1 - The motor state (Tango sense)
//
// arg(s) : - idx : The motor number (starting at 1)
//			- mot_info_ptr : Pointer to a struct. which willbe filled with
//							 motor status
//
//-----------------------------------------------------------------------------

void TIP551Ctrl::StateOne(int32_t idx, Controller::CtrlState *ior_info_ptr)
{
    Tango::DevLong state_tmp;
	
    if(ioregister_data[idx]->proxy == NULL){
	state_tmp = Tango::FAULT;
	return;
    }
    
    state_tmp = ioregister_data[idx]->proxy->state();
    
    ior_info_ptr->state = (int32_t)state_tmp;
    if(state_tmp == Tango::ON){
	ior_info_ptr->status = "IORegister is in ON state";
    } else if (state_tmp == Tango::FAULT){
	ior_info_ptr->status = "IORegister in in FAULT state";
    }
	
}


//-----------------------------------------------------------------------------
//
// method : 		TIP551Ctrl::GetExtraAttributePar
// 
// description : 	Get a counter ioregister extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData TIP551Ctrl::GetExtraAttributePar(int32_t idx,string &par_name)
{
  Controller::CtrlData par_value;

  if(ioregister_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "TIP551Ctrl Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"TIP551Ctrl_BadCtrlPtr",o.str(),
				   (const char *)"TIP551Ctrl::StartOne()");  
  }
  
  if(ioregister_data[idx]->device_available == false){
    try{
      ioregister_data[idx]->proxy->ping();
      ioregister_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      ioregister_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "TIP551Ctrl Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"TIP551Ctrl_BadCtrlPtr",o.str(),
				     (const char *)"TIP551Ctrl::GetExtraAttributeParameter()"); 
    }
  }
  
  Tango::DeviceAttribute d_out;
  
  if (par_name == "VoltageMax"){
    d_out = ioregister_data[idx]->proxy->read_attribute("VoltageMax");
    d_out >> par_value.db_data;
    par_value.data_type = Controller::DOUBLE;		
  } else if (par_name == "VoltageMin"){
    d_out = ioregister_data[idx]->proxy->read_attribute("VoltageMin");
    d_out >> par_value.db_data;
    par_value.data_type = Controller::DOUBLE;		
  } else {
    TangoSys_OMemStream o;
    o << "Extra attribute " << par_name << " is unknown for controller TIP551Ctrl/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"TIP551Ctrl_BadCtrlPtr",o.str(),
				   (const char *)"TIP551Ctrl::GetExtraAttributePar()");
  }
  
  return par_value;
}

//-----------------------------------------------------------------------------
//
// method : 		TIP551Ctrl::SetExtraAttributePar
// 
// description : 	Set extra attribute parameters.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void TIP551Ctrl::SetExtraAttributePar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{
  Tango::DeviceData d_in;
  
  if(ioregister_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "TIP551Ctrl Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"TIP551Ctrl_BadCtrlPtr",o.str(),
				   (const char *)"TIP551Ctrl::StartOne()");  
  }
  
  if(ioregister_data[idx]->device_available == false){
    try{
      ioregister_data[idx]->proxy->ping();
      ioregister_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      ioregister_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "TIP551Ctrl Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"TIP551Ctrl_BadCtrlPtr",o.str(),
				     (const char *)"TIP551Ctrl::SetExtraAttributeParameter()"); 
    }
  }

  if (par_name == "VoltageMax"){
    Tango::DeviceAttribute da_con("VoltageMax",new_value.db_data );
    if (new_value.data_type == Controller::DOUBLE)
      ioregister_data[idx]->proxy->write_attribute(da_con);
    else
      bad_data_type(par_name);
  } else if (par_name == "VoltageMin"){
    Tango::DeviceAttribute da_con("VoltageMin",new_value.db_data );
    if (new_value.data_type == Controller::DOUBLE)
      ioregister_data[idx]->proxy->write_attribute(da_con);
    else
      bad_data_type(par_name);
  } else {
    TangoSys_OMemStream o;
    o << "Extra attribute " << par_name << " is unknown for controller TIP551Ctrl/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"TIP551Ctrl_BadCtrlPtr",o.str(),
				   (const char *)"TIP551Ctrl::SetExtraAttributePar()");
  }


}


//-----------------------------------------------------------------------------
//
// method : 		TIP551Ctrl::send_to_ctrl
// 
// description : 	Send a string to the controller
//
// arg(s) : - in_str : the string to send to the ctrl
//
//-----------------------------------------------------------------------------

string TIP551Ctrl::SendToCtrl(string &in_str)
{
    cout << "[TIP551] I have received the string: " << in_str << endl;
    string returned_str("Nothing to do");
    return returned_str;	
}

//-----------------------------------------------------------------------------
//
// method : 		TIP551Ctrl::bad_data_type
// 
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void TIP551Ctrl::bad_data_type(string &par_name)
{
    TangoSys_OMemStream o;
    o << "A wrong data type has been used to set the parameter " << par_name << ends;
    
    Tango::Except::throw_exception((const char *)"TIP551Ctrl_BadParameter",o.str(),
				   (const char *)"TIP551Ctrl::SetPar()");
}

//
//===============================================================================================
//

const char *IORegister_Ctrl_class_name[] = {"TIP551Ctrl",NULL};

const char *TIP551Ctrl_doc = "This is the C++ controller for the TIP551Ctrl class";
const char *TIP551Ctrl_gender = "TIP551Ctrl";
const char *TIP55Ctrl1_model = "TIP551Ctrl";
const char *TIP551Ctrl_image = "fake_com.png";
const char *TIP551Ctrl_organization = "DESY";
const char *TIP551Ctrl_logo = "ALBA_logo.png";


Controller::PropInfo TIP551Ctrl_class_prop[] = {
    {"RootDeviceName","Root name for tango devices","DevString"}, 
    NULL};
							  			 
int32_t TIP551Ctrl_MaxDevice = 97;

extern "C"
{
	
Controller *_create_TIP551Ctrl(const char *inst,vector<Controller::Properties> &prop)
{
	return new TIP551Ctrl(inst,prop);
}

}
