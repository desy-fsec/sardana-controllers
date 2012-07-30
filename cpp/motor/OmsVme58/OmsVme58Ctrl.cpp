#include <iostream>
#include <OmsVme58Ctrl.h>
#include <pool/PoolAPI.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		OmsVme58Ctrl::OmsVme58Ctrl
// 
// description : 	Ctor of the OmsVme58Ctrl class
//					It retrieve some properties from Tango DB, build a 
//					connection to the Simulated controller and ping it
//					to check if it is alive
//
//-----------------------------------------------------------------------------

OmsVme58Ctrl::OmsVme58Ctrl(const char *inst,vector<Controller::Properties> &prop):MotorController(inst)
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
	MotorData *motor_data_elem = new MotorData;
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
// method : 		OmsVme58Ctrl::~OmsVme58Ctrl
// 
// description : 	Dtor of the OmsVme58Ctrl class
//
//-----------------------------------------------------------------------------

OmsVme58Ctrl::~OmsVme58Ctrl()
{
  //cout << "[OmsVme58Ctrl] class dtor" << endl;	
  map<int32_t, MotorData*>::iterator ite = motor_data.begin();
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
// method : 		OmsVme58Ctrl::AddDevice
// 
// description : 	Register a new device for the controller
//					For the simulated controller, this simply means increment
//					motor count
//
//-----------------------------------------------------------------------------

void OmsVme58Ctrl::AddDevice(int32_t idx)
{
  //cout << "[OmsVme58Ctrl] Creating a new motor with index " << idx << " on controller OmsVme58Ctrl/" << inst_name  << " (" << RootDeviceName << ")" << endl;	

    if(idx > max_device){
	TangoSys_OMemStream o;
	o << "The property 'TangoDevices' has no value for index " << idx << ".";
	o << " Please define a valid tango device before adding a new element to this controller"<< ends;
	
	Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadIndex",o.str(),
				       (const char *)"OmsVme58Ctrl::AddDevice()");
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
// method : 		OmsVme58Ctrl::DeleteDevice
// 
// description : 	Unregister a new device for the controller
//					For the simulated controller, this simply means decrement
//					motor count
//
//-----------------------------------------------------------------------------

void OmsVme58Ctrl::DeleteDevice(int32_t idx)
{
  //cout << "[OmsVme58Ctrl] Deleting motor with index " << idx << " on controller OmsVme58Ctrl/" << inst_name  << " (" << RootDeviceName << ")" << endl;
  if(idx > max_device){
    TangoSys_OMemStream o;
    o << "Trying to delete an inexisting element(" << idx << ") from the controller." << ends;
    
    Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadIndex",o.str(),
				   (const char *)"OmsVme58Ctrl::DeleteDevice()");
  }	
	
  if(motor_data[idx]->proxy != NULL){
    delete motor_data[idx]->proxy;
    motor_data[idx]->proxy = NULL;  
  }
  motor_data[idx]->device_available = false;
}

//-----------------------------------------------------------------------------
//
// method : 		OmsVme58Ctrl::AbortOne
// 
// description : 	Abort a movement.
//
// arg(s) : - idx : The motor number (starting at 1)
//
//-----------------------------------------------------------------------------

void OmsVme58Ctrl::AbortOne(int32_t idx)
{
  
  //cout << "[OmsVme58Ctrl] Aborting one motor with index " << idx  << endl;

  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "OmsVme58Ctrl Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadCtrlPtr",o.str(),
				   (const char *)"OmsVme58Ctrl::AbortOne()");  
  }
	
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "OmsVme58Ctrl Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadCtrlPtr",o.str(),
				     (const char *)"OmsVme58Ctrl::AbortOne()"); 
    }
  }

  motor_data[idx]->proxy->command_inout("StopMove");
}

//-----------------------------------------------------------------------------
//
// method : 		OmsVme58Ctrl::DefinePosition
// 
// description : 	Load a new position for one motor in controller
//
// arg(s) : - idx : The motor number (starting at 1)
//			- new_pos : The position to be loaded in controller
//
//-----------------------------------------------------------------------------

