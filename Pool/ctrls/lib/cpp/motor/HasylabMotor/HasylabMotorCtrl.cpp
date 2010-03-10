#include <iostream>
#include <HasylabMotorCtrl.h>
#include <pool/PoolAPI.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		HasylabMotor::HasylabMotor
// 
// description : 	Ctor of the HasylabMotor class
//					It retrieve some properties from Tango DB, build a 
//					connection to the Simulated controller and ping it
//					to check if it is alive
//
//-----------------------------------------------------------------------------

HasylabMotor::HasylabMotor(const char *inst,vector<Controller::Properties> &prop):MotorController(inst)
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
	HasylabMotorData *motor_data_elem = new HasylabMotorData;
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
// method : 		HasylabMotor::~HasylabMotor
// 
// description : 	Dtor of the HasylabMotor Controller class
//
//-----------------------------------------------------------------------------

HasylabMotor::~HasylabMotor()
{
  //cout << "[HasylabMotor] class dtor" << endl;	
  map<int32_t, HasylabMotorData*>::iterator ite = motor_data.begin();
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
// method : 		HasylabMotor::AddDevice
// 
// description : 	Register a new device for the controller
//					For the simulated controller, this simply means increment
//					motor count
//
//-----------------------------------------------------------------------------

void HasylabMotor::AddDevice(int32_t idx)
{
  //cout << "[HasylabMotor] Creating a new Motor with index " << idx << " on controller HasylabMotor/" << inst_name << endl;	

  if(idx > max_device){
    TangoSys_OMemStream o;
    o << "The property 'TangoDevices' has no value for index " << idx << ".";
    o << " Please define a valid tango device before adding a new element to this controller"<< ends;
    
    Tango::Except::throw_exception((const char *)"HasylabMotor_BadIndex",o.str(),
				   (const char *)"HasylabMotor::AddDevice()");
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
// method : 		HasylabMotor::DeleteDevice
// 
// description : 	Unregister a new device for the controller
//					For the simulated controller, this simply means decrement
//					motor count
//
//-----------------------------------------------------------------------------

void HasylabMotor::DeleteDevice(int32_t idx)
{
  //cout << "[HasylabMotor] Deleting OneD with index " << idx << " on controller HasylabMotor/" << inst_name << endl;
  if(idx > max_device){
    TangoSys_OMemStream o;
    o << "Trying to delete an inexisting element(" << idx << ") from the controller." << ends;
    
    Tango::Except::throw_exception((const char *)"HasylabMotor_BadIndex",o.str(),
				   (const char *)"HasylabMotor::DeleteDevice()");
  }	
	
  if(motor_data[idx]->proxy != NULL){
    delete motor_data[idx]->proxy;
    motor_data[idx]->proxy = NULL;  
  }
  motor_data[idx]->device_available = false;
}



void  HasylabMotor::AbortOne(int32_t idx)
{
  
  cout << "[HasylabMotor] In AbortOne" << endl;
  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "HasylabMotor Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"HasylabMotorCtrl_BadCtrlPtr",o.str(),
				   (const char *)"HasylabMotor::AbortOne()");  
  }
	
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "HasylabMotor Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"HasylabMotorCtrl_BadCtrlPtr",o.str(),
				     (const char *)"HasylabMotor::AbortOne()"); 
    }
  }

  motor_data[idx]->proxy->command_inout("StopMove");

}

void  HasylabMotor::DefinePosition(int32_t idx, double new_pos)
{
  
  //  cout << "[HasylabMotor] In DefinePosition - Set to this value the current position" << endl;
     
  Tango::DeviceData d_in;

  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "HasylabMotor Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"HasylabMotorCtrl_BadCtrlPtr",o.str(),
				   (const char *)"HasylabMotor::StartOne()");
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
	o << "HasylabMotor Device for idx " << idx << " not available" << ends;	
	Tango::Except::throw_exception((const char *)"HasylabMotorCtrl_BadCtrlPtr",o.str(),
				       (const char *)"HasylabMotor::StartOne()");	
      }
  }
  
  d_in << new_pos;
  motor_data[idx]->proxy->command_inout("Calibrate", d_in);

}


//-----------------------------------------------------------------------------
//
// method : 		HasylabMotor::ReadPosition
// 
// description : 	Read a motor position
//
// arg(s) : - idx : The motor number (starting at 1)
//
// This method returns the motor position
//-----------------------------------------------------------------------------



double HasylabMotor::ReadOne(int32_t idx)
{
  //  cout << "[HasylabMotor] In ReadOne" << endl;
  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "HasylabMotor Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"HasylabMotorCtrl_BadCtrlPtr",o.str(),
				   (const char *)"HasylabMotor::ReadOne()");  
  }
	
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "HasylabMotor Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"HasylabMotorCtrl_BadCtrlPtr",o.str(),
				     (const char *)"HasylabMotor::ReadOne()"); 
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
// method : 	       HasylabMotor::PreStartAll
// 
// description : 	Init movement data
//
//-----------------------------------------------------------------------------
	
