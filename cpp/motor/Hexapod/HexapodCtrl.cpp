#include <iostream>
#include <HexapodCtrl.h>
#include <pool/PoolAPI.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		Hexapod::Hexapod
// 
// description : 	Ctor of the Hexapod class
//					It retrieve some properties from Tango DB, build a 
//					connection to the Hexapod device and ping it
//					to check if it is alive
//
//-----------------------------------------------------------------------------

Hexapod::Hexapod(const char *inst,vector<Controller::Properties> &prop):MotorController(inst)
{
  max_device = 0;
  vector<Controller::Properties>::iterator prop_it;
  for (prop_it = prop.begin(); prop_it != prop.end(); ++prop_it){
    if(prop_it->name == "DeviceName"){
      //
      // Create a DeviceProxy of the Hexapod Tango Server and set
      // it in automatic reconnection mode
      //
      hexapod_proxy = Pool_ns::PoolUtil::instance()->get_device(inst_name, prop_it->value.string_prop[0]);
      
      //
      // Ping the device to be sure that it is present
      //
      if(hexapod_proxy == NULL)
	{
	  TangoSys_OMemStream o;
	  o << "Error in connecting to hexapod server" << ends;
	  Tango::Except::throw_exception((const char *)"HexapodCtrl_BadPoolAPI",o.str(),
					 (const char *)"Hexapod::Hexapod()");
	}
      
      try
	{
	  hexapod_proxy->ping();
	}
      catch (Tango::DevFailed &e)
	{
	  delete hexapod_proxy;
	  throw;
	}
      
    }
  }
}
    
//-----------------------------------------------------------------------------
//
// method : 		Hexapod::~Hexapod
// 
// description : 	Dtor of the Hexapod Controller class
//
//-----------------------------------------------------------------------------

Hexapod::~Hexapod()
{
  //cout << "[Hexapod] class dtor" << endl;
}

//-----------------------------------------------------------------------------
//
// method : 		Hexapod::AddDevice
// 
// description : 	Register a new device for the controller
//					For the simulated controller, this simply means increment
//					motor count
//
//-----------------------------------------------------------------------------

void Hexapod::AddDevice(int32_t idx)
{
  //cout << "[Hexapod] Creating a new Motor with index " << idx << " on controller Hexapod/" << inst_name << endl;
}

//-----------------------------------------------------------------------------
//
// method : 		Hexapod::DeleteDevice
// 
// description : 	Unregister a new device for the controller
//					For the simulated controller, this simply means decrement
//					motor count
//
//-----------------------------------------------------------------------------

void Hexapod::DeleteDevice(int32_t idx)
{
  //cout << "[Hexapod] Deleting OneD with index " << idx << " on controller Hexapod/" << inst_name << endl;
}



void  Hexapod::AbortOne(int32_t idx)
{
  
  //  cout << "[Hexapod] In AbortOne" << endl;


}

void  Hexapod::DefinePosition(int32_t idx, double new_pos)
{
  
  //  cout << "[Hexapod] In DefinePosition - Set to this value the current position" << endl;

}


//-----------------------------------------------------------------------------
//
// method : 		Hexapod::ReadPosition
// 
// description : 	Read a motor position
//
// arg(s) : - idx : The motor number (starting at 1)
//
// This method returns the motor position
//-----------------------------------------------------------------------------


double Hexapod::ReadOne(int32_t idx)
{

  double received_pos = 0;
  string axis_name;
  Tango::DeviceAttribute d_out;

  //  cout << "[Hexapod] In ReadOne" << endl;
  if (hexapod_proxy != NULL)
    {
      switch(idx){
      case 1:
	axis_name = "POSX";
	break;
      case 2:
	axis_name = "POSY";
	break;
      case 3:
	axis_name = "POSZ";
	break;
      case 4:
	axis_name = "POSU";
	break;
      case 5:
	axis_name = "POSV";
	break;
      case 6:
	axis_name = "POSW";
	break;
      case 7:
	axis_name = "PIVOTR";
	break;
      case 8:
	axis_name = "PIVOTS";
	break;
      case 9:
	axis_name = "PIVOTT";
	break;
      }

      d_out = hexapod_proxy->read_attribute(axis_name);
      d_out >> received_pos;
    }
  else
    {
      TangoSys_OMemStream o;
      o << "Controller " << get_name() << " for hexapod is NULL" << ends;
      
      Tango::Except::throw_exception((const char *)"HexapodCtrl_BadCtrlPtr",o.str(),
				     (const char *)"Hexapod::ReadOne()");
    }

  return received_pos;

}


//-----------------------------------------------------------------------------
//
// method : 	       Hexapod::PreStartAll
// 
// description : 	Init movement data
//
//-----------------------------------------------------------------------------
	
