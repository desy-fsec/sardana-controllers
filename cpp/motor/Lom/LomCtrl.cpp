#include <iostream>
#include <LomCtrl.h>
#include <pool/PoolAPI.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		Lom::Lom
// 
// description : 	Ctor of the Lom class
//					It retrieve some properties from Tango DB, build a 
//					connection to the Simulated controller and ping it
//					to check if it is alive
//
//-----------------------------------------------------------------------------

Lom::Lom(const char *inst,vector<Controller::Properties> &prop):MotorController(inst)
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
	LomData *motor_data_elem = new LomData;
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
// method : 		Lom::~Lom
// 
// description : 	Dtor of the Lom Controller class
//
//-----------------------------------------------------------------------------

Lom::~Lom()
{
  //cout << "[Lom] class dtor" << endl;	
  map<int32_t, LomData*>::iterator ite = motor_data.begin();
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
// method : 		Lom::AddDevice
// 
// description : 	Register a new device for the controller
//					For the simulated controller, this simply means increment
//					motor count
//
//-----------------------------------------------------------------------------

void Lom::AddDevice(int32_t idx)
{
  //cout << "[Lom] Creating a new Motor with index " << idx << " on controller Lom/" << inst_name << endl;	

  if(idx > max_device){
    TangoSys_OMemStream o;
    o << "The property 'RootDeviceName' has no found element with index " << idx << ".";
    o << " Please check the number of devices found"<< ends;
    
    Tango::Except::throw_exception((const char *)"Lom_BadIndex",o.str(),
				   (const char *)"Lom::AddDevice()");
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
// method : 		Lom::DeleteDevice
// 
// description : 	Unregister a new device for the controller
//					For the simulated controller, this simply means decrement
//					motor count
//
//-----------------------------------------------------------------------------

void Lom::DeleteDevice(int32_t idx)
{
  //cout << "[Lom] Deleting OneD with index " << idx << " on controller Lom/" << inst_name << endl;
  if(idx > max_device){
    TangoSys_OMemStream o;
    o << "Trying to delete an inexisting element(" << idx << ") from the controller." << ends;
    
    Tango::Except::throw_exception((const char *)"Lom_BadIndex",o.str(),
				   (const char *)"Lom::DeleteDevice()");
  }	
	
  if(motor_data[idx]->proxy != NULL){
    delete motor_data[idx]->proxy;
    motor_data[idx]->proxy = NULL;  
  }
  motor_data[idx]->device_available = false;
}



void  Lom::AbortOne(int32_t idx)
{
  
  cout << "[Lom] In AbortOne" << endl;
  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "Lom Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"LomCtrl_BadCtrlPtr",o.str(),
				   (const char *)"Lom::AbortOne()");  
  }
	
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "Lom Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"LomCtrl_BadCtrlPtr",o.str(),
				     (const char *)"Lom::AbortOne()"); 
    }
  }

  // Still not implemented
  //  motor_data[idx]->proxy->command_inout("StopMove");

}

void  Lom::DefinePosition(int32_t idx, double new_pos)
{
  
  cout << "[Lom] In DefinePosition - Set to this value the current position" << endl;
  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "Lom Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"LomCtrl_BadCtrlPtr",o.str(),
				   (const char *)"Lom::DefinePosition()");  
  }
	
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "Lom Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"LomCtrl_BadCtrlPtr",o.str(),
				     (const char *)"Lom::DefinePosition()"); 
    }
  }

  Tango::DeviceData d_in;
  d_in << new_pos;
  motor_data[idx]->proxy->command_inout("Calibrate",d_in);
  
}


//-----------------------------------------------------------------------------
//
// method : 		Lom::ReadOne
// 
// description : 	Read a motor position
//
// arg(s) : - idx : The motor number (starting at 1)
//
// This method returns the motor position
//-----------------------------------------------------------------------------



double Lom::ReadOne(int32_t idx)
{
  //  cout << "[Lom] In ReadOne" << endl;
  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "Lom Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"LomCtrl_BadCtrlPtr",o.str(),
				   (const char *)"Lom::ReadOne()");  
  }
	
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "Lom Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"LomCtrl_BadCtrlPtr",o.str(),
				     (const char *)"Lom::ReadOne()"); 
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
// method : 	       Lom::PreStartAll
// 
// description : 	Init movement data
//
//-----------------------------------------------------------------------------
	
