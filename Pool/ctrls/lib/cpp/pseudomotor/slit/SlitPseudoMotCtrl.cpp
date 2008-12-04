#include <SlitPseudoMotCtrl.h>

Slit::Slit(const char *inst,vector<Controller::Properties> &prop):
PseudoMotorController(inst) 
{
	//cout << "[Slit] class ctor" << endl;
}

Slit::~Slit ( ) 
{ 
	//cout << "[Slit] class dtor" << endl;
}

double Slit::CalcPhysical(int32_t axis, vector<double> &pseudo_pos)
{
	double half_gap = pseudo_pos[0]/2.0;
	if(axis == 1)
		return pseudo_pos[1] - half_gap;
	else
		return pseudo_pos[1] + half_gap;
}

double Slit::CalcPseudo(int32_t axis, vector<double> &physical_pos)
{
	if(axis == 1)
		return physical_pos[1] - physical_pos[0];
	else
		return (physical_pos[0] + physical_pos[1])/2.0;
}

//
//===============================================================================================
//

const char *PseudoMotor_Ctrl_class_name[] = {"Slit",NULL};

const char *Slit_doc = "This is the C++ pseudo motor controller for a slit system";
const char *Slit_gender = "PseudoMotor";
const char *Slit_model = "Slit";
const char *Slit_image = "dummy_com.png";
const char *Slit_organization = "CELLS - ALBA";
const char *Slit_logo = "ALBA_logo.png";

Controller::ExtraAttrInfo Slit_ctrl_extra_attributes[] = {{"Aaa","DevLong","Read"},
												 {"Bbb","DevDouble","Read_Write"},
												 {"Ccc","DevString","Read"},
												 NULL};

Controller::PropInfo Slit_class_prop[] = {{"The prop","The first CPP property","DevLong","12"},
							  			 {"Another_Prop","The second CPP property","DevString","Hola"},
							  			 {"Third_Prop","The third CPP property","DevVarLongArray","11,22,33"},
							  			 NULL};

const char *Slit_pseudo_motor_roles[] = { "Gap", "Offset", NULL };
const char *Slit_motor_roles[] = { "sl2t", "sl2b", NULL };

int32_t Slit_MaxDevice = 2; // should be the pseudo motor role #

extern "C"
{
	
Controller *_create_Slit(const char *inst,vector<Controller::Properties> &prop)
{
	return new Slit(inst,prop);
}

}
