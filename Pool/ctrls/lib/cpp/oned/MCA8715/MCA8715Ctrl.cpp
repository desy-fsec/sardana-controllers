#include <iostream>
#include <MCA8715Ctrl.h>
#include <pool/PoolAPI.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		MCA8715::MCA8715
// 
// description : 	Ctor of the MCA8715 class
//					It retrieve some properties from Tango DB, build a 
//					connection to the Simulated controller and ping it
//					to check if it is alive
//
//-----------------------------------------------------------------------------

MCA8715::MCA8715(const char *inst,vector<Controller::Properties> &prop):
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
	MCA8715Data *mca_data_elem = new MCA8715Data;
	mca_data_elem->tango_device = str_vec[l];
	mca_data_elem->device_available = false;
	mca_data_elem->proxy = NULL;
	mca_data.insert(make_pair(index, mca_data_elem));
	max_device++;
	index++;
      }
    }
  }
  
}

//-----------------------------------------------------------------------------
//
// method : 		MCA8715::~MCA8715
// 
// description : 	Dtor of the MCA8715 Controller class
//
//-----------------------------------------------------------------------------

MCA8715::~MCA8715()
{
  //cout << "[MCA8715] class dtor" << endl;	
  map<int32_t, MCA8715Data*>::iterator ite = mca_data.begin();
  for(;ite != mca_data.end();ite++)
    {
      if(ite->second->proxy != NULL)
	delete ite->second->proxy;
      delete ite->second;		
    }		
  mca_data.clear();
}

//-----------------------------------------------------------------------------
//
// method : 		MCA8715::AddDevice
// 
// description : 	Register a new device for the controller
//					For the simulated controller, this simply means increment
//					motor count
//
//-----------------------------------------------------------------------------

void MCA8715::AddDevice(int32_t idx)
{
	//cout << "[MCA8715] Creating a new OneD with index " << idx << " on controller MCA8715/" << inst_name << endl;
  if(idx > max_device){
    TangoSys_OMemStream o;
    o << "The property 'TangoDevices' has no value for index " << idx << ".";
    o << " Please define a valid tango device before adding a new element to this controller"<< ends;
    
    Tango::Except::throw_exception((const char *)"MCA8715_BadIndex",o.str(),
				   (const char *)"MCA8715::AddDevice()");
  }
  if(mca_data[idx]->device_available == false){
    if(mca_data[idx]->proxy == NULL)
      mca_data[idx]->proxy = new Tango::DeviceProxy(mca_data[idx]->tango_device);
    try{
      mca_data[idx]->proxy->ping();
      mca_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      mca_data[idx]->device_available = false;
    }
  }
}

//-----------------------------------------------------------------------------
//
// method : 		MCA8715::DeleteDevice
// 
// description : 	Unregister a new device for the controller
//					For the simulated controller, this simply means decrement
//					motor count
//
//-----------------------------------------------------------------------------

void MCA8715::DeleteDevice(int32_t idx)
{
  //cout << "[MCA8715] Deleting OneD with index " << idx << " on controller MCA8715/" << inst_name << endl;
  if(idx > max_device){
    TangoSys_OMemStream o;
    o << "Trying to delete an inexisting element(" << idx << ") from the controller." << ends;
    
    Tango::Except::throw_exception((const char *)"MCA8715_BadIndex",o.str(),
				   (const char *)"MCA8715::DeleteDevice()");
  }	
	
  if(mca_data[idx]->proxy != NULL){
    delete mca_data[idx]->proxy;
    mca_data[idx]->proxy = NULL;  
  }
  mca_data[idx]->device_available = false;
}

void MCA8715::PreReadOne(int32_t idx)
{
//  cout << "[MCA8715] In PreReadOne" << endl;
  
  if(mca_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "MCA8715 Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"MCA8715Ctrl_BadCtrlPtr",o.str(),
				   (const char *)"MCA8715::PreReadOne()");  
  }
	
  if(mca_data[idx]->device_available == false){
    try{
      mca_data[idx]->proxy->ping();
      mca_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      mca_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "MCA8715 Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"MCA8715Ctrl_BadCtrlPtr",o.str(),
				     (const char *)"MCA8715::PreReadOne()"); 
    }
  }

  mca_data[idx]->proxy->command_inout("Read");

}

double *MCA8715::ReadOne(int32_t idx)
{
  double *read_value;
  vector<Tango::DevLong> vector_data;
  
//  cout << "[MCA8715] In ReadOne" << endl;
  
  if(mca_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "MCA8715 Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"MCA8715Ctrl_BadCtrlPtr",o.str(),
				   (const char *)"MCA8715::ReadOne()");  
  }
	
  if(mca_data[idx]->device_available == false){
    try{
      mca_data[idx]->proxy->ping();
      mca_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      mca_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "MCA8715 Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"MCA8715Ctrl_BadCtrlPtr",o.str(),
				     (const char *)"MCA8715::ReadOne()"); 
    }
  }

  Tango::DeviceAttribute d_out;

  d_out = mca_data[idx]->proxy->read_attribute("Data");
  d_out >> vector_data;
  read_value =  new double[vector_data.size()];
  for(int i = 0; i < vector_data.size(); i++)
    read_value[i] = (double)vector_data[i];
 
  return read_value;
    
}

