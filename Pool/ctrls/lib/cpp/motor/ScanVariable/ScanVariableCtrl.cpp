#include <iostream>
#include <ScanVariableCtrl.h>
#include <pool/PoolAPI.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		ScanVariable::ScanVariable
// 
// description : 	Controller for any class with a variable that can be scanned
//			It retrieves devices from the DB according 
//                      to the given RootDeviceName and allows to scan the 
//                      variable given in VariableName 
//				      
//
//-----------------------------------------------------------------------------

ScanVariable::ScanVariable(const char *inst,vector<Controller::Properties> &prop):MotorController(inst)
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
	ScanVariableData *motor_data_elem = new ScanVariableData;
	motor_data_elem->tango_device = str_vec[l];
	motor_data_elem->device_available = false;
	motor_data_elem->proxy = NULL;
	motor_data.insert(make_pair(index, motor_data_elem));
	max_device++;
	index++;
      }
    } else if(prop_it->name == "VariableName"){
      variable_name = prop_it->value.string_prop[0];
    } else if(prop_it->name == "StopFunction"){
      stop_function = prop_it->value.string_prop[0];
    } else if(prop_it->name == "VariableType"){
      variable_type = prop_it->value.int32_prop[0];
    }
  }
  
}

//-----------------------------------------------------------------------------
//
// method : 		ScanVariable::~ScanVariable
// 
// description : 	Dtor of the ScanVariable Controller class
//
//-----------------------------------------------------------------------------

ScanVariable::~ScanVariable()
{
  //cout << "[ScanVariable] class dtor" << endl;	
  map<int32_t, ScanVariableData*>::iterator ite = motor_data.begin();
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
// method : 		ScanVariable::AddDevice
// 
// description : 	Register a new device for the controller
//					For the simulated controller, this simply means increment
//					motor count
//
//-----------------------------------------------------------------------------

void ScanVariable::AddDevice(int32_t idx)
{
  //cout << "[ScanVariable] Creating a new Motor with index " << idx << " on controller ScanVariable/" << inst_name << endl;	

  if(idx > max_device){
    TangoSys_OMemStream o;
    o << "The property 'TangoDevices' has no value for index " << idx << ".";
    o << " Please define a valid tango device before adding a new element to this controller"<< ends;
    
    Tango::Except::throw_exception((const char *)"ScanVariable_BadIndex",o.str(),
				   (const char *)"ScanVariable::AddDevice()");
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
// method : 		ScanVariable::DeleteDevice
// 
// description : 	Unregister a new device for the controller
//					For the simulated controller, this simply means decrement
//					motor count
//
//-----------------------------------------------------------------------------

void ScanVariable::DeleteDevice(int32_t idx)
{
  //cout << "[ScanVariable] Deleting OneD with index " << idx << " on controller ScanVariable/" << inst_name << endl;
  if(idx > max_device){
    TangoSys_OMemStream o;
    o << "Trying to delete an inexisting element(" << idx << ") from the controller." << ends;
    
    Tango::Except::throw_exception((const char *)"ScanVariable_BadIndex",o.str(),
				   (const char *)"ScanVariable::DeleteDevice()");
  }	
	
  if(motor_data[idx]->proxy != NULL){
    delete motor_data[idx]->proxy;
    motor_data[idx]->proxy = NULL;  
  }
  motor_data[idx]->device_available = false;
}



void  ScanVariable::AbortOne(int32_t idx)
{
  
  cout << "[ScanVariable] In AbortOne" << endl;
  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "ScanVariable Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"ScanVariableCtrl_BadCtrlPtr",o.str(),
				   (const char *)"ScanVariable::AbortOne()");  
  }
	
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "ScanVariable Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"ScanVariableCtrl_BadCtrlPtr",o.str(),
				     (const char *)"ScanVariable::AbortOne()"); 
    }
  }

  motor_data[idx]->proxy->command_inout(stop_function);

}

void  ScanVariable::DefinePosition(int32_t idx, double new_pos)
{
  
  //  cout << "[ScanVariable] In DefinePosition - Set to this value the current position" << endl;
     
  Tango::DeviceData d_in;

  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "ScanVariable Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"ScanVariableCtrl_BadCtrlPtr",o.str(),
				   (const char *)"ScanVariable::DefinePosition()");
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
	o << "ScanVariable Device for idx " << idx << " not available" << ends;	
	Tango::Except::throw_exception((const char *)"ScanVariableCtrl_BadCtrlPtr",o.str(),
				       (const char *)"ScanVariable::DefinePosition()");	
      }
  }
  
  //  d_in << new_pos;
  //  motor_data[idx]->proxy->command_inout("Calibrate", d_in);

  Tango::Except::throw_exception((const char *)"ScanVariableCtrl","Calibrate not defined",
				 (const char *)"ScanVariable::DefinePosition()");
  
}


