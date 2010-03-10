#include <iostream>
#include <MotorViaADSCtrl.h>
#include <pool/PoolAPI.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		MotorViaADS::MotorViaADS
// 
// description : 	Ctor of the MotorViaADS class
//					It retrieve some properties from Tango DB, build a 
//					connection to the Simulated controller and ping it
//					to check if it is alive
//
//-----------------------------------------------------------------------------

MotorViaADS::MotorViaADS(const char *inst,vector<Controller::Properties> &prop):MotorController(inst)
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
	MotorViaADSData *motor_data_elem = new MotorViaADSData;
	motor_data_elem->tango_device = str_vec[l];
	motor_data_elem->device_available = false;
	motor_data_elem->proxy = NULL;
	motor_data.insert(make_pair(index, motor_data_elem));
	max_device++;
	index++;
      }
    }
  }
  
}

//-----------------------------------------------------------------------------
//
// method : 		MotorViaADS::~MotorViaADS
// 
// description : 	Dtor of the MotorViaADS Controller class
//
//-----------------------------------------------------------------------------

MotorViaADS::~MotorViaADS()
{
  //cout << "[MotorViaADS] class dtor" << endl;	
  map<int32_t, MotorViaADSData*>::iterator ite = motor_data.begin();
  for(;ite != motor_data.end();ite++)
    {
      if(ite->second->proxy != NULL)
	delete ite->second->proxy;
      delete ite->second;		
    }		
  motor_data.clear();
}

//-----------------------------------------------------------------------------
//
// method : 		MotorViaADS::AddDevice
// 
// description : 	Register a new device for the controller
//					For the simulated controller, this simply means increment
//					motor count
//
//-----------------------------------------------------------------------------

void MotorViaADS::AddDevice(int32_t idx)
{
  //cout << "[MotorViaADS] Creating a new Motor with index " << idx << " on controller MotorViaADS/" << inst_name << endl;	

  if(idx > max_device){
    TangoSys_OMemStream o;
    o << "The property 'TangoDevices' has no value for index " << idx << ".";
    o << " Please define a valid tango device before adding a new element to this controller"<< ends;
    
    Tango::Except::throw_exception((const char *)"MotorViaADS_BadIndex",o.str(),
				   (const char *)"MotorViaADS::AddDevice()");
  }
  if(motor_data[idx]->device_available == false){
    if(motor_data[idx]->proxy == NULL)
      motor_data[idx]->proxy = new Tango::DeviceProxy(motor_data[idx]->tango_device);
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
    }
  }
}

//-----------------------------------------------------------------------------
//
// method : 		MotorViaADS::DeleteDevice
// 
// description : 	Unregister a new device for the controller
//					For the simulated controller, this simply means decrement
//					motor count
//
//-----------------------------------------------------------------------------

void MotorViaADS::DeleteDevice(int32_t idx)
{
  //cout << "[MotorViaADS] Deleting OneD with index " << idx << " on controller MotorViaADS/" << inst_name << endl;
  if(idx > max_device){
    TangoSys_OMemStream o;
    o << "Trying to delete an inexisting element(" << idx << ") from the controller." << ends;
    
    Tango::Except::throw_exception((const char *)"MotorViaADS_BadIndex",o.str(),
				   (const char *)"MotorViaADS::DeleteDevice()");
  }	
	
  if(motor_data[idx]->proxy != NULL){
    delete motor_data[idx]->proxy;
    motor_data[idx]->proxy = NULL;  
  }
  motor_data[idx]->device_available = false;
}



void  MotorViaADS::AbortOne(int32_t idx)
{
  
  cout << "[MotorViaADS] In AbortOne" << endl;
  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "MotorViaADS Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"MotorViaADSCtrl_BadCtrlPtr",o.str(),
				   (const char *)"MotorViaADS::AbortOne()");  
  }
	
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "MotorViaADS Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"MotorViaADSCtrl_BadCtrlPtr",o.str(),
				     (const char *)"MotorViaADS::AbortOne()"); 
    }
  }

  motor_data[idx]->proxy->command_inout("StopMove");

}

