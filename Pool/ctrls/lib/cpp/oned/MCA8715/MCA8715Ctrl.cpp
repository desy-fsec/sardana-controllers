#include <iostream>
#include <MCA8715Ctrl.h>
#include <pool/PoolAPI.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		MCA8715::MCA8715
// 
// description : 	Ctor of the MCA8715 class
//					It retrieve some properties from Tango DB, build a 
//					connection to the Simulated controller and ping it
//					to check if it is alive
//
//-----------------------------------------------------------------------------

MCA8715::MCA8715(const char *inst,vector<Controller::Properties> &prop):
OneDController(inst)
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
	// Create a DeviceProxy on the mca8715 controller and set
	// it in automatic reconnection mode
	//
	mca8715_ctrl = Pool_ns::PoolUtil::instance()->get_device(inst_name, DevName);
	//
	// Ping the device to be sure that it is present
	//
	if(mca8715_ctrl == NULL)
    {
		TangoSys_OMemStream o;
		o << "The PoolAPI did not provide a valid mca8715 device" << ends;
		Tango::Except::throw_exception((const char *)"MCA8715Ctrl_BadPoolAPI",o.str(),
									   (const char *)"MCA8715::MCA8715()");
    }
	
	try
    {
		mca8715_ctrl->ping();
    }
	catch (Tango::DevFailed &e)
    {
		throw;
    }
	
}

//-----------------------------------------------------------------------------
//
// method : 		MCA8715::~MCA8715
// 
// description : 	Dtor of the MCA8715 Controller class
//
//-----------------------------------------------------------------------------

MCA8715::~MCA8715()
{
}

//-----------------------------------------------------------------------------
//
// method : 		MCA8715::AddDevice
// 
// description : 	Register a new device for the controller
//					For the simulated controller, this simply means increment
//					motor count
//
//-----------------------------------------------------------------------------

void MCA8715::AddDevice(int32_t idx)
{
	//cout << "[MCA8715] Creating a new OneD with index " << idx << " on controller MCA8715/" << inst_name << endl;
}

//-----------------------------------------------------------------------------
//
// method : 		MCA8715::DeleteDevice
// 
// description : 	Unregister a new device for the controller
//					For the simulated controller, this simply means decrement
//					motor count
//
//-----------------------------------------------------------------------------

void MCA8715::DeleteDevice(int32_t idx)
{
	//cout << "[MCA8715] Deleting OneD with index " << idx << " on controller MCA8715/" << inst_name << endl;
}

void MCA8715::PreReadOne(int32_t idx)
{

	if (mca8715_ctrl != NULL)
    {
		Tango::DeviceData d_in;
		d_in << (Tango::DevLong)idx;
		mca8715_ctrl->command_inout("ReadAxis",d_in);
	}
	else
    { 
		TangoSys_OMemStream o;
		o << "MCA8715 Controller for controller MCA8715Ctrl/" << get_name() << " is NULL" << ends;	
		Tango::Except::throw_exception((const char *)"MCA8715Ctrl_BadCtrlPtr",o.str(),
									   (const char *)"MCA8715::PreReadOne()");
    }


}

double *MCA8715::ReadOne(int32_t idx)
{
    double *read_value;
    vector<Tango::DevLong> vector_data;

    read_nb++;
	
	if (mca8715_ctrl != NULL)
    {
		Tango::DeviceData d_out, d_in;
		d_in << (Tango::DevLong)idx;
		d_out = mca8715_ctrl->command_inout("GetAxisData",d_in);
        d_out >> vector_data;
		read_value =  new double[vector_data.size()];
        for(int i = 0; i < vector_data.size(); i++)
			read_value[i] = (double)vector_data[i];
	   
  
	}
	else
    { 
		TangoSys_OMemStream o;
		o << "MCA8715 Controller for controller MCA8715Ctrl/" << get_name() << " is NULL" << ends;	
		Tango::Except::throw_exception((const char *)"MCA8715Ctrl_BadCtrlPtr",o.str(),
									   (const char *)"MCA8715::ReadOne()");
    }

	 return read_value;
    
}

void  MCA8715::StartOne(int32_t idx)
{

	if (mca8715_ctrl != NULL)
    {
		Tango::DeviceData d_in;
		d_in << (Tango::DevLong)idx;
		mca8715_ctrl->command_inout("StartAxis",d_in);
    }
	else
    {
		TangoSys_OMemStream o;
		o << "MCA8715 Controller for controller MCA8715Ctrl/" << get_name() << " is NULL" << ends;	
		Tango::Except::throw_exception((const char *)"MCA8715Ctrl_BadCtrlPtr",o.str(),
									   (const char *)"MCA8715::StartOne()");
    }


}

