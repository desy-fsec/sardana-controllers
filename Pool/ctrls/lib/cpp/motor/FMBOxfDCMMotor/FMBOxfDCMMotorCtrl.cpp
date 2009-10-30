#include <iostream>
#include <FMBOxfDCMMotorCtrl.h>
#include <pool/PoolAPI.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		FMBOxfDCMMotor::FMBOxfDCMMotor
// 
// description : 	Ctor of the FMBOxfDCMMotor class
//					It retrieve some properties from Tango DB, build a 
//					connection to the Simulated controller and ping it
//					to check if it is alive
//
//-----------------------------------------------------------------------------

FMBOxfDCMMotor::FMBOxfDCMMotor(const char *inst,vector<Controller::Properties> &prop):MotorController(inst)
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
	FMBOxfDCMMotorData *motor_data_elem = new FMBOxfDCMMotorData;
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
// method : 		FMBOxfDCMMotor::~FMBOxfDCMMotor
// 
// description : 	Dtor of the FMBOxfDCMMotor Controller class
//
//-----------------------------------------------------------------------------

FMBOxfDCMMotor::~FMBOxfDCMMotor()
{
  //cout << "[FMBOxfDCMMotor] class dtor" << endl;	
  map<int32_t, FMBOxfDCMMotorData*>::iterator ite = motor_data.begin();
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
// method : 		FMBOxfDCMMotor::AddDevice
// 
// description : 	Register a new device for the controller
//					For the simulated controller, this simply means increment
//					motor count
//
//-----------------------------------------------------------------------------

void FMBOxfDCMMotor::AddDevice(int32_t idx)
{
  //cout << "[FMBOxfDCMMotor] Creating a new Motor with index " << idx << " on controller FMBOxfDCMMotor/" << inst_name << endl;	

  if(idx > max_device){
    TangoSys_OMemStream o;
    o << "The property 'RootDeviceName' has no found element with index " << idx << ".";
    o << " Please check the number of devices found"<< ends;
    
    Tango::Except::throw_exception((const char *)"FMBOxfDCMMotor_BadIndex",o.str(),
				   (const char *)"FMBOxfDCMMotor::AddDevice()");
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
// method : 		FMBOxfDCMMotor::DeleteDevice
// 
// description : 	Unregister a new device for the controller
//					For the simulated controller, this simply means decrement
//					motor count
//
//-----------------------------------------------------------------------------

void FMBOxfDCMMotor::DeleteDevice(int32_t idx)
{
  //cout << "[FMBOxfDCMMotor] Deleting OneD with index " << idx << " on controller FMBOxfDCMMotor/" << inst_name << endl;
  if(idx > max_device){
    TangoSys_OMemStream o;
    o << "Trying to delete an inexisting element(" << idx << ") from the controller." << ends;
    
    Tango::Except::throw_exception((const char *)"FMBOxfDCMMotor_BadIndex",o.str(),
				   (const char *)"FMBOxfDCMMotor::DeleteDevice()");
  }	
	
  if(motor_data[idx]->proxy != NULL){
    delete motor_data[idx]->proxy;
    motor_data[idx]->proxy = NULL;  
  }
  motor_data[idx]->device_available = false;
}



void  FMBOxfDCMMotor::AbortOne(int32_t idx)
{
  
  cout << "[FMBOxfDCMMotor] In AbortOne" << endl;
  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "FMBOxfDCMMotor Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"FMBOxfDCMMotorCtrl_BadCtrlPtr",o.str(),
				   (const char *)"FMBOxfDCMMotor::AbortOne()");  
  }
	
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "FMBOxfDCMMotor Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"FMBOxfDCMMotorCtrl_BadCtrlPtr",o.str(),
				     (const char *)"FMBOxfDCMMotor::AbortOne()"); 
    }
  }

  // Still not implemented
  //  motor_data[idx]->proxy->command_inout("StopMove");

}

void  FMBOxfDCMMotor::DefinePosition(int32_t idx, double new_pos)
{
  
  cout << "[FMBOxfDCMMotor] In DefinePosition - Set to this value the current position" << endl;
  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "FMBOxfDCMMotor Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"FMBOxfDCMMotorCtrl_BadCtrlPtr",o.str(),
				   (const char *)"FMBOxfDCMMotor::DefinePosition()");  
  }
	
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "FMBOxfDCMMotor Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"FMBOxfDCMMotorCtrl_BadCtrlPtr",o.str(),
				     (const char *)"FMBOxfDCMMotor::DefinePosition()"); 
    }
  }

  Tango::DeviceData d_in;
  d_in << new_pos;
  motor_data[idx]->proxy->command_inout("Calibrate",d_in);
  
}


//-----------------------------------------------------------------------------
//
// method : 		FMBOxfDCMMotor::ReadPosition
// 
// description : 	Read a motor position
//
// arg(s) : - idx : The motor number (starting at 1)
//
// This method returns the motor position
//-----------------------------------------------------------------------------