void  MotorViaADS::DefinePosition(int32_t idx, double new_pos)
{
  
  //  cout << "[MotorViaADS] In DefinePosition - Set to this value the current position" << endl;
     
  Tango::DeviceData d_in;

  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "MotorViaADS Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"MotorViaADSCtrl_BadCtrlPtr",o.str(),
				   (const char *)"MotorViaADS::StartOne()");
  }
  
  if(motor_data[idx]->device_available == false){
    try
      {
	motor_data[idx]->proxy->ping();
	motor_data[idx]->device_available = true;	
      }
    catch(Tango::DevFailed &e)
      {
	motor_data[idx]->device_available = false;
	TangoSys_OMemStream o;
	o << "MotorViaADS Device for idx " << idx << " not available" << ends;	
	Tango::Except::throw_exception((const char *)"MotorViaADSCtrl_BadCtrlPtr",o.str(),
				       (const char *)"MotorViaADS::StartOne()");	
      }
  }
  
  d_in << new_pos;
  motor_data[idx]->proxy->command_inout("Calibrate", d_in);

}


//-----------------------------------------------------------------------------
//
// method : 		MotorViaADS::ReadPosition
// 
// description : 	Read a motor position
//
// arg(s) : - idx : The motor number (starting at 1)
//
// This method returns the motor position
//-----------------------------------------------------------------------------



double MotorViaADS::ReadOne(int32_t idx)
{
  //  cout << "[MotorViaADS] In ReadOne" << endl;
  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "MotorViaADS Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"MotorViaADSCtrl_BadCtrlPtr",o.str(),
				   (const char *)"MotorViaADS::ReadOne()");  
  }
	
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "MotorViaADS Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"MotorViaADSCtrl_BadCtrlPtr",o.str(),
				     (const char *)"MotorViaADS::ReadOne()"); 
    }
  }

  Tango::DeviceAttribute d_out;
  double value;

  d_out = motor_data[idx]->proxy->read_attribute("CurrentUnitPosition");
  d_out >> value;
 
  return value;

}


//-----------------------------------------------------------------------------
//
// method : 	       MotorViaADS::PreStartAll
// 
// description : 	Init movement data
//
//-----------------------------------------------------------------------------
	
void MotorViaADS::PreStartAll()
{
	//cout << "[MotorViaADS] PreStartAll on controller MotorViaADS/" << inst_name << " (" << DevName << ")" << endl;
	
	wanted_mot_pos.clear();
	wanted_mot.clear();
}


void  MotorViaADS::StartOne(int32_t idx, double new_pos)
{
  
  //  cout << "[MotorViaADS] In StartOne" << endl;
  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "MotorViaADS Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"MotorViaADSCtrl_BadCtrlPtr",o.str(),
				   (const char *)"MotorViaADS::StartOne()");  
  }
	
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "MotorViaADS Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"MotorViaADSCtrl_BadCtrlPtr",o.str(),
				     (const char *)"MotorViaADS::StartOne()"); 
    }
  }

  wanted_mot_pos.push_back(new_pos);
  wanted_mot.push_back(idx);

}


void  MotorViaADS::StartAll()
{
  
  //  cout << "[MotorViaADS] In StartAll" << endl;
  

  int32_t nb_mot = wanted_mot.size();
  
  for (int32_t loop = 0;loop < nb_mot;loop++)
    {
      
      Tango::DeviceData d_in;

      int idx = wanted_mot[loop];
      double position = wanted_mot_pos[loop];

      if(motor_data[idx]->proxy == NULL){
	TangoSys_OMemStream o;
	o << "MotorViaADS Device Proxy for idx " << idx << " is NULL" << ends;	
	Tango::Except::throw_exception((const char *)"MotorViaADSCtrl_BadCtrlPtr",o.str(),
				       (const char *)"MotorViaADS::StartOne()");  
      }
      
      if(motor_data[idx]->device_available == false){
	try{
	  motor_data[idx]->proxy->ping();
	  motor_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
	  motor_data[idx]->device_available = false;
	  TangoSys_OMemStream o;
	  o << "MotorViaADS Device for idx " << idx << " not available" << ends;	
	  Tango::Except::throw_exception((const char *)"MotorViaADSCtrl_BadCtrlPtr",o.str(),
					 (const char *)"MotorViaADS::StartOne()"); 
	}
      }
      d_in << position;
      motor_data[idx]->proxy->command_inout("Move", d_in);

    }
}

