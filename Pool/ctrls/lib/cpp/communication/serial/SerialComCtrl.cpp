#include <iostream>
#include <SerialComCtrl.h>

using namespace std;

//
//====== REMOTE PYTANGO SERIAL CONTROLLER ======================================
//

//-----------------------------------------------------------------------------
//
// method : 		RemotePyTangoSerialController::RemotePyTangoSerialController
// 
// description : 	Ctor of the RemotePyTangoSerialController class
//					It retrieve some properties from Tango DB, build a 
//					connection to the Simulated controller and ping it
//					to check if it is alive
//
//-----------------------------------------------------------------------------

RemotePyTangoSerialController::RemotePyTangoSerialController(const char *inst,vector<Controller::Properties> &prop):
ComController(inst)
{
	max_device = 0;
    vector<Controller::Properties>::iterator prop_it;
    for (prop_it = prop.begin(); prop_it != prop.end(); ++prop_it)
    {
		if(prop_it->name == "TangoDevices")
		{
			int index = 1;
			vector<string> &str_vec = prop_it->value.string_prop;
			
			for(unsigned long l = 0; l < str_vec.size(); l++)
			{
				// all possible serial lines will be defined here
				SerialLineData *sl_data_elem = new SerialLineData;
				sl_data_elem->tango_device = str_vec[l];
				sl_data_elem->device_available = false;
				sl_data_elem->proxy = NULL;
				sl_data.insert(make_pair(index, sl_data_elem));
				max_device++;
				index++;
			}
		}
	}
}

//-----------------------------------------------------------------------------
//
// method : 		RemotePyTangoSerialController::~RemotePyTangoSerialController
// 
// description : 	Dtor of the DummyController class
//
//-----------------------------------------------------------------------------

RemotePyTangoSerialController::~RemotePyTangoSerialController()
{
	//cout << "[RemotePyTangoSerialController] class dtor" << endl;
	
	map<int32_t, SerialLineData*>::iterator ite = sl_data.begin();
	for(;ite != sl_data.end();ite++)
	{
		if(ite->second->proxy != NULL)
			delete ite->second->proxy;
		delete ite->second;		
	}		
	sl_data.clear();
}

void RemotePyTangoSerialController::OpenOne(int32_t idx)
{
	if(idx > max_device)
	{
cout << "OpenOne not allowed: exceeds limit!"  << endl;
		return;	
	}
	
	if(sl_data[idx]->device_available == false)
	{
		if(sl_data[idx]->proxy == NULL)
			sl_data[idx]->proxy = new Tango::DeviceProxy(sl_data[idx]->tango_device);
		try
		{
			sl_data[idx]->proxy->ping();
			sl_data[idx]->device_available = true;	
		}
		catch(Tango::DevFailed &e)
		{
			sl_data[idx]->device_available = false;
			return;
		}
	}
	
	if(sl_data[idx]->proxy->state() == Tango::OFF)
	{
		sl_data[idx]->proxy->command_inout("Open");	
	}
}

void RemotePyTangoSerialController::CloseOne(int32_t idx)
{
	if(idx > max_device)
	{
cout << "CloseOne not allowed: exceeds limit!"  << endl;
		return;	
	}
	
	if(sl_data[idx]->device_available == false)
	{
		if(sl_data[idx]->proxy == NULL)
			sl_data[idx]->proxy = new Tango::DeviceProxy(sl_data[idx]->tango_device);
		try
		{
			sl_data[idx]->proxy->ping();
			sl_data[idx]->device_available = true;	
		}
		catch(Tango::DevFailed &e)
		{
			sl_data[idx]->device_available = false;
			return;
		}
	}
	
	if(sl_data[idx]->proxy->state() == Tango::ON)
	{
		sl_data[idx]->proxy->command_inout("Close");	
	}	
}


//-----------------------------------------------------------------------------
//
// method : 		RemotePyTangoSerialController::AddDevice
// 
// description : 	Register a new device for the controller
//					For the simulated controller, this simply means increment
//					motor count
//
//-----------------------------------------------------------------------------

void RemotePyTangoSerialController::AddDevice(int32_t idx)
{
	//cout << "[RemotePyTangoSerialController] Creating a new Communication Channel with index " << idx << " on controller RemotePyTangoSerialController/" << inst_name << endl;
	
	if(idx > max_device)
	{
		TangoSys_OMemStream o;
		o << "The property 'TangoDevices' has no value for index " << idx << ".";
		o << " Please define a valid tango device before adding a new element to this controller"<< ends;
		
		Tango::Except::throw_exception((const char *)"RemotePyTangoSerialController_BadIndex",o.str(),
					       			   (const char *)"RemotePyTangoSerialController::AddDevice()");
	}
	
	if(sl_data[idx]->device_available == false)
	{
		if(sl_data[idx]->proxy == NULL)
			sl_data[idx]->proxy = new Tango::DeviceProxy(sl_data[idx]->tango_device);
		try
		{
			sl_data[idx]->proxy->ping();
			sl_data[idx]->device_available = true;	
		}
		catch(Tango::DevFailed &e)
		{
			sl_data[idx]->device_available = false;
		}
	}	
}

