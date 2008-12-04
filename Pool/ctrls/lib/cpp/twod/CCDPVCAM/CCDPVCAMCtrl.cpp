#include <iostream>
#include <CCDPVCAMCtrl.h>
#include <pool/PoolAPI.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		CCDPVCAM::CCDPVCAM
// 
// description : 	Ctor of the CCDPVCAM class
//					It retrieve some properties from Tango DB, build a 
//					connection to the Simulated controller and ping it
//					to check if it is alive
//
//-----------------------------------------------------------------------------

CCDPVCAM::CCDPVCAM(const char *inst,vector<Controller::Properties> &prop):
TwoDController(inst)
{
	read_nb = 0;
	write_nb = 0;
	
    for (unsigned long loop = 0;loop < prop.size();loop++)
    {
		if( prop[loop].name == "DevName" )
        {
			DevName = prop[loop].value.string_prop[0];
        }
    }
	
	//
	// Create a DeviceProxy on the ccdpvcam controller and set
	// it in automatic reconnection mode
	//
	ccdpvcam_ctrl = Pool_ns::PoolUtil::instance()->get_device(inst_name, DevName);
	//
	// Ping the device to be sure that it is present
	//
	if(ccdpvcam_ctrl == NULL)
    {
		TangoSys_OMemStream o;
		o << "The PoolAPI did not provide a valid ccdpvcam device" << ends;
		Tango::Except::throw_exception((const char *)"CCDPVCAMCtrl_BadPoolAPI",o.str(),
									   (const char *)"CCDPVCAM::CCDPVCAM()");
    }
	
	try
    {
		ccdpvcam_ctrl->ping();
    }
	catch (Tango::DevFailed &e)
    {
		delete ccdpvcam_ctrl;
		throw;
    }
	
}

//-----------------------------------------------------------------------------
//
// method : 		CCDPVCAM::~CCDPVCAM
// 
// description : 	Dtor of the CCDPVCAM Controller class
//
//-----------------------------------------------------------------------------

CCDPVCAM::~CCDPVCAM()
{
	//cout << "[CCDPVCAM] class dtor" << endl;
	if(ccdpvcam_ctrl != NULL)
		delete ccdpvcam_ctrl;
}

//-----------------------------------------------------------------------------
//
// method : 		CCDPVCAM::AddDevice
// 
// description : 	Register a new device for the controller
//					For the simulated controller, this simply means increment
//					motor count
//
//-----------------------------------------------------------------------------

void CCDPVCAM::AddDevice(int32_t idx)
{
	//cout << "[CCDPVCAM] Creating a new TwoD with index " << idx << " on controller CCDPVCAM/" << inst_name << endl;
}

//-----------------------------------------------------------------------------
//
// method : 		CCDPVCAM::DeleteDevice
// 
// description : 	Unregister a new device for the controller
//					For the simulated controller, this simply means decrement
//					motor count
//
//-----------------------------------------------------------------------------

void CCDPVCAM::DeleteDevice(int32_t idx)
{
	//cout << "[CCDPVCAM] Deleting TwoD with index " << idx << " on controller CCDPVCAM/" << inst_name << endl;
}

void CCDPVCAM::PreReadOne(int32_t idx)
{


}

double *CCDPVCAM::ReadOne(int32_t idx)
{
    double *read_value;
    vector<Tango::DevUShort> vector_data;

    read_nb++;
	
	if (ccdpvcam_ctrl != NULL)
    {
		Tango::DeviceData d_out, d_in;
		d_in << (Tango::DevLong)idx;
		d_out = ccdpvcam_ctrl->command_inout("GetAxisImage",d_in);
        d_out >> vector_data;
		read_value =  new double[vector_data.size()];
        for(int i = 0; i < vector_data.size(); i++)
			read_value[i] = (double)vector_data[i];  
  
	}
	else
    { 
		TangoSys_OMemStream o;
		o << "CCDPVCAM Controller for controller CCDPVCAMCtrl/" << get_name() << " is NULL" << ends;	
		Tango::Except::throw_exception((const char *)"CCDPVCAMCtrl_BadCtrlPtr",o.str(),
									   (const char *)"CCDPVCAM::ReadOne()");
    }

	 return read_value;
    
}