//-----------------------------------------------------------------------------
//
// method : 		MotorViaADS::GetState
// 
// description : 	Get one motor status. Motor status means two things :
//					1 - The motor state (Tango sense)
//
// arg(s) : - idx : The motor number (starting at 1)
//			- mot_info_ptr : Pointer to a struct. which will be filled with
//							 motor status
//
//-----------------------------------------------------------------------------

void MotorViaADS::StateOne(int32_t idx,Controller::CtrlState *info_ptr)
{
  MotorController::MotorState *mot_info_ptr = static_cast<MotorController::MotorState *>(info_ptr);
  
  if(motor_data[idx]->proxy == NULL){
    mot_info_ptr->state = Tango::FAULT;
    return;
  }
  
  if(motor_data[idx]->device_available == false){
    try
      {
	motor_data[idx]->proxy->ping();
	motor_data[idx]->device_available = true;	
      }
    catch(Tango::DevFailed &e)
      {
	motor_data[idx]->device_available = false;
	mot_info_ptr->state = Tango::FAULT;
	return;
      }
  }
  
  Tango::DevState s = motor_data[idx]->proxy->state();
  Tango::DeviceAttribute d_out;

  if(s == Tango::ON){
    mot_info_ptr->state = Tango::ON;
    mot_info_ptr->status = "Motor is iddle";
  } else if(s == Tango::FAULT){
    mot_info_ptr->state = Tango::FAULT;
    mot_info_ptr->status = "Motor is in error";
  } else if(s == Tango::MOVING){
    mot_info_ptr->state = Tango::MOVING;
    mot_info_ptr->status = "Motor is moving";
  }
  
  Tango::DevLong cwlimit;
  Tango::DevLong ccwlimit;

  int32_t switches;

  d_out = motor_data[idx]->proxy->read_attribute("CwLimit");
  d_out >> cwlimit;

  d_out = motor_data[idx]->proxy->read_attribute("CcwLimit");
  d_out >> ccwlimit;

  switches = 0;

  if(cwlimit)  switches = switches + 2;
  if(ccwlimit)  switches = switches + 4;

  mot_info_ptr->switches = switches;
}

//-----------------------------------------------------------------------------
//
// method : 		MotorViaADS::GetPar
// 
// description : 	Get a oned exp channel parameter. Actually, 1 parameters is supported.
//					This is DataLength
//
// arg(s) : - idx : The oned exp channel  number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData MotorViaADS::GetPar(int32_t idx, string &par_name)
{
	//cout << "[MotorViaADS] Getting parameter " << par_name << " for oned exp channel with index " << idx << " on controller MotorViaADS/" << inst_name << " (" << DevName << ")" << endl;

  Controller::CtrlData par_value;
	
  TangoSys_OMemStream o;
  o << "MotorViaADS::GetPar parameter " << par_name << " is not used " << ends;	
  Tango::Except::throw_exception((const char *)"MotorViaADSCtrl_BadCtrlPtr",o.str(),
				 (const char *)"MotorViaADS::GetPar()");
  
  return par_value;

}

//-----------------------------------------------------------------------------
//
// method : 		MotorViaADS::SetPar
// 
// description : 	Set a oned parameter. Actually, 1 parameters is supported.
//					This is DataLength
//
// arg(s) : - idx : The oned exp channel number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void MotorViaADS::SetPar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{
  //cout << "[MotorViaADS] Setting parameter " << par_name << " for oned channel with index " << idx << " on controller MotorViaADS/" << inst_name << " (" << DevName << ")" << endl;

 
}


