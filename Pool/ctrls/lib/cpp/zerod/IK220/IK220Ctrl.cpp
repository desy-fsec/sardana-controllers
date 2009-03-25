#include <iostream>
#include <IK220Ctrl.h>
#include <pool/PoolAPI.h>

#include <sys/types.h>
#include <sys/time.h>
#include <unistd.h>
#include <stdlib.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		IK220Ctrl::IK220Ctrl
// 
// description : 	Ctor of the IK220Ctrl class
//					It retrieve some properties from Tango DB, build a 
//					connection to the IK220 Tango Device controller and ping it
//					to check if it is alive
//
//-----------------------------------------------------------------------------

IK220Ctrl::IK220Ctrl(const char *inst,vector<Controller::Properties> &prop):ZeroDController(inst)
{

	for (unsigned long loop = 0;loop < prop.size();loop++)
	{
		if( prop[loop].name == "DevName" )
		{
			DevName = prop[loop].value.string_prop[0];
		}
	}
	
//
// Create a DeviceProxy on the ik220 controller and set
// it in automatic reconnection mode
//
	encoder_ctrl = Pool_ns::PoolUtil::instance()->get_device(inst_name, DevName);
	
//
// Ping the device to be sure that it is present
//
	if(encoder_ctrl == NULL)
	{
		TangoSys_OMemStream o;
		o << "The PoolAPI did not provide a valid ik220 device" << ends;
		Tango::Except::throw_exception((const char *)"IK220Ctrl_BadPoolAPI",o.str(),
									   (const char *)"IK220Ctrl::IK220Ctrl()");
	}
	
	try
	{
		encoder_ctrl->ping();
	}
	catch (Tango::DevFailed &e)
	{
		throw;
	}
	
}

//-----------------------------------------------------------------------------
//
// method : 		IK220Ctrl::~IK220Ctrl
// 
// description : 	Dtor of the IK220Ctrl class
//
//-----------------------------------------------------------------------------

IK220Ctrl::~IK220Ctrl()
{
}

//-----------------------------------------------------------------------------
//
// method : 		IK220Ctrl::AddDevice
// 
// description : 	Register a new device for the controller
//					
//
//-----------------------------------------------------------------------------

void IK220Ctrl::AddDevice(int32_t idx)
{
	//cout << "[IK220Ctrl] Creating a new Zero D Exp Channel with index " << idx << " on controller IK220Ctrl/" << inst_name << endl;
}

//-----------------------------------------------------------------------------
//
// method : 		IK220Ctrl::DeleteDevice
// 
// description : 	Unregister a new device for the controller
//					For the simulated controller, this simply means decrement
//					motor count
//
//-----------------------------------------------------------------------------

void IK220Ctrl::DeleteDevice(int32_t idx)
{
	//cout << "[IK220Ctrl] Deleting Counter Timer with index " << idx << " on controller IK220Ctrl/" << inst_name  << endl;
}

//-----------------------------------------------------------------------------
//
// method : 		IK220Ctrl::ReadOne
// 
// description : 	Read a encoder
//
// arg(s) : - idx : The encoder number (starting at 1)
//
// This method returns the encoder position 
//-----------------------------------------------------------------------------

double IK220Ctrl::ReadOne(int32_t idx)
{
//	cout << "[IK220Ctrl] Getting value for exp channel with index " << idx << " on controller IK220Ctrl/" << endl;
	double returned_val;

	if (encoder_ctrl != NULL)
	{
		Tango::DeviceData d_in,d_out;
		
		d_in << (Tango::DevLong)idx;

		d_out = encoder_ctrl->command_inout("GetAxePosition",d_in);
		d_out >> returned_val;
	}
	else
	{
		TangoSys_OMemStream o;
		o << "IK220Ctrl for controller IK220Ctrl/" << get_name() << " is NULL" << ends;
		Tango::Except::throw_exception((const char *)"IK220Ctrl_BadCtrlPtr",o.str(),
									   (const char *)"IK220Ctrl::ReadOne()");
	}
	
	return returned_val;
}