void Lom::PreStartAll()
{
	//cout << "[Lom] PreStartAll on controller Lom/" << inst_name << " (" << DevName << ")" << endl;
	
	wanted_mot_pos.clear();
	wanted_mot.clear();
}


void  Lom::StartOne(int32_t idx, double new_pos)
{
  
  //  cout << "[Lom] In StartOne" << endl;
  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "Lom Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"LomCtrl_BadCtrlPtr",o.str(),
				   (const char *)"Lom::StartOne()");  
  }
	
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "Lom Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"LomCtrl_BadCtrlPtr",o.str(),
				     (const char *)"Lom::StartOne()"); 
    }
  }

  wanted_mot_pos.push_back(new_pos);
  wanted_mot.push_back(idx);

}


void  Lom::StartAll()
{
  
  //  cout << "[Lom] In StartAll" << endl;
  
  
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
	o << "Lom Device Proxy for idx " << idx << " is NULL" << ends;	
	Tango::Except::throw_exception((const char *)"LomCtrl_BadCtrlPtr",o.str(),
				       (const char *)"Lom::StartOne()");  
      }
      
      if(motor_data[idx]->device_available == false){
	try{
	  motor_data[idx]->proxy->ping();
	  motor_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
	  motor_data[idx]->device_available = false;
	  TangoSys_OMemStream o;
	  o << "Lom Device for idx " << idx << " not available" << ends;	
	  Tango::Except::throw_exception((const char *)"LomCtrl_BadCtrlPtr",o.str(),
					 (const char *)"Lom::StartOne()"); 
	}
      }


      value = position;

      Tango::DeviceAttribute da("Position",value);
      motor_data[idx]->proxy->write_attribute(da);

    }
}

//-----------------------------------------------------------------------------
//
// method : 		Lom::GetState
// 
// description : 	Get one motor status. Motor status means two things :
//					1 - The motor state (Tango sense)
//
// arg(s) : - idx : The motor number (starting at 1)
//			- mot_info_ptr : Pointer to a struct. which will be filled with
//							 motor status
//
//-----------------------------------------------------------------------------

void Lom::StateOne(int32_t idx,Controller::CtrlState *info_ptr)
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
// method : 		Lom::GetPar
// 
// description : 	Get a oned exp channel parameter. Actually, 1 parameters is supported.
//					This is DataLength
//
// arg(s) : - idx : The oned exp channel  number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData Lom::GetPar(int32_t idx, string &par_name)
{
	//cout << "[Lom] Getting parameter " << par_name << " for oned motor with index " << idx << " on controller Lom/" << inst_name << " (" << DevName << ")" << endl;

  Controller::CtrlData par_value;
   	
  TangoSys_OMemStream o;
  o << "Lom::GetPar parameter " << par_name << " is not used " << ends;	
  Tango::Except::throw_exception((const char *)"LomCtrl_BadCtrlPtr",o.str(),
				 (const char *)"Lom::GetPar()");
  
  return par_value;


}

//-----------------------------------------------------------------------------
//
// method : 		Lom::SetPar
// 
// description : 	Set a oned parameter.
//
// arg(s) : - idx : The oned exp channel number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void Lom::SetPar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{
  //cout << "[Lom] Setting parameter " << par_name << " for motor with index " << idx << " on controller Lom/" << inst_name << " (" << DevName << ")" << endl;

}


