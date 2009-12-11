#include <iostream>
#include <CCDPVCAMCtrl.h>
#include <pool/PoolAPI.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		CCDPVCAM::CCDPVCAM
// 
// description : 	Ctor of the CCDPVCAM class
//					It retrieve some properties from Tango DB, build a 
//					connection to the Simulated controller and ping it
//					to check if it is alive
//
//-----------------------------------------------------------------------------

CCDPVCAM::CCDPVCAM(const char *inst,vector<Controller::Properties> &prop):
TwoDController(inst)
{
  max_device = 0;
  vector<Controller::Properties>::iterator prop_it;
  for (prop_it = prop.begin(); prop_it != prop.end(); ++prop_it){
    if(prop_it->name == "TangoDevices"){
      int index = 1;
      vector<string> &str_vec = prop_it->value.string_prop;
      
      for(unsigned long l = 0; l < str_vec.size(); l++){
	// all possible serial lines will be defined here
	CCDPVCAMData *ccdpvcam_data_elem = new CCDPVCAMData;
	ccdpvcam_data_elem->tango_device = str_vec[l];
	ccdpvcam_data_elem->device_available = false;
	ccdpvcam_data_elem->proxy = NULL;
	ccdpvcam_data.insert(make_pair(index, ccdpvcam_data_elem));
	max_device++;
	index++;
      }
    }
  } 

  acq_mode = new int32_t[max_device];
  ::memset(acq_mode, 0,  max_device * sizeof(int32_t));
  
}

//-----------------------------------------------------------------------------
//
// method : 		CCDPVCAM::~CCDPVCAM
// 
// description : 	Dtor of the CCDPVCAM Controller class
//
//-----------------------------------------------------------------------------

CCDPVCAM::~CCDPVCAM()
{
  //cout << "[CCDPVCAM] class dtor" << endl;	
  map<int32_t, CCDPVCAMData*>::iterator ite = ccdpvcam_data.begin();
  for(;ite != ccdpvcam_data.end();ite++)
    {
      if(ite->second->proxy != NULL)
	delete ite->second->proxy;
      delete ite->second;		
    }		
  ccdpvcam_data.clear();
}

//-----------------------------------------------------------------------------
//
// method : 		CCDPVCAM::AddDevice
// 
// description : 	Register a new device for the controller
//					For the simulated controller, this simply means increment
//					motor count
//
//-----------------------------------------------------------------------------

void CCDPVCAM::AddDevice(int32_t idx)
{
	//cout << "[CCDPVCAM] Creating a new TwoD with index " << idx << " on controller CCDPVCAM/" << inst_name << endl;
  if(idx > max_device){
    TangoSys_OMemStream o;
    o << "The property 'TangoDevices' has no value for index " << idx << ".";
    o << " Please define a valid tango device before adding a new element to this controller"<< ends;
    
    Tango::Except::throw_exception((const char *)"CCDPVCAM_BadIndex",o.str(),
				   (const char *)"CCDPVCAM::AddDevice()");
  }
  if(ccdpvcam_data[idx]->device_available == false){
    if(ccdpvcam_data[idx]->proxy == NULL)
      ccdpvcam_data[idx]->proxy = new Tango::DeviceProxy(ccdpvcam_data[idx]->tango_device);
    try{
      ccdpvcam_data[idx]->proxy->ping();
      ccdpvcam_data[idx]->device_available = true;
      acq_mode[idx] = 0; 
    }
    catch(Tango::DevFailed &e){
      ccdpvcam_data[idx]->device_available = false;
    }
  }

  read_value =  new double[2000*2000];
}

//-----------------------------------------------------------------------------
//
// method : 		CCDPVCAM::DeleteDevice
// 
// description : 	Unregister a new device for the controller
//					For the simulated controller, this simply means decrement
//					motor count
//
//-----------------------------------------------------------------------------