double FMBOxfDCMMotor::ReadOne(int32_t idx)
{
  //  cout << "[FMBOxfDCMMotor] In ReadOne" << endl;
  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "FMBOxfDCMMotor Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"FMBOxfDCMMotorCtrl_BadCtrlPtr",o.str(),
				   (const char *)"FMBOxfDCMMotor::ReadOne()");  
  }
	
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "FMBOxfDCMMotor Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"FMBOxfDCMMotorCtrl_BadCtrlPtr",o.str(),
				     (const char *)"FMBOxfDCMMotor::ReadOne()"); 
    }
  }

  Tango::DeviceAttribute d_out;
  double value;

  d_out = motor_data[idx]->proxy->read_attribute("Position");
  d_out >> value;
 
  return value;

}


//-----------------------------------------------------------------------------
//
// method : 	       FMBOxfDCMMotor::PreStartAll
// 
// description : 	Init movement data
//
//-----------------------------------------------------------------------------
	
void FMBOxfDCMMotor::PreStartAll()
{
	//cout << "[FMBOxfDCMMotor] PreStartAll on controller FMBOxfDCMMotor/" << inst_name << " (" << DevName << ")" << endl;
	
	wanted_mot_pos.clear();
	wanted_mot.clear();
}


void  FMBOxfDCMMotor::StartOne(int32_t idx, double new_pos)
{
  
  //  cout << "[FMBOxfDCMMotor] In StartOne" << endl;
  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "FMBOxfDCMMotor Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"FMBOxfDCMMotorCtrl_BadCtrlPtr",o.str(),
				   (const char *)"FMBOxfDCMMotor::StartOne()");  
  }
	
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "FMBOxfDCMMotor Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"FMBOxfDCMMotorCtrl_BadCtrlPtr",o.str(),
				     (const char *)"FMBOxfDCMMotor::StartOne()"); 
    }
  }

  wanted_mot_pos.push_back(new_pos);
  wanted_mot.push_back(idx);

}


void  FMBOxfDCMMotor::StartAll()
{
  
  //  cout << "[FMBOxfDCMMotor] In StartAll" << endl;
  
  
  int idx;
  double position;

  Tango::DevDouble value;
  
  int32_t nb_mot = wanted_mot.size();
  
  for (int32_t loop = 0;loop < nb_mot;loop++)
    {
      
      idx = wanted_mot[loop];
      position = wanted_mot_pos[loop];

      if(motor_data[idx]->proxy == NULL){
	TangoSys_OMemStream o;
	o << "FMBOxfDCMMotor Device Proxy for idx " << idx << " is NULL" << ends;	
	Tango::Except::throw_exception((const char *)"FMBOxfDCMMotorCtrl_BadCtrlPtr",o.str(),
				       (const char *)"FMBOxfDCMMotor::StartOne()");  
      }
      
      if(motor_data[idx]->device_available == false){
	try{
	  motor_data[idx]->proxy->ping();
	  motor_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
	  motor_data[idx]->device_available = false;
	  TangoSys_OMemStream o;
	  o << "FMBOxfDCMMotor Device for idx " << idx << " not available" << ends;	
	  Tango::Except::throw_exception((const char *)"FMBOxfDCMMotorCtrl_BadCtrlPtr",o.str(),
					 (const char *)"FMBOxfDCMMotor::StartOne()"); 
	}
      }


      value = position;

      Tango::DeviceAttribute da("Position",value);
      motor_data[idx]->proxy->write_attribute(da);

    }
}

//-----------------------------------------------------------------------------
//
// method : 		FMBOxfDCMMotor::GetState
// 
// description : 	Get one motor status. Motor status means two things :
//					1 - The motor state (Tango sense)
//
// arg(s) : - idx : The motor number (starting at 1)
//			- mot_info_ptr : Pointer to a struct. which will be filled with
//							 motor status
//
//-----------------------------------------------------------------------------

void FMBOxfDCMMotor::StateOne(int32_t idx,Controller::CtrlState *info_ptr)
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
  } else if(s == Tango::UNKNOWN){
    mot_info_ptr->state = Tango::UNKNOWN;
    mot_info_ptr->status = "Controller not able to read motor state";
  }

  mot_info_ptr->switches = 0;
}

//-----------------------------------------------------------------------------
//
// method : 		FMBOxfDCMMotor::GetPar
// 
// description : 	Get a oned exp channel parameter. Actually, 1 parameters is supported.
//					This is DataLength
//
// arg(s) : - idx : The oned exp channel  number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData FMBOxfDCMMotor::GetPar(int32_t idx, string &par_name)
{
	//cout << "[FMBOxfDCMMotor] Getting parameter " << par_name << " for oned motor with index " << idx << " on controller FMBOxfDCMMotor/" << inst_name << " (" << DevName << ")" << endl;

  Controller::CtrlData par_value;
   	
  TangoSys_OMemStream o;
  o << "FMBOxfDCMMotor::GetPar parameter " << par_name << " is not used " << ends;	
  Tango::Except::throw_exception((const char *)"FMBOxfDCMMotorCtrl_BadCtrlPtr",o.str(),
				 (const char *)"FMBOxfDCMMotor::GetPar()");
  
  return par_value;


}