void HasylabMotor::PreStartAll()
{
	//cout << "[HasylabMotor] PreStartAll on controller HasylabMotor/" << inst_name << " (" << DevName << ")" << endl;
	
	wanted_mot_pos.clear();
	wanted_mot.clear();
}


void  HasylabMotor::StartOne(int32_t idx, double new_pos)
{
  
  //  cout << "[HasylabMotor] In StartOne" << endl;
  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "HasylabMotor Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"HasylabMotorCtrl_BadCtrlPtr",o.str(),
				   (const char *)"HasylabMotor::StartOne()");  
  }
	
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "HasylabMotor Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"HasylabMotorCtrl_BadCtrlPtr",o.str(),
				     (const char *)"HasylabMotor::StartOne()"); 
    }
  }

  wanted_mot_pos.push_back(new_pos);
  wanted_mot.push_back(idx);

}


void  HasylabMotor::StartAll()
{
  
  //  cout << "[HasylabMotor] In StartAll" << endl;
  

  int32_t nb_mot = wanted_mot.size();
  
  for (int32_t loop = 0;loop < nb_mot;loop++)
    {
      
      int idx = wanted_mot[loop];
      Tango::DevDouble position = wanted_mot_pos[loop];

      if(motor_data[idx]->proxy == NULL){
	TangoSys_OMemStream o;
	o << "HasylabMotor Device Proxy for idx " << idx << " is NULL" << ends;	
	Tango::Except::throw_exception((const char *)"HasylabMotorCtrl_BadCtrlPtr",o.str(),
				       (const char *)"HasylabMotor::StartOne()");  
      }
      
      if(motor_data[idx]->device_available == false){
	try{
	  motor_data[idx]->proxy->ping();
	  motor_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
	  motor_data[idx]->device_available = false;
	  TangoSys_OMemStream o;
	  o << "HasylabMotor Device for idx " << idx << " not available" << ends;	
	  Tango::Except::throw_exception((const char *)"HasylabMotorCtrl_BadCtrlPtr",o.str(),
					 (const char *)"HasylabMotor::StartOne()"); 
	}
      }
      Tango::DeviceAttribute da("Position",position);
      motor_data[idx]->proxy->write_attribute(da);

    }
}

//-----------------------------------------------------------------------------
//
// method : 		HasylabMotor::GetState
// 
// description : 	Get one motor status. Motor status means two things :
//					1 - The motor state (Tango sense)
//
// arg(s) : - idx : The motor number (starting at 1)
//			- mot_info_ptr : Pointer to a struct. which will be filled with
//							 motor status
//
//-----------------------------------------------------------------------------

void HasylabMotor::StateOne(int32_t idx,Controller::CtrlState *info_ptr)
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
// method : 		HasylabMotor::GetPar
// 
// description : 	Get a oned exp channel parameter. Actually, 1 parameters is supported.
//					This is DataLength
//
// arg(s) : - idx : The oned exp channel  number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData HasylabMotor::GetPar(int32_t idx, string &par_name)
{
	//cout << "[HasylabMotor] Getting parameter " << par_name << " for oned exp channel with index " << idx << " on controller HasylabMotor/" << inst_name << " (" << DevName << ")" << endl;

  Controller::CtrlData par_value;
	
  TangoSys_OMemStream o;
  o << "HasylabMotor::GetPar parameter " << par_name << " is not used " << ends;	
  Tango::Except::throw_exception((const char *)"HasylabMotorCtrl_BadCtrlPtr",o.str(),
				 (const char *)"HasylabMotor::GetPar()");
  
  return par_value;

}

//-----------------------------------------------------------------------------
//
// method : 		HasylabMotor::SetPar
// 
// description : 	Set a oned parameter. Actually, 1 parameters is supported.
//					This is DataLength
//
// arg(s) : - idx : The oned exp channel number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void HasylabMotor::SetPar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{
  //cout << "[HasylabMotor] Setting parameter " << par_name << " for oned channel with index " << idx << " on controller HasylabMotor/" << inst_name << " (" << DevName << ")" << endl;

 
}


