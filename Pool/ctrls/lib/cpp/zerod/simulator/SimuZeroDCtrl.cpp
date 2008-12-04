#include <iostream>
#include <SimuZeroDCtrl.h>

#include <sys/types.h>
#include <sys/time.h>
#include <unistd.h>
#include <stdlib.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		SimuZeroDController::SimuZeroDController
// 
// description : 	Ctor of the SimuZeroDController class
//					It retrieve some properties from Tango DB, build a 
//					connection to the Simulated controller and ping it
//					to check if it is alive
//
//-----------------------------------------------------------------------------

SimuZeroDController::SimuZeroDController(const char *inst,vector<Controller::Properties> &prop):ZeroDController(inst)
{
	/*
	cout << "Received " << prop.size() << " properties" << endl;
	for (unsigned long loop = 0;loop < prop.size();loop++)
	{
		cout << "\tProperty name = " << prop[loop].name << endl;
		if (prop[loop].value.bool_prop.size() != 0)
		{
			for (unsigned ll = 0;ll < prop[loop].value.bool_prop.size();ll++)
				cout << "\t\tProp value = " << prop[loop].value.bool_prop[ll] << endl;
		}
		else if (prop[loop].value.long_prop.size() != 0)
		{
			for (unsigned ll = 0;ll < prop[loop].value.long_prop.size();ll++)
				cout << "\t\tProp value = " << prop[loop].value.long_prop[ll] << endl;
		}
		else if (prop[loop].value.double_prop.size() != 0)
		{
			for (unsigned ll = 0;ll < prop[loop].value.double_prop.size();ll++)
				cout << "\t\tProp value = " << prop[loop].value.double_prop[ll] << endl;
		}
		else
		{
			for (unsigned ll = 0;ll < prop[loop].value.string_prop.size();ll++)
				cout << "\t\tProp value = " << prop[loop].value.string_prop[ll] << endl;
		}
	}
	*/
			
	simu_ctrl = NULL;
	
}

//-----------------------------------------------------------------------------
//
// method : 		SimuZeroDController::~SimuZeroDController
// 
// description : 	Dtor of the SimuController class
//
//-----------------------------------------------------------------------------

SimuZeroDController::~SimuZeroDController()
{
	//cout << "[SimuZeroDController] class dtor" << endl;
	if (simu_ctrl != NULL)
		delete simu_ctrl;
}

//-----------------------------------------------------------------------------
//
// method : 		SimuZeroDController::AddDevice
// 
// description : 	Register a new device for the controller
//					For the simulated controller, this simply means increment
//					motor count
//
//-----------------------------------------------------------------------------

void SimuZeroDController::AddDevice(int32_t idx)
{
	//cout << "[SimuZeroDController] Creating a new Zero D Exp Channel with index " << idx << " on controller SimuZeroDController/" << inst_name << endl;
}

//-----------------------------------------------------------------------------
//
// method : 		SimuZeroDController::DeleteDevice
// 
// description : 	Unregister a new device for the controller
//					For the simulated controller, this simply means decrement
//					motor count
//
//-----------------------------------------------------------------------------

void SimuZeroDController::DeleteDevice(int32_t idx)
{
	//cout << "[SimuZeroDController] Deleting Counter Timer with index " << idx << " on controller SimuZeroDController/" << inst_name  << endl;
}

//-----------------------------------------------------------------------------
//
// method : 		SimuController::ReadOne
// 
// description : 	Read a counter timer
//
// arg(s) : - idx : The counter timer number (starting at 1)
//
// This method returns the counter timer value
//-----------------------------------------------------------------------------

double SimuZeroDController::ReadOne(int32_t idx)
{
	//cout << "[SimuZeroDController] Getting value for exp channel with index " << idx << " on controller SimuZeroDController/" << endl;
	double returned_val;
	static int32_t ctr = 0;

	struct timeval now;
	gettimeofday(&now,NULL);
	srand(time(&now.tv_usec));
	
	double added_rand = (double)rand() / (double)RAND_MAX;	
	returned_val = 10.0 + added_rand;
	
//
// Sleep for 100 mS to simulate a GPIB device
//

	struct timespec req_sleep;
	req_sleep.tv_sec = 0;
	req_sleep.tv_nsec = 100000000;
	
	nanosleep(&req_sleep,NULL);
	
	if (idx == 1)
	{
		ctr++;
		if (ctr == 4)
		{
			ctr = 0;
			
			Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",
										   (const char *)"Simulated exception",
						       			   (const char *)"SimuZeroDController::ReadOne()");
		}
	}

	return returned_val;
}


