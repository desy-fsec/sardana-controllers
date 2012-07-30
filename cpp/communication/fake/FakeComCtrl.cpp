#include <iostream>
#include <FakeComCtrl.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		FakeComController::FakeComController
// 
// description : 	Ctor of the FakeComController class
//					It retrieve some properties from Tango DB, build a 
//					connection to the Simulated controller and ping it
//					to check if it is alive
//
//-----------------------------------------------------------------------------

FakeComController::FakeComController(const char *inst,vector<Controller::Properties> &prop):
ComController(inst)
{
	read_nb = 0;
	write_nb = 0;
	CppComCh_extra_2 = 0.0;
	
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
}

//-----------------------------------------------------------------------------
//
// method : 		FakeComController::~FakeComController
// 
// description : 	Dtor of the DummyController class
//
//-----------------------------------------------------------------------------

FakeComController::~FakeComController()
{
	//cout << "[FakeComController] class dtor" << endl;
}

//-----------------------------------------------------------------------------
//
// method : 		FakeComController::AddDevice
// 
// description : 	Register a new device for the controller
//					For the simulated controller, this simply means increment
//					motor count
//
//-----------------------------------------------------------------------------

void FakeComController::AddDevice(int32_t idx)
{
	//cout << "[FakeComController] Creating a new Communication Channel with index " << idx << " on controller FakeComController/" << inst_name << endl;
}

//-----------------------------------------------------------------------------
//
// method : 		FakeComController::DeleteDevice
// 
// description : 	Unregister a new device for the controller
//					For the simulated controller, this simply means decrement
//					motor count
//
//-----------------------------------------------------------------------------

void FakeComController::DeleteDevice(int32_t idx)
{
	//cout << "[FakeComController] Deleting Communication Channel with index " << idx << " on controller FakeComController/" << inst_name << endl;
}

string &FakeComController::ReadOne(int32_t idx, int32_t max_read_len /* = -1*/)
{
	if(max_read_len == 0)
	{
		read_buff.clear();
		return read_buff;
	}
	
	ostringstream oss;
	oss << "Read Message #" << read_nb++;
	string msg(oss.str());
	
	int32_t read_count = (int32_t)msg.size();
	
	if(max_read_len != -1)
	{
		if(max_read_len < read_count)
		{
			read_count = max_read_len;
		}
	}
	
	//carefull here
	read_buff.assign(msg.c_str(),read_count);
	
	return read_buff;
}

string &FakeComController::ReadLineOne(int32_t idx)
{
	ostringstream oss;
	oss << "ReadLine Message";
	string msg(oss.str());
	
	int32_t read_count = (int32_t)msg.size();
	
	read_buff.assign(msg.c_str(),read_count);
	return read_buff;
}

int32_t FakeComController::WriteOne(int32_t, string &istr, int32_t write_len /*= -1*/)
{	
	write_nb++;
	
	if(write_len == 0)
		return 0;
	
	int32_t write_count;

  	int32_t buf_size = (int32_t) istr.size();
	
	if(write_len == -1)
		write_count = buf_size;
	else
		write_count = write_len > buf_size ? buf_size : write_len;

	cout << "[FakeComController]::WriteOne Sending stream: [" << std::hex;
	
	for(int32_t i = 0; i < write_count; i++)
	{
		char c = istr[i];
		cout << "'" << c << "' (0x" << (unsigned short)c << ")" ;
		if(i < write_count-1) 
			cout << ", ";
	}
	cout << std::dec << "]" << endl; 	
	
	return write_count;
}

string &FakeComController::WriteReadOne(int32_t idx, string &istr, int32_t write_len /*= -1*/, int32_t max_read_len /*= -1*/)
{	
	WriteOne(idx, istr, write_len);
	return ReadOne(idx, max_read_len);

}

//-----------------------------------------------------------------------------
//
// method : 		FakeComController::GetState
// 
// description : 	Get one motor status. Motor status means two things :
//					1 - The motor state (Tango sense)
//
// arg(s) : - idx : The motor number (starting at 1)
//			- mot_info_ptr : Pointer to a struct. which willbe filled with
//							 motor status
//
//-----------------------------------------------------------------------------