void  CCDPVCAM::StartOne(int32_t idx)
{

	if (ccdpvcam_ctrl != NULL)
    {
		Tango::DeviceData d_in;
		d_in << (Tango::DevLong)idx;
		ccdpvcam_ctrl->command_inout("StartAxis",d_in);
    }
	else
    {
		TangoSys_OMemStream o;
		o << "CCDPVCAM Controller for controller CCDPVCAMCtrl/" << get_name() << " is NULL" << ends;	
		Tango::Except::throw_exception((const char *)"CCDPVCAMCtrl_BadCtrlPtr",o.str(),
									   (const char *)"CCDPVCAM::StartOne()");
    }


}

void  CCDPVCAM::AbortOne(int32_t idx)
{

	if (ccdpvcam_ctrl != NULL)
    {
		Tango::DeviceData d_in;
		d_in << (Tango::DevLong)idx;
		ccdpvcam_ctrl->command_inout("StopAxis",d_in);
    }
	else
    {
		TangoSys_OMemStream o;
		o << "CCDPVCAM Controller for controller CCDPVCAMCtrl/" << get_name() << " is NULL" << ends;	
		Tango::Except::throw_exception((const char *)"CCDPVCAMCtrl_BadCtrlPtr",o.str(),
									   (const char *)"CCDPVCAM::AbortOne()");
    }
	
}

//-----------------------------------------------------------------------------
//
// method : 		CCDPVCAM::GetState
// 
// description : 	Get one motor status. Motor status means two things :
//					1 - The motor state (Tango sense)
//
// arg(s) : - idx : The motor number (starting at 1)
//			- mot_info_ptr : Pointer to a struct. which will be filled with
//							 motor status
//
//-----------------------------------------------------------------------------

void CCDPVCAM::StateOne(int32_t idx,Controller::CtrlState *ior_info_ptr)
{
	long state_tmp;


	if (ccdpvcam_ctrl != NULL)
    {
		Tango::DeviceData d_in,d_out;
		d_in << (Tango::DevLong)idx;
		d_out = ccdpvcam_ctrl->command_inout("GetAxisStatus",d_in);
		
		d_out >> state_tmp;
		
		ior_info_ptr->state = state_tmp;
		if(state_tmp == Tango::ON){
			ior_info_ptr->status = "TwoD is in ON state";
		} else if (state_tmp == Tango::FAULT){
			ior_info_ptr->status = "TwoD is in FAULT state";
		}
		
    }
	else
    {
		TangoSys_OMemStream o;
		o << "CCDPVCAM Controller for controller CCDPVCAMCtrl/" << get_name() << " is NULL" << ends;
		
		Tango::Except::throw_exception((const char *)"CCDPVCAMCtrl_BadCtrlPtr",o.str(),
									   (const char *)"CCDPVCAM::GetStatus()");
    }
	
}