//-----------------------------------------------------------------------------
//
// method : 		SimuZeroDController::GetState
// 
// description : 	Get one motor status. Motor status means two things :
//					1 - The motor state (Tango sense)
//
// arg(s) : - idx : The motor number (starting at 1)
//			- mot_info_ptr : Pointer to a struct. which willbe filled with
//							 motor status
//
//-----------------------------------------------------------------------------

void SimuZeroDController::StateOne(int32_t idx, Controller::CtrlState *mot_info_ptr)
{
	//cout << "[SimuZeroDController] Getting state for Exp Channel with index " << idx << " on controller SimuController/" << inst_name << endl;

	mot_info_ptr->state = Tango::ON;
	mot_info_ptr->status = "Testing FAULT state in movement";

}


//-----------------------------------------------------------------------------
//
// method : 		SimuZeroDController::GetExtraAttributePar
// 
// description : 	Get a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData SimuZeroDController::GetExtraAttributePar(int32_t idx, string &par_name)
{
	Controller::CtrlData par_value;	

	if (par_name == "CppZeroD_extra_1")
	{
		par_value.int32_data = 1234;
		par_value.data_type = Controller::INT32;	
	}
	else if (par_name == "CppZeroD_extra_2")
	{
		par_value.db_data = 7.8899;
		par_value.data_type = Controller::DOUBLE;	
	}
	else
	{
		TangoSys_OMemStream o;
		o << "Extra attribute " << par_name << " is unknown for controller SimuController/" << get_name() << ends;
			
		Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",o.str(),
						       			   (const char *)"SimuController::GetExtraAttributePar()");
	}
	
	return par_value;
}

//-----------------------------------------------------------------------------
//
// method : 		SimuZeroDController::SetExtraAttributePar
// 
// description : 	Set a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void SimuZeroDController::SetExtraAttributePar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{
	if (par_name == "CppZeroD_extra_1")
	{
		if (new_value.data_type == INT32)
			cout << "New value for CppZeroD_extra_1 extra attribute is " << new_value.int32_data << endl;
		else
			bad_data_type(par_name);		
	}
	else if (par_name == "CppZeroD_extra_2")
	{
		if (new_value.data_type == DOUBLE)
			cout << "New value for CppZeroD_extra_2 extra attribute is " << new_value.db_data << endl;
		else
			bad_data_type(par_name);
	}
	else
	{
		TangoSys_OMemStream o;
		o << "Extra attribute " << par_name << " is unknown for controller SimuController/" << get_name() << ends;
			
		Tango::Except::throw_exception((const char *)"SimuCtrl_BadCtrlPtr",o.str(),
						       			   (const char *)"SimuController::SetExtraAttributePar()");
	}
}


//-----------------------------------------------------------------------------
//
// method : 		SimuZeroDController::send_to_ctrl
// 
// description : 	Send a string to the controller
//
// arg(s) : - in_str : the string to send to the ctrl
//
//-----------------------------------------------------------------------------

string SimuZeroDController::SendToCtrl(string &in_str)
{
	//cout << "[SimuZeroDController] I have received the string: " << in_str << endl;
	string returned_str("Hasta luego");
	return returned_str;	
}

//-----------------------------------------------------------------------------
//
// method : 		SimuZeroDController::bad_data_type
// 
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void SimuZeroDController::bad_data_type(string &par_name)
{
	TangoSys_OMemStream o;
	o << "A wrong data type has been used to set the parameter " << par_name << ends;

	Tango::Except::throw_exception((const char *)"SimuZeroDCtrl_BadParameter",o.str(),
			       			   	   (const char *)"SimuZeroDController::SetPar()");
}

//
//===============================================================================================
//

const char *ZeroDExpChannel_Ctrl_class_name[] = {"SimuZeroDController","Glop","Chose",NULL};
const char *SimuZeroDController_doc = "This is the C++ controller for the SimuZeroDController class";

Controller::ExtraAttrInfo SimuZeroDController_ctrl_extra_attributes[] = {{"CppZeroD_extra_1","DevLong","Read"},
												 {"CppZeroD_extra_2","DevDouble","Read_Write"},
												 NULL};

Controller::PropInfo SimuZeroDController_class_prop[] = {{"The prop","The first CPP property","DevLong","12"},
							  			 {"Another_Prop","The second CPP property","DevString","Hola"},
							  			 {"Third_Prop","The third CPP property","DevVarLongArray","11,22,33"},
							  			 NULL};

int32_t SimuZeroDController_MaxDevice = 2;

extern "C"
{
	
Controller *_create_SimuZeroDController(const char *inst,vector<Controller::Properties> &prop)
{
	return new SimuZeroDController(inst,prop);
}

}