//-----------------------------------------------------------------------------
//
// method : 		RemotePyTangoSerialController::DeleteDevice
// 
// description : 	Unregister a new device for the controller
//					For the simulated controller, this simply means decrement
//					motor count
//
//-----------------------------------------------------------------------------

void RemotePyTangoSerialController::DeleteDevice(int32_t idx)
{
	//cout << "[RemotePyTangoSerialController] Deleting Communication Channel with index " << idx << " on controller RemotePyTangoSerialController/" << inst_name << endl;
	
	if(idx > max_device)
	{
		TangoSys_OMemStream o;
		o << "Trying to delete an inexisting element(" << idx << ") from the controller." << ends;
		
		Tango::Except::throw_exception((const char *)"RemotePyTangoSerialController_BadIndex",o.str(),
					       			   (const char *)"RemotePyTangoSerialController::DeleteDevice()");
	}	
	
	if(sl_data[idx]->proxy != NULL)
	{
		delete sl_data[idx]->proxy;
		sl_data[idx]->proxy = NULL;
		
	}
	sl_data[idx]->device_available = false;
}

string &RemotePyTangoSerialController::ReadOne(int32_t idx, int32_t max_read_len /* = -1*/)
{
	cout << "[RemotePyTangoSerialController] In ReadOne with max_read_len = "<< max_read_len << endl;
	if(max_read_len == 0 || sl_data[idx]->proxy == NULL)
	{
		read_buff.clear();
		return read_buff;
	}
	
	if(sl_data[idx]->device_available == false)
	{
		try
		{
			sl_data[idx]->proxy->ping();
			sl_data[idx]->device_available = true;	
		}
		catch(Tango::DevFailed &e)
		{
			sl_data[idx]->device_available = false;
			read_buff.clear();
			return read_buff;
		}
	}
	
	Tango::DevLong len;
	if(max_read_len > 0)
	{	
		
		len = (Tango::DevLong)max_read_len;	
	}
	else
	{
		Tango::DeviceAttribute da = sl_data[idx]->proxy->read_attribute("InputBuffer");
		Tango::DevLong l;
		da >> l;
		len = l;
	}
	
	Tango::DeviceData out;
	if(len > 0)
	{
		Tango::DeviceData in;
		in << len; 
		out = sl_data[idx]->proxy->command_inout("Read",in);
	}
	else
	{
		out = sl_data[idx]->proxy->command_inout("ReadLine");
	}
	const Tango::DevVarCharArray *array;
	out >> array;
	
	read_buff.assign((const char*)array->get_buffer(),array->length());
	
	return read_buff;
}

string &RemotePyTangoSerialController::ReadLineOne(int32_t idx)
{
	//cout << "[RemotePyTangoSerialController] In ReadLineOne" << endl;
	if(sl_data[idx]->proxy == NULL)
	{
		read_buff.clear();
		return read_buff;
	}
	
	if(sl_data[idx]->device_available == false)
	{
		try
		{
			sl_data[idx]->proxy->ping();
			sl_data[idx]->device_available = true;	
		}
		catch(Tango::DevFailed &e)
		{
			sl_data[idx]->device_available = false;
			read_buff.clear();
			return read_buff;
		}
	}
	
	Tango::DeviceData out;
	out = sl_data[idx]->proxy->command_inout("ReadLine");

	const Tango::DevVarCharArray *array;
	out >> array;
	
	read_buff.assign((const char*)array->get_buffer(),array->length());
	
	return read_buff;
}

int32_t RemotePyTangoSerialController::WriteOne(int32_t idx, string &istr, int32_t write_len /*= -1*/)
{	
	//cout << "[RemotePyTangoSerialController] In WriteOne with write_len = "<< write_len << endl;
	if(write_len == 0 || sl_data[idx]->proxy == NULL)
		return 0;

	if(sl_data[idx]->device_available == false)
	{
		try
		{
			sl_data[idx]->proxy->ping();
			sl_data[idx]->device_available = true;	
		}
		catch(Tango::DevFailed &e)
		{
			sl_data[idx]->device_available = false;
			return 0;
		}
	}
	
	int32_t write_count;

  	int32_t buf_size = (int32_t) istr.size();
	
	if(write_len == -1)
		write_count = buf_size;
	else
		write_count = write_len > buf_size ? buf_size : write_len;
	
	Tango::DevVarCharArray *array = new Tango::DevVarCharArray;
	array->length(write_count);
	for(int32_t i = 0; i < write_count; i++)
	{
		char c = istr[i];
		(*array)[i] = c;
	}
	
	sl_data[idx]->proxy->command_inout("FlushInput");
	sl_data[idx]->proxy->command_inout("FlushOutput");
	
	Tango::DeviceData in;
	in << array;
	sl_data[idx]->proxy->command_inout("Write",in);
	
	return write_count;
}