//-----------------------------------------------------------------------------
//
// method : 		HasylabMotor::GetExtraAttributePar
// 
// description : 	Get a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData HasylabMotor::GetExtraAttributePar(int32_t idx, string &par_name)
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

  try{
    in = motor_data[idx]->proxy->read_attribute(par_name);
  } catch(Tango::DevFailed &e){
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " can not be read from server/" << ends;
    
    Tango::Except::throw_exception((const char *)"HasylabMotor_BadCtrlPtr",o.str(),
				   (const char *)"HasylabMotor::GetExtraAttributePar()"); 
    
  }

  if (par_name_lower == "unitlimitmax"){
    Tango::DevDouble value;
    in >> value;
    par_value.db_data = value;
    par_value.data_type = Controller::DOUBLE;
  } else if(par_name_lower == "unitlimitmin"){
    Tango::DevDouble value;
    in >> value;
    par_value.db_data = value;
    par_value.data_type = Controller::DOUBLE;
  } else if(par_name_lower == "positionsim"){
    Tango::DevDouble value;
    in >> value;
    par_value.db_data = value;
    par_value.data_type = Controller::DOUBLE;
  } else if(par_name_lower == "resultsim"){
    vector<string> value;
    char output[200];
    output[0] = '\0';
    in >> value;
    for(int i = 0; i < in.dim_x; i++){
      strcat(output, value[i].c_str());
    }
    par_value.str_data = output;
    par_value.data_type = Controller::STRING;
  } else {
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " is unknown for controller RemotePyTangoSerialController/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"HasylabMotor_BadCtrlPtr",o.str(),
				   (const char *)"HasylabMotor::GetExtraAttributePar()");
  }
  
  return par_value;
	
}

//-----------------------------------------------------------------------------
//
// method : 		HasylabMotor::SetExtraAttributePar
// 
// description : 	Set a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void HasylabMotor::SetExtraAttributePar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{  
  string par_name_lower(par_name);
  
  transform(par_name_lower.begin(),par_name_lower.end(),par_name_lower.begin(),::tolower);
  
  if (par_name_lower == "unitlimitmax"){
    Tango::DevDouble value = (Tango::DevDouble)new_value.db_data;
    Tango::DeviceAttribute out(par_name,value);
    motor_data[idx]->proxy->write_attribute(out);
  } else if (par_name_lower == "unitlimitmin"){
    Tango::DevDouble value = (Tango::DevDouble)new_value.db_data;
    Tango::DeviceAttribute out(par_name,value);
    motor_data[idx]->proxy->write_attribute(out);
  } else if (par_name_lower == "positionsim"){
    Tango::DevDouble value = (Tango::DevDouble)new_value.db_data;
    Tango::DeviceAttribute out(par_name,value);
    motor_data[idx]->proxy->write_attribute(out);
  } else{
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " is unknown for controller HasylabMotorController/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"HasylabMotor_BadCtrlPtr",o.str(),
				   (const char *)"HasylabMotor::SetExtraAttributePars()");
  }

}


//-----------------------------------------------------------------------------
//
// method : 		HasylabMotor::send_to_ctrl
// 
// description : 	Send a string to the controller
//
// arg(s) : - in_str : the string to send to the ctrl
//
//-----------------------------------------------------------------------------

string HasylabMotor::SendToCtrl(string &in_str)
{
	cout << "[HasylabMotor] I have received the string: " << in_str << endl;
	string returned_str("Nothing to be done");
	return returned_str;	
}

//-----------------------------------------------------------------------------
//
// method : 		HasylabMotor::bad_data_type
// 
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void HasylabMotor::bad_data_type(string &par_name)
{
	TangoSys_OMemStream o;
	o << "A wrong data type has been used to set the parameter " << par_name << ends;

	Tango::Except::throw_exception((const char *)"HasylabMotorCtrl_BadParameter",o.str(),
			       			   	   (const char *)"HasylabMotor::SetPar()");
}

//
//===============================================================================================
//

const char *Motor_Ctrl_class_name[] = {"HasylabMotor",NULL};

const char *HasylabMotor_doc = "This is the C++ controller for the HasylabMotor class";
const char *HasylabMotor_gender = "HasylabMotor";
const char *HasylabMotor_model = "HasylabMotor";
const char *HasylabMotor_image = "fake_com.png";
const char *HasylabMotor_organization = "DESY";
const char *HasylabMotor_logo = "ALBA_logo.png";

Controller::ExtraAttrInfo HasylabMotor_ctrl_extra_attributes[] = {
	{"UnitLimitMax","DevDouble","Read_Write"},
	{"UnitLimitMin","DevDouble","Read_Write"},
	{"PositionSim","DevDouble","Read_Write"},
	{"ResultSim","DevString","Read_Write"},
	NULL};

Controller::PropInfo HasylabMotor_class_prop[] = {
	{"RootDeviceName","Root name for tango devices","DevString",NULL},
	NULL};
							  			 
int32_t HasylabMotor_MaxDevice = 97;

extern "C"
{
	
Controller *_create_HasylabMotor(const char *inst,vector<Controller::Properties> &prop)
{
	return new HasylabMotor(inst,prop);
}

}