void OmsVme58Ctrl::DefinePosition(int32_t idx,double new_pos)
{
  //cout << "[OmsVme58Ctrl] Defining position for motor with index " << idx << " on controller OmsVme58Ctrl/" << inst_name << " (" << RootDeviceName << ")" << endl;
     
  Tango::DeviceData d_in;

  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << " OmsVme58Ctrl Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadCtrlPtr",o.str(),
				   (const char *)"OmsVme58Ctrl::StartOne()");
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
	o << "OmsVme58Ctrl Device for idx " << idx << " not available" << ends;	
	Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadCtrlPtr",o.str(),
				       (const char *)"OmsVme58Ctrl::StartOne()");	
      }
  }
  
  d_in << new_pos;
  motor_data[idx]->proxy->command_inout("Calibrate", d_in);

}

//-----------------------------------------------------------------------------
//
// method : 		OmsVme58Ctrl::ReadPosition
// 
// description : 	Read a motor position
//
// arg(s) : - idx : The motor number (starting at 1)
//
// This method returns the motor position
//-----------------------------------------------------------------------------

double OmsVme58Ctrl::ReadOne(int32_t idx)
{
  //cout << "[OmsVme58Ctrl] Getting position for motor with index " << idx << " on controller OmsVme58Ctrl/" << inst_name << " (" << RootDeviceName << ")" << endl;
  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "OmsVme58Ctrl Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadCtrlPtr",o.str(),
				   (const char *)"OmsVme58Ctrl::ReadOne()");  
  }
	
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "OmsVme58Ctrl Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadCtrlPtr",o.str(),
				     (const char *)"OmsVme58Ctrl::ReadOne()"); 
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
// method : 		OmsVme58Ctrl::PreStartAll
// 
// description : 	Init movement data
//
//-----------------------------------------------------------------------------
	
void OmsVme58Ctrl::PreStartAll()
{
	//cout << "[OmsVme58Ctrl] PreStartAll on controller OmsVme58Ctrl/" << inst_name << " (" << RootDeviceName << ")" << endl;
	
	wanted_mot_pos.clear();
	wanted_mot.clear();
}

//-----------------------------------------------------------------------------
//
// method : 		OmsVme58Ctrl::StartOne
// 
// description : 	Ask a motor to move
//
// arg(s) : - idx : The motor number (starting at 1)
//			- new_pos : The wanted motor position
//
//-----------------------------------------------------------------------------
	
void OmsVme58Ctrl::StartOne(int32_t idx,double new_pos)
{
	//cout << "[OmsVme58Ctrl] Starting one motor with index " << idx << " on controller OmsVme58Ctrl/" << inst_name << " (" << RootDeviceName << ")" << endl;
  
  if(motor_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "OmsVme58Ctrl Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadCtrlPtr",o.str(),
				   (const char *)"OmsVme58Ctrl::StartOne()");  
  }
	
  if(motor_data[idx]->device_available == false){
    try{
      motor_data[idx]->proxy->ping();
      motor_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      motor_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "OmsVme58Ctrl Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadCtrlPtr",o.str(),
				     (const char *)"OmsVme58Ctrl::StartOne()"); 
    }
  }

  wanted_mot_pos.push_back(new_pos);
  wanted_mot.push_back(idx);
}

//-----------------------------------------------------------------------------
//
// method : 		OmsVme58Ctrl::StartAll
// 
// description : 	Ask a motor to move
//
// arg(s) : - idx : The motor number (starting at 1)
//			- new_pos : The wanted motor position
//
//-----------------------------------------------------------------------------
	
