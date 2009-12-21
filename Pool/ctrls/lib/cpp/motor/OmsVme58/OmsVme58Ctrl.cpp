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
  //cout << "[OmsVme58Ctrl] Received " << prop.size() << " properties" << endl;
  for (unsigned long loop = 0;loop < prop.size();loop++)
    {
      if( prop[loop].name == "DevName" )
	{
	  DevName = prop[loop].value.string_prop[0]; 
	}
    }
  
  simu_ctrl = NULL;
  home_acc = 1.0;
  
  //
  // Create a DeviceProxy on the simulated controller and set
  // it in automatic reconnection mode
  //
  simu_ctrl = Pool_ns::PoolUtil::instance()->get_device(inst_name, DevName);
  
  //
  // Ping the device to be sure that it is present
  //
  if(simu_ctrl == NULL)
    {
      TangoSys_OMemStream o;
      o << "The PoolAPI did not provide a valid simulator device" << ends;
      Tango::Except::throw_exception((const char *)"SimuCtrl_BadPoolAPI",o.str(),
				     (const char *)"OmsVme58Ctrl::OmsVme58Ctrl()");
    }
  
  try
    {
      simu_ctrl->ping();
    }
  catch (Tango::DevFailed &e)
    {
      throw;
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
  //if (simu_ctrl != NULL)
  //	delete simu_ctrl;
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
  //cout << "[OmsVme58Ctrl] Creating a new motor with index " << idx << " on controller OmsVme58Ctrl/" << inst_name  << " (" << DevName << ")" << endl;
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
  //cout << "[OmsVme58Ctrl] Deleting motor with index " << idx << " on controller OmsVme58Ctrl/" << inst_name  << " (" << DevName << ")" << endl;
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
  //cout << "[OmsVme58Ctrl] Aborting one motor with index " << idx << " on controller OmsVme58Ctrl/" << inst_name << " (" << DevName << ")" << endl;
  if (simu_ctrl != NULL)
    {
      Tango::DeviceData d_in;
      d_in << (Tango::DevLong)idx;
      simu_ctrl->command_inout("Abort",d_in);
    }
  else
    {
      TangoSys_OMemStream o;
      o << "Simulated controller for controller OmsVme58Ctrl/" << get_name() << " is NULL" << ends;
      
      Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",o.str(),
				     (const char *)"OmsVme58Ctrl::AbortOne()");
    }
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
  //cout << "[OmsVme58Ctrl] Defining position for motor with index " << idx << " on controller OmsVme58Ctrl/" << inst_name << " (" << DevName << ")" << endl;
  if (simu_ctrl != NULL)
    {
      Tango::DeviceData d_in;
      
      vector<double> v_db;
      v_db.push_back(new_pos);
      
      vector<string> v_str;
      convert_stream << (Tango::DevLong)idx;
      v_str.push_back(convert_stream.str());
      convert_stream.str("");
      
      d_in.insert(v_db,v_str);	
      simu_ctrl->command_inout("LoadAxePosition",d_in);
    }
  else
    {
      TangoSys_OMemStream o;
      o << "Simulated controller for controller OmsVme58Ctrl/" << get_name() << " is NULL" << ends;
      
      Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",o.str(),
				     (const char *)"OmsVme58Ctrl::DefinePosition()");
    }
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
  //cout << "[OmsVme58Ctrl] Getting position for motor with index " << idx << " on controller OmsVme58Ctrl/" << inst_name << " (" << DevName << ")" << endl;
  double received_pos;
  
  if (simu_ctrl != NULL)
    {
      Tango::DeviceData d_in,d_out;

      d_in << (Tango::DevLong)idx;
      
      d_out = simu_ctrl->command_inout("GetAxePosition",d_in);
      d_out >> received_pos;
    }
  else
    {
      TangoSys_OMemStream o;
      o << "Simulated controller for controller OmsVme58Ctrl/" << get_name() << " is NULL" << ends;
      
      Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",o.str(),
				     (const char *)"OmsVme58Ctrl::ReadOne()");
    }
  return received_pos;
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
	//cout << "[OmsVme58Ctrl] PreStartAll on controller OmsVme58Ctrl/" << inst_name << " (" << DevName << ")" << endl;
	
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
	//cout << "[OmsVme58Ctrl] Starting one motor with index " << idx << " on controller OmsVme58Ctrl/" << inst_name << " (" << DevName << ")" << endl;

	if (simu_ctrl != NULL)
	{
		wanted_mot_pos.push_back(new_pos);
		wanted_mot.push_back(idx);
	}
	else
	{
		TangoSys_OMemStream o;
		o << "Simulated controller for controller OmsVme58Ctrl/" << get_name() << " is NULL" << ends;
		
		Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",o.str(),
					       			   (const char *)"OmsVme58Ctrl::StartOne()");
	}
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
  //cout << "[OmsVme58Ctrl] StartAll() on controller OmsVme58Ctrl/" << inst_name << " (" << DevName << ")" << endl;
  
  if (simu_ctrl != NULL)
    {
      int32_t nb_mot = wanted_mot.size();
      
      for (int32_t loop = 0;loop < nb_mot;loop++)
	{
	  Tango::DeviceData d_in;
	  
	  vector<double> v_db;
	  v_db.push_back(wanted_mot_pos[loop]);
	  
	  vector<string> v_str;
	  convert_stream << wanted_mot[loop];
	  v_str.push_back(convert_stream.str());
	  convert_stream.str("");

	  
	  d_in.insert(v_db,v_str);	
	  simu_ctrl->command_inout("SetAxePosition",d_in);
	}
    }
  else
    {
      TangoSys_OMemStream o;
      o << "Simulated controller for controller OmsVme58Ctrl/" << get_name() << " is NULL" << ends;
      
      Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",o.str(),
				     (const char *)"OmsVme58Ctrl::StartOne()");
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
//cout << "[OmsVme58Ctrl] Getting state for motor with index " << idx << " on controller OmsVme58Ctrl/" << inst_name << " (" << DevName << ")" << endl;

	MotorController::MotorState *mot_info_ptr = static_cast<MotorController::MotorState *>(info_ptr);

	if (simu_ctrl != NULL)
	{
		Tango::DeviceData d_in,d_out;
		d_in << (Tango::DevLong)idx;
		d_out = simu_ctrl->command_inout("GetAxeStatus",d_in);

		const Tango::DevVarLongArray *dvla;
		d_out >> dvla;
		mot_info_ptr->state = (*dvla)[0];
		mot_info_ptr->switches = (*dvla)[1];

	}
	else
	{
		TangoSys_OMemStream o;
		o << "Simulated controller for controller OmsVme58Ctrl/" << get_name() << " is NULL" << ends;
		
		Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",o.str(),
					       			   (const char *)"OmsVme58Ctrl::GetStatus()");
	}
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
	//cout << "[OmsVme58Ctrl] Getting parameter " << par_name << " for motor with index " << idx << " on controller OmsVme58Ctrl/" << inst_name << " (" << DevName << ")" << endl;

	Controller::CtrlData par_value;	
	if (simu_ctrl != NULL)
	{
		Tango::DeviceData d_in,d_out;

		d_in << (Tango::DevLong)idx;		
		if (par_name == "Acceleration")
		{
			d_out = simu_ctrl->command_inout("GetAxeAcceleration",d_in);
			d_out >> par_value.db_data;
			par_value.data_type = Controller::DOUBLE;		
		}
		else if (par_name == "Velocity")
		{
			d_out = simu_ctrl->command_inout("GetAxeVelocity",d_in);
			d_out >> par_value.db_data;
			par_value.data_type = Controller::DOUBLE;		
		}
		else if (par_name == "Base_rate")
		{
			d_out = simu_ctrl->command_inout("GetAxeBase_rate",d_in);
			d_out >> par_value.db_data;
			par_value.data_type = Controller::DOUBLE;
		}
		else if (par_name == "Deceleration")
		{
			d_out = simu_ctrl->command_inout("GetAxeDeceleration",d_in);
			d_out >> par_value.db_data;
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
			
			Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",o.str(),
						       			   (const char *)"OmsVme58Ctrl::GetPar()");
		}
	}
	else
	{
		TangoSys_OMemStream o;
		o << "Simulated controller for controller OmsVme58Ctrl/" << get_name() << " is NULL" << ends;
		
		Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",o.str(),
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
	//cout << "[OmsVme58Ctrl] Setting parameter " << par_name << " for motor with index " << idx << " on controller OmsVme58Ctrl/" << inst_name << " (" << DevName << ")" << endl;

	if (simu_ctrl != NULL)
	{
		Tango::DeviceData d_in;

		vector<double> v_db;
		if (par_name != "Backlash")
		{
			if (new_value.data_type == Controller::DOUBLE)	
				v_db.push_back(new_value.db_data);
			else
				bad_data_type(par_name);
		}
	
		vector<string> v_str;
		convert_stream << (Tango::DevLong)idx;
		v_str.push_back(convert_stream.str());
		convert_stream.str("");
	
		d_in.insert(v_db,v_str);	
				
		if (par_name == "Acceleration")
		{
			simu_ctrl->command_inout("SetAxeAcceleration",d_in);
		}
		else if (par_name == "Velocity")
		{
			simu_ctrl->command_inout("SetAxeVelocity",d_in);
		}
		else if (par_name == "Base_rate")
		{
			simu_ctrl->command_inout("SetAxeBase_rate",d_in);
		}
		else if (par_name == "Deceleration")
		{
			simu_ctrl->command_inout("SetAxeDeceleration",d_in);
		}
		else if (par_name == "Step_per_unit")
		{
		  //			cout << "[OmsVme58Ctrl] New Step_per_unit feature is " << new_value.db_data << endl;
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
			
			Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",o.str(),
						       			   (const char *)"OmsVme58Ctrl::GetPar()");
		}
	}
	else
	{
		TangoSys_OMemStream o;
		o << "Simulated controller for controller OmsVme58Ctrl/" << get_name() << " is NULL" << ends;
		
		Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",o.str(),
					       			   (const char *)"OmsVme58Ctrl::SetPar()");
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

    double par_tmp_db;
    Tango::DevLong   par_tmp_l;

	if (par_name == "Conversion")
	{
		if (simu_ctrl != NULL)
		{
			Tango::DeviceData d_in,d_out;
			
			d_in << (Tango::DevLong)idx;
			d_out = simu_ctrl->command_inout("GetAxeConversion",d_in);
			d_out >> par_tmp_db;
            par_value.db_data = par_tmp_db;
			par_value.data_type = Controller::DOUBLE;
		}	
	}
    else if (par_name == "SettleTime")
	{

		Tango::DeviceData d_in,d_out;
		
		d_in << (Tango::DevLong)idx;
		d_out = simu_ctrl->command_inout("GetAxeSettleTime",d_in);
		d_out >> par_tmp_db;
		par_value.db_data = par_tmp_db;
		par_value.data_type = Controller::DOUBLE;
    }
	else if (par_name == "UnitBacklash")
	{

		Tango::DeviceData d_in,d_out;
		
		d_in << (Tango::DevLong)idx;
		d_out = simu_ctrl->command_inout("GetAxeUnitBacklash",d_in);
		d_out >> par_tmp_db;
		par_value.db_data = par_tmp_db;
		par_value.data_type = Controller::DOUBLE;
    }
	else if (par_name == "VelocityMax")
	{

		Tango::DeviceData d_in,d_out;
		
		d_in << (Tango::DevLong)idx;
		d_out = simu_ctrl->command_inout("GetAxeVelocityMax",d_in);
		d_out >> par_tmp_l;
        
		par_value.int32_data = (int32_t)par_tmp_l;
		par_value.data_type = Controller::INT32;
    }
	else if (par_name == "VelocityMin")
	{

		Tango::DeviceData d_in,d_out;
		
		d_in << (Tango::DevLong)idx;
		d_out = simu_ctrl->command_inout("GetAxeVelocityMin",d_in);
		d_out >> par_tmp_l;
		par_value.int32_data = (int32_t)par_tmp_l;
		par_value.data_type = Controller::INT32;
    }
	else if (par_name == "StepBacklash")
	{

		Tango::DeviceData d_in,d_out;
		
		d_in << (Tango::DevLong)idx;
		d_out = simu_ctrl->command_inout("GetAxeStepBacklash",d_in);
		d_out >> par_tmp_l;
		par_value.int32_data = (int32_t)par_tmp_l;
		par_value.data_type = Controller::INT32;
    }
	else if (par_name == "StepPosition")
	{

		Tango::DeviceData d_in,d_out;
		
		d_in << (Tango::DevLong)idx;
		d_out = simu_ctrl->command_inout("GetAxeStepPosition",d_in);
		d_out >> par_tmp_l;
		par_value.int32_data = (int32_t)par_tmp_l;
		par_value.data_type = Controller::INT32;
    }
	else if ( ( par_name == "Calibrate") || ( par_name == "UserCalibrate"))
	{
	        par_value.db_data = 0;
		par_value.data_type = Controller::DOUBLE;
	}
	else if (par_name == "PositionEncoder")
	{

	  Tango::DeviceData d_in,d_out;
	  
	  d_in << (Tango::DevLong)idx;
	  d_out = simu_ctrl->command_inout("GetAxisPositionEncoder",d_in);
	  d_out >> par_tmp_db;
	  par_value.db_data = par_tmp_db;
	  par_value.data_type = Controller::DOUBLE;
	}
	else if (par_name == "HomePosition")
	{

	  Tango::DeviceData d_in,d_out;
	  
	  d_in << (Tango::DevLong)idx;
	  d_out = simu_ctrl->command_inout("GetAxisHomePosition",d_in);
	  d_out >> par_tmp_db;
	  par_value.db_data = par_tmp_db;
	  par_value.data_type = Controller::DOUBLE;
	}
	else if (par_name == "FlagUseEncoderPosition")
	{
	  
	  Tango::DeviceData d_in,d_out;
	  
	  d_in << (Tango::DevLong)idx;
	  d_out = simu_ctrl->command_inout("GetAxisFlagUseEncoderPosition",d_in);
	  d_out >> par_tmp_l;
	  
	  par_value.int32_data = (int32_t)par_tmp_l;
	  par_value.data_type = Controller::INT32;
	}
	else
	{
		TangoSys_OMemStream o;
		o << "Extra attribute " << par_name << " is unknown for controller OmsVme58Ctrl/" << get_name() << ends;
			
		Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",o.str(),
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
  if (par_name == "Conversion")
    {
      if(simu_ctrl != NULL)
	{
	  Tango::DeviceData d_in;
	  
	  vector<double> v_db;
	  if (new_value.data_type == DOUBLE){
	    cout << "[OmsVme58Ctrl] New value for Conversion extra attribute is " << new_value.db_data << endl;
	    v_db.push_back(new_value.db_data);
	    
	  }else
	    bad_data_type(par_name);
	  
	  vector<string> v_str;
	  convert_stream << (Tango::DevLong)idx;
	  v_str.push_back(convert_stream.str());
	  convert_stream.str("");
	  d_in.insert(v_db,v_str);
	  simu_ctrl->command_inout("SetAxeConversion",d_in);		
	}
    }
  else if (par_name == "SettleTime")
    {
      if(simu_ctrl != NULL)
	{
	  Tango::DeviceData d_in;
	  
	  vector<double> v_db;
	  if (new_value.data_type == DOUBLE){
	    cout << "[OmsVme58Ctrl] New value for SettleTime extra attribute is " << new_value.db_data << endl;
	    v_db.push_back(new_value.db_data);
	    
	  }else
	    bad_data_type(par_name);
	  
	  vector<string> v_str;
	  convert_stream << (Tango::DevLong)idx;
	  v_str.push_back(convert_stream.str());
	  convert_stream.str("");
	  d_in.insert(v_db,v_str);
	  simu_ctrl->command_inout("SetAxeSettleTime",d_in);		
	}
    }
  else if (par_name == "UnitBacklash")
    {
      if(simu_ctrl != NULL)
	{
	  Tango::DeviceData d_in;
	  
	  vector<double> v_db;
	  if (new_value.data_type == DOUBLE){
	    cout << "[OmsVme58Ctrl] New value for UnitBacklash extra attribute is " << new_value.db_data << endl;
	    v_db.push_back(new_value.db_data);
	    
	  }else
	    bad_data_type(par_name);
	  
	  vector<string> v_str;
	  convert_stream << (Tango::DevLong)idx;
	  v_str.push_back(convert_stream.str());
	  convert_stream.str("");
	  d_in.insert(v_db,v_str);
	  simu_ctrl->command_inout("SetAxeUnitBacklash",d_in);		
	}
    }
  else if (par_name == "VelocityMax")
    {
      if(simu_ctrl != NULL)
	{
	  Tango::DeviceData d_in;
	  
	  vector<Tango::DevLong> v_db;
	  if (new_value.data_type == INT32){
	    cout << "[OmsVme58Ctrl] New value for VelocityMax extra attribute is " << new_value.int32_data << endl;
	    v_db.push_back((Tango::DevLong)new_value.int32_data);
	    
	  }else
	    bad_data_type(par_name);
	  
	  vector<string> v_str;
	  convert_stream << (Tango::DevLong)idx;
	  v_str.push_back(convert_stream.str());
	  convert_stream.str("");
	  d_in.insert(v_db,v_str);
	  simu_ctrl->command_inout("SetAxeVelocityMax",d_in);		
	}
    }
  else if (par_name == "VelocityMin")
    {
      if(simu_ctrl != NULL)
	{
	  Tango::DeviceData d_in;
	  
	  vector<Tango::DevLong> v_db;
	  if (new_value.data_type == INT32){
	    cout << "[OmsVme58Ctrl] New value for VelocityMin extra attribute is " << new_value.int32_data << endl;
	    v_db.push_back((Tango::DevLong)new_value.int32_data);
	    
	  }else
	    bad_data_type(par_name);
	  
	  vector<string> v_str;
	  convert_stream << (Tango::DevLong)idx;
	  v_str.push_back(convert_stream.str());
	  convert_stream.str("");
	  d_in.insert(v_db,v_str);
            simu_ctrl->command_inout("SetAxeVelocityMin",d_in);		
		}
	}
  else if (par_name == "StepBacklash")
    {
      if(simu_ctrl != NULL)
	{
	  Tango::DeviceData d_in;
	  
	  vector<Tango::DevLong> v_db;
	  if (new_value.data_type == INT32){
	    cout << "[OmsVme58Ctrl] New value for StepBacklash extra attribute is " << new_value.int32_data << endl;
	    v_db.push_back((Tango::DevLong)new_value.int32_data);
	    
	  }else
	    bad_data_type(par_name);
	  
	  vector<string> v_str;
	  convert_stream << (Tango::DevLong)idx;
	  v_str.push_back(convert_stream.str());
	  convert_stream.str("");
	  d_in.insert(v_db,v_str);
	  simu_ctrl->command_inout("SetAxeStepBacklash",d_in);		
	}
    }
  else if (par_name == "StepPosition")
    {
      if(simu_ctrl != NULL)
	{
	  Tango::DeviceData d_in;
	  
	  vector<Tango::DevLong> v_db;
	  
	  if (new_value.data_type == INT32){
	    cout << "[OmsVme58Ctrl] New value for StepPosition extra attribute is " << new_value.int32_data << endl;
	    v_db.push_back((Tango::DevLong)new_value.int32_data);
	    
	  }else
	    bad_data_type(par_name);
	  
	  vector<string> v_str;
	  convert_stream << (Tango::DevLong)idx;
	  v_str.push_back(convert_stream.str());
	  convert_stream.str("");
	  d_in.insert(v_db,v_str);
	  simu_ctrl->command_inout("SetAxeStepPosition",d_in);		
	}
    }
  else if (par_name == "Calibrate")
    {
      if(simu_ctrl != NULL)
	{
	  Tango::DeviceData d_in;
	  
	  vector<double> v_db;
	  if (new_value.data_type == DOUBLE){
	    cout << "[OmsVme58Ctrl] New value for Calibrate extra attribute is " << new_value.db_data << endl;
	    v_db.push_back(new_value.db_data);
	    
	  }else
	    bad_data_type(par_name);
	  
	  vector<string> v_str;
	  convert_stream << (Tango::DevLong)idx;
	  v_str.push_back(convert_stream.str());
	  convert_stream.str("");
	  d_in.insert(v_db,v_str);
	  simu_ctrl->command_inout("AxeCalibrate",d_in);		
	}
    }
  else if (par_name == "UserCalibrate")
    {
      if(simu_ctrl != NULL)
	{
	  Tango::DeviceData d_in;
	  
	  vector<double> v_db;
	  if (new_value.data_type == DOUBLE){
	    cout << "[OmsVme58Ctrl] New value for UserCalibrate extra attribute is " << new_value.db_data << endl;
	    v_db.push_back(new_value.db_data);
	    
	  }else
	    bad_data_type(par_name);
	  
	  vector<string> v_str;
	  convert_stream << (Tango::DevLong)idx;
	  v_str.push_back(convert_stream.str());
	  convert_stream.str("");
	  d_in.insert(v_db,v_str);
            simu_ctrl->command_inout("AxeUserCalibrate",d_in);		
	}
    }
  if (par_name == "HomePosition")
    {
      if(simu_ctrl != NULL)
	{
	  Tango::DeviceData d_in;
	  
	  vector<double> v_db;
	  if (new_value.data_type == DOUBLE){
	    cout << "[OmsVme58Ctrl] New value for Conversion extra attribute is " << new_value.db_data << endl;
	    v_db.push_back(new_value.db_data);
	    
	  }else
	    bad_data_type(par_name);
	  
	  vector<string> v_str;
	  convert_stream << (Tango::DevLong)idx;
	  v_str.push_back(convert_stream.str());
	  convert_stream.str("");
	  d_in.insert(v_db,v_str);
	  simu_ctrl->command_inout("SetAxisHomePosition",d_in);		
	}
    }
  else if (par_name == "MoveHome")
    {
      if(simu_ctrl != NULL)
	{
	  Tango::DeviceData d_in;

	  d_in << (Tango::DevLong)idx;

	  simu_ctrl->command_inout("AxisMoveHome",d_in);		
	}
    }
  else if (par_name == "FlagUseEncoderPosition")
    {
      if(simu_ctrl != NULL)
	{
	  Tango::DeviceData d_in;
	  
	  vector<Tango::DevLong> v_db;
	  
	  if (new_value.data_type == INT32){
	    cout << "[OmsVme58Ctrl] New value FlagUseEncoderPosition extra attribute is " << new_value.int32_data << endl;
	    v_db.push_back((Tango::DevLong)new_value.int32_data);
	    
	  }else
	    bad_data_type(par_name);
	  
	  vector<string> v_str;
	  convert_stream << (Tango::DevLong)idx;
	  v_str.push_back(convert_stream.str());
	  convert_stream.str("");
	  d_in.insert(v_db,v_str);
	  simu_ctrl->command_inout("SetAxisFlagUseEncoderPosition",d_in);		
	}
    }
  else
    {
      TangoSys_OMemStream o;
      o << "Extra attribute " << par_name << " is unknown for controller OmsVme58Ctrl/" << get_name() << ends;
      
      Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",o.str(),
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
	string returned_str("Hasta luego");
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

	Tango::Except::throw_exception((const char *)"SimuCtrl_BadParameter",o.str(),
			       			   	   (const char *)"OmsVme58Ctrl::SetPar()");
}

//
//===============================================================================================
//

const char *Motor_Ctrl_class_name[] = {"OmsVme58Ctrl","Toto","Bidule",NULL};
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


Controller::PropInfo OmsVme58Ctrl_class_prop[] = {{"DevName","The tango device name of the OmsVme58Ctrl","DevString"},
										 {"The prop","The first CPP property","DevLong","12"},
							  			 {"Another_Prop","The second CPP property","DevString","Hola"},
							  			 {"Third_Prop","The third CPP property","DevVarLongArray","11,22,33"},
							  			 NULL};
							  			 
int32_t OmsVme58Ctrl_MaxDevice = 16;

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
