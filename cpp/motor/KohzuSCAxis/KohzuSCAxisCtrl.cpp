#include <iostream>
#include <KohzuSCAxisCtrl.h>
#include <pool/PoolAPI.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		KohzuSCAxis::KohzuSCAxis
// 
// description : 	Ctor of the KohzuSCAxis class
//					It retrieve some properties from Tango DB, build a 
//					connection to the Simulated controller and ping it
//					to check if it is alive
//
//-----------------------------------------------------------------------------

KohzuSCAxis::KohzuSCAxis(const char *inst,vector<Controller::Properties> &prop):MotorController(inst)
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
	KohzuSCAxisData *motor_data_elem = new KohzuSCAxisData;
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
// method : 		KohzuSCAxis::~KohzuSCAxis
// 
// description : 	Dtor of the KohzuSCAxis Controller class
//
//-----------------------------------------------------------------------------

KohzuSCAxis::~KohzuSCAxis()
{
  //cout << "[KohzuSCAxis] class dtor" << endl;	
  map<int32_t, KohzuSCAxisData*>::iterator ite = motor_data.begin();
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
// method : 		KohzuSCAxis::AddDevice
// 
// description : 	Register a new device for the controller
//					For the simulated controller, this simply means increment
//					motor count
//
//-----------------------------------------------------------------------------

void KohzuSCAxis::AddDevice(int32_t idx)
{
  //cout << "[KohzuSCAxis] Creating a new Motor with index " << idx << " on controller KohzuSCAxis/" << inst_name << endl;	

  if(idx > max_device){
    TangoSys_OMemStream o;
    o << "The property 'RootDeviceName' has no found element with index " << idx << ".";
    o << " Please check the number of devices found"<< ends;
    
    Tango::Except::throw_exception((const char *)"KohzuSCAxis_BadIndex",o.str(),
				   (const char *)"KohzuSCAxis::AddDevice()");
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
// method : 		KohzuSCAxis::DeleteDevice
// 
// description : 	Unregister a new device for the controller
//					For the simulated controller, this simply means decrement
//					motor count
//
//-----------------------------------------------------------------------------

void KohzuSCAxis::DeleteDevice(int32_t idx)
{
  //cout << "[KohzuSCAxis] Deleting OneD with index " << idx << " on controller KohzuSCAxis/" << inst_name << endl;
  if(idx > max_device){
    TangoSys_OMemStream o;
    o << "Trying to delete an inexisting element(" << idx << ") from the controller." << ends;
    
    Tango::Except::throw_exception((const char *)"KohzuSCAxis_BadIndex",o.str(),
				   (const char *)"KohzuSCAxis::DeleteDevice()");
  }	
	
  if(motor_data[idx]->proxy != NULL){
    delete motor_data[idx]->proxy;
    motor_data[idx]->proxy = NULL;  
  }
  motor_data[idx]->device_available = false;
}



void  KohzuSCAxis::AbortOne(int32_t idx)
{
  
  cout << "[KohzuSCAxis] In AbortOne" << endl;
  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "KohzuSCAxis Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"KohzuSCAxisCtrl_BadCtrlPtr",o.str(),
				   (const char *)"KohzuSCAxis::AbortOne()");  
  }
	
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "KohzuSCAxis Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"KohzuSCAxisCtrl_BadCtrlPtr",o.str(),
				     (const char *)"KohzuSCAxis::AbortOne()"); 
    }
  }

  motor_data[idx]->proxy->command_inout("StopMove");

}

void  KohzuSCAxis::DefinePosition(int32_t idx, double new_pos)
{
  
  //  cout << "[KohzuSCAxis] In DefinePosition - Set to this value the current position" << endl;
     

  TangoSys_OMemStream o;
  o << "DefinePosition (calibration) not defined for KohzuSC motors " << idx << " is NULL" << ends;	
  Tango::Except::throw_exception((const char *)"KohzuSCAxisCtrl_BadCtrlPtr",o.str(),
				 (const char *)"KohzuSCAxis::StartOne()");
  


}


//-----------------------------------------------------------------------------
//
// method : 		KohzuSCAxis::ReadPosition
// 
// description : 	Read a motor position
//
// arg(s) : - idx : The motor number (starting at 1)
//
// This method returns the motor position
//-----------------------------------------------------------------------------



double KohzuSCAxis::ReadOne(int32_t idx)
{
  //  cout << "[KohzuSCAxis] In ReadOne" << endl;
  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "KohzuSCAxis Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"KohzuSCAxisCtrl_BadCtrlPtr",o.str(),
				   (const char *)"KohzuSCAxis::ReadOne()");  
  }
	
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "KohzuSCAxis Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"KohzuSCAxisCtrl_BadCtrlPtr",o.str(),
				     (const char *)"KohzuSCAxis::ReadOne()"); 
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
// method : 	       KohzuSCAxis::PreStartAll
// 
// description : 	Init movement data
//
//-----------------------------------------------------------------------------
	