//-----------------------------------------------------------------------------
//
// method : 		MotorViaADS::GetExtraAttributePar
// 
// description : 	Get a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData MotorViaADS::GetExtraAttributePar(int32_t idx, string &par_name)
{


  Controller::CtrlData par_value;	
  
  string par_name_lower(par_name);
  transform(par_name_lower.begin(),par_name_lower.end(),par_name_lower.begin(),::tolower);
  
  if(motor_data[idx]->proxy == NULL)
    return par_value;
  
 		
  if(motor_data[idx]->device_available == false){
    try
      {
	motor_data[idx]->proxy->ping();
	motor_data[idx]->device_available = true;	
      }
    catch(Tango::DevFailed &e)
      {
	motor_data[idx]->device_available = false;
	return par_value;
      }
  }
  
  Tango::DeviceAttribute in;
  in = motor_data[idx]->proxy->read_attribute(par_name);
  		
  if (par_name_lower == "flagprotected"){
    Tango::DevLong value;
    in >> value;
    par_value.int32_data = value;
    par_value.data_type = Controller::INT32;
  }  else {
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " is unknown for controller RemotePyTangoSerialController/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"MotorViaADS_BadCtrlPtr",o.str(),
				   (const char *)"MotorViaADS::GetPar()");
  }
  
  return par_value;
	
}

//-----------------------------------------------------------------------------
//
// method : 		MotorViaADS::SetExtraAttributePar
// 
// description : 	Set a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void MotorViaADS::SetExtraAttributePar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{  
  string par_name_lower(par_name);
  
  transform(par_name_lower.begin(),par_name_lower.end(),par_name_lower.begin(),::tolower);
  
  if (par_name_lower == "flagprotected"){
    Tango::DevLong value = (Tango::DevLong)new_value.int32_data;
    Tango::DeviceAttribute out(par_name,value);
    motor_data[idx]->proxy->write_attribute(out);
  } else{
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " is unknown for controller MotorViaADSController/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"MotorViaADS_BadCtrlPtr",o.str(),
				   (const char *)"MotorViaADS::SetExtraAttributePars()");
  }

}


//-----------------------------------------------------------------------------
//
// method : 		MotorViaADS::send_to_ctrl
// 
// description : 	Send a string to the controller
//
// arg(s) : - in_str : the string to send to the ctrl
//
//-----------------------------------------------------------------------------

string MotorViaADS::SendToCtrl(string &in_str)
{
	cout << "[MotorViaADS] I have received the string: " << in_str << endl;
	string returned_str("Nothing to be done");
	return returned_str;	
}

//-----------------------------------------------------------------------------
//
// method : 		MotorViaADS::bad_data_type
// 
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void MotorViaADS::bad_data_type(string &par_name)
{
	TangoSys_OMemStream o;
	o << "A wrong data type has been used to set the parameter " << par_name << ends;

	Tango::Except::throw_exception((const char *)"MotorViaADSCtrl_BadParameter",o.str(),
			       			   	   (const char *)"MotorViaADS::SetPar()");
}

//
//===============================================================================================
//

const char *Motor_Ctrl_class_name[] = {"MotorViaADS",NULL};

const char *MotorViaADS_doc = "This is the C++ controller for the MotorViaADS class";
const char *MotorViaADS_gender = "MotorViaADS";
const char *MotorViaADS_model = "MotorViaADS";
const char *MotorViaADS_image = "fake_com.png";
const char *MotorViaADS_organization = "DESY";
const char *MotorViaADS_logo = "ALBA_logo.png";

Controller::ExtraAttrInfo MotorViaADS_ctrl_extra_attributes[] = {
	{"FlagProtected","DevLong","Read_Write"},
	NULL};

Controller::PropInfo MotorViaADS_class_prop[] = {
	{"RootDeviceName","Root name for tango devices","DevString",NULL},
	NULL};
							  			 
int32_t MotorViaADS_MaxDevice = 97;

extern "C"
{
	
Controller *_create_MotorViaADS(const char *inst,vector<Controller::Properties> &prop)
{
	return new MotorViaADS(inst,prop);
}

}