void OmsVme58Ctrl::StartAll()
{
  //cout << "[OmsVme58Ctrl] StartAll() on controller OmsVme58Ctrl/" << inst_name << " (" << RootDeviceName << ")" << endl;
  

  int32_t nb_mot = wanted_mot.size();
  
  for (int32_t loop = 0;loop < nb_mot;loop++)
    {
      
      int idx = wanted_mot[loop];
      Tango::DevDouble position = wanted_mot_pos[loop];

      if(motor_data[idx]->proxy == NULL){
	TangoSys_OMemStream o;
	o << "OmsVme58Ctrl Device Proxy for idx " << idx << " is NULL" << ends;	
	Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadCtrlPtr",o.str(),
				       (const char *)"OmsVme58Ctrl::StartOne()");  
      }
      
      if(motor_data[idx]->device_available == false){
	try{
	  motor_data[idx]->proxy->ping();
	  motor_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
	  motor_data[idx]->device_available = false;
	  TangoSys_OMemStream o;
	  o << "OmsVme58Ctrl Device for idx " << idx << " not available" << ends;	
	  Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadCtrlPtr",o.str(),
					 (const char *)"OmsVme58Ctrl::StartOne()"); 
	}
      }
      Tango::DeviceAttribute da("Position",position);
      motor_data[idx]->proxy->write_attribute(da);

    }
}

//-----------------------------------------------------------------------------
//
// method : 		OmsVme58Ctrl::GetState
// 
// description : 	Get one motor status. Motor status means two things :
//					1 - The motor state (Tango sense)
//					2 - A flag word (long) with switches info
//
// arg(s) : - idx : The motor number (starting at 1)
//			- info_ptr : Pointer to a struct. which willbe filled with
//							 motor status
//
//-----------------------------------------------------------------------------

void OmsVme58Ctrl::StateOne(int32_t idx,Controller::CtrlState *info_ptr)
{
//cout << "[OmsVme58Ctrl] Getting state for motor with index " << idx << " on controller OmsVme58Ctrl/" << inst_name << " (" << RootDeviceName << ")" << endl;

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
// method : 		OmsVme58Ctrl::GetPar
// 
// description : 	Get a motor parameter. Actually, 4 parameters are supported.
//					These are Acceleration, Deceleration, Velocity and Base_rate
//
// arg(s) : - idx : The motor number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData OmsVme58Ctrl::GetPar(int32_t idx,string &par_name)
{
    //cout << "[OmsVme58Ctrl] Getting parameter " << par_name << " for motor with index " << idx << " on controller OmsVme58Ctrl/" << inst_name << " (" << RootDeviceName << ")" << endl;
    
    Controller::CtrlData par_value;
    
    if(motor_data[idx]->proxy == NULL){
	TangoSys_OMemStream o;
	o << "OmsVme58Ctrl Device Proxy for idx " << idx << " is NULL" << ends;	
	Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadCtrlPtr",o.str(),
				       (const char *)"OmsVme58Ctrl::StartOne()");  
    }
    
    if(motor_data[idx]->device_available == false){
	try{
	    motor_data[idx]->proxy->ping();
	    motor_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
	    motor_data[idx]->device_available = false;
	    TangoSys_OMemStream o;
	    o << "OmsVme58Ctrl Device for idx " << idx << " not available" << ends;	
	    Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadCtrlPtr",o.str(),
					   (const char *)"OmsVme58Ctrl::StartOne()"); 
	}
    }

    Tango::DeviceAttribute d_out;
    Tango::DevLong l_value;

    if (par_name == "Acceleration")
    {
	d_out = motor_data[idx]->proxy->read_attribute("Acceleration");
	d_out >> l_value;
	par_value.db_data = (double) l_value;
	par_value.data_type = Controller::DOUBLE;		
    }
    else if (par_name == "Velocity")
    {
	d_out = motor_data[idx]->proxy->read_attribute("SlewRate");
	d_out >> l_value;
	par_value.db_data = (double) l_value;
	par_value.data_type = Controller::DOUBLE;		
    }
    else if (par_name == "Base_rate")
    {
	d_out = motor_data[idx]->proxy->read_attribute("BaseRate");
	d_out >> l_value;
	par_value.db_data = (double) l_value;
	par_value.data_type = Controller::DOUBLE;
    }
    else if (par_name == "Deceleration")
    {
	d_out = motor_data[idx]->proxy->read_attribute("Acceleration");
	d_out >> l_value;
	par_value.db_data = (double) l_value;
	par_value.data_type = Controller::DOUBLE;	
    }
    else if (par_name == "Backlash")
    {
	par_value.db_data = 11.111;
	par_value.data_type = Controller::DOUBLE;
    }
    else
    {
	TangoSys_OMemStream o;
	o << "Parameter " << par_name << " is unknown for controller OmsVme58Ctrl/" << get_name() << ends;
	
	Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadCtrlPtr",o.str(),
				       (const char *)"OmsVme58Ctrl::GetPar()");
    }
    
    return par_value;
}

