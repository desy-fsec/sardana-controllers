#include <CurrentPseudoCoCtrl.h>

Current::Current(const char *inst,vector<Controller::Properties> &prop):
PseudoCounterController(inst)
{
	//cout << "[Current] class ctor" << endl;
}

Current::~Current ( )
{
	//cout << "[Current] class dtor" << endl;
}

double Current::Calc(int32_t idx, vector<double> &counter_values)
{
	return counter_values[0]/counter_values[1];
}

//
//===============================================================================================
//

const char *PseudoCounter_Ctrl_class_name[] = {"Current",NULL};

const char *Current_doc = "This is the C++ pseudo counter controller for a simple I/I0 current";
const char *Current_gender = "PseudoCounter";
const char *Current_model = "Current";
const char *Current_image = "dummy_com.png";
const char *Current_organization = "CELLS - ALBA";
const char *Current_logo = "ALBA_logo.png";

Controller::ExtraAttrInfo Current_ctrl_extra_attributes[] = {{"Aaa","DevLong","Read"},
												 {"Bbb","DevDouble","Read_Write"},
												 {"Ccc","DevString","Read"},
												 NULL};

Controller::PropInfo Current_class_prop[] = {{"DevName","The tango device name of the SimuMotorCtrl","DevString"},
										 {"The prop","The first CPP property","DevLong","12"},
							  			 {"Another_Prop","The second CPP property","DevString","Hola"},
							  			 {"Third_Prop","The third CPP property","DevVarLongArray","11,22,33"},
							  			 NULL};

const char *Current_counter_roles[] = { "I", "I0", NULL };

int32_t Current_MaxDevice = 2; // should be the pseudo counter role #

extern "C"
{

Controller *_create_Current(const char *inst,vector<Controller::Properties> &prop)
{
	return new Current(inst,prop);
}

}