void  MCA8715::AbortOne(int32_t idx)
{

	if (mca8715_ctrl != NULL)
    {
		Tango::DeviceData d_in;
		d_in << (Tango::DevLong)idx;
		mca8715_ctrl->command_inout("StopAxis",d_in);
    }
	else
    {
		TangoSys_OMemStream o;
		o << "MCA8715 Controller for controller MCA8715Ctrl/" << get_name() << " is NULL" << ends;	
		Tango::Except::throw_exception((const char *)"MCA8715Ctrl_BadCtrlPtr",o.str(),
									   (const char *)"MCA8715::AbortOne()");
    }
	
}

//-----------------------------------------------------------------------------
//
// method : 		MCA8715::GetState
// 
// description : 	Get one motor status. Motor status means two things :
//					1 - The motor state (Tango sense)
//
// arg(s) : - idx : The motor number (starting at 1)
//			- mot_info_ptr : Pointer to a struct. which will be filled with
//							 motor status
//
//-----------------------------------------------------------------------------

void MCA8715::StateOne(int32_t idx,Controller::CtrlState *ior_info_ptr)
{
	Tango::DevLong state_tmp;


	if (mca8715_ctrl != NULL)
    {
		Tango::DeviceData d_in,d_out;
		d_in << (Tango::DevLong)idx;
		d_out = mca8715_ctrl->command_inout("GetAxisStatus",d_in);
		
		d_out >> state_tmp;
		
		ior_info_ptr->state = state_tmp;
		if(state_tmp == Tango::ON){
			ior_info_ptr->status = "OneD is in ON state";
		} else if (state_tmp == Tango::FAULT){
			ior_info_ptr->status = "OneD is in FAULT state";
		}
		
    }
	else
    {
		TangoSys_OMemStream o;
		o << "MCA8715 Controller for controller MCA8715Ctrl/" << get_name() << " is NULL" << ends;
		
		Tango::Except::throw_exception((const char *)"MCA8715Ctrl_BadCtrlPtr",o.str(),
									   (const char *)"MCA8715::GetStatus()");
    }
	
}

//-----------------------------------------------------------------------------
//
// method : 		MCA8715::GetPar
// 
// description : 	Get a oned exp channel parameter. Actually, 1 parameters is supported.
//					This is DataLength
//
// arg(s) : - idx : The oned exp channel  number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData MCA8715::GetPar(int32_t idx, string &par_name)
{
	//cout << "[MCA8715] Getting parameter " << par_name << " for oned exp channel with index " << idx << " on controller MCA8715/" << inst_name << " (" << DevName << ")" << endl;

	Controller::CtrlData par_value;	
	if (mca8715_ctrl != NULL)
	{
		Tango::DeviceData d_in,d_out;

		d_in << (Tango::DevLong)idx;		
		if (par_name == "DataLength")
		{
			d_out = mca8715_ctrl->command_inout("GetAxisDataLength",d_in);
            Tango::DevLong tmp_v;
			d_out >> tmp_v;
            par_value.int32_data = (int32_t)tmp_v;
			par_value.data_type = Controller::INT32;		
		}
		else
		{
			TangoSys_OMemStream o;
			o << "Parameter " << par_name << " is unknown for controller MCA8715/" << get_name() << ends;
			
			Tango::Except::throw_exception((const char *)"MCA8715_BadCtrlPtr",o.str(),
						       			   (const char *)"MCA8715::GetPar()");
		}
	}
	else
	{
		TangoSys_OMemStream o;
		o << "Simulated controller for controller MCA8715/" << get_name() << " is NULL" << ends;
		
		Tango::Except::throw_exception((const char *)"MCA8715_BadCtrlPtr",o.str(),
					       			   (const char *)"MCA8715::GetPar()");
	}
	
	return par_value;
}

//-----------------------------------------------------------------------------
//
// method : 		MCA8715::SetPar
// 
// description : 	Set a oned parameter. Actually, 1 parameters is supported.
//					This is DataLength
//
// arg(s) : - idx : The oned exp channel number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void MCA8715::SetPar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{
	//cout << "[MCA8715Controller] Setting parameter " << par_name << " for oned channel with index " << idx << " on controller MCA8715Controller/" << inst_name << " (" << DevName << ")" << endl;

	if (mca8715_ctrl != NULL)
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
				
		if (par_name == "DataLength")
		{
			mca8715_ctrl->command_inout("SetAxisDataLength",d_in);
		}
		else
		{
			TangoSys_OMemStream o;
			o << "Parameter " << par_name << " is unknown for controller MCA8715/" << get_name() << ends;
			
			Tango::Except::throw_exception((const char *)"MCA8715Ctrl_BadCtrlPtr",o.str(),
						       			   (const char *)"MCA8715::GetPar()");
		}
	}
	else
	{
		TangoSys_OMemStream o;
		o << "Simulated controller for controller MCA8715/" << get_name() << " is NULL" << ends;
		
		Tango::Except::throw_exception((const char *)"MCA8715Ctrl_BadCtrlPtr",o.str(),
					       			   (const char *)"MCA8715::SetPar()");
	}
}




