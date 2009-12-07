#include <iostream>
#include <XIACtrl.h>
#include <pool/PoolAPI.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		XIA::XIA
// 
// description : 	Ctor of the XIA class
//					It retrieve some properties from Tango DB, build a 
//					connection to the Simulated controller and ping it
//					to check if it is alive
//
//-----------------------------------------------------------------------------

XIA::XIA(const char *inst,vector<Controller::Properties> &prop):
OneDController(inst)
{
  max_device = 0;
  vector<Controller::Properties>::iterator prop_it;
  for (prop_it = prop.begin(); prop_it != prop.end(); ++prop_it){
    if(prop_it->name == "TangoDevices"){
      int index = 1;
      vector<string> &str_vec = prop_it->value.string_prop;
      
      for(unsigned long l = 0; l < str_vec.size(); l++){
	// all possible serial lines will be defined here
	XIAData *xia_data_elem = new XIAData;
	xia_data_elem->tango_device = str_vec[l];
	xia_data_elem->device_available = false;
	xia_data_elem->proxy = NULL;
	xia_data.insert(make_pair(index, xia_data_elem));
	max_device++;
	index++;
      }
    }
  }
  
}

//-----------------------------------------------------------------------------
//
// method : 		XIA::~XIA
// 
// description : 	Dtor of the XIA Controller class
//
//-----------------------------------------------------------------------------

XIA::~XIA()
{
  //cout << "[XIA] class dtor" << endl;	
  map<int32_t, XIAData*>::iterator ite = xia_data.begin();
  for(;ite != xia_data.end();ite++)
    {
      if(ite->second->proxy != NULL)
	delete ite->second->proxy;
      delete ite->second;		
    }		
  xia_data.clear();
}

//-----------------------------------------------------------------------------
//
// method : 		XIA::AddDevice
// 
// description : 	Register a new device for the controller
//					For the simulated controller, this simply means increment
//					motor count
//
//-----------------------------------------------------------------------------

void XIA::AddDevice(int32_t idx)
{
	//cout << "[XIA] Creating a new OneD with index " << idx << " on controller XIA/" << inst_name << endl;	
  cout << " Teresa en AddDevice: idx " << idx << endl;
  if(idx > max_device){
    TangoSys_OMemStream o;
    o << "The property 'TangoDevices' has no value for index " << idx << ".";
    o << " Please define a valid tango device before adding a new element to this controller"<< ends;
    
    Tango::Except::throw_exception((const char *)"XIA_BadIndex",o.str(),
				   (const char *)"XIA::AddDevice()");
  }
  if(xia_data[idx]->device_available == false){
    if(xia_data[idx]->proxy == NULL)
      xia_data[idx]->proxy = new Tango::DeviceProxy(xia_data[idx]->tango_device);
    try{
      xia_data[idx]->proxy->ping();
      xia_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      xia_data[idx]->device_available = false;
    }
  }
}

//-----------------------------------------------------------------------------
//
// method : 		XIA::DeleteDevice
// 
// description : 	Unregister a new device for the controller
//					For the simulated controller, this simply means decrement
//					motor count
//
//-----------------------------------------------------------------------------

void XIA::DeleteDevice(int32_t idx)
{
  //cout << "[XIA] Deleting OneD with index " << idx << " on controller XIA/" << inst_name << endl;
  if(idx > max_device){
    TangoSys_OMemStream o;
    o << "Trying to delete an inexisting element(" << idx << ") from the controller." << ends;
    
    Tango::Except::throw_exception((const char *)"XIA_BadIndex",o.str(),
				   (const char *)"XIA::DeleteDevice()");
  }	
	
  if(xia_data[idx]->proxy != NULL){
    delete xia_data[idx]->proxy;
    xia_data[idx]->proxy = NULL;  
  }
  xia_data[idx]->device_available = false;
}

void XIA::PreReadOne(int32_t idx)
{
  cout << "[XIA] In PreReadOne" << endl;
  
  if(xia_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "XIA Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"XIACtrl_BadCtrlPtr",o.str(),
				   (const char *)"XIA::PreReadOne()");  
  }
	
  if(xia_data[idx]->device_available == false){
    try{
      xia_data[idx]->proxy->ping();
      xia_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      xia_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "XIA Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"XIACtrl_BadCtrlPtr",o.str(),
				     (const char *)"XIA::PreReadOne()"); 
    }
  }

  xia_data[idx]->proxy->command_inout("Stop");

}