//-----------------------------------------------------------------------------
//
// method : 		OmsVme58Ctrl::SetPar
// 
// description : 	Set a motor parameter. Actually, 4 parameters are supported.
//					These are Acceleration, Deceleration, Velocity and Base_rate
//
// arg(s) : - idx : The motor number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void OmsVme58Ctrl::SetPar(int32_t idx,string &par_name,Controller::CtrlData &new_value)
{
    //cout << "[OmsVme58Ctrl] Setting parameter " << par_name << " for motor with index " << idx << " on controller OmsVme58Ctrl/" << inst_name << " (" << RootDeviceName << ")" << endl
    
    Tango::DevLong l_value;

    if(motor_data[idx]->proxy == NULL){
	TangoSys_OMemStream o;
	o << "OmsVme58Ctrl Device Proxy for idx " << idx << " is NULL" << ends;	
	Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadCtrlPtr",o.str(),
				       (const char *)"OmsVme58Ctrl::StartOne()");  
    }
    
    if(motor_data[idx]->device_available == false){
	try{
	    motor_data[idx]->proxy->ping();
	    motor_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
	    motor_data[idx]->device_available = false;
	    TangoSys_OMemStream o;
	    o << "OmsVme58Ctrl Device for idx " << idx << " not available" << ends;	
	    Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadCtrlPtr",o.str(),
					   (const char *)"OmsVme58Ctrl::StartOne()"); 
	}
    } 
    
    if (par_name == "Acceleration" || par_name == "Deceleration")
    {
	l_value = (long) new_value.db_data;
	Tango::DeviceAttribute da_acc("Acceleration",l_value );
	if (new_value.data_type == Controller::DOUBLE)
	    motor_data[idx]->proxy->write_attribute(da_acc);
	else
	    bad_data_type(par_name);
    } 
    else if(par_name == "Velocity")
    {
	l_value = (long) new_value.db_data;
	Tango::DeviceAttribute da_vel("SlewRate",l_value);
	if (new_value.data_type == Controller::DOUBLE)
	    motor_data[idx]->proxy->write_attribute(da_vel);
	else
	    bad_data_type(par_name);
    } 
    else if(par_name == "Base_rate")
    {
	l_value = (long) new_value.db_data;
	Tango::DeviceAttribute da_br("BaseRate",l_value );
	if (new_value.data_type == Controller::DOUBLE)
	    motor_data[idx]->proxy->write_attribute(da_br);
	else
	    bad_data_type(par_name);
    }  
    else if(par_name == "Step_per_unit")
    {
    }
    else if (par_name == "Backlash")
    {
	if (new_value.data_type == Controller::INT32)	
	    cout << "[OmsVme58Ctrl] New value for backlash is " << new_value.int32_data << endl;
	else
	    bad_data_type(par_name);
    }
    else
    {
	TangoSys_OMemStream o;
	o << "Parameter " << par_name << " is unknown for controller OmsVme58Ctrl/" << get_name() << ends;
	
	Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadCtrlPtr",o.str(),
				       (const char *)"OmsVme58Ctrl::GetPar()");
    }
    
}