void CCDPVCAM::DeleteDevice(int32_t idx)
{
  //cout << "[CCDPVCAM] Deleting TwoD with index " << idx << " on controller CCDPVCAM/" << inst_name << endl;
  if(idx > max_device){
    TangoSys_OMemStream o;
    o << "Trying to delete an inexisting element(" << idx << ") from the controller." << ends;
    
    Tango::Except::throw_exception((const char *)"CCDPVCAM_BadIndex",o.str(),
				   (const char *)"CCDPVCAM::DeleteDevice()");
  }	
	
  if(ccdpvcam_data[idx]->proxy != NULL){
    delete ccdpvcam_data[idx]->proxy;
    ccdpvcam_data[idx]->proxy = NULL;  
  }
  ccdpvcam_data[idx]->device_available = false;
}

void CCDPVCAM::PreReadOne(int32_t idx)
{
}

double *CCDPVCAM::ReadOne(int32_t idx)
{

  
  cout << "[CCDPVCAM] In ReadOne" << endl;

  
  if(ccdpvcam_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "CCDPVCAM Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"CCDPVCAMCtrl_BadCtrlPtr",o.str(),
				   (const char *)"CCDPVCAM::ReadOne()");  
  }
  if(ccdpvcam_data[idx]->device_available == false){
    try{
      ccdpvcam_data[idx]->proxy->ping();
      ccdpvcam_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      ccdpvcam_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "CCDPVCAM Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"CCDPVCAMCtrl_BadCtrlPtr",o.str(),
				     (const char *)"CCDPVCAM::ReadOne()"); 
    }
  }

  Tango::DeviceAttribute d_out;

  d_out = ccdpvcam_data[idx]->proxy->read_attribute("Bild");
  d_out >> vector_data;

  for(int i = 0; i < vector_data.size(); i++)
    read_value[i] = (double)vector_data[i];

  return read_value;
    
}

void  CCDPVCAM::StartOne(int32_t idx)
{
  
  cout << "[CCDPVCAM] In StartOne" << endl;
  
  if(ccdpvcam_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "CCDPVCAM Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"CCDPVCAMCtrl_BadCtrlPtr",o.str(),
				   (const char *)"CCDPVCAM::StartOne()");  
  }
  
  if(ccdpvcam_data[idx]->device_available == false){
    try{
      ccdpvcam_data[idx]->proxy->ping();
      ccdpvcam_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      ccdpvcam_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "CCDPVCAM Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"CCDPVCAMCtrl_BadCtrlPtr",o.str(),
				     (const char *)"CCDPVCAM::StartOne()"); 
    }
  }

  if(acq_mode[idx] == 0){
    ccdpvcam_data[idx]->proxy->command_inout("StartStandardAcq");
  } else if (acq_mode[idx] == 0){
    ccdpvcam_data[idx]->proxy->command_inout("StartContinuousAcq");
  } else if (acq_mode[idx] == 0){
    ccdpvcam_data[idx]->proxy->command_inout("StartFocusAcq");
  }

}

void  CCDPVCAM::AbortOne(int32_t idx)
{
  
  cout << "[CCDPVCAM] In AbortOne" << endl;

}

//-----------------------------------------------------------------------------
//
// method : 		CCDPVCAM::GetState
// 
// description : 	Get one motor status. Motor status means two things :
//					1 - The motor state (Tango sense)
//
// arg(s) : - idx : The motor number (starting at 1)
//			- mot_info_ptr : Pointer to a struct. which will be filled with
//							 motor status
//
//-----------------------------------------------------------------------------

void CCDPVCAM::StateOne(int32_t idx,Controller::CtrlState *ior_info_ptr)
{
  if(ccdpvcam_data[idx]->proxy == NULL){
    ior_info_ptr->state = Tango::FAULT;
    return;
  }
  if(ccdpvcam_data[idx]->device_available == false){
    try
      {
	ccdpvcam_data[idx]->proxy->ping();
	ccdpvcam_data[idx]->device_available = true;	
      }
    catch(Tango::DevFailed &e)
      {
	ccdpvcam_data[idx]->device_available = false;
	ior_info_ptr->state = Tango::FAULT;
	return;
      }
  }
  
  Tango::DevState s = ccdpvcam_data[idx]->proxy->state();
  
  if(s == Tango::OPEN){
    ior_info_ptr->state = Tango::ON;
    ior_info_ptr->status = "The CCDPVCAM is ready";
  } else if (s == Tango::FAULT){
    ior_info_ptr->state = Tango::FAULT;
    ior_info_ptr->status = "TwoD is in FAULT state";
  } else if (s == Tango::RUNNING){
    ior_info_ptr->state = Tango::MOVING;
    ior_info_ptr->status = "TwoD is taking images";
  }
  
}