string &RemotePyTangoSerialController::WriteReadOne(int32_t idx, string &istr, int32_t write_len /*= -1*/, int32_t max_read_len /*= -1*/)
{	
	//cout << "[RemotePyTangoSerialController] In WriteReadOne with write_len = "<< write_len << " max_read_len = " << max_read_len << endl;
	WriteOne(idx,istr,write_len);
	return ReadOne(idx,max_read_len);

}

//-----------------------------------------------------------------------------
//
// method : 		RemotePyTangoSerialController::GetState
// 
// description : 	Get one motor status. Motor status means two things :
//					1 - The motor state (Tango sense)
//
// arg(s) : - idx : The motor number (starting at 1)
//			- mot_info_ptr : Pointer to a struct. which willbe filled with
//							 motor status
//
//-----------------------------------------------------------------------------

void RemotePyTangoSerialController::StateOne(int32_t idx, Controller::CtrlState *ch_info_ptr)
{
	if(sl_data[idx]->proxy == NULL)
	{
		ch_info_ptr->state = Tango::FAULT;
		return;
	}
		
	if(sl_data[idx]->device_available == false)
	{
		try
		{
			sl_data[idx]->proxy->ping();
			sl_data[idx]->device_available = true;	
		}
		catch(Tango::DevFailed &e)
		{
			sl_data[idx]->device_available = false;
			ch_info_ptr->state = Tango::FAULT;
			return;
		}
	}
	
	Tango::DevState s = sl_data[idx]->proxy->state();
	
	if(s == Tango::ON)
	{
		ch_info_ptr->state = Tango::ON;
		ch_info_ptr->status = "The serial line is ready";
	}
	else if(s == Tango::OFF)
	{
		ch_info_ptr->state = Tango::ON;
		ch_info_ptr->status = "The serial line is closed";
	}
	else if(s == Tango::FAULT || s == Tango::UNKNOWN)
	{
		ch_info_ptr->state = s;
		ch_info_ptr->status = sl_data[idx]->proxy->status();
	}
}


//-----------------------------------------------------------------------------
//
// method : 		RemotePyTangoSerialController::GetExtraAttributePar
// 
// description : 	Get a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData RemotePyTangoSerialController::GetExtraAttributePar(int32_t idx, string &par_name)
{
	Controller::CtrlData par_value;	
	
	string par_name_lower(par_name);
	transform(par_name_lower.begin(),par_name_lower.end(),par_name_lower.begin(),::tolower);
	
	if(sl_data[idx]->proxy == NULL)
		return par_value;
		
	if(sl_data[idx]->device_available == false)
	{
		try
		{
			sl_data[idx]->proxy->ping();
			sl_data[idx]->device_available = true;	
		}
		catch(Tango::DevFailed &e)
		{
			sl_data[idx]->device_available = false;
			return par_value;
		}
	}
	
	Tango::DeviceAttribute in;
	in = sl_data[idx]->proxy->read_attribute(par_name);
		
	if (par_name_lower == "baudrate")
	{
		Tango::DevShort value;
		in >> value;
		par_value.int32_data = value;
		par_value.data_type = Controller::INT32;		
	} 
	else if (par_name_lower == "databits")
	{
		Tango::DevShort value;
		in >> value;
		par_value.int32_data = value;
		par_value.data_type = Controller::INT32;		
	} 
	else if (par_name_lower == "flowcontrol")
	{
		in >> par_value.str_data;
		par_value.data_type = Controller::STRING;		
	} 
	else if (par_name_lower == "inputbuffer")
	{   
        Tango::DevLong tmp_data;
		in >> tmp_data;
        par_value.int32_data = (int32_t)tmp_data;
		par_value.data_type = Controller::INT32;		
	} 
	else if (par_name_lower == "parity")
	{
		in >> par_value.str_data;
		par_value.data_type = Controller::STRING;		
	} 
	else if (par_name_lower == "port")
	{
		in >> par_value.str_data;
		par_value.data_type = Controller::STRING;		
	} 
	else if (par_name_lower == "stopbits")
	{
		Tango::DevShort value;
		in >> value;
		par_value.int32_data = (int32_t)value;
		par_value.data_type = Controller::INT32;		
	} 
	else if (par_name_lower == "terminator")
	{
		in >> par_value.str_data;
		par_value.data_type = Controller::STRING;		
	} 
	else if (par_name_lower == "timeout")
	{
		Tango::DevShort value;
		in >> value;
		par_value.int32_data = value;
		par_value.data_type = Controller::INT32;		
	} 
	else
	{
		TangoSys_OMemStream o;
		o << "Parameter " << par_name << " is unknown for controller RemotePyTangoSerialController/" << get_name() << ends;
		
		Tango::Except::throw_exception((const char *)"RemotePyTangoSerialController_BadCtrlPtr",o.str(),
					       			   (const char *)"RemotePyTangoSerialController::GetPar()");
	}
	
	return par_value;
}

