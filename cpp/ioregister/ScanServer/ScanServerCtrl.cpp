#include <iostream>
#include <ScanServerCtrl.h>
#include <pool/PoolAPI.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		ScanServer::ScanServer
// 
// description : 	Ctor of the ScanServer class
//					It retrieve some properties from Tango DB, build a 
//					connection to the Simulated controller and ping it
//					to check if it is alive
//
//-----------------------------------------------------------------------------

ScanServer::ScanServer(const char *inst,vector<Controller::Properties> &prop):
IORegisterController(inst)
{

    for (unsigned long loop = 0;loop < prop.size();loop++)
    {
		if( prop[loop].name == "DevName" )
        {
			DevName = prop[loop].value.string_prop[0];
        }
    }
	
	//
	// Create a DeviceProxy on the ScanServer controller and set
	// it in automatic reconnection mode
	//
	scanserver_ctrl = Pool_ns::PoolUtil::instance()->get_device(inst_name, DevName);
	
	//
	// Ping the device to be sure that it is present
	//
	if(scanserver_ctrl == NULL)
    {
		TangoSys_OMemStream o;
		o << "The PoolAPI did not provide a valid scanserver device" << ends;
		Tango::Except::throw_exception((const char *)"ScanServerCtrl_BadPoolAPI",o.str(),
									   (const char *)"ScanServer::ScanServer()");
    }
	
	try
    {
		scanserver_ctrl->ping();
    }
	catch (Tango::DevFailed &e)
    {
		delete scanserver_ctrl;
		throw;
    }
	
}

//-----------------------------------------------------------------------------
//
// method : 		ScanServer::~ScanServer
// 
// description : 	Dtor of the ScanServer Controller class
//
//-----------------------------------------------------------------------------

ScanServer::~ScanServer()
{
	//cout << "[ScanServer] class dtor" << endl;
	if(scanserver_ctrl != NULL)
		delete scanserver_ctrl;
}

//-----------------------------------------------------------------------------
//
// method :             ScanServer::AddDevice
// 
// description :        Register a new device for the controller
//                                      For the simulated controller, this simply means increment
//                                      motor count
//
//-----------------------------------------------------------------------------

void ScanServer::AddDevice(int32_t idx)
{
        //cout << "[ScanServer] Creating a new IORegister with index " << idx << " on controller ScanServer/" << inst_name << endl;
}

//-----------------------------------------------------------------------------
//
// method :             ScanServer::DeleteDevice
// 
// description :        Unregister a new device for the controller
//                                      For the simulated controller, this simply means decrement
//                                      motor count
//
//-----------------------------------------------------------------------------

void ScanServer::DeleteDevice(int32_t idx)
{
        //cout << "[ScanServer] Deleting IORegister with index " << idx << " on controller ScanServer/" << inst_name << endl;
}




int32_t ScanServer::ReadOne(int32_t idx)
{
	return 1;
}



void ScanServer::WriteOne(int32_t idx, int32_t write_value)
{

}


//-----------------------------------------------------------------------------
//
// method : 		ScanServer::StateOne
// 
// description : 	Get one motor status. Motor status means two things :
//					1 - The motor state (Tango sense)
//
// arg(s) : - idx : The motor number (starting at 1)
//			- mot_info_ptr : Pointer to a struct. which willbe filled with
//							 motor status
//
//-----------------------------------------------------------------------------