//-----------------------------------------------------------------------------
//
// method : 		CCDPVCAM::GetPar
// 
// description : 	Get a twod exp channel parameter. Actually, 2 parameters are supported.
//					This is DataLength
//
// arg(s) : - idx : The twod exp channel  number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData CCDPVCAM::GetPar(int32_t idx,string &par_name)
{
	//cout << "[CCDPVCAM] Getting parameter " << par_name << " for twod exp channel with index " << idx << " on controller CCDPVCAM/" << inst_name << " (" << DevName << ")" << endl;
	Controller::CtrlData par_value;	
    Tango::DevLong tmp_v;
    
	if (ccdpvcam_ctrl != NULL)
	{
		Tango::DeviceData d_in,d_out;

		d_in << (Tango::DevLong)idx;	
		if (par_name == "XDim")
		{
			d_out = ccdpvcam_ctrl->command_inout("GetAxisXDim",d_in);
			d_out >> tmp_v;
            par_value.int32_data = (int32_t)tmp_v;
			par_value.data_type = Controller::INT32;		
		}
		else if (par_name == "YDim")
		{
			d_out = ccdpvcam_ctrl->command_inout("GetAxisYDim",d_in);
			d_out >> tmp_v;
            par_value.int32_data = (int32_t)tmp_v;
			par_value.data_type = Controller::INT32;		
		}
        else if (par_name == "IFormat")
		{
			d_out = ccdpvcam_ctrl->command_inout("GetAxisIFormat",d_in);
			d_out >> tmp_v;
            par_value.int32_data = (int32_t)tmp_v;
			par_value.data_type = Controller::INT32;	           
		}  
		else
		{
			TangoSys_OMemStream o;
			o << "Parameter " << par_name << " is unknown for controller CCDPVCAM/" << get_name() << ends;
			
			Tango::Except::throw_exception((const char *)"CCDPVCAM_BadCtrlPtr",o.str(),
						       			   (const char *)"CCDPVCAM::GetPar()");
		}
	}
	else
	{
		TangoSys_OMemStream o;
		o << "Simulated controller for controller CCDPVCAM/" << get_name() << " is NULL" << ends;
		
		Tango::Except::throw_exception((const char *)"CCDPVCAM_BadCtrlPtr",o.str(),
					       			   (const char *)"CCDPVCAM::GetPar()");
	}
	
	return par_value;
}

//-----------------------------------------------------------------------------
//
// method : 		CCDPVCAM::SetPar
// 
// description : 	Set a twod parameter. Actually, 2 parameters are supported.
//					This is DataLength
//
// arg(s) : - idx : The twod exp channel number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void CCDPVCAM::SetPar(int32_t idx,string &par_name,Controller::CtrlData &new_value)
{
	//cout << "[CCDPVCAMController] Setting parameter " << par_name << " for twod channel with index " << idx << " on controller CCDPVCAMController/" << inst_name << " (" << DevName << ")" << endl;

	if (ccdpvcam_ctrl != NULL)
	{
		Tango::DeviceData d_in;

		vector<Tango::DevLong> v_dl;
	   
		if (new_value.data_type == Controller::INT32)	
			v_dl.push_back((Tango::DevLong)new_value.int32_data);
		else
			bad_data_type(par_name);

		vector<string> v_str;
		convert_stream << (Tango::DevLong)idx;
		v_str.push_back(convert_stream.str());
		convert_stream.str("");
	
		d_in.insert(v_dl,v_str);	
				
		if (par_name == "XDim")
		{
			ccdpvcam_ctrl->command_inout("SetAxisXDim",d_in);
		}
		else if (par_name == "YDim")
		{
			ccdpvcam_ctrl->command_inout("SetAxisYDim",d_in);
		}
		else
		{
			TangoSys_OMemStream o;
			o << "Parameter " << par_name << " is unknown for controller CCDPVCAM/" << get_name() << ends;
			
			Tango::Except::throw_exception((const char *)"CCDPVCAMCtrl_BadCtrlPtr",o.str(),
						       			   (const char *)"CCDPVCAM::GetPar()");
		}
	}
	else
	{
		TangoSys_OMemStream o;
		o << "Simulated controller for controller CCDPVCAM/" << get_name() << " is NULL" << ends;
		
		Tango::Except::throw_exception((const char *)"CCDPVCAMCtrl_BadCtrlPtr",o.str(),
					       			   (const char *)"CCDPVCAM::SetPar()");
	}
}




//-----------------------------------------------------------------------------
//
// method : 		CCDPVCAM::GetExtraAttributePar
// 
// description : 	Get a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData CCDPVCAM::GetExtraAttributePar(int32_t idx,string &par_name)
{
	Controller::CtrlData par_value;	

	Tango::DevLong par_tmp_l;

	if (par_name == "AcqMode")
	{
		
		Tango::DeviceData d_in,d_out;
		
		d_in << (Tango::DevLong)idx;
		d_out = ccdpvcam_ctrl->command_inout("GetAxisAcqMode",d_in);
		d_out >> par_tmp_l;
        
		par_value.int32_data = (int32_t)par_tmp_l;
		par_value.data_type = Controller::INT32;
    }
	else
	{
		TangoSys_OMemStream o;
		o << "Parameter " << par_name << " is unknown for controller CCDPVCAM/" << get_name() << ends;
		
		Tango::Except::throw_exception((const char *)"CCDPVCAM_BadCtrlPtr",o.str(),
					       			   (const char *)"CCDPVCAM::GetExtraAttributePar()");
	}
	
	return par_value;
}

