#include <iostream>
#include <SIS3610Ctrl.h>
#include <pool/PoolAPI.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		SIS3610::SIS3610
// 
// description : 	Ctor of the SIS3610 class
//					It retrieve some properties from Tango DB, build a 
//					connection to the Simulated controller and ping it
//					to check if it is alive
//
//-----------------------------------------------------------------------------

SIS3610::SIS3610(const char *inst, vector<Controller::Properties> &prop):
IORegisterController(inst)
{
	read_nb = 0;
	write_nb = 0;
	
	vector<Controller::Properties>::iterator prop_it;
    for (prop_it = prop.begin(); prop_it != prop.end(); ++prop_it)
    {
        if (prop_it->name == "DevName")
        {
            DevName = prop_it->value.string_prop[0];
        }
    }
	
	//
	// Create a DeviceProxy on the sis3610 controller and set
	// it in automatic reconnection mode
	//
	sis3610_ctrl = Pool_ns::PoolUtil::instance()->get_device(inst_name, DevName);
	
	//
	// Ping the device to be sure that it is present
	//
	if(sis3610_ctrl == NULL)
    {
		TangoSys_OMemStream o;
		o << "The PoolAPI did not provide a valid sis3610 device" << ends;
		Tango::Except::throw_exception((const char *)"SIS3610Ctrl_BadPoolAPI",o.str(),
									   (const char *)"SIS3610::SIS3610()");
    }
	
	try
    {
		sis3610_ctrl->ping();
    }
	catch (Tango::DevFailed &e)
    {
		delete sis3610_ctrl;
		throw;
    }
	
}

//-----------------------------------------------------------------------------
//
// method : 		SIS3610::~SIS3610
// 
// description : 	Dtor of the SIS3610 Controller class
//
//-----------------------------------------------------------------------------

SIS3610::~SIS3610()
{
	//cout << "[SIS3610] class dtor" << endl;
	if(sis3610_ctrl != NULL)
		delete sis3610_ctrl;
}

//-----------------------------------------------------------------------------
//
// method : 		SIS3610::AddDevice
// 
// description : 	Register a new device for the controller
//					For the simulated controller, this simply means increment
//					motor count
//
//-----------------------------------------------------------------------------

void SIS3610::AddDevice(int32_t idx)
{
	//cout << "[SIS3610] Creating a new IORegister with index " << idx << " on controller SIS3610/" << inst_name << endl;
}

//-----------------------------------------------------------------------------
//
// method : 		SIS3610::DeleteDevice
// 
// description : 	Unregister a new device for the controller
//					For the simulated controller, this simply means decrement
//					motor count
//
//-----------------------------------------------------------------------------

void SIS3610::DeleteDevice(int32_t idx)
{
	//cout << "[SIS3610] Deleting IORegister with index " << idx << " on controller SIS3610/" << inst_name << endl;
}

int32_t SIS3610::ReadOne(int32_t idx)
{
	Tango::DevLong read_value;

    read_nb++;

	if (sis3610_ctrl != NULL)
    {
		Tango::DeviceData d_in, d_out;
		
		d_in << (Tango::DevLong)idx;
		
		d_out = sis3610_ctrl->command_inout("GetAxisValue",d_in);
		d_out >> read_value;
    }
	else
    {
      TangoSys_OMemStream o;
	  o << "SIS3610Controller for controller SIS3610Ctrl/" << get_name() << " is NULL" << ends;
	  
      Tango::Except::throw_exception((const char *)"SIS3610Ctrl_BadCtrlPtr",o.str(),
                                     (const char *)"SIS3610::ReadOne()");
    }
	
	
	return (int32_t)read_value;
}



void SIS3610::WriteOne(int32_t idx, int32_t write_value)
{	
	write_nb++;
	
	if (sis3610_ctrl != NULL)
    {
		Tango::DeviceData d_in;
		vector<Tango::DevLong> v_l;
        vector<string> v_str;

        convert_stream << (Tango::DevLong)idx;
		v_l.push_back(write_value);
		v_str.push_back(convert_stream.str());
		convert_stream.str("");

        d_in.insert(v_l, v_str);
        sis3610_ctrl->command_inout("SetAxisValue",d_in);

	} else{
		TangoSys_OMemStream o;
		o << "SIS3610Controller for controller SIS3610Ctrl/" << get_name() << " is NULL" << ends;
		
		Tango::Except::throw_exception((const char *)"SIS3610Ctrl_BadCtrlPtr",o.str(),
									   (const char *)"SIS3610::WriteOne()");		
	} 


}