//-----------------------------------------------------------------------------
//
// method : 		ScanVariable::ReadPosition
// 
// description : 	Read a motor position
//
// arg(s) : - idx : The motor number (starting at 1)
//
// This method returns the motor position
//-----------------------------------------------------------------------------



double ScanVariable::ReadOne(int32_t idx)
{
  //  cout << "[ScanVariable] In ReadOne" << endl;
  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "ScanVariable Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"ScanVariableCtrl_BadCtrlPtr",o.str(),
				   (const char *)"ScanVariable::ReadOne()");  
  }
	
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "ScanVariable Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"ScanVariableCtrl_BadCtrlPtr",o.str(),
				     (const char *)"ScanVariable::ReadOne()"); 
    }
  }

  Tango::DeviceAttribute d_out;
  Tango::DevDouble d_value;
  Tango::DevFloat  f_value;
  Tango::DevLong   l_value;

  double value;

  d_out = motor_data[idx]->proxy->read_attribute(variable_name);
  if(variable_type == 0){
    d_out >> d_value; 
    value = d_value;
  } else if ( variable_type == 1){
    d_out >> f_value;
    value = (double) f_value;
  } else if ( variable_type == 2){
    d_out >> l_value;
    value = (double) l_value;
  } else {
    d_out >> d_value; 
    value = d_value;
  }

  return value;

}


//-----------------------------------------------------------------------------
//
// method : 	       ScanVariable::PreStartAll
// 
// description : 	Init movement data
//
//-----------------------------------------------------------------------------
	
void ScanVariable::PreStartAll()
{
	//cout << "[ScanVariable] PreStartAll on controller ScanVariable/" << inst_name << " (" << DevName << ")" << endl;
	
	wanted_mot_pos.clear();
	wanted_mot.clear();
}


void  ScanVariable::StartOne(int32_t idx, double new_pos)
{
  
  //  cout << "[ScanVariable] In StartOne" << endl;
  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "ScanVariable Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"ScanVariableCtrl_BadCtrlPtr",o.str(),
				   (const char *)"ScanVariable::StartOne()");  
  }
	
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "ScanVariable Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"ScanVariableCtrl_BadCtrlPtr",o.str(),
				     (const char *)"ScanVariable::StartOne()"); 
    }
  }

  wanted_mot_pos.push_back(new_pos);
  wanted_mot.push_back(idx);

}


void  ScanVariable::StartAll()
{
  
  //  cout << "[ScanVariable] In StartAll" << endl;
  

  int32_t nb_mot = wanted_mot.size();
  
  for (int32_t loop = 0;loop < nb_mot;loop++)
    {
 
      int idx = wanted_mot[loop];

      if(motor_data[idx]->proxy == NULL){
	TangoSys_OMemStream o;
	o << "ScanVariable Device Proxy for idx " << idx << " is NULL" << ends;	
	Tango::Except::throw_exception((const char *)"ScanVariableCtrl_BadCtrlPtr",o.str(),
				       (const char *)"ScanVariable::StartOne()");  
      }
      
      if(motor_data[idx]->device_available == false){
	try{
	  motor_data[idx]->proxy->ping();
	  motor_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
	  motor_data[idx]->device_available = false;
	  TangoSys_OMemStream o;
	  o << "ScanVariable Device for idx " << idx << " not available" << ends;	
	  Tango::Except::throw_exception((const char *)"ScanVariableCtrl_BadCtrlPtr",o.str(),
					 (const char *)"ScanVariable::StartOne()"); 
	}
      }

      if(variable_type == 0) {
	Tango::DevDouble position = wanted_mot_pos[loop];
	Tango::DeviceAttribute da(variable_name,position);
	motor_data[idx]->proxy->write_attribute(da);
      } else if (variable_type == 1) {
	Tango::DevFloat position = (float) wanted_mot_pos[loop];
	Tango::DeviceAttribute da(variable_name,position);
	motor_data[idx]->proxy->write_attribute(da);
      } else if (variable_type == 2) {
	Tango::DevLong position = (long) wanted_mot_pos[loop];
	Tango::DeviceAttribute da(variable_name,position);
	motor_data[idx]->proxy->write_attribute(da);
      }


    }
}

//-----------------------------------------------------------------------------
//
// method : 		ScanVariable::GetState
// 
// description : 	Get one motor status. Motor status means two things :
//					1 - The motor state (Tango sense)
//
// arg(s) : - idx : The motor number (starting at 1)
//			- mot_info_ptr : Pointer to a struct. which will be filled with
//							 motor status
//
//-----------------------------------------------------------------------------

void ScanVariable::StateOne(int32_t idx,Controller::CtrlState *info_ptr)
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

  try{
    d_out = motor_data[idx]->proxy->read_attribute("CwLimit");
    d_out >> cwlimit;
    
    d_out = motor_data[idx]->proxy->read_attribute("CcwLimit");
    d_out >> ccwlimit;	
  }
  catch(Tango::DevFailed &e){
    cwlimit = 0;
    ccwlimit = 0;
  }

  switches = 0;

  if(cwlimit)  switches = switches + 2;
  if(ccwlimit)  switches = switches + 4;

  mot_info_ptr->switches = switches;
}