void KohzuSCAxis::PreStartAll()
{
	//cout << "[KohzuSCAxis] PreStartAll on controller KohzuSCAxis/" << inst_name << " (" << DevName << ")" << endl;
	
	wanted_mot_pos.clear();
	wanted_mot.clear();
}


void  KohzuSCAxis::StartOne(int32_t idx, double new_pos)
{
  
  //  cout << "[KohzuSCAxis] In StartOne" << endl;
  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "KohzuSCAxis Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"KohzuSCAxisCtrl_BadCtrlPtr",o.str(),
				   (const char *)"KohzuSCAxis::StartOne()");  
  }
	
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "KohzuSCAxis Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"KohzuSCAxisCtrl_BadCtrlPtr",o.str(),
				     (const char *)"KohzuSCAxis::StartOne()"); 
    }
  }

  wanted_mot_pos.push_back(new_pos);
  wanted_mot.push_back(idx);

}


void  KohzuSCAxis::StartAll()
{
  
  //  cout << "[KohzuSCAxis] In StartAll" << endl;
  
      
  Tango::DeviceData d_in;
  
  int idx;
  double position;
  
  int32_t nb_mot = wanted_mot.size();
  
  for (int32_t loop = 0;loop < nb_mot;loop++)
    {
      
      idx = wanted_mot[loop];
      position = wanted_mot_pos[loop];

      if(motor_data[idx]->proxy == NULL){
	TangoSys_OMemStream o;
	o << "KohzuSCAxis Device Proxy for idx " << idx << " is NULL" << ends;	
	Tango::Except::throw_exception((const char *)"KohzuSCAxisCtrl_BadCtrlPtr",o.str(),
				       (const char *)"KohzuSCAxis::StartOne()");  
      }
      
      if(motor_data[idx]->device_available == false){
	try{
	  motor_data[idx]->proxy->ping();
	  motor_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
	  motor_data[idx]->device_available = false;
	  TangoSys_OMemStream o;
	  o << "KohzuSCAxis Device for idx " << idx << " not available" << ends;	
	  Tango::Except::throw_exception((const char *)"KohzuSCAxisCtrl_BadCtrlPtr",o.str(),
					 (const char *)"KohzuSCAxis::StartOne()"); 
	}
      }
      d_in << position;
      motor_data[idx]->proxy->command_inout("Move", d_in);

    }
}

//-----------------------------------------------------------------------------
//
// method : 		KohzuSCAxis::GetState
// 
// description : 	Get one motor status. Motor status means two things :
//					1 - The motor state (Tango sense)
//
// arg(s) : - idx : The motor number (starting at 1)
//			- mot_info_ptr : Pointer to a struct. which will be filled with
//							 motor status
//
//-----------------------------------------------------------------------------

void KohzuSCAxis::StateOne(int32_t idx,Controller::CtrlState *info_ptr)
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
  
  Tango::DevLong cwlimit;
  Tango::DevLong ccwlimit;

  int32_t switches;

  d_out = motor_data[idx]->proxy->read_attribute("CwLimit");
  d_out >> cwlimit;

  d_out = motor_data[idx]->proxy->read_attribute("CcwLimit");
  d_out >> ccwlimit;

  switches = 0;

  if(cwlimit)  switches = switches + 2;
  if(cwlimit)  switches = switches + 4;

  mot_info_ptr->switches = switches;
}