void  MCA8715::StartOne(int32_t idx)
{
  
//  cout << "[MCA8715] In StartOne" << endl;
  
  if(mca_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "MCA8715 Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"MCA8715Ctrl_BadCtrlPtr",o.str(),
				   (const char *)"MCA8715::StartOne()");  
  }
	
  if(mca_data[idx]->device_available == false){
    try{
      mca_data[idx]->proxy->ping();
      mca_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      mca_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "MCA8715 Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"MCA8715Ctrl_BadCtrlPtr",o.str(),
				     (const char *)"MCA8715::StartOne()"); 
    }
  }

  mca_data[idx]->proxy->command_inout("Start");

}

void  MCA8715::AbortOne(int32_t idx)
{
  
//  cout << "[MCA8715] In AbortOne" << endl;
  
  if(mca_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "MCA8715 Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"MCA8715Ctrl_BadCtrlPtr",o.str(),
				   (const char *)"MCA8715::AbortOne()");  
  }
	
  if(mca_data[idx]->device_available == false){
    try{
      mca_data[idx]->proxy->ping();
      mca_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      mca_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "MCA8715 Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"MCA8715Ctrl_BadCtrlPtr",o.str(),
				     (const char *)"MCA8715::AbortOne()"); 
    }
  }

  mca_data[idx]->proxy->command_inout("Stop");



}

//-----------------------------------------------------------------------------
//
// method : 		MCA8715::GetState
// 
// description : 	Get one motor status. Motor status means two things :
//					1 - The motor state (Tango sense)
//
// arg(s) : - idx : The motor number (starting at 1)
//			- mot_info_ptr : Pointer to a struct. which will be filled with
//							 motor status
//
//-----------------------------------------------------------------------------

void MCA8715::StateOne(int32_t idx,Controller::CtrlState *ior_info_ptr)
{
  if(mca_data[idx]->proxy == NULL){
    ior_info_ptr->state = Tango::FAULT;
    return;
  }
  
  if(mca_data[idx]->device_available == false){
    try
      {
	mca_data[idx]->proxy->ping();
	mca_data[idx]->device_available = true;	
      }
    catch(Tango::DevFailed &e)
      {
	mca_data[idx]->device_available = false;
	ior_info_ptr->state = Tango::FAULT;
	return;
      }
  }
  
  Tango::DevState s = mca_data[idx]->proxy->state();
  
  if(s == Tango::ON){
    ior_info_ptr->state = Tango::ON;
    ior_info_ptr->status = "The MCA is ready";
  }
  
}

//-----------------------------------------------------------------------------
//
// method : 		MCA8715::GetPar
// 
// description : 	Get a oned exp channel parameter. Actually, 1 parameters is supported.
//					This is DataLength
//
// arg(s) : - idx : The oned exp channel  number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData MCA8715::GetPar(int32_t idx, string &par_name)
{
	//cout << "[MCA8715] Getting parameter " << par_name << " for oned exp channel with index " << idx << " on controller MCA8715/" << inst_name << " (" << DevName << ")" << endl;


  Controller::CtrlData par_value;	
  
  
  string par_name_lower(par_name);
  transform(par_name_lower.begin(),par_name_lower.end(),par_name_lower.begin(),::tolower);
  
  if(mca_data[idx]->proxy == NULL)
    return par_value;
  
  if(mca_data[idx]->device_available == false)
    {
      try
	{
	  mca_data[idx]->proxy->ping();
	  mca_data[idx]->device_available = true;	
	}
      catch(Tango::DevFailed &e)
	{
	  mca_data[idx]->device_available = false;
	  return par_value;
	}
    }
  
  Tango::DeviceAttribute in;
  in = mca_data[idx]->proxy->read_attribute(par_name);
  
  if (par_name_lower == "datalength")
    {
      Tango::DevLong value;
      in >> value;
      par_value.int32_data = (int32_t)value;
      par_value.data_type = Controller::INT32;		
    }  
  else
    {
      TangoSys_OMemStream o;
      o << "Parameter " << par_name << " is unknown for controller MCA8715/" << get_name() << ends;
      
      Tango::Except::throw_exception((const char *)"MCA8715_BadCtrlPtr",o.str(),
				     (const char *)"MCA8715::GetPar()");
    }
  
  return par_value;

}