//-----------------------------------------------------------------------------
//
// method : 		Lom::GetExtraAttributePar
// 
// description : 	Get a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData Lom::GetExtraAttributePar(int32_t idx, string &par_name)
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
  
  if (par_name_lower == "positionhw"){    
    in = motor_data[idx]->proxy->read_attribute("PositionHw");
    in >> tmp_double;
    par_value.db_data = tmp_double;
    par_value.data_type = Controller::DOUBLE;
  } else if(par_name_lower == "positionsetpoint"){    
    in = motor_data[idx]->proxy->read_attribute("PositionSetPoint");
    in >> tmp_double;
    par_value.db_data = tmp_double;
    par_value.data_type = Controller::DOUBLE;
  } else if(par_name_lower == "startall"){    
    in = motor_data[idx]->proxy->read_attribute("StartAll");
    in >> tmp_long;
    par_value.db_data = tmp_long;
    par_value.data_type = Controller::INT32;
  } else {
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " is unknown for controller RemotePyTangoSerialController/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"Lom_BadCtrlPtr",o.str(),
				   (const char *)"Lom::GetPar()");
  }
  
  return par_value;
	
}

//-----------------------------------------------------------------------------
//
// method : 		Lom::SetExtraAttributePar
// 
// description : 	Set a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void Lom::SetExtraAttributePar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{  
  string par_name_lower(par_name);
  
  transform(par_name_lower.begin(),par_name_lower.end(),par_name_lower.begin(),::tolower);
  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "Lom Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"LomCtrl_BadCtrlPtr",o.str(),
				   (const char *)"Lom::SetExtraAttributePar()");  
  }

  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "Lom Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"LomCtrl_BadCtrlPtr",o.str(),
				     (const char *)"Lom::SetExtraAttributePar()"); 
    }
  }

  
  Tango::DevDouble tmp_double;
  Tango::DevLong tmp_long;
      
  Tango::DeviceData d_in;

  if (par_name_lower == "positionhw"){
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " can not be set for controller LomController/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"Lom_BadCtrlPtr",o.str(),
				   (const char *)"Lom::SetExtraAttributePars()");
  } else if (par_name_lower == "positionsetpoint"){
    tmp_double = new_value.db_data;
    Tango::DeviceAttribute out1("PositionSetPoint",tmp_double);
    motor_data[idx]->proxy->write_attribute(out1);
  } else if (par_name_lower == "startall"){
    tmp_long = new_value.int32_data;
    Tango::DeviceAttribute out2("StartAll",tmp_long);
    motor_data[idx]->proxy->write_attribute(out2);
  } else {
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " is unknown for controller LomController/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"Lom_BadCtrlPtr",o.str(),
				   (const char *)"Lom::SetExtraAttributePars()");
  }

}


//-----------------------------------------------------------------------------
//
// method : 		Lom::send_to_ctrl
// 
// description : 	Send a string to the controller
//
// arg(s) : - in_str : the string to send to the ctrl
//
//-----------------------------------------------------------------------------

string Lom::SendToCtrl(string &in_str)
{
	cout << "[Lom] I have received the string: " << in_str << endl;
	string returned_str("Nothing to be done");
	return returned_str;	
}

//-----------------------------------------------------------------------------
//
// method : 		Lom::bad_data_type
// 
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void Lom::bad_data_type(string &par_name)
{
	TangoSys_OMemStream o;
	o << "A wrong data type has been used to set the parameter " << par_name << ends;

	Tango::Except::throw_exception((const char *)"LomCtrl_BadParameter",o.str(),
			       			   	   (const char *)"Lom::SetPar()");
}

//
//===============================================================================================
//

const char *Motor_Ctrl_class_name[] = {"Lom",NULL};

const char *Lom_doc = "This is the C++ controller for the Lom class";
const char *Lom_gender = "Lom";
const char *Lom_model = "Lom";
const char *Lom_image = "fake_com.png";
const char *Lom_organization = "DESY";
const char *Lom_logo = "ALBA_logo.png";

Controller::ExtraAttrInfo Lom_ctrl_extra_attributes[] = {
        {"PositionHw","DevDouble","Read_Write"},
        {"PositionSetPoint","DevDouble","Read_Write"},
        {"StartAll","DevLong","Read_Write"},
	NULL};

Controller::PropInfo Lom_class_prop[] = {
	{"RootDeviceName","Root name for tango devices","DevString",NULL},
	NULL};
							  			 
int32_t Lom_MaxDevice = 97;

extern "C"
{
	
Controller *_create_Lom(const char *inst,vector<Controller::Properties> &prop)
{
	return new Lom(inst,prop);
}

}