//-----------------------------------------------------------------------------
//
// method : 		MCA8715::GetExtraAttributePar
// 
// description : 	Get a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData MCA8715::GetExtraAttributePar(int32_t idx, string &par_name)
{
	Controller::CtrlData par_value;	

	Tango::DevLong par_tmp_l;

	if(par_name == "Clear")
	{
		TangoSys_OMemStream o;
		o << "Parameter " << par_name << " can not be readout" << ends;
		
		Tango::Except::throw_exception((const char *)"MCA8715_BadCtrlPtr",o.str(),
									   (const char *)"MCA8715::GetExtraAttributePar()");
		
	} 
	else if (par_name == "BankId")
	{
		
		Tango::DeviceData d_in,d_out;
		
		d_in << (Tango::DevLong)idx;
		d_out = mca8715_ctrl->command_inout("GetAxisBankId",d_in);
		d_out >> par_tmp_l;
        
		par_value.int32_data = (int32_t)par_tmp_l;
		par_value.data_type = Controller::INT32;
    }
	else
	{
		TangoSys_OMemStream o;
		o << "Parameter " << par_name << " is unknown for controller MCA8715/" << get_name() << ends;
		
		Tango::Except::throw_exception((const char *)"MCA8715_BadCtrlPtr",o.str(),
					       			   (const char *)"MCA8715::GetExtraAttributePar()");
	}
	
	return par_value;
}

//-----------------------------------------------------------------------------
//
// method : 		MCA8715::SetExtraAttributePar
// 
// description : 	Set a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void MCA8715::SetExtraAttributePar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{
	if (par_name == "Clear")
	{
		if (mca8715_ctrl != NULL)
		{
		
			Tango::DeviceData d_in;
		   
			Tango::DevLong dlo = (Tango::DevLong)idx;
			d_in << dlo;
			mca8715_ctrl->command_inout("ClearAxis",d_in);		
		}	
	}
	else if(par_name == "BankId")
	{

       if (mca8715_ctrl != NULL)
		{
			Tango::DeviceData d_in;
			
			vector<Tango::DevLong> v_db;
			
			if (new_value.data_type == Controller::INT32) {
				cout << "[MCA8715Ctrl] New value for BankId extra attribute is " << new_value.int32_data << endl;
				v_db.push_back((Tango::DevLong)new_value.int32_data);
				
			}else
				bad_data_type(par_name);
			
			vector<string> v_str;
			convert_stream << (Tango::DevLong)idx;
			v_str.push_back(convert_stream.str());
			convert_stream.str("");
			d_in.insert(v_db,v_str);
            mca8715_ctrl->command_inout("SetAxisBankId",d_in);	
		}
	}
	else
	{
		TangoSys_OMemStream o;
		o << "Parameter " << par_name << " is unknown for controller MCA8715/" << get_name() << ends;
		
		Tango::Except::throw_exception((const char *)"MCA8715_BadCtrlPtr",o.str(),
					       			   (const char *)"MCA8715::SetExtraAttribute()");
	}
    

    

}


//-----------------------------------------------------------------------------
//
// method : 		MCA8715::send_to_ctrl
// 
// description : 	Send a string to the controller
//
// arg(s) : - in_str : the string to send to the ctrl
//
//-----------------------------------------------------------------------------

string MCA8715::SendToCtrl(string &in_str)
{
	cout << "[MCA8715] I have received the string: " << in_str << endl;
	string returned_str("Hasta luego");
	return returned_str;	
}

//-----------------------------------------------------------------------------
//
// method : 		MCA8715::bad_data_type
// 
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void MCA8715::bad_data_type(string &par_name)
{
	TangoSys_OMemStream o;
	o << "A wrong data type has been used to set the parameter " << par_name << ends;

	Tango::Except::throw_exception((const char *)"MCA8715Ctrl_BadParameter",o.str(),
			       			   	   (const char *)"MCA8715::SetPar()");
}

//
//===============================================================================================
//

const char *OneDExpChannel_Ctrl_class_name[] = {"MCA8715",NULL};

const char *MCA8715_doc = "This is the C++ controller for the MCA8715 class";
const char *MCA8715_gender = "MCA8715";
const char *MCA8715_model = "MCA8715";
const char *MCA8715_image = "fake_com.png";
const char *MCA8715_organization = "DESY";
const char *MCA8715_logo = "ALBA_logo.png";

Controller::ExtraAttrInfo MCA8715_ctrl_extra_attributes[] = {
	{"Clear","DevLong","Read_Write"},
    {"BankId","DevLong","Read_Write"},
	NULL};

Controller::PropInfo MCA8715_class_prop[] = {
	{"DevName","The tango device name of the MCA8715Ctrl","DevString"},
	NULL};
							  			 
int32_t MCA8715_MaxDevice = 97;

extern "C"
{
	
Controller *_create_MCA8715(const char *inst,vector<Controller::Properties> &prop)
{
	return new MCA8715(inst,prop);
}

}