double *XIA::ReadOne(int32_t idx)
{
  double *read_value;
  vector<Tango::DevLong> vector_data;
  
  cout << "[XIA] In ReadOne" << endl;
  
  if(xia_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "XIA Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"XIACtrl_BadCtrlPtr",o.str(),
				   (const char *)"XIA::ReadOne()");  
  }
	
  if(xia_data[idx]->device_available == false){
    try{
      xia_data[idx]->proxy->ping();
      xia_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      xia_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "XIA Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"XIACtrl_BadCtrlPtr",o.str(),
				     (const char *)"XIA::ReadOne()"); 
    }
  }

  Tango::DeviceAttribute d_out;

  d_out = xia_data[idx]->proxy->read_attribute("Spectrum");
  d_out >> vector_data;
  read_value =  new double[vector_data.size()];
  for(int i = 0; i < vector_data.size(); i++)
    read_value[i] = (double)vector_data[i];
 
  return read_value;
    
}

void  XIA::StartOne(int32_t idx)
{
  
  cout << "[XIA] In StartOne" << endl;
  
  if(xia_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "XIA Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"XIACtrl_BadCtrlPtr",o.str(),
				   (const char *)"XIA::StartOne()");  
  }
	
  if(xia_data[idx]->device_available == false){
    try{
      xia_data[idx]->proxy->ping();
      xia_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      xia_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "XIA Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"XIACtrl_BadCtrlPtr",o.str(),
				     (const char *)"XIA::StartOne()"); 
    }
  }

  xia_data[idx]->proxy->command_inout("Start");

}

void  XIA::AbortOne(int32_t idx)
{
  
  cout << "[XIA] In AbortOne" << endl;
  
  if(xia_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "XIA Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"XIACtrl_BadCtrlPtr",o.str(),
				   (const char *)"XIA::AbortOne()");  
  }
	
  if(xia_data[idx]->device_available == false){
    try{
      xia_data[idx]->proxy->ping();
      xia_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      xia_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "XIA Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"XIACtrl_BadCtrlPtr",o.str(),
				     (const char *)"XIA::AbortOne()"); 
    }
  }

  xia_data[idx]->proxy->command_inout("Stop");



}

//-----------------------------------------------------------------------------
//
// method : 		XIA::GetState
// 
// description : 	Get one motor status. Motor status means two things :
//					1 - The motor state (Tango sense)
//
// arg(s) : - idx : The motor number (starting at 1)
//			- mot_info_ptr : Pointer to a struct. which will be filled with
//							 motor status
//
//-----------------------------------------------------------------------------

void XIA::StateOne(int32_t idx,Controller::CtrlState *ior_info_ptr)
{
  if(xia_data[idx]->proxy == NULL){
    ior_info_ptr->state = Tango::FAULT;
    return;
  }
  
  if(xia_data[idx]->device_available == false){
    try
      {
	xia_data[idx]->proxy->ping();
	xia_data[idx]->device_available = true;	
      }
    catch(Tango::DevFailed &e)
      {
	xia_data[idx]->device_available = false;
	ior_info_ptr->state = Tango::FAULT;
	return;
      }
  }
  
  Tango::DevState s = xia_data[idx]->proxy->state();
  
  if(s == Tango::ON){
    ior_info_ptr->state = Tango::ON;
    ior_info_ptr->status = "The XIA is ready";
  }
  
}

//-----------------------------------------------------------------------------
//
// method : 		XIA::GetPar
// 
// description : 	Get a oned exp channel parameter. Actually, 1 parameters is supported.
//					This is DataLength
//
// arg(s) : - idx : The oned exp channel  number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData XIA::GetPar(int32_t idx, string &par_name)
{
	//cout << "[XIA] Getting parameter " << par_name << " for oned exp channel with index " << idx << " on controller XIA/" << inst_name << " (" << DevName << ")" << endl;


  Controller::CtrlData par_value;	
  
  
  string par_name_lower(par_name);
  transform(par_name_lower.begin(),par_name_lower.end(),par_name_lower.begin(),::tolower);
  
  if(xia_data[idx]->proxy == NULL)
    return par_value;
  
  if(xia_data[idx]->device_available == false)
    {
      try
	{
	  xia_data[idx]->proxy->ping();
	  xia_data[idx]->device_available = true;	
	}
      catch(Tango::DevFailed &e)
	{
	  xia_data[idx]->device_available = false;
	  return par_value;
	}
    }
  
  Tango::DeviceAttribute in;
  
  if (par_name_lower == "datalength")
    {
      Tango::DevLong value;
      in = xia_data[idx]->proxy->read_attribute("McaLength");
      in >> value;
      par_value.int32_data = (int32_t)value;
      par_value.data_type = Controller::INT32;		
    }  
  else
    {
      TangoSys_OMemStream o;
      o << "Parameter " << par_name << " is unknown for controller XIA/" << get_name() << ends;
      
      Tango::Except::throw_exception((const char *)"XIA_BadCtrlPtr",o.str(),
				     (const char *)"XIA::GetPar()");
    }
  
  return par_value;

}