//-----------------------------------------------------------------------------
//
// method : 		KohzuSCAxis::GetPar
// 
// description : 	Get a oned exp channel parameter. Actually, 1 parameters is supported.
//					This is DataLength
//
// arg(s) : - idx : The oned exp channel  number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData KohzuSCAxis::GetPar(int32_t idx, string &par_name)
{
	//cout << "[KohzuSCAxis] Getting parameter " << par_name << " for oned exp channel with index " << idx << " on controller KohzuSCAxis/" << inst_name << " (" << DevName << ")" << endl;

  Controller::CtrlData par_value;
    
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "KohzuSCAxis Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"KohzuSCAxisCtrl_BadCtrlPtr",o.str(),
				   (const char *)"KohzuSCAxis::GetPar()");  
  }
  
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "KohzuSCAxis Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"KohzuSCAxisCtrl_BadCtrlPtr",o.str(),
				     (const char *)"KohzuSCAxis::GetPar()"); 
    }
  }

  Tango::DeviceAttribute d_out;
  Tango::DevLong tmp_long;
  Tango::DevDouble tmp_double;
		
  if (par_name == "Acceleration")
    {
      d_out = motor_data[idx]->proxy->read_attribute("AcceleratingTime");
      d_out >> tmp_long;
      par_value.db_data = (double) tmp_long;
      par_value.data_type = Controller::DOUBLE;		
    }
  else if (par_name == "Velocity")
    {
      d_out = motor_data[idx]->proxy->read_attribute("SlewRate");
      d_out >> tmp_long;
      par_value.db_data = (double) tmp_long;
      par_value.data_type = Controller::DOUBLE;	
    }
  else if (par_name == "Base_rate")
    {
      d_out = motor_data[idx]->proxy->read_attribute("BaseRate");
      d_out >> tmp_long;
      par_value.db_data = (double) tmp_long;
      par_value.data_type = Controller::DOUBLE;
    }
  else if (par_name == "Offset")
    {
      d_out = motor_data[idx]->proxy->read_attribute("Offset");
      d_out >> tmp_double;
      par_value.db_data = (double) tmp_double;
      par_value.data_type = Controller::DOUBLE;	
    }
  else if (par_name == "Backlash")
    {
      d_out = motor_data[idx]->proxy->read_attribute("FlagBacklash");
      d_out >> tmp_long;
      par_value.int32_data = tmp_long;
      par_value.data_type = Controller::INT32;
    }
  else
    {
      TangoSys_OMemStream o;
      o << "Parameter " << par_name << " is unknown for controller KohzuSCAxisCtrl/" << get_name() << ends;
      
      Tango::Except::throw_exception((const char *)"KohzuSCAxisCtrl_BadCtrlPtr",o.str(),
				     (const char *)"KohzuSCAxis::GetPar()");
    }
  
  
  return par_value;

}

//-----------------------------------------------------------------------------
//
// method : 		KohzuSCAxis::SetPar
// 
// description : 	Set a oned parameter. Actually, 1 parameters is supported.
//					This is DataLength
//
// arg(s) : - idx : The oned exp channel number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void KohzuSCAxis::SetPar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{
  //cout << "[KohzuSCAxis] Setting parameter " << par_name << " for oned channel with index " << idx << " on controller KohzuSCAxis/" << inst_name << " (" << DevName << ")" << endl;

  Controller::CtrlData par_value;
    
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "KohzuSCAxis Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"KohzuSCAxisCtrl_BadCtrlPtr",o.str(),
				   (const char *)"KohzuSCAxis::SetPar()");  
  }
  
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "KohzuSCAxis Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"KohzuSCAxisCtrl_BadCtrlPtr",o.str(),
				     (const char *)"KohzuSCAxis::SetPar()"); 
    }
  }

  Tango::DevLong tmp_long;
  Tango::DevDouble tmp_double;
  
  if (par_name == "Acceleration")
    {
      tmp_long = (Tango::DevLong)new_value.db_data;
      Tango::DeviceAttribute out_at("AcceleratingTime",tmp_long);
      motor_data[idx]->proxy->write_attribute(out_at);		
    }
  else if (par_name == "Velocity")
    {
      tmp_long = (Tango::DevLong)new_value.db_data;
      Tango::DeviceAttribute out_sr("SlewRate",tmp_long);
      motor_data[idx]->proxy->write_attribute(out_sr);
    }
  else if (par_name == "Base_rate")
    {
      tmp_long = (Tango::DevLong)new_value.db_data;
      Tango::DeviceAttribute out_br("BaseRate",tmp_long);
      motor_data[idx]->proxy->write_attribute(out_br);
    }
  else if (par_name == "Offset")
    {
      tmp_double = (Tango::DevDouble)new_value.db_data;
      Tango::DeviceAttribute out_o("Offset",tmp_double);
      motor_data[idx]->proxy->write_attribute(out_o);
    }
  else if (par_name == "Backlash")
    {
      tmp_long = (Tango::DevLong)new_value.int32_data;
      Tango::DeviceAttribute out_bs("FlagBacklash",tmp_long);
      motor_data[idx]->proxy->write_attribute(out_bs);
    }
  else if (par_name == "Step_per_unit")
    {
      // The controller will look for this parameter when creating a motor, so
      // even if it is empty, it has to be here.
    }
  else
    {
      TangoSys_OMemStream o;
      o << "Parameter " << par_name << " is unknown for controller KohzuSCAxisCtrl/" << get_name() << ends;
      
      Tango::Except::throw_exception((const char *)"KohzuSCAxisCtrl_BadCtrlPtr",o.str(),
				     (const char *)"KohzuSCAxis::SetPar()");
    }

}