//-----------------------------------------------------------------------------
//
// method : 		ScanVariable::GetPar
// 
// description : 	Get a oned exp channel parameter. Actually, 1 parameters is supported.
//					This is DataLength
//
// arg(s) : - idx : The oned exp channel  number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData ScanVariable::GetPar(int32_t idx, string &par_name)
{
	//cout << "[ScanVariable] Getting parameter " << par_name << " for oned exp channel with index " << idx << " on controller ScanVariable/" << inst_name << " (" << DevName << ")" << endl;

  Controller::CtrlData par_value;
	
  TangoSys_OMemStream o;
  o << "ScanVariable::GetPar parameter " << par_name << " is not used " << ends;	
  Tango::Except::throw_exception((const char *)"ScanVariableCtrl_BadCtrlPtr",o.str(),
				 (const char *)"ScanVariable::GetPar()");
  
  return par_value;

}

//-----------------------------------------------------------------------------
//
// method : 		ScanVariable::SetPar
// 
// description : 	Set a oned parameter. Actually, 1 parameters is supported.
//					This is DataLength
//
// arg(s) : - idx : The oned exp channel number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void ScanVariable::SetPar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{
  //cout << "[ScanVariable] Setting parameter " << par_name << " for oned channel with index " << idx << " on controller ScanVariable/" << inst_name << " (" << DevName << ")" << endl;

 
}


//-----------------------------------------------------------------------------
//
// method : 		ScanVariable::GetExtraAttributePar
// 
// description : 	Get a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData ScanVariable::GetExtraAttributePar(int32_t idx, string &par_name)
{

  Controller::CtrlData par_value;

  TangoSys_OMemStream o;
  o << "Not extra attribute parameteres for ScanVariable Controller" << ends;
  
  Tango::Except::throw_exception((const char *)"ScanVariable_BadCtrlPtr",o.str(),
				 (const char *)"ScanVariable::GetExtraAttributePar()");
  
  
  return par_value;
	
}

//-----------------------------------------------------------------------------
//
// method : 		ScanVariable::SetExtraAttributePar
// 
// description : 	Set a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void ScanVariable::SetExtraAttributePar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{  

  TangoSys_OMemStream o;
  o << "Not extra attribute parameteres for ScanVariable Controller" << ends;
  
  Tango::Except::throw_exception((const char *)"ScanVariable_BadCtrlPtr",o.str(),
				 (const char *)"ScanVariable::SetExtraAttributePar()");

}


//-----------------------------------------------------------------------------
//
// method : 		ScanVariable::send_to_ctrl
// 
// description : 	Send a string to the controller
//
// arg(s) : - in_str : the string to send to the ctrl
//
//-----------------------------------------------------------------------------

string ScanVariable::SendToCtrl(string &in_str)
{
	cout << "[ScanVariable] I have received the string: " << in_str << endl;
	string returned_str("Nothing to be done");
	return returned_str;	
}

//-----------------------------------------------------------------------------
//
// method : 		ScanVariable::bad_data_type
// 
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void ScanVariable::bad_data_type(string &par_name)
{
	TangoSys_OMemStream o;
	o << "A wrong data type has been used to set the parameter " << par_name << ends;

	Tango::Except::throw_exception((const char *)"ScanVariableCtrl_BadParameter",o.str(),
			       			   	   (const char *)"ScanVariable::SetPar()");
}

//
//===============================================================================================
//

const char *Motor_Ctrl_class_name[] = {"ScanVariable",NULL};

const char *ScanVariable_doc = "This is the C++ controller for the ScanVariable class";
const char *ScanVariable_gender = "ScanVariable";
const char *ScanVariable_model = "ScanVariable";
const char *ScanVariable_image = "fake_com.png";
const char *ScanVariable_organization = "DESY";
const char *ScanVariable_logo = "ALBA_logo.png";

Controller::ExtraAttrInfo ScanVariable_ctrl_extra_attributes[] = {
	NULL};

Controller::PropInfo ScanVariable_class_prop[] = {
	{"RootDeviceName","Root name for tango devices","DevString",NULL},
	{"VariableName","Variable to scan","DevString",NULL},
	{"VariableType","0 double, 1 float, 2 long","DevLong","0"},
	{"StopFunction","Name of the function to stop move","DevString","StopMove"},
	NULL};
							  			 
int32_t ScanVariable_MaxDevice = 97;

extern "C"
{
	
Controller *_create_ScanVariable(const char *inst,vector<Controller::Properties> &prop)
{
	return new ScanVariable(inst,prop);
}

}