void FakeComController::StateOne(int32_t idx,Controller::CtrlState *ch_info_ptr)
{
	ch_info_ptr->state = Tango::ON;
}


//-----------------------------------------------------------------------------
//
// method : 		FakeComController::GetExtraAttributePar
// 
// description : 	Get a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData FakeComController::GetExtraAttributePar(int32_t idx,string &par_name)
{
	Controller::CtrlData par_value;	
	if (par_name == "CppComCh_extra_1")
	{
		par_value.int32_data = 12345;
		par_value.data_type = Controller::INT32;		
	}
	else if (par_name == "CppComCh_extra_2")
	{
		par_value.db_data = CppComCh_extra_2;
		par_value.data_type = Controller::DOUBLE;		
	} 
	else
	{
		TangoSys_OMemStream o;
		o << "Parameter " << par_name << " is unknown for controller FakeComController/" << get_name() << ends;
		
		Tango::Except::throw_exception((const char *)"FakeComController_BadCtrlPtr",o.str(),
					       			   (const char *)"FakeComController::GetPar()");
	}
	
	return par_value;
}

//-----------------------------------------------------------------------------
//
// method : 		FakeComController::SetExtraAttributePar
// 
// description : 	Set a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void FakeComController::SetExtraAttributePar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{
	if (par_name == "CppComCh_extra_2")
	{
		CppComCh_extra_2 = new_value.db_data;
	}
 	else
	{
		TangoSys_OMemStream o;
		o << "Parameter " << par_name << " is unknown for controller FakeComController/" << get_name() << ends;
		
		Tango::Except::throw_exception((const char *)"FakeComController_BadCtrlPtr",o.str(),
					       			   (const char *)"FakeComController::GetPar()");
	}
}


//-----------------------------------------------------------------------------
//
// method : 		FakeComController::send_to_ctrl
// 
// description : 	Send a string to the controller
//
// arg(s) : - in_str : the string to send to the ctrl
//
//-----------------------------------------------------------------------------

string FakeComController::SendToCtrl(string &in_str)
{
	cout << "[FakeComController] I have received the string: " << in_str << endl;
	string returned_str("Hasta luego");
	return returned_str;	
}

//-----------------------------------------------------------------------------
//
// method : 		FakeComController::bad_data_type
// 
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void FakeComController::bad_data_type(string &par_name)
{
	TangoSys_OMemStream o;
	o << "A wrong data type has been used to set the parameter " << par_name << ends;

	Tango::Except::throw_exception((const char *)"DummyComCtrl_BadParameter",o.str(),
			       			   	   (const char *)"FakeComController::SetPar()");
}

//
//===============================================================================================
//

const char *Communication_Ctrl_class_name[] = {"FakeComController",NULL};

const char *FakeComController_doc = "This is the C++ controller for the FakeComController class";
const char *FakeComController_gender = "Fake";
const char *FakeComController_model = "Fake 2000";
const char *FakeComController_image = "fake_com.png";
const char *FakeComController_organization = "Fake Inc.";
const char *FakeComController_logo = "ALBA_logo.png";

Controller::ExtraAttrInfo FakeComController_ctrl_extra_attributes[] = {{"CppComCh_extra_1","DevLong","Read"},
												 {"CppComCh_extra_2","DevDouble","Read_Write"},
												 NULL};

Controller::PropInfo FakeComController_class_prop[] = {{"The prop","The first CPP property","DevLong","12"},
							  			 {"Another_Prop","The second CPP property","DevString","Hola"},
							  			 {"Third_Prop","The third CPP property","DevVarLongArray","11,22,33"},
							  			 NULL};
							  			 
int32_t FakeComController_MaxDevice = 12;

extern "C"
{
	
Controller *_create_FakeComController(const char *inst,vector<Controller::Properties> &prop)
{
	return new FakeComController(inst,prop);
}

}
