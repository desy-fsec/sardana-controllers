#include <iostream>
#include <SimuMotorCtrl.h>
#include <pool/PoolAPI.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		SimuMotorController::SimuMotorController
//
// description : 	Ctor of the SimuMotorController class
//					It retrieve some properties from Tango DB, build a
//					connection to the Simulated controller and ping it
//					to check if it is alive
//
//-----------------------------------------------------------------------------

SimuMotorController::SimuMotorController(const char *inst,vector<Controller::Properties> &prop):MotorController(inst)
{
	//cout << "[SimuMotorController] Received " << prop.size() << " properties" << endl;
	for (unsigned long loop = 0;loop < prop.size();loop++)
	{
		if( prop[loop].name == "DevName" )
		{
			DevName = prop[loop].value.string_prop[0];
		}
	}

	simu_ctrl = NULL;
	ctr_11 = 0;
	mot_10_fault = false;
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
    			   (const char *)"SimuMotorController::SimuMotorController()");
	}

	try
	{
		simu_ctrl->ping();
	}
	catch (Tango::DevFailed &e)
	{
		delete simu_ctrl;
		throw;
	}
}

//-----------------------------------------------------------------------------
//
// method : 		SimuMotorController::~SimuMotorController
//
// description : 	Dtor of the SimuMotorController class
//
//-----------------------------------------------------------------------------

SimuMotorController::~SimuMotorController()
{
	//cout << "[SimuMotorController] class dtor" << endl;
	//if (simu_ctrl != NULL)
	//	delete simu_ctrl;
}

//-----------------------------------------------------------------------------
//
// method : 		SimuMotorController::AddDevice
//
// description : 	Register a new device for the controller
//					For the simulated controller, this simply means increment
//					motor count
//
//-----------------------------------------------------------------------------

void SimuMotorController::AddDevice(int32_t idx)
{
	//cout << "[SimuMotorController] Creating a new motor with index " << idx << " on controller SimuMotorController/" << inst_name  << " (" << DevName << ")" << endl;
}

//-----------------------------------------------------------------------------
//
// method : 		SimuMotorController::DeleteDevice
//
// description : 	Unregister a new device for the controller
//					For the simulated controller, this simply means decrement
//					motor count
//
//-----------------------------------------------------------------------------

void SimuMotorController::DeleteDevice(int32_t idx)
{
	//cout << "[SimuMotorController] Deleting motor with index " << idx << " on controller SimuMotorController/" << inst_name  << " (" << DevName << ")" << endl;
}

//-----------------------------------------------------------------------------
//
// method : 		SimuMotorController::AbortOne
//
// description : 	Abort a movement.
//
// arg(s) : - idx : The motor number (starting at 1)
//
//-----------------------------------------------------------------------------

void SimuMotorController::AbortOne(int32_t idx)
{
	//cout << "[SimuMotorController] Aborting one motor with index " << idx << " on controller SimuMotorController/" << inst_name << " (" << DevName << ")" << endl;
	if (simu_ctrl != NULL)
	{
		Tango::DeviceData d_in;
		d_in << (Tango::DevLong)idx;
		simu_ctrl->command_inout("Abort",d_in);
	}
	else
	{
		TangoSys_OMemStream o;
		o << "Simulated controller for controller SimuMotorController/" << get_name() << " is NULL" << ends;

		Tango::Except::throw_exception(
				(const char *)"SimuCtrl_BadCtrlPtr",o.str(),
				(const char *)"SimuMotorController::AbortOne()");
	}
}

//-----------------------------------------------------------------------------
//
// method : 		SimuMotorController::DefinePosition
//
// description : 	Load a new position for one motor in controller
//
// arg(s) : - idx : The motor number (starting at 1)
//			- new_pos : The position to be loaded in controller
//
//-----------------------------------------------------------------------------

void SimuMotorController::DefinePosition(int32_t idx,double new_pos)
{
	//cout << "[SimuMotorController] Defining position for motor with index " << idx << " on controller SimuMotorController/" << inst_name << " (" << DevName << ")" << endl;
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
		o << "Simulated controller for controller SimuMotorController/" << get_name() << " is NULL" << ends;

		Tango::Except::throw_exception(
				(const char *)"SimuCtrl_BadCtrlPtr",o.str(),
				(const char *)"SimuMotorController::DefinePosition()");
	}
}