//-----------------------------------------------------------------------------
//
// method : 		SIS3610::GetState
// 
// description : 	Get one motor status. Motor status means two things :
//					1 - The motor state (Tango sense)
//
// arg(s) : - idx : The motor number (starting at 1)
//			- mot_info_ptr : Pointer to a struct. which willbe filled with
//							 motor status
//
//-----------------------------------------------------------------------------

void SIS3610::StateOne(int32_t idx, Controller::CtrlState *ior_info_ptr)
{
	Tango::DevLong state_tmp;
	
	if (sis3610_ctrl != NULL)
    {
		Tango::DeviceData d_in,d_out;
		d_in << (Tango::DevLong)idx;
		d_out = sis3610_ctrl->command_inout("GetAxisStatus",d_in);
		
		d_out >> state_tmp;
		
		ior_info_ptr->state = state_tmp;
		if(state_tmp == Tango::ON){
			ior_info_ptr->status = "IORegister is in ON state";
		} else if (state_tmp == Tango::FAULT){
			ior_info_ptr->status = "IORegister is in FAULT state";
		}
		
    }
	else
    {
		TangoSys_OMemStream o;
		o << "SIS3610 Controller for controller SIS3610Ctrl/" << get_name() << " is NULL" << ends;
		
		Tango::Except::throw_exception((const char *)"SIS3610Ctrl_BadCtrlPtr",o.str(),
									   (const char *)"SIS3610::GetStatus()");
    }
	
}


//-----------------------------------------------------------------------------
//
// method : 		SIS3610::GetExtraAttributePar
// 
// description : 	Get a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData SIS3610::GetExtraAttributePar(int32_t idx,string &par_name)
{
	Controller::CtrlData par_value;	
//	if (par_name == "CppComCh_extra_1")
//	{
//		par_value.lo_data = 12345;
//		par_value.data_type = Controller::LONG;		
//	}
//	else if (par_name == "CppComCh_extra_2")
//	{
//		par_value.db_data = CppComCh_extra_2;
//		par_value.data_type = Controller::DOUBLE;		
//	} 
//	else
//	{
//		TangoSys_OMemStream o;
//		o << "Parameter " << par_name << " is unknown for controller SIS3610/" << get_name() << ends//;
//		
//		Tango::Except::throw_exception((const char *)"SIS3610_BadCtrlPtr",o.str(),
//					       			   (const char *)"SIS3610::GetPar()");
//	}
	
	return par_value;
}

//-----------------------------------------------------------------------------
//
// method : 		SIS3610::SetExtraAttributePar
// 
// description : 	Set a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void SIS3610::SetExtraAttributePar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{
//	if (par_name == "CppComCh_extra_2")
//	{
////		CppComCh_extra_2 = new_value.db_data;
//	}
	//	else
//	{
//		TangoSys_OMemStream o;
//		o << "Parameter " << par_name << " is unknown for controller SIS3610/" << get_name() << ends;
//		
//		Tango::Except::throw_exception((const char *)"SIS3610_BadCtrlPtr",o.str(),
//					       			   (const char *)"SIS3610::GetPar()");
//	}
}


//-----------------------------------------------------------------------------
//
// method : 		SIS3610::send_to_ctrl
// 
// description : 	Send a string to the controller
//
// arg(s) : - in_str : the string to send to the ctrl
//
//-----------------------------------------------------------------------------

string SIS3610::SendToCtrl(string &in_str)
{
	cout << "[SIS3610] I have received the string: " << in_str << endl;
	string returned_str("Hasta luego");
	return returned_str;	
}

//-----------------------------------------------------------------------------
//
// method : 		SIS3610::bad_data_type
// 
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void SIS3610::bad_data_type(string &par_name)
{
	TangoSys_OMemStream o;
	o << "A wrong data type has been used to set the parameter " << par_name << ends;

	Tango::Except::throw_exception((const char *)"SIS3610Ctrl_BadParameter",o.str(),
			       			   	   (const char *)"SIS3610::SetPar()");
}

//
//===============================================================================================
//

const char *IORegister_Ctrl_class_name[] = {"SIS3610",NULL};

const char *SIS3610_doc = "This is the C++ controller for the SIS3610 class";
const char *SIS3610_gender = "SIS3610";
const char *SIS3610_model = "SIS3610";
const char *SIS3610_image = "fake_com.png";
const char *SIS3610_organization = "DESY";
const char *SIS3610_logo = "ALBA_logo.png";


Controller::PropInfo SIS3610_class_prop[] = {{"DevName","The tango device name of the SIS3610Ctrl","DevString"},
							  			 NULL};
							  			 
int32_t SIS3610_MaxDevice = 97;

extern "C"
{
	
Controller *_create_SIS3610(const char *inst,vector<Controller::Properties> &prop)
{
	return new SIS3610(inst,prop);
}

}