void ScanServer::StateOne(int32_t idx,Controller::CtrlState *ior_info_ptr)
{
	Tango::DevState state_tmp;
	
	if (scanserver_ctrl != NULL)
    {
		Tango::DeviceData d_out;
		d_out = scanserver_ctrl->command_inout("State");
		
		d_out >> state_tmp;
		
		ior_info_ptr->state = state_tmp;
		if(state_tmp == Tango::ON){
			ior_info_ptr->status = "ScanServer is in ON state";
		} else if (state_tmp == Tango::FAULT){
			ior_info_ptr->status = "ScanServer is in FAULT state";
		} else if (state_tmp == Tango::MOVING){ // When the scan is running
			ior_info_ptr->status = "ScanServer is in MOVING state"; 
		} else if (state_tmp == Tango::RUNNING){// I think it is not used (converted to MOVING in scansl/src/State.cpp)
			ior_info_ptr->status = "ScanServer is in RUNNING state";  
		} else if (state_tmp == Tango::STANDBY){ // If the scan has been paused
			ior_info_ptr->status = "ScanServer is in STANDBY state";
		}
		
    }
	else
    {
		TangoSys_OMemStream o;
		o << "ScanServer Controller for controller ScanServerCtrl/" << get_name() << " is NULL" << ends;
		
		Tango::Except::throw_exception((const char *)"ScanServerCtrl_BadCtrlPtr",o.str(),
									   (const char *)"ScanServer::GetStatus()");
    }
	
}



//-----------------------------------------------------------------------------
//
// method : 		ScanServer::send_to_ctrl
// 
// description : 	Send a string to the controller
//
// arg(s) : - in_str : the string to send to the ctrl
//
//-----------------------------------------------------------------------------