//-----------------------------------------------------------------------------
//
// method : 		SimuMotorController::ReadPosition
//
// description : 	Read a motor position
//
// arg(s) : - idx : The motor number (starting at 1)
//
// This method returns the motor position
//-----------------------------------------------------------------------------

double SimuMotorController::ReadOne(int32_t idx)
{
	//cout << "[SimuMotorController] Getting position for motor with index " << idx << " on controller SimuMotorController/" << inst_name << " (" << DevName << ")" << endl;
	double received_pos;

	if (simu_ctrl != NULL)
	{
		Tango::DeviceData d_in,d_out;
		if (idx == 12)
		{
				Tango::Except::throw_exception((const char *)"Aaaaaa",
										   (const char *)"Bbbbbb",
										   (const char *)"Cccccc");
		}
		d_in << (Tango::DevLong)idx;

		d_out = simu_ctrl->command_inout("GetAxePosition",d_in);
		d_out >> received_pos;
	}
	else
	{
		TangoSys_OMemStream o;
		o << "Simulated controller for controller SimuMotorController/" << get_name() << " is NULL" << ends;

		Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",o.str(),
					       			   (const char *)"SimuMotorController::ReadOne()");
	}
	return received_pos;
}

//-----------------------------------------------------------------------------
//
// method : 		SimuMotorController::PreStartAll
//
// description : 	Init movement data
//
//-----------------------------------------------------------------------------

void SimuMotorController::PreStartAll()
{
	//cout << "[SimuMotorController] PreStartAll on controller SimuMotorController/" << inst_name << " (" << DevName << ")" << endl;

	wanted_mot_pos.clear();
	wanted_mot.clear();
}

//-----------------------------------------------------------------------------
//
// method : 		SimuMotorController::StartOne
//
// description : 	Ask a motor to move
//
// arg(s) : - idx : The motor number (starting at 1)
//			- new_pos : The wanted motor position
//
//-----------------------------------------------------------------------------

void SimuMotorController::StartOne(int32_t idx,double new_pos)
{
cout << "[SimuMotorController] Starting one motor with index "
     << idx << " on controller SimuMotorController/" << inst_name
     << " (" << DevName << ")"
     << "with position " << new_pos << endl;

	if (simu_ctrl != NULL)
	{
		wanted_mot_pos.push_back(new_pos);
		wanted_mot.push_back(idx);
	}
	else
	{
		TangoSys_OMemStream o;
		o << "Simulated controller for controller SimuMotorController/" << get_name() << " is NULL" << ends;

		Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",o.str(),
					       			   (const char *)"SimuMotorController::StartOne()");
	}
}

//-----------------------------------------------------------------------------
//
// method : 		SimuMotorController::StartAll
//
// description : 	Ask a motor to move
//
// arg(s) : - idx : The motor number (starting at 1)
//			- new_pos : The wanted motor position
//
//-----------------------------------------------------------------------------

void SimuMotorController::StartAll()
{
	//cout << "[SimuMotorController] StartAll() on controller SimuMotorController/" << inst_name << " (" << DevName << ")" << endl;

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

//
// For test purpose
//

			if (wanted_mot[loop] == 9)
			{
				Tango::Except::throw_exception((const char *)"Aaaaaa",
										   (const char *)"Bbbbbb",
										   (const char *)"Cccccc");
			}

			if (wanted_mot[loop] == 10)
			{
				mot_10_fault = true;
			}

			d_in.insert(v_db,v_str);
			simu_ctrl->command_inout("SetAxePosition",d_in);
		}
	}
	else
	{
		TangoSys_OMemStream o;
		o << "Simulated controller for controller SimuMotorController/" << get_name() << " is NULL" << ends;

		Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",o.str(),
					       			   (const char *)"SimuMotorController::StartOne()");
	}
}

//-----------------------------------------------------------------------------
//
// method : 		SimuMotorController::GetState
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