//-----------------------------------------------------------------------------
//
// method : 		IK220Ctrl::GetState
// 
// description : 	Get one Encoder status.
//
// arg(s) : - idx : The encoder number (starting at 1)
//			- ct_info_ptr : Pointer to a struct. which will be filled with
//							Encoder status
//
//-----------------------------------------------------------------------------

void IK220Ctrl::StateOne(int32_t idx, Controller::CtrlState *ct_info_ptr)
{
	//cout << "[IK220Ctrl] Getting state for Exp Channel with index " << idx << " on controller IK220Ctrl/" << inst_name << endl;

	long state_tmp;
	
	if (encoder_ctrl != NULL)
	{
		Tango::DeviceData d_in,d_out;
		d_in << (Tango::DevLong)idx;
		d_out = encoder_ctrl->command_inout("GetAxeStatus",d_in);
		
        d_out >> state_tmp;
		
        ct_info_ptr->state = state_tmp;
        if(state_tmp == Tango::ON){
			ct_info_ptr->status = "Encoder is in ON state";
		} 
	}
	else
        {
			TangoSys_OMemStream o;
                o << "IK220Encoder Controller for controller IK220Ctrl/" << get_name() << " is NULL" << ends;
				
                Tango::Except::throw_exception((const char *)"IK220Ctrl_BadCtrlPtr",o.str(),
											   (const char *)"IK220Ctrl::GetStatus()");
        }
	
}


//-----------------------------------------------------------------------------
//
// method :             IK220Ctrl::GetExtraAttributePar
// 
// description :        Get a encoder extra attribute parameter.
//
// arg(s) : - idx : The encoder number (starting at 1)
//                      - par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------
                               
  
Controller::CtrlData IK220Ctrl::GetExtraAttributePar(int32_t idx, string &par_name)
{
	Controller::CtrlData par_value;	

    double par_tmp_db;
    Tango::DevLong   par_tmp_l;

	if (par_name == "Conversion")
	{
		if (encoder_ctrl != NULL)
		{
			Tango::DeviceData d_in, d_out;
			
			d_in << (Tango::DevLong)idx;
			d_out = encoder_ctrl->command_inout("GetAxeConversion",d_in);
			d_out >> par_tmp_db;
            par_value.db_data = par_tmp_db;
			par_value.data_type = Controller::DOUBLE;
		}	
	}
    else if (par_name == "Offset")
	{

		Tango::DeviceData d_in,d_out;
		
		d_in << (Tango::DevLong)idx;
		d_out = encoder_ctrl->command_inout("GetAxeOffset",d_in);
		d_out >> par_tmp_db;
		par_value.db_data = par_tmp_db;
		par_value.data_type = Controller::DOUBLE;
    }
    else if (par_name == "FlagIgnoreStatus")
	{

		Tango::DeviceData d_in,d_out;
		
		d_in << (Tango::DevLong)idx;
		d_out = encoder_ctrl->command_inout("GetAxeFlagIgnoreStatus",d_in);
		d_out >> par_tmp_l;
		par_value.int32_data = (int32_t)par_tmp_l;
		par_value.data_type = Controller::INT32;
    }
    else if (par_name == "StatusPort")
	{

		Tango::DeviceData d_in,d_out;
		
		d_in << (Tango::DevLong)idx;
		d_out = encoder_ctrl->command_inout("GetAxeStatusPort",d_in);
		d_out >> par_tmp_l;
		par_value.int32_data = (int32_t)par_tmp_l;
		par_value.data_type = Controller::INT32;
    }
    else if ( (par_name == "Calibrate") || (par_name == "CancelReference") || (par_name == "DoReference") || (par_name == "InitEncoder") || (par_name == "SetCorrectionOffOn") )
	{
		TangoSys_OMemStream o;
		o << "Extra attribute " << par_name << " is actually a command. Write to execute it/" << get_name() << ends;
		
		Tango::Except::throw_exception((const char *)"Ctrl_BadCtrlPtr",o.str(),
									   (const char *)"IK220Ctrl::GetExtraAttributePar()");
	}
	else
	{
		TangoSys_OMemStream o;
		o << "Extra attribute " << par_name << " is unknown for controller IK220Ctrl/" << get_name() << ends;
			
		Tango::Except::throw_exception((const char *)"Ctrl_BadCtrlPtr",o.str(),
						       			   (const char *)"IK220Ctrl::GetExtraAttributePar()");
	}
	
	return par_value;
}