//-----------------------------------------------------------------------------
//
// method : 		OmsVme58Ctrl::GetExtraAttributePar
// 
// description : 	Get a motor extra attribute parameter.
//
// arg(s) : - idx : The motor number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData OmsVme58Ctrl::GetExtraAttributePar(int32_t idx,string &par_name)
{ 
    Controller::CtrlData par_value;
    
    Tango::DevLong par_tmp_l;

    if(motor_data[idx]->proxy == NULL){
	TangoSys_OMemStream o;
	o << "OmsVme58Ctrl Device Proxy for idx " << idx << " is NULL" << ends;	
	Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadCtrlPtr",o.str(),
				       (const char *)"OmsVme58Ctrl::StartOne()");  
    }
    
    if(motor_data[idx]->device_available == false){
	try{
	    motor_data[idx]->proxy->ping();
	    motor_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
	    motor_data[idx]->device_available = false;
	    TangoSys_OMemStream o;
	    o << "OmsVme58Ctrl Device for idx " << idx << " not available" << ends;	
	    Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadCtrlPtr",o.str(),
					   (const char *)"OmsVme58Ctrl::StartOne()"); 
	}
    }

    Tango::DeviceAttribute d_out;

    if (par_name == "Conversion")
    {
	d_out = motor_data[idx]->proxy->read_attribute("Conversion");
	d_out >> par_value.db_data;
	par_value.data_type = Controller::DOUBLE;		
    } 
    else if (par_name == "SettleTime")
    {
	d_out = motor_data[idx]->proxy->read_attribute("SettleTime");
	d_out >> par_value.db_data;
	par_value.data_type = Controller::DOUBLE;		
    }
    else if (par_name == "UnitBacklash")
    {
	d_out = motor_data[idx]->proxy->read_attribute("UnitBacklash");
	d_out >> par_value.db_data;
	par_value.data_type = Controller::DOUBLE;		
    }
    else if (par_name == "VelocityMax")
    {
	d_out = motor_data[idx]->proxy->read_attribute("SlewRateMax");
	d_out >> par_tmp_l;
	par_value.int32_data = (int32_t) par_tmp_l;
	par_value.data_type = Controller::INT32;		
    }
    else if (par_name == "VelocityMin")
    {
	d_out = motor_data[idx]->proxy->read_attribute("SlewRateMin");
	d_out >> par_tmp_l;
	par_value.int32_data = (int32_t) par_tmp_l;
	par_value.data_type = Controller::INT32;		
    }
    else if (par_name == "StepBacklash")
    {
	d_out = motor_data[idx]->proxy->read_attribute("StepBacklash");
	d_out >> par_tmp_l;
	par_value.int32_data = (int32_t) par_tmp_l;
	par_value.data_type = Controller::INT32;		
    }
    else if (par_name == "StepPosition")
    {
	d_out = motor_data[idx]->proxy->read_attribute("StepPositionController");
	d_out >> par_tmp_l;
	par_value.int32_data = (int32_t) par_tmp_l;
	par_value.data_type = Controller::INT32;		
    }
    else if ( ( par_name == "Calibrate") || ( par_name == "UserCalibrate"))
    {
	par_value.db_data = 0;
	par_value.data_type = Controller::DOUBLE;
    } 
    else if (par_name == "PositionEncoder")
    {
	d_out = motor_data[idx]->proxy->read_attribute("PositionEncoder");
	d_out >> par_value.db_data;
	par_value.data_type = Controller::DOUBLE;		
    }
    else if (par_name == "HomePosition")
    {
	d_out = motor_data[idx]->proxy->read_attribute("HomePosition");
	d_out >> par_value.db_data;
	par_value.data_type = Controller::DOUBLE;		
    }
    else if (par_name == "FlagUseEncoderPosition")
    {
	d_out = motor_data[idx]->proxy->read_attribute("FlagUseEncoderPosition");
	d_out >> par_tmp_l;
	par_value.int32_data = (int32_t) par_tmp_l;
	par_value.data_type = Controller::INT32;		
    }
    else
    {
	TangoSys_OMemStream o;
	o << "Extra attribute " << par_name << " is unknown for controller OmsVme58Ctrl/" << get_name() << ends;
	
	Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadCtrlPtr",o.str(),
				       (const char *)"OmsVme58Ctrl::GetExtraAttributePar()");
    }	
    return par_value;
}