void SimuMotorController::StateOne(int32_t idx,Controller::CtrlState *info_ptr)
{
//cout << "[SimuMotorController] Getting state for motor with index " << idx << " on controller SimuMotorController/" << inst_name << " (" << DevName << ")" << endl;

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

		if ((idx == 10) && (mot_10_fault == true))
		{
			mot_info_ptr->state = Tango::FAULT;
			mot_info_ptr->status = "Testing FAULT state in movement";
		}

		if (idx == 11)
		{
			Tango::Util *tg = Tango::Util::instance();
			int th_id = omni_thread::self()->id();
			int poll_th_id = tg->get_polling_thread_id();
			if (th_id != poll_th_id)
			{
				ctr_11++;
				if (ctr_11 >= 20)
				{
					Tango::Except::throw_exception((const char *)"XXXXXXXX",
											 	  (const char *)"YYYYYYYY",
							       			   	(const char *)"ZZZZZZZZZ");
				}
			}
		}
	}
	else
	{
		TangoSys_OMemStream o;
		o << "Simulated controller for controller SimuMotorController/" << get_name() << " is NULL" << ends;

		Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",o.str(),
					       			   (const char *)"SimuMotorController::GetStatus()");
	}
}

//-----------------------------------------------------------------------------
//
// method : 		SimuMotorController::GetPar
//
// description : 	Get a motor parameter. Actually, 4 parameters are supported.
//					These are Acceleration, Deceleration, Velocity and Base_rate
//
// arg(s) : - idx : The motor number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData SimuMotorController::GetPar(int32_t idx,string &par_name)
{
	//cout << "[SimuMotorController] Getting parameter " << par_name << " for motor with index " << idx << " on controller SimuMotorController/" << inst_name << " (" << DevName << ")" << endl;

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
			o << "Parameter " << par_name << " is unknown for controller SimuMotorController/" << get_name() << ends;

			Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",o.str(),
						       			   (const char *)"SimuMotorController::GetPar()");
		}
	}
	else
	{
		TangoSys_OMemStream o;
		o << "Simulated controller for controller SimuMotorController/" << get_name() << " is NULL" << ends;

		Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",o.str(),
					       			   (const char *)"SimuMotorController::GetPar()");
	}

	return par_value;
}

//-----------------------------------------------------------------------------
//
// method : 		SimuMotorController::SetPar
//
// description : 	Set a motor parameter. Actually, 4 parameters are supported.
//					These are Acceleration, Deceleration, Velocity and Base_rate
//
// arg(s) : - idx : The motor number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void SimuMotorController::SetPar(int32_t idx,string &par_name,Controller::CtrlData &new_value)
{
	//cout << "[SimuMotorController] Setting parameter " << par_name << " for motor with index " << idx << " on controller SimuMotorController/" << inst_name << " (" << DevName << ")" << endl;

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
			cout << "[SimuMotorController] New Step_per_unit feature is " << new_value.db_data << endl;
		}
		else if (par_name == "Backlash")
		{
			if (new_value.data_type == Controller::INT32)
				cout << "[SimuMotorController] New value for backlash is " << new_value.int32_data << endl;
			else
				bad_data_type(par_name);
		}
		else
		{
			TangoSys_OMemStream o;
			o << "Parameter " << par_name << " is unknown for controller SimuMotorController/" << get_name() << ends;

			Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",o.str(),
						       			   (const char *)"SimuMotorController::GetPar()");
		}
	}
	else
	{
		TangoSys_OMemStream o;
		o << "Simulated controller for controller SimuMotorController/" << get_name() << " is NULL" << ends;

		Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",o.str(),
					       			   (const char *)"SimuMotorController::SetPar()");
	}
}

//-----------------------------------------------------------------------------
//
// method : 		SimuMotorController::GetExtraAttributePar
//
// description : 	Get a motor extra attribute parameter.
//
// arg(s) : - idx : The motor number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData SimuMotorController::GetExtraAttributePar(int32_t idx,string &par_name)
{
	Controller::CtrlData par_value;

	if (par_name == "Aaa")
	{
		par_value.int32_data = 1234;
		par_value.data_type = Controller::INT32;
	}
	else if (par_name == "Bbb")
	{
		par_value.db_data = 7.8899;
		par_value.data_type = Controller::DOUBLE;
	}
	else if (par_name == "Ccc")
	{
		par_value.str_data = "Ccc value";
		par_value.data_type = Controller::STRING;
	}
	else
	{
		TangoSys_OMemStream o;
		o << "Extra attribute " << par_name << " is unknown for controller SimuMotorController/" << get_name() << ends;

		Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",o.str(),
						       			   (const char *)"SimuMotorController::GetExtraAttributePar()");
	}

	return par_value;
}