//-----------------------------------------------------------------------------
//
// method : 		IK220Ctrl::SetExtraAttributePar
// 
// description : 	Set a encoder extra attribute parameter.
//
// arg(s) : - idx : The encoder number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void IK220Ctrl::SetExtraAttributePar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{
	if (par_name == "Conversion")
	{
		if(encoder_ctrl != NULL)
		{
			Tango::DeviceData d_in;

			vector<double> v_db;
			if (new_value.data_type == DOUBLE){
				cout << "[IK220Ctrl] New value for Conversion extra attribute is " << new_value.db_data << endl;
				v_db.push_back(new_value.db_data);

			}else
				bad_data_type(par_name);
			
			vector<string> v_str;
			convert_stream << (Tango::DevLong)idx;
			v_str.push_back(convert_stream.str());
			convert_stream.str("");
			d_in.insert(v_db,v_str);
            encoder_ctrl->command_inout("SetAxeConversion",d_in);		
		}
	}
	else if (par_name == "Offset")
	{
		if(encoder_ctrl != NULL)
		{
			Tango::DeviceData d_in;

			vector<double> v_db;
			if (new_value.data_type == DOUBLE){
				cout << "[IK220Ctrl] New value for Offset extra attribute is " << new_value.db_data << endl;
				v_db.push_back(new_value.db_data);

			}else
				bad_data_type(par_name);
			
			vector<string> v_str;
			convert_stream << (Tango::DevLong)idx;
			v_str.push_back(convert_stream.str());
			convert_stream.str("");
			d_in.insert(v_db,v_str);
            encoder_ctrl->command_inout("SetAxeOffset",d_in);		
		}
	}
	else if (par_name == "Calibrate")
	{
		if(encoder_ctrl != NULL)
		{
			Tango::DeviceData d_in;

			vector<double> v_db;
			if (new_value.data_type == DOUBLE){
				cout << "[IK220Ctrl] New value for Calibrate extra attribute is " << new_value.db_data << endl;
				v_db.push_back(new_value.db_data);

			}else
				bad_data_type(par_name);
			
			vector<string> v_str;
			convert_stream << (Tango::DevLong)idx;
			v_str.push_back(convert_stream.str());
			convert_stream.str("");
			d_in.insert(v_db,v_str);
            encoder_ctrl->command_inout("AxeCalibrate",d_in);		
		}
	}
	else if (par_name == "FlagIgnoreStatus")
	{
		if(encoder_ctrl != NULL)
		{
			Tango::DeviceData d_in;

			vector<Tango::DevLong> v_db;
			if (new_value.data_type == INT32){
				cout << "[IK220Ctrl] New value for FlagIgnoreStatus extra attribute is " << new_value.db_data << endl;
				v_db.push_back((Tango::DevLong)new_value.int32_data);

			}else
				bad_data_type(par_name);
			
			vector<string> v_str;
			convert_stream << (Tango::DevLong)idx;
			v_str.push_back(convert_stream.str());
			convert_stream.str("");
			d_in.insert(v_db,v_str);
            encoder_ctrl->command_inout("SetAxeFlagIgnoreStatus",d_in);		
		}
	}
	else if (par_name == "StatusPort")
	{
		if(encoder_ctrl != NULL)
		{
			Tango::DeviceData d_in;

			vector<Tango::DevLong> v_db;
			if (new_value.data_type == INT32){
				cout << "[IK220Ctrl] New value for StatusPort extra attribute is " << new_value.db_data << endl;
				v_db.push_back((Tango::DevLong)new_value.int32_data);

			}else
				bad_data_type(par_name);
			
			vector<string> v_str;
			convert_stream << (Tango::DevLong)idx;
			v_str.push_back(convert_stream.str());
			convert_stream.str("");
			d_in.insert(v_db,v_str);
            encoder_ctrl->command_inout("SetAxeStatusPort",d_in);		
		}
	}
	else if (par_name == "CancelReference")
	{
		if(encoder_ctrl != NULL)
		{
			Tango::DeviceData d_in;

			d_in << (Tango::DevLong)idx;
            encoder_ctrl->command_inout("AxeCancelReference",d_in);		
		}
	}
	else if (par_name == "DoReference")
	{
		if(encoder_ctrl != NULL)
		{
			Tango::DeviceData d_in;

			d_in << (Tango::DevLong)idx;
            encoder_ctrl->command_inout("AxeDoReference",d_in);		
		}
	}
	else if (par_name == "InitEncoder")
	{
		if(encoder_ctrl != NULL)
		{
			Tango::DeviceData d_in;

			d_in << (Tango::DevLong)idx;
            encoder_ctrl->command_inout("AxeInitEncoder",d_in);		
		}
	}
	else if (par_name == "SetCorrectionOffOn")
	{
		if(encoder_ctrl != NULL)
		{
			Tango::DeviceData d_in;

			vector<Tango::DevLong> v_db;
			if (new_value.data_type == INT32){
				cout << "[IK220Ctrl] New value for StatusPort extra attribute is " << new_value.db_data << endl;
				v_db.push_back((Tango::DevLong)new_value.int32_data);

			}else
				bad_data_type(par_name);
			
			vector<string> v_str;
			convert_stream << (Tango::DevLong)idx;
			v_str.push_back(convert_stream.str());
			convert_stream.str("");
			d_in.insert(v_db,v_str);
            encoder_ctrl->command_inout("AxeSetCorrectionOffOn",d_in);		
		}
	}
	else
	{
		TangoSys_OMemStream o;
		o << "Extra attribute " << par_name << " is unknown for controller IK220Ctrl/" << get_name() << ends;
			
		Tango::Except::throw_exception((const char *)"IK220Ctrl_BadCtrlPtr",o.str(),
						       			   (const char *)"IK220Ctrl::SetExtraAttributePar()");
	}
}