string ScanServer::SendToCtrl(string &str)
{
	int i = 0;
	string buf;
	string cmd;
	stringstream ss(str);
	vector<string> params;

	while(ss >> buf)
	{
		if (i == 0)
			cmd = buf;
		else
			params.push_back(buf);
		i++;
	}
	
	bool question = cmd[0] == '?';
	if(question) cmd = cmd.substr(1);
	
	transform(cmd.begin(),cmd.end(),cmd.begin(),::tolower);

	const char *ret;

	if(scanserver_ctrl == NULL){
		return "Not ScanServer Device";
	}


    if(cmd == "start")
	{
		try
		{
			scanserver_ctrl->command_inout("Start");
			ret = "Start command executed";
		}
		catch(Tango::DevFailed &e)
		{
			ret = "Error in executing Start command (DevFailed)";
		}
	}
	else if(cmd == "pause")
	{
		try
		{
			scanserver_ctrl->command_inout("Pause");
			ret = "Pause command executed";
		}
		catch(Tango::DevFailed &e)
		{
			ret = "Error in executing Pause command (DevFailed)";
		}
	}
	else if(cmd == "resume")
	{
		try
		{
			scanserver_ctrl->command_inout("Resume");
			ret = "Resume command executed";
		}
		catch(Tango::DevFailed &e)
		{
			ret = "Error in executing Resume command (DevFailed)";
		}
	}
	else if(cmd == "clean")
	{
		try
		{
			scanserver_ctrl->command_inout("Clean");
			ret = "Clean command executed";
		}
		catch(Tango::DevFailed &e)
		{
			ret = "Error in executing Clean command (DevFailed)";
		}
	}
	else if(cmd == "sensors")
	{
		if(question){

			try
			{   
				vector<string> vstr_read;
				Tango::DeviceAttribute da_read;
				da_read = scanserver_ctrl->read_attribute("sensors");
				da_read >> vstr_read;
                long nb_read = da_read.get_nb_read();
				string output_string = "Sensors: \n";
				for(int i = 0; i < nb_read; ++i){
					output_string.append(vstr_read[i]);
					output_string.append("\n");
				}
				return output_string;
				
			}
			catch(Tango::DevFailed &e)
			{
				ret = "Error in reading sensors(DevFailed)";
			}
			
		}else{
			try
			{
				Tango::DeviceAttribute *attr_sensors = new Tango::DeviceAttribute( "sensors", params);
				scanserver_ctrl->write_attribute(*attr_sensors);
				ret = "Sensors written";
			}
			catch(Tango::DevFailed &e)
			{
				ret = "Error in writting sensors(DevFailed)";
			}
		}
	}
	else if(cmd == "actuators")
	{
		if(question){

			try
			{   
				vector<string> vstr_read;
				Tango::DeviceAttribute da_read;
				da_read = scanserver_ctrl->read_attribute("actuators");
				da_read >> vstr_read;
                long nb_read = da_read.get_nb_read();
				string output_string = "Actuators: \n";
				for(int i = 0; i < nb_read; ++i){
					output_string.append(vstr_read[i]);
					output_string.append("\n");
				}
				return output_string;
				
			}
			catch(Tango::DevFailed &e)
			{
				ret = "Error in reading actuators (DevFailed)";
			}
			
		}else{
			try
			{
				Tango::DeviceAttribute *attr_actuators = new Tango::DeviceAttribute( "actuators", params);
				scanserver_ctrl->write_attribute(*attr_actuators);
				ret = "Actuators written";
			}
			catch(Tango::DevFailed &e)
			{
				ret = "Error in writting actuators (DevFailed)";
			}
		}
	}
	else if(cmd == "actuators2")
	{
		if(question){

			try
			{   
				vector<string> vstr_read;
				Tango::DeviceAttribute da_read;
				da_read = scanserver_ctrl->read_attribute("actuators2");
				da_read >> vstr_read;
                long nb_read = da_read.get_nb_read();
				string output_string = "Actuators2 (extern loop): \n";
				for(int i = 0; i < nb_read; ++i){
					output_string.append(vstr_read[i]);
					output_string.append("\n");
				}
				return output_string;
				
			}
			catch(Tango::DevFailed &e)
			{
				ret = "Error in reading actuators2 (DevFailed)";
			}
			
		}else{
			try
			{
				Tango::DeviceAttribute *attr_actuators = new Tango::DeviceAttribute( "actuators2", params);
				scanserver_ctrl->write_attribute(*attr_actuators);
				ret = "Actuators2 written";
			}
			catch(Tango::DevFailed &e)
			{
				ret = "Error in writting actuators2 (DevFailed)";
			}
		}
	}
	else if(cmd == "integrationtimes")
	{
		if(question){

			try
			{   
				vector<double> vd_read;
				Tango::DeviceAttribute da_read;
				da_read = scanserver_ctrl->read_attribute("integrationTimes");
				da_read >> vd_read;
                long nb_read = da_read.get_nb_read();
				string output_string = "Integration times: \n";
				for(int i = 0; i < nb_read; ++i){
					output_string.append(ToString(vd_read[i]));
					output_string.append("\n");
				}
				return output_string;
				
			}
			catch(Tango::DevFailed &e)
			{
				ret = "Error in reading integrationTimes (DevFailed)";
			}
			
		}else{
			try
			{
                vector<double> dparams;
                for(int i = 0; i < params.size(); i++){

					dparams.push_back(ToDouble(params[i]));
				}
				Tango::DeviceAttribute *attr_integrationTimes = new Tango::DeviceAttribute( "integrationTimes", dparams);
				scanserver_ctrl->write_attribute(*attr_integrationTimes);
				ret = "integrationTimes written";
			}
			catch(Tango::DevFailed &e)
			{
				ret = "Error in writting integrationTimes (DevFailed)";
			}
		}
	}
	else if(cmd == "trajectories")
	{
		if(question){

			try
			{   
				vector<double> vd_read;
				Tango::DeviceAttribute da_read;
				da_read = scanserver_ctrl->read_attribute("trajectories");
				da_read >> vd_read;
                long nb_read = da_read.get_nb_read();
				string output_string = "Trajectories: \n";
				for(int i = 0; i < nb_read; ++i){
					output_string.append(ToString(vd_read[i]));
					output_string.append("\n");
				}
				return output_string;
				
			}
			catch(Tango::DevFailed &e)
			{
				ret = "Error in reading trajectories (DevFailed)";
			}
			
		}else{
			try
			{
                vector<double> dparams;
                if (params.size() < 2) return "Too few parameters";
                int x_dim = (int) ToDouble(params[0]);
                int y_dim = (int) ToDouble(params[1]);
                for(int i = 2; i < params.size(); i++)
				{
					dparams.push_back(ToDouble(params[i]));
				}
				Tango::DeviceAttribute *attr_trajectories = new Tango::DeviceAttribute( "trajectories", dparams, x_dim, y_dim);
				scanserver_ctrl->write_attribute(*attr_trajectories);
				ret = "trajectories written";
			}
			catch(Tango::DevFailed &e)
			{
				ret = "Error in writting trajectories (DevFailed)";
			}
		}
	}
	else if(cmd == "trajectories2")
	{
		if(question){

			try
			{   
				vector<double> vd_read;
				Tango::DeviceAttribute da_read;
				da_read = scanserver_ctrl->read_attribute("trajectories2");
				da_read >> vd_read;
                long nb_read = da_read.get_nb_read();
				string output_string = "Trajectories2 (extern loop): \n";
				for(int i = 0; i < nb_read; ++i){
					output_string.append(ToString(vd_read[i]));
					output_string.append("\n");
				}
				return output_string;
				
			}
			catch(Tango::DevFailed &e)
			{
				ret = "Error in reading trajectories2 (DevFailed)";
			}
			
		}else{
			try
			{
                vector<double> dparams;
                if (params.size() < 2) return "Too few parameters";
                int x_dim = (int) ToDouble(params[0]);
                int y_dim = (int) ToDouble(params[1]);
                for(int i = 2; i < params.size(); i++)
				{
					dparams.push_back(ToDouble(params[i]));
				}
				Tango::DeviceAttribute *attr_trajectories2 = new Tango::DeviceAttribute( "trajectories2", dparams, x_dim, y_dim);
				scanserver_ctrl->write_attribute(*attr_trajectories2);
				ret = "trajectories2 written";
			}
			catch(Tango::DevFailed &e)
			{
				ret = "Error in writting trajectories2 (DevFailed)";
			}
		}
	}
	else if(cmd == "timebases")
	{
		if(question){

			try
			{   
				vector<string> vstr_read;
				Tango::DeviceAttribute da_read;
				da_read = scanserver_ctrl->read_attribute("timebases");
				da_read >> vstr_read;
                long nb_read = da_read.get_nb_read();
				string output_string = "Timebases: \n";
				for(int i = 0; i < nb_read; ++i){
					output_string.append(vstr_read[i]);
					output_string.append("\n");
				}
				return output_string;
				
			}
			catch(Tango::DevFailed &e)
			{
				ret = "Error in reading timebases (DevFailed)";
			}
			
		}else{
			try
			{
				Tango::DeviceAttribute *attr_timebases = new Tango::DeviceAttribute( "timebases", params);
				scanserver_ctrl->write_attribute(*attr_timebases);
				ret = "Actuators written";
			}
			catch(Tango::DevFailed &e)
			{
				ret = "Error in writting timebases (DevFailed)";
			}
		}
	}
	else if(cmd == "state")
	{
		if(question){

			Tango::DevState state_tmp;

			try
			{
				Tango::DeviceData d_out;
			   
				d_out = scanserver_ctrl->command_inout("State");

			 
				char p[3];
				
				d_out >> state_tmp;
				if(state_tmp == Tango::ON){
					sprintf(p,"%d", Tango::ON);
				} else if (state_tmp == Tango::FAULT){
					sprintf(p,"%d", Tango::FAULT);
				} else if (state_tmp == Tango::MOVING){
					sprintf(p,"%d", Tango::MOVING);
				} else if (state_tmp == Tango::RUNNING){
					sprintf(p,"%d", Tango::RUNNING);
				} else if (state_tmp == Tango::STANDBY){
					sprintf(p,"%d", Tango::STANDBY);
				}

				string output_string = p;

				return output_string;

			}
			catch(Tango::DevFailed &e)
			{
				ret = "Error in reading state (DevFailed)";
			}
			
		}else{
			ret = "Error in trying to write state (read only -> usage: ?state)";
		}
	}
	else if(cmd == "data")
	{
		if(question){

			try
			{	

				char p[1000] = " ";
                char tmp[1000];
				// Read actuators data
				
				vector<string> actuators_list;
				Tango::DeviceAttribute da_actuators;
				da_actuators = scanserver_ctrl->read_attribute("actuators");
				da_actuators >> actuators_list;
				long nb_actuators = da_actuators.get_nb_read();
				
				vector<string> vstr_actuators_datalist;
				Tango::DeviceAttribute da_actuators_datalist;
				da_actuators_datalist = scanserver_ctrl->read_attribute("actuatorsDataList");
				da_actuators_datalist >> vstr_actuators_datalist;
				long nb_actuators_list = da_actuators_datalist.get_nb_read();
				
				Tango::DeviceAttribute da_data_actuators;
				vector<Tango::DevDouble> d_data_actuators;
				vector<Tango::DevLong> l_data_actuators;
				vector<Tango::DevShort> s_data_actuators;
				vector<Tango::DevFloat> f_data_actuators;
				long idata_actuators;
				int actuator_type;
				
				for(int i = 0; i < nb_actuators; ++i){
					sprintf(tmp,"Actuator %s \n", actuators_list[i].c_str());
					strcat(p,tmp);
					da_data_actuators = scanserver_ctrl->read_attribute(vstr_actuators_datalist[i]);
					idata_actuators = da_data_actuators.get_nb_read();
					actuator_type = da_data_actuators.get_type();
					if(actuator_type == Tango::DEV_DOUBLE){
						da_data_actuators >> d_data_actuators;
					} else if(actuator_type == Tango::DEV_LONG){
						da_data_actuators >> l_data_actuators;
					} else if(actuator_type == Tango::DEV_SHORT){
						da_data_actuators >> s_data_actuators;
					} else if(actuator_type == Tango::DEV_FLOAT){
						da_data_actuators >> f_data_actuators;
					} 
					// da_data_actuators >> data_actuators;
					for (int j = 0; j < idata_actuators; j++){
						if(actuator_type == Tango::DEV_DOUBLE){
							sprintf(tmp,"%f ", d_data_actuators[j]);
							strcat(p,tmp);
						} else if(actuator_type == Tango::DEV_LONG){
							sprintf(tmp,"%d ", l_data_actuators[j]);
							strcat(p,tmp);
						} else if(actuator_type == Tango::DEV_SHORT){
							sprintf(tmp,"%d ", s_data_actuators[j]);
							strcat(p,tmp);
						} else if(actuator_type == Tango::DEV_FLOAT){
							sprintf(tmp,"%f ", f_data_actuators[j]);
							strcat(p,tmp);
						} 
					}
					strcat(p,"\n");       
				}

				// Read sensors data
				
				vector<string> sensors_list;
				Tango::DeviceAttribute da_sensors;
				da_sensors = scanserver_ctrl->read_attribute("sensors");
				da_sensors >> sensors_list;
				long nb_sensors = da_sensors.get_nb_read();
				
				vector<string> vstr_read;
				Tango::DeviceAttribute da_read;
				da_read = scanserver_ctrl->read_attribute("sensorsDataList");
				da_read >> vstr_read;
				long read = da_read.get_nb_read();
				
				Tango::DeviceAttribute da_data_sensors;
				vector<Tango::DevDouble> d_data_sensors;
				vector<Tango::DevLong> l_data_sensors;
				vector<Tango::DevShort> s_data_sensors;
				vector<Tango::DevFloat> f_data_sensors;
				long idata_sensors;
				int sensor_type;
				
				
				for(int i = 0; i < read; ++i){
					sprintf(tmp,"Sensor %s \n", sensors_list[i].c_str());
					strcat(p,tmp);
					da_data_sensors = scanserver_ctrl->read_attribute(vstr_read[i]);
					idata_sensors = da_data_sensors.get_nb_read();
					sensor_type = da_data_sensors.get_type();
					
					if(sensor_type == Tango::DEV_DOUBLE){
						da_data_sensors >> d_data_sensors;
					} else if(sensor_type == Tango::DEV_LONG){
						da_data_sensors >> l_data_sensors;
					} else if(sensor_type == Tango::DEV_SHORT){
						da_data_sensors >> s_data_sensors;
					} else if(sensor_type == Tango::DEV_FLOAT){
						da_data_sensors >> f_data_sensors;
					}
					for (int j = 0; j < idata_sensors; j++){
						if(sensor_type == Tango::DEV_DOUBLE){
							sprintf(tmp,"%f ", d_data_sensors[j]);
							strcat(p,tmp);
						} else if(sensor_type == Tango::DEV_LONG){
							sprintf(tmp,"%d ", l_data_sensors[j]);
							strcat(p,tmp);
						} else if(sensor_type == Tango::DEV_SHORT){
							sprintf(tmp,"%d ", s_data_sensors[j]);
							strcat(p,tmp);
						} else if(sensor_type == Tango::DEV_FLOAT){
							sprintf(tmp,"%f ", f_data_sensors[j]);
							strcat(p,tmp);
						} 
					}  
					strcat(p,"\n");
				}

				string output_string = p;
				return output_string;

			}
			catch(Tango::DevFailed &e)
			{
				ret = "Error in reading data (DevFailed)";
			}
			
		}else{
			ret = "Error in trying to write data (read only -> usage: ?data)";
		}
	}
	else if(cmd == "scan_extra_attribute")
	{
		if(params[0] == "actuatorsDelay"){
			if(question){
				
				try
				{   
					vector<double> vd_read;
					Tango::DeviceAttribute da_read;
					da_read = scanserver_ctrl->read_attribute("actuatorsDelay");
					da_read >> vd_read;
					long nb_read = da_read.get_nb_read();
					string output_string = "actuatorsDelay: \n";
					for(int i = 0; i < nb_read; ++i){
						output_string.append(ToString(vd_read[i]));
						output_string.append("\n");
					}
					return output_string;
					
				}
				catch(Tango::DevFailed &e)
				{
					ret = "Error in reading actuatorsDelay (DevFailed)";
				}
				
			}else{
				try
				{
					vector<double> dparams;
					for(int i = 1; i < params.size(); i++){
						
						dparams.push_back(ToDouble(params[i]));
					}
					Tango::DeviceAttribute *attr_actuatorsDelay = new Tango::DeviceAttribute( "actuatorsDelay", dparams);
					scanserver_ctrl->write_attribute(*attr_actuatorsDelay);
					ret = "actuatorsDelay written";
				}
				catch(Tango::DevFailed &e)
				{
					ret = "Error in writting integrationTimes(DevFailed)";
				}
			}
		} else {
            return "Attribute not implemented in Sardana ScanServer controller";
		}

	}
    else 
	{
		return "Unknown command";
	}

	return ret;

}

string ScanServer::ToString(double v)
{
	std::stringstream strm;
	strm << v;
	return strm.str();
}

double ScanServer::ToDouble(string str)
{
	std::stringstream strm;
	strm.str(str);
	double d;
	strm >>d;
	return d;

}


//
//===============================================================================================
//

const char *IORegister_Ctrl_class_name[] = {"ScanServer",NULL};

const char *ScanServer_doc = "This is the C++ controller for the ScanServer class";
const char *ScanServer_gender = "ScanServer";
const char *ScanServer_model = "ScanServer";
const char *ScanServer_image = "fake_com.png";
const char *ScanServer_organization = "DESY";
const char *ScanServer_logo = "ALBA_logo.png";


Controller::PropInfo ScanServer_class_prop[] = {{"DevName","The tango device name of the ScanServer","DevString"},
							  			 NULL};

							  			 
long ScanServer_MaxDevice = 1;

extern "C"
{
	
Controller *_create_ScanServer(const char *inst,vector<Controller::Properties> &prop)
{
	return new ScanServer(inst,prop);
}

}