//-----------------------------------------------------------------------------
//
// method : 		CCDPVCAM::GetPar
// 
// description : 	Get a twod exp channel parameter. Actually, 1 parameters is supported.
//					This is DataLength
//
// arg(s) : - idx : The twod exp channel  number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData CCDPVCAM::GetPar(int32_t idx, string &par_name)
{
  //cout << "[CCDPVCAM] Getting parameter " << par_name << " for twod exp channel with index " << idx << " on controller CCDPVCAM/" << inst_name << " (" << DevName << ")" << endl;
  
  
  Controller::CtrlData par_value;	
  
  
  string par_name_lower(par_name);
  transform(par_name_lower.begin(),par_name_lower.end(),par_name_lower.begin(),::tolower);
  
  if(ccdpvcam_data[idx]->proxy == NULL)
    return par_value;
  
  if(ccdpvcam_data[idx]->device_available == false)
    {
      try
	{
	  ccdpvcam_data[idx]->proxy->ping();
	  ccdpvcam_data[idx]->device_available = true;	
	}
      catch(Tango::DevFailed &e)
	{
	  ccdpvcam_data[idx]->device_available = false;
	  return par_value;
	}
    }
  
  Tango::DeviceAttribute in;
  if (par_name_lower == "xdim"){
    in = ccdpvcam_data[idx]->proxy->read_attribute("Width");
    Tango::DevLong value;
    in >> value;
    par_value.int32_data = (int32_t)value;
    par_value.data_type = Controller::INT32;		
  } else if (par_name_lower == "ydim"){
    in = ccdpvcam_data[idx]->proxy->read_attribute("Height");
    Tango::DevLong value;
    in >> value;
    par_value.int32_data = (int32_t)value;
    par_value.data_type = Controller::INT32;		
  } else if (par_name_lower == "iformat") {
    in = ccdpvcam_data[idx]->proxy->read_attribute("ImageFormat");
    string str_value;
    in >> str_value;
    Tango::DevLong value;
    if(str_value == "UChar"){
      value = 1;
    } else if (str_value == "UShort"){
      value = 2;
    }else {
      value = 3;
    }  
    par_value.int32_data = (int32_t)value;
    par_value.data_type = Controller::INT32;		
  } 
  else
    {
      TangoSys_OMemStream o;
      o << "Parameter " << par_name << " is unknown for controller CCDPVCAM/" << get_name() << ends;
      
      Tango::Except::throw_exception((const char *)"CCDPVCAM_BadCtrlPtr",o.str(),
				     (const char *)"CCDPVCAM::GetPar()");
    }
  
  return par_value;

}

//-----------------------------------------------------------------------------
//
// method : 		CCDPVCAM::SetPar
// 
// description : 	Set a twod parameter. Actually, 1 parameters is supported.
//					This is DataLength
//
// arg(s) : - idx : The twod exp channel number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void CCDPVCAM::SetPar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{
  //cout << "[CCDPVCAM] Setting parameter " << par_name << " for twod channel with index " << idx << " on controller CCDPVCAM/" << inst_name << " (" << DevName << ")" << endl;
  
  
  string par_name_lower(par_name);
  
  transform(par_name_lower.begin(),par_name_lower.end(),par_name_lower.begin(),::tolower);
  
  if (par_name_lower == "xdim"){
    Tango::DevLong value = (Tango::DevLong)new_value.int32_data;
    Tango::DeviceAttribute out("Width",value);
    ccdpvcam_data[idx]->proxy->write_attribute(out);
  } else if (par_name_lower == "ydim"){
    Tango::DevLong value = (Tango::DevLong)new_value.int32_data;
    Tango::DeviceAttribute out("Height",value);
    ccdpvcam_data[idx]->proxy->write_attribute(out);
  } else if (par_name_lower == "iformat"){
    string value = new_value.str_data;
    Tango::DeviceAttribute out("ImageFormat",value);
    ccdpvcam_data[idx]->proxy->write_attribute(out);
  } else{
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " is unknown for controller MC8715Controller/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"CCDPVCAM_BadCtrlPtr",o.str(),
				   (const char *)"CCDPVCAM::SetPar()");
  }
  
}