//-----------------------------------------------------------------------------
//
// method : 		OmsVme58Ctrl::SetExtraAttributePar
// 
// description : 	Set a motor extra attribute parameter.
//
// arg(s) : - idx : The motor number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void OmsVme58Ctrl::SetExtraAttributePar(int32_t idx,string &par_name,Controller::CtrlData &new_value)
{

     
    Tango::DeviceData d_in;
  
    if(motor_data[idx]->proxy == NULL){
	TangoSys_OMemStream o;
	o << "OmsVme58Ctrl Device Proxy for idx " << idx << " is NULL" << ends;	
	Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadCtrlPtr",o.str(),
				       (const char *)"OmsVme58Ctrl::StartOne()");  
    }
    
    if(motor_data[idx]->device_available == false){
	try{
	    motor_data[idx]->proxy->ping();
	    motor_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
	    motor_data[idx]->device_available = false;
	    TangoSys_OMemStream o;
	    o << "OmsVme58Ctrl Device for idx " << idx << " not available" << ends;	
	    Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadCtrlPtr",o.str(),
					   (const char *)"OmsVme58Ctrl::StartOne()"); 
	}
    } 
    
    if (par_name == "Conversion")
    {
	Tango::DeviceAttribute da_con("Conversion",new_value.db_data );
	if (new_value.data_type == Controller::DOUBLE)
	    motor_data[idx]->proxy->write_attribute(da_con);
	else
	    bad_data_type(par_name);
    }
    else if (par_name == "SettleTime")
    {
	Tango::DeviceAttribute da_st("SettleTime",new_value.db_data );
	if (new_value.data_type == Controller::DOUBLE)
	    motor_data[idx]->proxy->write_attribute(da_st);
	else
	    bad_data_type(par_name);
    }
    else if (par_name == "UnitBacklash")
    {
	Tango::DeviceAttribute da_ub("UnitBacklash",new_value.db_data );
	if (new_value.data_type == Controller::DOUBLE)
	    motor_data[idx]->proxy->write_attribute(da_ub);
	else
	    bad_data_type(par_name);
    } 
    else if (par_name == "VelocityMax")
    {
	Tango::DeviceAttribute da_vmax("SlewRateMax",(Tango::DevLong)new_value.int32_data );
	if (new_value.data_type == Controller::INT32)
	    motor_data[idx]->proxy->write_attribute(da_vmax);
	else
	    bad_data_type(par_name);
    } 
    else if (par_name == "VelocityMin")
    {
	Tango::DeviceAttribute da_vmin("SlewRateMin",(Tango::DevLong)new_value.int32_data );
	if (new_value.data_type == Controller::INT32)
	    motor_data[idx]->proxy->write_attribute(da_vmin);
	else
	    bad_data_type(par_name);
    } 
    else if (par_name == "StepBacklash")
    {
	Tango::DeviceAttribute da_sb("StepBacklash",(Tango::DevLong)new_value.int32_data );
	if (new_value.data_type == Controller::INT32)
	    motor_data[idx]->proxy->write_attribute(da_sb);
	else
	    bad_data_type(par_name);
    }
    else if (par_name == "StepPosition")
    {
	Tango::DeviceAttribute da_sp("StepPosition",(Tango::DevLong)new_value.int32_data );
	if (new_value.data_type == Controller::INT32)
	    motor_data[idx]->proxy->write_attribute(da_sp);
	else
	    bad_data_type(par_name);
    } 
    else if (par_name == "Calibrate")
    {
	if (new_value.data_type == Controller::DOUBLE){
	    d_in << new_value.db_data;
	    motor_data[idx]->proxy->command_inout("Calibrate", d_in);
	}
	else
	    bad_data_type(par_name);
    } 
    else if (par_name == "UserCalibrate")
    {
	if (new_value.data_type == Controller::DOUBLE){
	    d_in << new_value.db_data;
	    motor_data[idx]->proxy->command_inout("UserCalibrate", d_in);
	}
	else
	    bad_data_type(par_name);
    }
    else if (par_name == "HomePosition")
    {
	Tango::DeviceAttribute da_hp("HomePosition",new_value.db_data );
	if (new_value.data_type == Controller::DOUBLE)
	    motor_data[idx]->proxy->write_attribute(da_hp);
	else
	    bad_data_type(par_name);
    } 
    else if (par_name == "MoveHome")
    {
	motor_data[idx]->proxy->command_inout("MoveHome");
    }
    else if (par_name == "FlagUseEncoderPosition")
    {
	Tango::DeviceAttribute da_fuep("FlagUseEncoderPosition",(Tango::DevLong)new_value.int32_data );
	if (new_value.data_type == Controller::INT32)
	    motor_data[idx]->proxy->write_attribute(da_fuep);
	else
	    bad_data_type(par_name);
    }
    else
    {
	TangoSys_OMemStream o;
	o << "Extra attribute " << par_name << " is unknown for controller OmsVme58Ctrl/" << get_name() << ends;
	
	Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadCtrlPtr",o.str(),
				       (const char *)"OmsVme58Ctrl::SetExtraAttributePar()");
    }
}