//-----------------------------------------------------------------------------
//
// method : 		MCA8715::SetPar
// 
// description : 	Set a oned parameter. Actually, 1 parameters is supported.
//					This is DataLength
//
// arg(s) : - idx : The oned exp channel number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void MCA8715::SetPar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{
  //cout << "[MCA8715] Setting parameter " << par_name << " for oned channel with index " << idx << " on controller MCA8715/" << inst_name << " (" << DevName << ")" << endl;
  
  
  string par_name_lower(par_name);
  
  transform(par_name_lower.begin(),par_name_lower.end(),par_name_lower.begin(),::tolower);
  
  if (par_name_lower == "datalength"){
    Tango::DevLong value = (Tango::DevLong)new_value.int32_data;
    Tango::DeviceAttribute out(par_name,value);
    mca_data[idx]->proxy->write_attribute(out);
  }
  else{
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " is unknown for controller MC8715Controller/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"MCA8715_BadCtrlPtr",o.str(),
				   (const char *)"MCA8715::SetPar()");
  }
  
}


//-----------------------------------------------------------------------------
//
// method : 		MCA8715::GetExtraAttributePar
// 
// description : 	Get a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData MCA8715::GetExtraAttributePar(int32_t idx, string &par_name)
{


  Controller::CtrlData par_value;	
  
  string par_name_lower(par_name);
  transform(par_name_lower.begin(),par_name_lower.end(),par_name_lower.begin(),::tolower);
  
  if(mca_data[idx]->proxy == NULL)
    return par_value;
  
 		
  if(mca_data[idx]->device_available == false){
    try
      {
	mca_data[idx]->proxy->ping();
	mca_data[idx]->device_available = true;	
      }
    catch(Tango::DevFailed &e)
      {
	mca_data[idx]->device_available = false;
	return par_value;
      }
  }
  
  Tango::DeviceAttribute in;
  in = mca_data[idx]->proxy->read_attribute(par_name);
  
  		
  if (par_name_lower == "bankid"){
    Tango::DevLong value;
    in >> value;
    par_value.int32_data = value;
    par_value.data_type = Controller::INT32;
  } else if( par_name_lower == "clear"){ 
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " can not be readout" << ends;
    
    Tango::Except::throw_exception((const char *)"MCA8715_BadCtrlPtr",o.str(),
				   (const char *)"MCA8715::GetExtraAttributePar()");    
  } else {
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " is unknown for controller RemotePyTangoSerialController/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"MCA8715_BadCtrlPtr",o.str(),
				   (const char *)"MCA8715::GetPar()");
  }
  
  return par_value;
	
}

//-----------------------------------------------------------------------------
//
// method : 		MCA8715::SetExtraAttributePar
// 
// description : 	Set a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void MCA8715::SetExtraAttributePar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{  
  string par_name_lower(par_name);
  
  transform(par_name_lower.begin(),par_name_lower.end(),par_name_lower.begin(),::tolower);
  
  if (par_name_lower == "bankid"){
    Tango::DevLong value = (Tango::DevLong)new_value.int32_data;
    Tango::DeviceAttribute out(par_name,value);
    mca_data[idx]->proxy->write_attribute(out);
  } else if (par_name_lower == "clear"){    
    mca_data[idx]->proxy->command_inout(par_name);
  }else{
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " is unknown for controller MC8715Controller/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"MCA8715_BadCtrlPtr",o.str(),
				   (const char *)"MCA8715::SetExtraAttributePars()");
  }

}


//-----------------------------------------------------------------------------
//
// method : 		MCA8715::send_to_ctrl
// 
// description : 	Send a string to the controller
//
// arg(s) : - in_str : the string to send to the ctrl
//
//-----------------------------------------------------------------------------

string MCA8715::SendToCtrl(string &in_str)
{
//	cout << "[MCA8715] I have received the string: " << in_str << endl;
	string returned_str("Hasta luego");
	return returned_str;	
}

//-----------------------------------------------------------------------------
//
// method : 		MCA8715::bad_data_type
// 
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void MCA8715::bad_data_type(string &par_name)
{
	TangoSys_OMemStream o;
	o << "A wrong data type has been used to set the parameter " << par_name << ends;

	Tango::Except::throw_exception((const char *)"MCA8715Ctrl_BadParameter",o.str(),
			       			   	   (const char *)"MCA8715::SetPar()");
}

//
//===============================================================================================
//

const char *OneDExpChannel_Ctrl_class_name[] = {"MCA8715",NULL};

const char *MCA8715_doc = "This is the C++ controller for the MCA8715 class";
const char *MCA8715_gender = "MCA8715";
const char *MCA8715_model = "MCA8715";
const char *MCA8715_image = "fake_com.png";
const char *MCA8715_organization = "DESY";
const char *MCA8715_logo = "ALBA_logo.png";

Controller::ExtraAttrInfo MCA8715_ctrl_extra_attributes[] = {
	{"Clear","DevLong","Read_Write"},
    {"BankId","DevLong","Read_Write"},
	NULL};

Controller::PropInfo MCA8715_class_prop[] = {
	{"TangoDevices","MCA8715 device names","DevVarStringArray",NULL},
	NULL};
							  			 
int32_t MCA8715_MaxDevice = 97;

extern "C"
{
	
Controller *_create_MCA8715(const char *inst,vector<Controller::Properties> &prop)
{
	return new MCA8715(inst,prop);
}

}