//-----------------------------------------------------------------------------
//
// method : 		XIA::SetPar
// 
// description : 	Set a oned parameter. Actually, 1 parameters is supported.
//					This is DataLength
//
// arg(s) : - idx : The oned exp channel number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void XIA::SetPar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{
  //cout << "[XIA] Setting parameter " << par_name << " for oned channel with index " << idx << " on controller XIA/" << inst_name << " (" << DevName << ")" << endl;
  
  
  string par_name_lower(par_name);
  
  transform(par_name_lower.begin(),par_name_lower.end(),par_name_lower.begin(),::tolower);
  
  if (par_name_lower == "datalength"){
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " can not be written for controller XIAController/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"XIA_BadCtrlPtr",o.str(),
				   (const char *)"XIA::SetPar()");
  }else{
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " is unknown for controller XIAController/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"XIA_BadCtrlPtr",o.str(),
				   (const char *)"XIA::SetPar()");
  }
  
}


//-----------------------------------------------------------------------------
//
// method : 		XIA::GetExtraAttributePar
// 
// description : 	Get a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData XIA::GetExtraAttributePar(int32_t idx, string &par_name)
{


  Controller::CtrlData par_value;	
  
  string par_name_lower(par_name);
  transform(par_name_lower.begin(),par_name_lower.end(),par_name_lower.begin(),::tolower);
  
  if(xia_data[idx]->proxy == NULL)
    return par_value;
  
 		
  if(xia_data[idx]->device_available == false){
    try
      {
	xia_data[idx]->proxy->ping();
	xia_data[idx]->device_available = true;	
      }
    catch(Tango::DevFailed &e)
      {
	xia_data[idx]->device_available = false;
	return par_value;
      }
  }
  
  Tango::DeviceAttribute in;
  in = xia_data[idx]->proxy->read_attribute(par_name);
  
  if( par_name_lower == "clear"){ 
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " can not be readout" << ends;
    
    Tango::Except::throw_exception((const char *)"XIA_BadCtrlPtr",o.str(),
				   (const char *)"XIA::GetExtraAttributePar()");    
  } else {
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " is unknown for controller RemotePyTangoSerialController/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"XIA_BadCtrlPtr",o.str(),
				   (const char *)"XIA::GetPar()");
  }
  
  return par_value;
	
}

//-----------------------------------------------------------------------------
//
// method : 		XIA::SetExtraAttributePar
// 
// description : 	Set a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void XIA::SetExtraAttributePar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{  
  string par_name_lower(par_name);
  
  transform(par_name_lower.begin(),par_name_lower.end(),par_name_lower.begin(),::tolower);
  
  if (par_name_lower == "clear"){    
    xia_data[idx]->proxy->command_inout(par_name);
  }else{
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " is unknown for controller XIAController/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"XIA_BadCtrlPtr",o.str(),
				   (const char *)"XIA::SetExtraAttributePars()");
  }

}


//-----------------------------------------------------------------------------
//
// method : 		XIA::send_to_ctrl
// 
// description : 	Send a string to the controller
//
// arg(s) : - in_str : the string to send to the ctrl
//
//-----------------------------------------------------------------------------

string XIA::SendToCtrl(string &in_str)
{
	cout << "[XIA] I have received the string: " << in_str << endl;
	string returned_str("Hasta luego");
	return returned_str;	
}

//-----------------------------------------------------------------------------
//
// method : 		XIA::bad_data_type
// 
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void XIA::bad_data_type(string &par_name)
{
	TangoSys_OMemStream o;
	o << "A wrong data type has been used to set the parameter " << par_name << ends;

	Tango::Except::throw_exception((const char *)"XIACtrl_BadParameter",o.str(),
			       			   	   (const char *)"XIA::SetPar()");
}

//
//===============================================================================================
//

const char *OneDExpChannel_Ctrl_class_name[] = {"XIA",NULL};

const char *XIA_doc = "This is the C++ controller for the XIA class";
const char *XIA_gender = "XIA";
const char *XIA_model = "XIA";
const char *XIA_image = "fake_com.png";
const char *XIA_organization = "DESY";
const char *XIA_logo = "ALBA_logo.png";

Controller::ExtraAttrInfo XIA_ctrl_extra_attributes[] = {
  {"Clear","DevLong","Read_Write"},
  NULL};

Controller::PropInfo XIA_class_prop[] = {
  {"TangoDevices","XIA device names","DevVarStringArray",NULL},
  NULL};

int32_t XIA_MaxDevice = 97;

extern "C"
{
	
Controller *_create_XIA(const char *inst,vector<Controller::Properties> &prop)
{
	return new XIA(inst,prop);
}

}