//-----------------------------------------------------------------------------
//
// method : 		FMBOxfDCMMotor::SetPar
// 
// description : 	Set a oned parameter. Actually, 1 parameters is supported.
//					This is DataLength
//
// arg(s) : - idx : The oned exp channel number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void FMBOxfDCMMotor::SetPar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{
  //cout << "[FMBOxfDCMMotor] Setting parameter " << par_name << " for motor with index " << idx << " on controller FMBOxfDCMMotor/" << inst_name << " (" << DevName << ")" << endl;

}


//-----------------------------------------------------------------------------
//
// method : 		FMBOxfDCMMotor::GetExtraAttributePar
// 
// description : 	Get a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData FMBOxfDCMMotor::GetExtraAttributePar(int32_t idx, string &par_name)
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
  Tango::DevDouble tmp_double;
  Tango::DevLong tmp_long;
  
  if (par_name_lower == "positionencoder"){    
    in = motor_data[idx]->proxy->read_attribute("PositionCts");
    in >> tmp_double;
    par_value.db_data = tmp_double;
    par_value.data_type = Controller::DOUBLE;
  } else {
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " is unknown for controller RemotePyTangoSerialController/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"FMBOxfDCMMotor_BadCtrlPtr",o.str(),
				   (const char *)"FMBOxfDCMMotor::GetPar()");
  }
  
  return par_value;
	
}

//-----------------------------------------------------------------------------
//
// method : 		FMBOxfDCMMotor::SetExtraAttributePar
// 
// description : 	Set a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void FMBOxfDCMMotor::SetExtraAttributePar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{  
  string par_name_lower(par_name);
  
  transform(par_name_lower.begin(),par_name_lower.end(),par_name_lower.begin(),::tolower);

  if (par_name_lower == "positionencoder"){
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " can not be set for controller FMBOxfDCMMotorController/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"FMBOxfDCMMotor_BadCtrlPtr",o.str(),
				   (const char *)"FMBOxfDCMMotor::SetExtraAttributePars()");
  } else {
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " is unknown for controller FMBOxfDCMMotorController/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"FMBOxfDCMMotor_BadCtrlPtr",o.str(),
				   (const char *)"FMBOxfDCMMotor::SetExtraAttributePars()");
  }

}


//-----------------------------------------------------------------------------
//
// method : 		FMBOxfDCMMotor::send_to_ctrl
// 
// description : 	Send a string to the controller
//
// arg(s) : - in_str : the string to send to the ctrl
//
//-----------------------------------------------------------------------------

string FMBOxfDCMMotor::SendToCtrl(string &in_str)
{
	cout << "[FMBOxfDCMMotor] I have received the string: " << in_str << endl;
	string returned_str("Nothing to be done");
	return returned_str;	
}

//-----------------------------------------------------------------------------
//
// method : 		FMBOxfDCMMotor::bad_data_type
// 
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void FMBOxfDCMMotor::bad_data_type(string &par_name)
{
	TangoSys_OMemStream o;
	o << "A wrong data type has been used to set the parameter " << par_name << ends;

	Tango::Except::throw_exception((const char *)"FMBOxfDCMMotorCtrl_BadParameter",o.str(),
			       			   	   (const char *)"FMBOxfDCMMotor::SetPar()");
}

//
//===============================================================================================
//

const char *Motor_Ctrl_class_name[] = {"FMBOxfDCMMotor",NULL};

const char *FMBOxfDCMMotor_doc = "This is the C++ controller for the FMBOxfDCMMotor class";
const char *FMBOxfDCMMotor_gender = "FMBOxfDCMMotor";
const char *FMBOxfDCMMotor_model = "FMBOxfDCMMotor";
const char *FMBOxfDCMMotor_image = "fake_com.png";
const char *FMBOxfDCMMotor_organization = "DESY";
const char *FMBOxfDCMMotor_logo = "ALBA_logo.png";

Controller::ExtraAttrInfo FMBOxfDCMMotor_ctrl_extra_attributes[] = {
        {"PositionEncoder","DevDouble","Read_Write"},
	NULL};

Controller::PropInfo FMBOxfDCMMotor_class_prop[] = {
	{"RootDeviceName","Root name for tango devices","DevString",NULL},
	NULL};
							  			 
int32_t FMBOxfDCMMotor_MaxDevice = 97;

extern "C"
{
	
Controller *_create_FMBOxfDCMMotor(const char *inst,vector<Controller::Properties> &prop)
{
	return new FMBOxfDCMMotor(inst,prop);
}

}