void Hexapod::PreStartAll()
{
	//cout << "[Hexapod] PreStartAll on controller Hexapod/" << inst_name << " (" << DevName << ")" << endl;
	
	wanted_mot_pos.clear();
	wanted_mot.clear();
}


void  Hexapod::StartOne(int32_t idx, double new_pos)
{
  
  //  cout << "[Hexapod] In StartOne" << endl;

  wanted_mot_pos.push_back(new_pos);
  wanted_mot.push_back(idx);

}


void  Hexapod::StartAll()
{
  
  //  cout << "[Hexapod] In StartAll" << endl;
  
  int32_t nb_mot = wanted_mot.size();
  
  if (hexapod_proxy != NULL){

    for (int32_t loop = 0;loop < nb_mot;loop++)
      {
	
	Tango::DeviceData d_in;
	
	int idx = wanted_mot[loop];
	double position = wanted_mot_pos[loop];
	string axis_name;
	
	switch(idx){
	case 1:
	  axis_name = "POSXABS";
	  break;
	case 2:
	  axis_name = "POSYABS";
	  break;
	case 3:
	  axis_name = "POSZABS";
	  break;
	case 4:
	  axis_name = "POSUABS";
	  break;
	case 5:
	  axis_name = "POSVABS";
	  break;
	case 6:
	  axis_name = "POSWABS";
	  break;
	case 7:
	  axis_name = "PIVOTR";
	  break;
	case 8:
	  axis_name = "PIVOTS";
	  break;
	case 9:
	  axis_name = "PIVOTT";
	  break;
	}
	
	Tango::DeviceAttribute *da_write = new Tango::DeviceAttribute( axis_name, position);

	hexapod_proxy->write_attribute(*da_write);
      
      }
    hexapod_proxy->command_inout("MoveAbs");

  }else{
    TangoSys_OMemStream o;
    o << "Controller " << get_name() << " for hexapod is NULL" << ends;
    
    Tango::Except::throw_exception((const char *)"HexapodCtrl_BadCtrlPtr",o.str(),
				   (const char *)"Hexapod::ReadOne()");
  }
          
}

//-----------------------------------------------------------------------------
//
// method : 		Hexapod::GetState
// 
// description : 	Get one motor status. Motor status means two things :
//					1 - The motor state (Tango sense)
//
// arg(s) : - idx : The motor number (starting at 1)
//			- mot_info_ptr : Pointer to a struct. which will be filled with
//							 motor status
//
//-----------------------------------------------------------------------------

void Hexapod::StateOne(int32_t idx,Controller::CtrlState *info_ptr)
{
  MotorController::MotorState *mot_info_ptr = static_cast<MotorController::MotorState *>(info_ptr);
  
  if (hexapod_proxy != NULL){
    Tango::DevState dev_state;
    dev_state = hexapod_proxy->state();
    
    mot_info_ptr->state = dev_state;
    mot_info_ptr->switches = 0;
    
  } else {
    TangoSys_OMemStream o;
    o << "Controller " << get_name() << "for Hexapod is NULL" << ends;
    
    Tango::Except::throw_exception((const char *)"HexapodCtrl_BadCtrlPtr",o.str(),
				   (const char *)"HexapodCtrl::GetStatus()");
  }

}

//-----------------------------------------------------------------------------
//
// method : 		Hexapod::GetPar
// 
// description : 	Get a oned exp channel parameter. Actually, 1 parameters is supported.
//					This is DataLength
//
// arg(s) : - idx : The oned exp channel  number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData Hexapod::GetPar(int32_t idx, string &par_name)
{
	//cout << "[Hexapod] Getting parameter " << par_name << " for oned exp channel with index " << idx << " on controller Hexapod/" << inst_name << " (" << DevName << ")" << endl;

  Controller::CtrlData par_value;

  if (hexapod_proxy != NULL){

    Tango::DeviceAttribute d_out;

    if (par_name == "Velocity"){
      d_out = hexapod_proxy->read_attribute("Speed");
      d_out >> par_value.db_data;
      par_value.data_type = Controller::DOUBLE;		
    } else {
      TangoSys_OMemStream o;
      o << "Parameter " << par_name << " is unknown for controller HexapodCtrl/" << get_name() << ends;
      
      Tango::Except::throw_exception((const char *)"HexapodCtrl_BadCtrlPtr",o.str(),
				     (const char *)"HexapodCtrl::GetPar()");
    }
  } else {
    TangoSys_OMemStream o;
    o << "Hexapod::GetPar parameter " << par_name << " is not used " << ends;	
    Tango::Except::throw_exception((const char *)"HexapodCtrl_BadCtrlPtr",o.str(),
				   (const char *)"Hexapod::GetPar()");
  }
  return par_value;

}