//-----------------------------------------------------------------------------
//
// method : 		OmsVme58Ctrl::send_to_ctrl
// 
// description : 	Send a string to the controller
//
// arg(s) : - idx : The motor number (starting at 1)
//			- featr_name : The feature name
//			- new_value : The feature value
//
//-----------------------------------------------------------------------------

string OmsVme58Ctrl::SendToCtrl(string &in_str)
{
	//cout << "[OmsVme58Ctrl] I have received the string: " << in_str << endl;
	string returned_str("Nothing to send");
	return returned_str;	
}

//-----------------------------------------------------------------------------
//
// method : 		OmsVme58Ctrl::bad_data_type
// 
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void OmsVme58Ctrl::bad_data_type(string &par_name)
{
	TangoSys_OMemStream o;
	o << "A wrong data type has been used to set the parameter " << par_name << ends;

	Tango::Except::throw_exception((const char *)"OmsVme58Ctrl_BadParameter",o.str(),
			       			   	   (const char *)"OmsVme58Ctrl::SetPar()");
}

//
//===============================================================================================
//

const char *Motor_Ctrl_class_name[] = {"OmsVme58Ctrl",NULL};
const char *OmsVme58Ctrl_doc = "This is the C++ controller for the OmsVme58Ctrl class";
		
Controller::ExtraAttrInfo OmsVme58Ctrl_ctrl_extra_attributes[] = {
  {"Conversion","DevDouble","Read_Write"},
  {"SettleTime","DevDouble","Read_Write"},
  {"UnitBacklash","DevDouble","Read_Write"},
  {"VelocityMax","DevLong","Read_Write"},
  {"VelocityMin","DevLong","Read_Write"},
  {"StepBacklash","DevLong","Read_Write"},
  {"Calibrate","DevDouble","Read_Write"},
  {"UserCalibrate","DevDouble","Read_Write"},
  {"StepPosition","DevLong","Read_Write"},
  {"PositionEncoder","DevDouble","Read_Write"},
  {"HomePosition","DevDouble","Read_Write"},
  {"MoveHome","DevLong","Read_Write"},
  {"FlagUseEncoderPosition","DevLong","Read_Write"},
  NULL};


//char *OmsVme58Ctrl_ctrl_features[] = {"Backlash","Rounding","Encoder","Home_acceleration",NULL};
//const char *OmsVme58Ctrl_ctrl_features[] = {"WantRounding","Encoder","Home_acceleration",NULL};
const char *OmsVme58Ctrl_ctrl_features[] = {"Encoder","Home_acceleration",NULL};


Controller::PropInfo OmsVme58Ctrl_class_prop[] = {
    {"RootDeviceName","Root name for tango devices","DevString"}, 
    NULL};
							  			 
int32_t OmsVme58Ctrl_MaxDevice = 99;

extern "C"
{
	
Controller *_create_OmsVme58Ctrl(const char *inst,vector<Controller::Properties> &prop)
{
	return new OmsVme58Ctrl(inst,prop);
}

Controller *_create_Toto(const char *inst,vector<Controller::Properties> &prop)
{
	return new OmsVme58Ctrl(inst,prop);
}
}