//-----------------------------------------------------------------------------
//
// method : 		CCDPVCAM::SetExtraAttributePar
// 
// description : 	Set a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void CCDPVCAM::SetExtraAttributePar(int32_t idx,string &par_name,Controller::CtrlData &new_value)
{
	if(par_name == "AcqMode")
	{

       if (ccdpvcam_ctrl != NULL)
		{
			Tango::DeviceData d_in;
			
			vector<Tango::DevLong> v_db;
			
			if (new_value.data_type == Controller::INT32){
				cout << "[CCDPVCAMCtrl] New value for AcqMode extra attribute is " << new_value.int32_data << endl;
				v_db.push_back((Tango::DevLong)new_value.int32_data);
				
			}else
				bad_data_type(par_name);
			
			vector<string> v_str;
			convert_stream << (Tango::DevLong)idx;
			v_str.push_back(convert_stream.str());
			convert_stream.str("");
			d_in.insert(v_db,v_str);
            ccdpvcam_ctrl->command_inout("SetAxisAcqMode",d_in);	
		}
	}
	else
	{
		TangoSys_OMemStream o;
		o << "Parameter " << par_name << " is unknown for controller CCDPVCAM/" << get_name() << ends;
		
		Tango::Except::throw_exception((const char *)"CCDPVCAM_BadCtrlPtr",o.str(),
					       			   (const char *)"CCDPVCAM::SetExtraAttribute()");
	}
    

    

}


//-----------------------------------------------------------------------------
//
// method : 		CCDPVCAM::send_to_ctrl
// 
// description : 	Send a string to the controller
//
// arg(s) : - in_str : the string to send to the ctrl
//
//-----------------------------------------------------------------------------

string CCDPVCAM::SendToCtrl(string &in_str)
{
	cout << "[CCDPVCAM] I have received the string: " << in_str << endl;
	string returned_str("Hasta luego");
	return returned_str;	
}

//-----------------------------------------------------------------------------
//
// method : 		CCDPVCAM::bad_data_type
// 
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void CCDPVCAM::bad_data_type(string &par_name)
{
	TangoSys_OMemStream o;
	o << "A wrong data type has been used to set the parameter " << par_name << ends;

	Tango::Except::throw_exception((const char *)"CCDPVCAMCtrl_BadParameter",o.str(),
			       			   	   (const char *)"CCDPVCAM::SetPar()");
}

//
//===============================================================================================
//

const char *TwoDExpChannel_Ctrl_class_name[] = {"CCDPVCAM",NULL};

const char *CCDPVCAM_doc = "This is the C++ controller for the CCDPVCAM class";
const char *CCDPVCAM_gender = "CCDPVCAM";
const char *CCDPVCAM_model = "CCDPVCAM";
const char *CCDPVCAM_image = "fake_com.png";
const char *CCDPVCAM_organization = "DESY";
const char *CCDPVCAM_logo = "ALBA_logo.png";

Controller::ExtraAttrInfo CCDPVCAM_ctrl_extra_attributes[] = {
	{"AcqMode","DevLong","Read_Write"},
	NULL};

Controller::PropInfo CCDPVCAM_class_prop[] = {
	{"DevName","The tango device name of the CCDPVCAMCtrl","DevString"},
	NULL};
							  			 
int32_t CCDPVCAM_MaxDevice = 97;

extern "C"
{
	
Controller *_create_CCDPVCAM(const char *inst,vector<Controller::Properties> &prop)
{
	return new CCDPVCAM(inst,prop);
}

}