//-----------------------------------------------------------------------------
//
// method : 		SimuMotorController::SetExtraAttributePar
//
// description : 	Set a motor extra attribute parameter.
//
// arg(s) : - idx : The motor number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void SimuMotorController::SetExtraAttributePar(int32_t idx,string &par_name,Controller::CtrlData &new_value)
{
	if (par_name == "Aaa")
	{
		if (new_value.data_type == INT32)
			cout << "[SimuMotorController] New value for Aaa extra attribute is " << new_value.int32_data << endl;
		else
			bad_data_type(par_name);
	}
	else if (par_name == "Bbb")
	{
		if (new_value.data_type == DOUBLE)
			cout << "[SimuMotorController] New value for Bbb extra attribute is " << new_value.db_data << endl;
		else
			bad_data_type(par_name);
	}
	else if (par_name == "Ccc")
	{
		if (new_value.data_type == STRING)
			cout << "[SimuMotorController] New value for Ccc extra attribute is " << new_value.str_data << endl;
		else
			bad_data_type(par_name);
	}
	else
	{
		TangoSys_OMemStream o;
		o << "Extra attribute " << par_name << " is unknown for controller SimuMotorController/" << get_name() << ends;

		Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",o.str(),
						       			   (const char *)"SimuMotorController::SetExtraAttributePar()");
	}
}


//-----------------------------------------------------------------------------
//
// method : 		SimuMotorController::send_to_ctrl
//
// description : 	Send a string to the controller
//
// arg(s) : - idx : The motor number (starting at 1)
//			- featr_name : The feature name
//			- new_value : The feature value
//
//-----------------------------------------------------------------------------

string SimuMotorController::SendToCtrl(string &in_str)
{
	//cout << "[SimuMotorController] I have received the string: " << in_str << endl;
	string returned_str("Hasta luego");
	return returned_str;
}

//-----------------------------------------------------------------------------
//
// method : 		SimuMotorController::bad_data_type
//
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void SimuMotorController::bad_data_type(string &par_name)
{
	TangoSys_OMemStream o;
	o << "A wrong data type has been used to set the parameter " << par_name << ends;

	Tango::Except::throw_exception((const char *)"SimuCtrl_BadParameter",o.str(),
			       			   	   (const char *)"SimuMotorController::SetPar()");
}

//
//===============================================================================================
//

const char *Motor_Ctrl_class_name[] = {"SimuMotorController","Toto","Bidule",NULL};
const char *SimuMotorController_doc = "This is the C++ controller for the SimuMotorController class";
const char *SimuMotorController_gender = "Simulation";
const char *SimuMotorController_model = "Simulation";
const char *SimuMotorController_image = "motor_simulator.png";
const char *SimuMotorController_icon = "motor_simulator_icon.png";
const char *SimuMotorController_organization = "CELLS - ALBA";
const char *SimuMotorController_logo = "ALBA_logo.png";

Controller::ExtraAttrInfo SimuMotorController_ctrl_extra_attributes[] = {{"Aaa","DevLong","Read"},
												 {"Bbb","DevDouble","Read_Write"},
												 {"Ccc","DevString","Read"},
												 NULL};
//char *SimuMotorController_ctrl_features[] = {"Backlash","Rounding","Encoder","Home_acceleration",NULL};
const char *SimuMotorController_ctrl_features[] = {"WantRounding","Encoder","Home_acceleration",NULL};

Controller::PropInfo SimuMotorController_class_prop[] = {{"DevName","The tango device name of the SimuMotorCtrl","DevString"},
										 {"The prop","The first CPP property","DevLong","12"},
							  			 {"Another_Prop","The second CPP property","DevString","Hola"},
							  			 {"Third_Prop","The third CPP property","DevVarLongArray","11,22,33"},
							  			 NULL};

int32_t SimuMotorController_MaxDevice = 1024;


extern "C"
{

Controller *_create_SimuMotorController(const char *inst,vector<Controller::Properties> &prop)
{
	return new SimuMotorController(inst,prop);
}

}