//-----------------------------------------------------------------------------
//
// method : 		RemotePyTangoSerialController::SetExtraAttributePar
// 
// description : 	Set a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void RemotePyTangoSerialController::SetExtraAttributePar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{
	string par_name_lower(par_name);
	transform(par_name_lower.begin(),par_name_lower.end(),par_name_lower.begin(),::tolower);
	
	if (par_name_lower == "flowcontrol" || 
	    par_name_lower == "parity" ||
	    par_name_lower == "terminator" ||
	    par_name_lower == "port")
	{
		Tango::DeviceAttribute out(par_name_lower,new_value.str_data);
		sl_data[idx]->proxy->write_attribute(out);
	}
	else if (par_name_lower == "baudrate" ||
			 par_name_lower == "databits" ||
			 par_name_lower == "stopbits" ||
			 par_name_lower == "timeout")
	{
		Tango::DevShort value = (Tango::DevShort)new_value.int32_data;
		Tango::DeviceAttribute out(par_name,value);
		sl_data[idx]->proxy->write_attribute(out);
	}
 	else
	{
		TangoSys_OMemStream o;
		o << "Parameter " << par_name << " is unknown for controller RemotePyTangoSerialController/" << get_name() << ends;
		
		Tango::Except::throw_exception((const char *)"RemotePyTangoSerialController_BadCtrlPtr",o.str(),
					       			   (const char *)"RemotePyTangoSerialController::GetPar()");
	}
}


//-----------------------------------------------------------------------------
//
// method : 		RemotePyTangoSerialController::send_to_ctrl
// 
// description : 	Send a string to the controller
//
// arg(s) : - in_str : the string to send to the ctrl
//
//-----------------------------------------------------------------------------

string RemotePyTangoSerialController::SendToCtrl(string &in_str)
{
	//cout << "[RemotePyTangoSerialController] I have received the string: " << in_str << endl;
	string returned_str("Hasta luego");
	return returned_str;	
}

//-----------------------------------------------------------------------------
//
// method : 		RemotePyTangoSerialController::bad_data_type
// 
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void RemotePyTangoSerialController::bad_data_type(string &par_name)
{
	TangoSys_OMemStream o;
	o << "A wrong data type has been used to set the parameter " << par_name << ends;

	Tango::Except::throw_exception((const char *)"RemotePyTangoSerialController_BadParameter",o.str(),
			       			   	   (const char *)"RemotePyTangoSerialController::SetPar()");
}

//
//==============================================================================
//

const char *Communication_Ctrl_class_name[] = {"RemotePyTangoSerialController", NULL};

/*******************************************************************************
 *
 * C++ Tango serial device server
 * 
 ******************************************************************************/

const char *RemotePyTangoSerialController_doc = "C++ controller for a remote serial line through a Python Tango device server";

Controller::ExtraAttrInfo RemotePyTangoSerialController_ctrl_extra_attributes[] = {
	{"BaudRate",	"DevLong",	"Read_Write"},
	{"DataBits",	"DevLong",	"Read_Write"},
	{"FlowControl",	"DevString","Read_Write"},
	{"InputBuffer",	"DevLong",	"Read"},
	{"Parity",		"DevString","Read_Write"},
	{"Port",		"DevString","Read_Write"},
	{"StopBits",	"DevLong",	"Read_Write"},
	{"Terminator",	"DevString","Read_Write"},
	{"Timeout",		"DevLong",	"Read_Write"},
	NULL};

Controller::PropInfo RemotePyTangoSerialController_class_prop[] = {
	{"TangoDevices","Serial device names","DevVarStringArray",NULL},
	NULL};
							  			 
int32_t RemotePyTangoSerialController_MaxDevice = 64;


extern "C"
{
	
Controller *_create_RemotePyTangoSerialController(const char *inst,vector<Controller::Properties> &prop)
{
	return new RemotePyTangoSerialController(inst,prop);
}

}