//-----------------------------------------------------------------------------
//
// method : 		CCDPVCAM::GetExtraAttributePar
// 
// description : 	Get a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData CCDPVCAM::GetExtraAttributePar(int32_t idx, string &par_name)
{

  Controller::CtrlData par_value;	
  
  string par_name_lower(par_name);
  transform(par_name_lower.begin(),par_name_lower.end(),par_name_lower.begin(),::tolower);
    		
  if (par_name_lower == "acqmode"){
    Tango::DevLong value;
    value = acq_mode[idx];
    par_value.int32_data = value;
    par_value.data_type = Controller::INT32;   
  } else {
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " is unknown for controller RemotePyTangoSerialController/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"CCDPVCAM_BadCtrlPtr",o.str(),
				   (const char *)"CCDPVCAM::GetPar()");
  }
  
  return par_value;
	
}

//-----------------------------------------------------------------------------
//
// method : 		CCDPVCAM::SetExtraAttributePar
// 
// description : 	Set a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void CCDPVCAM::SetExtraAttributePar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{  
  string par_name_lower(par_name);
  
  transform(par_name_lower.begin(),par_name_lower.end(),par_name_lower.begin(),::tolower);
  
  if (par_name_lower == "acqmode"){
    Tango::DevLong value = (Tango::DevLong)new_value.int32_data;
    acq_mode[idx] = value; 
  }else{
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " is unknown for controller MC8715Controller/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"CCDPVCAM_BadCtrlPtr",o.str(),
				   (const char *)"CCDPVCAM::SetExtraAttributePars()");
  }

}


//-----------------------------------------------------------------------------
//
// method : 		CCDPVCAM::send_to_ctrl
// 
// description : 	Send a string to the controller
//
// arg(s) : - in_str : the string to send to the ctrl
//
//-----------------------------------------------------------------------------

string CCDPVCAM::SendToCtrl(string &in_str)
{
	cout << "[CCDPVCAM] I have received the string: " << in_str << endl;
	string returned_str("Hasta luego");
	return returned_str;	
}

//-----------------------------------------------------------------------------
//
// method : 		CCDPVCAM::bad_data_type
// 
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void CCDPVCAM::bad_data_type(string &par_name)
{
	TangoSys_OMemStream o;
	o << "A wrong data type has been used to set the parameter " << par_name << ends;

	Tango::Except::throw_exception((const char *)"CCDPVCAMCtrl_BadParameter",o.str(),
			       			   	   (const char *)"CCDPVCAM::SetPar()");
}

//
//===============================================================================================
//

const char *TwoDExpChannel_Ctrl_class_name[] = {"CCDPVCAM",NULL};

const char *CCDPVCAM_doc = "This is the C++ controller for the CCDPVCAM class";
const char *CCDPVCAM_gender = "CCDPVCAM";
const char *CCDPVCAM_model = "CCDPVCAM";
const char *CCDPVCAM_image = "fake_com.png";
const char *CCDPVCAM_organization = "DESY";
const char *CCDPVCAM_logo = "ALBA_logo.png";

Controller::ExtraAttrInfo CCDPVCAM_ctrl_extra_attributes[] = {
  {"AcqMode","DevLong","Read_Write"},
  NULL};

Controller::PropInfo CCDPVCAM_class_prop[] = {
	{"TangoDevices","CCDPVCAM device names","DevVarStringArray",NULL},
	NULL};
							  			 
int32_t CCDPVCAM_MaxDevice = 97;

extern "C"
{
	
Controller *_create_CCDPVCAM(const char *inst,vector<Controller::Properties> &prop)
{
	return new CCDPVCAM(inst,prop);
}

}