//-----------------------------------------------------------------------------
//
// method : 		Hexapod::SetPar
// 
// description : 	Set a oned parameter. Actually, 1 parameters is supported.
//					This is DataLength
//
// arg(s) : - idx : The oned exp channel number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void Hexapod::SetPar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{
  //cout << "[Hexapod] Setting parameter " << par_name << " for oned channel with index " << idx << " on controller Hexapod/" << inst_name << " (" << DevName << ")" << endl;

  if (hexapod_proxy != NULL){

    if(par_name == "Velocity"){
      double speed;
      if (new_value.data_type == Controller::DOUBLE)	
	speed = new_value.db_data;
      else
	bad_data_type(par_name);

      Tango::DeviceAttribute *da_write = new Tango::DeviceAttribute("Speed ", speed);

      hexapod_proxy->write_attribute(*da_write);
    }

  } else {
    TangoSys_OMemStream o;
    o << " Controller " << get_name() << " for hexapod is NULL" << ends;
    
    Tango::Except::throw_exception((const char *)"HexapodCtrl_BadCtrlPtr",o.str(),
				   (const char *)"Hexapod::SetPar()");
  }


}


//-----------------------------------------------------------------------------
//
// method : 		Hexapod::GetExtraAttributePar
// 
// description : 	Get a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData Hexapod::GetExtraAttributePar(int32_t idx, string &par_name)
{
  Controller::CtrlData par_value;	
  
  string par_name_lower(par_name);
  transform(par_name_lower.begin(),par_name_lower.end(),par_name_lower.begin(),::tolower);
  if (par_name_lower == "reset"){
    TangoSys_OMemStream o;
    o << "Extra attribute " << par_name << " has not sense to be read. Write a value to reset the Hexapod connected to " << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"HexapodCtrl_BadCtrlPtr",o.str(),
				   (const char *)"HexapodCtrl::SetExtraAttributePar()");
  }

  return par_value;
	
}

//-----------------------------------------------------------------------------
//
// method : 		Hexapod::SetExtraAttributePar
// 
// description : 	Set a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void Hexapod::SetExtraAttributePar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{  
  string par_name_lower(par_name);
  
  transform(par_name_lower.begin(),par_name_lower.end(),par_name_lower.begin(),::tolower);
  if (hexapod_proxy != NULL){
    if (par_name_lower == "reset"){
      hexapod_proxy->command_inout("Reset");      
    } else {
      TangoSys_OMemStream o;
      o << "Extra attribute " << par_name << " is unknown for controller HexapodCtrl/" << get_name() << ends;
      
      Tango::Except::throw_exception((const char *)"HexapodCtrl_BadCtrlPtr",o.str(),
				     (const char *)"HexapodCtrl::SetExtraAttributePar()");
    }

  } else {
    TangoSys_OMemStream o;
    o << " Controller " << get_name() << " for hexapod is NULL" << ends;
    
    Tango::Except::throw_exception((const char *)"HexapodCtrl_BadCtrlPtr",o.str(),
				   (const char *)"Hexapod::SetExtraAttributePar()");
  }  
  
}


//-----------------------------------------------------------------------------
//
// method : 		Hexapod::send_to_ctrl
// 
// description : 	Send a string to the controller
//
// arg(s) : - in_str : the string to send to the ctrl
//
//-----------------------------------------------------------------------------

string Hexapod::SendToCtrl(string &in_str)
{
	cout << "[Hexapod] I have received the string: " << in_str << endl;
	string returned_str("Nothing to be done");
	return returned_str;	
}

//-----------------------------------------------------------------------------
//
// method : 		Hexapod::bad_data_type
// 
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void Hexapod::bad_data_type(string &par_name)
{
	TangoSys_OMemStream o;
	o << "A wrong data type has been used to set the parameter " << par_name << ends;

	Tango::Except::throw_exception((const char *)"HexapodCtrl_BadParameter",o.str(),
			       			   	   (const char *)"Hexapod::SetPar()");
}

//
//===============================================================================================
//

const char *Motor_Ctrl_class_name[] = {"Hexapod",NULL};

const char *Hexapod_doc = "This is the C++ controller for the Hexapod class";
const char *Hexapod_gender = "Motor";
const char *Hexapod_model = "Hexapod";
const char *Hexapod_image = "fake_com.png";
const char *Hexapod_organization = "DESY";
const char *Hexapod_logo = "ALBA_logo.png";

Controller::ExtraAttrInfo Hexapod_ctrl_extra_attributes[] = {
  {"Reset","DevLong","Read_Write"},
  NULL};

Controller::PropInfo Hexapod_class_prop[] = {
	{"DeviceName","Name for the Hexapod tango device","DevString",NULL},
	NULL};
							  			 
int32_t Hexapod_MaxDevice = 9; /* Every hexapod tango device moves 6 axis: X,Y,Z,U,V,W + pivot positions (three coordinates) */

extern "C"
{
	
Controller *_create_Hexapod(const char *inst,vector<Controller::Properties> &prop)
{
	return new Hexapod(inst,prop);
}

}