//-----------------------------------------------------------------------------
//
// method : 		IK220Ctrl::bad_data_type
// 
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void IK220Ctrl::bad_data_type(string &par_name)
{
	TangoSys_OMemStream o;
	o << "A wrong data type has been used to set the parameter " << par_name << ends;

	Tango::Except::throw_exception((const char *)"IK220Ctrl_BadParameter",o.str(),
			       			   	   (const char *)"IK220Ctrl::SetPar()");
}

//
//===============================================================================================
//

const char *ZeroDExpChannel_Ctrl_class_name[] = {"IK220Ctrl",NULL};

const char *IK220Ctrl_doc = "This is the C++ controller for the IK220Ctrl class";


Controller::PropInfo IK220Ctrl_class_prop[] = {{"DevName","The tango device name of the IK220Ctrl","DevString"},
															
															NULL};

Controller::ExtraAttrInfo IK220Ctrl_ctrl_extra_attributes[] = {{"Conversion","DevDouble","Read_Write"},
																			{"Calibrate","DevDouble","Read_Write"},
																			{"Offset","DevDouble","Read_Write"},
																			{"FlagIgnoreStatus","DevLong","Read_Write"},
																			{"StatusPort","DevLong","Read"},
																			{"CancelReference","DevLong","Read_Write"},
																			{"DoReference","DevLong","Read_Write"},
																			{"InitEncoder","DevLong","Read_Write"},
																			{"SetCorrectionOffOn","DevLong","Read_Write"},
																			NULL};


int32_t IK220Ctrl_MaxDevice = 97;

extern "C"
{
	
Controller *_create_IK220Ctrl(const char *inst,vector<Controller::Properties> &prop)
{
	return new IK220Ctrl(inst,prop);
}

}