//-----------------------------------------------------------------------------
//
// method : 		KohzuSCAxis::GetExtraAttributePar
// 
// description : 	Get a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData KohzuSCAxis::GetExtraAttributePar(int32_t idx, string &par_name)
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
    in = motor_data[idx]->proxy->read_attribute("Encoder");
    in >> tmp_double;
    par_value.db_data = tmp_double;
    par_value.data_type = Controller::DOUBLE;
  } else {
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " is unknown for controller RemotePyTangoSerialController/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"KohzuSCAxis_BadCtrlPtr",o.str(),
				   (const char *)"KohzuSCAxis::GetPar()");
  }
  
  return par_value;
	
}

//-----------------------------------------------------------------------------
//
// method : 		KohzuSCAxis::SetExtraAttributePar
// 
// description : 	Set a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void KohzuSCAxis::SetExtraAttributePar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{  
  string par_name_lower(par_name);
  
  transform(par_name_lower.begin(),par_name_lower.end(),par_name_lower.begin(),::tolower);
  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "KohzuSCAxis Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"KohzuSCAxisCtrl_BadCtrlPtr",o.str(),
				   (const char *)"KohzuSCAxis::SetExtraAttributePar()");  
  }
  
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "KohzuSCAxis Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"KohzuSCAxisCtrl_BadCtrlPtr",o.str(),
				     (const char *)"KohzuSCAxis::SetExtraAttributePar()"); 
    }
  }

  Tango::DevDouble tmp_double;
  Tango::DevLong tmp_long;
      
  Tango::DeviceData d_in;

  if (par_name_lower == "positionencoder"){
    tmp_double = new_value.db_data;
    Tango::DeviceAttribute out("Encoder",tmp_double);
    motor_data[idx]->proxy->write_attribute(out);
  } else if (par_name_lower == "movehome"){
    motor_data[idx]->proxy->command_inout("MoveHome");
  } else if (par_name_lower == "moverel"){
    tmp_double = new_value.db_data;
    d_in << tmp_double;
    motor_data[idx]->proxy->command_inout("MoveRel", d_in);
  } else if (par_name_lower == "resetfaultstate"){
    motor_data[idx]->proxy->command_inout("ResetFAULTState");
  } else {
    TangoSys_OMemStream o;
    o << "Parameter " << par_name << " is unknown for controller KohzuSCAxisController/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"KohzuSCAxis_BadCtrlPtr",o.str(),
				   (const char *)"KohzuSCAxis::SetExtraAttributePars()");
  }

}


//-----------------------------------------------------------------------------
//
// method : 		KohzuSCAxis::send_to_ctrl
// 
// description : 	Send a string to the controller
//
// arg(s) : - in_str : the string to send to the ctrl
//
//-----------------------------------------------------------------------------

string KohzuSCAxis::SendToCtrl(string &in_str)
{
	cout << "[KohzuSCAxis] I have received the string: " << in_str << endl;
	string returned_str("Nothing to be done");
	return returned_str;	
}

//-----------------------------------------------------------------------------
//
// method : 		KohzuSCAxis::bad_data_type
// 
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void KohzuSCAxis::bad_data_type(string &par_name)
{
	TangoSys_OMemStream o;
	o << "A wrong data type has been used to set the parameter " << par_name << ends;

	Tango::Except::throw_exception((const char *)"KohzuSCAxisCtrl_BadParameter",o.str(),
			       			   	   (const char *)"KohzuSCAxis::SetPar()");
}

//
//===============================================================================================
//

const char *Motor_Ctrl_class_name[] = {"KohzuSCAxis",NULL};

const char *KohzuSCAxis_doc = "This is the C++ controller for the KohzuSCAxis class";
const char *KohzuSCAxis_gender = "KohzuSCAxis";
const char *KohzuSCAxis_model = "KohzuSCAxis";
const char *KohzuSCAxis_image = "fake_com.png";
const char *KohzuSCAxis_organization = "DESY";
const char *KohzuSCAxis_logo = "ALBA_logo.png";

Controller::ExtraAttrInfo KohzuSCAxis_ctrl_extra_attributes[] = {
        {"PositionEncoder","DevDouble","Read_Write"},
        {"MoveRel","DevDouble","Read_Write"},
        {"MoveHome","DevLong","Read_Write"},
        {"ResetFAULTState","DevLong","Read_Write"},
	NULL};

Controller::PropInfo KohzuSCAxis_class_prop[] = {
	{"RootDeviceName","Root name for tango devices","DevString",NULL},
	NULL};
							  			 
int32_t KohzuSCAxis_MaxDevice = 97;

extern "C"
{
	
Controller *_create_KohzuSCAxis(const char *inst,vector<Controller::Properties> &prop)
{
	return new KohzuSCAxis(inst,prop);
}

}
