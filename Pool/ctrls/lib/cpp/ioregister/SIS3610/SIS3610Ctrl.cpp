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

int SIS3610::classInit = 0; 

SIS3610::SIS3610(const char *inst, vector<Controller::Properties> &prop):
  IORegisterController(inst)
{
  read_nb = 0;
  write_nb = 0;

  if( classInit == 0)
    {
      classInit = 1;
      fprintf( stderr, "\nRecent changes SIS3610Ctrl \n"); 
      fprintf( stderr, "12.8.2011 debugged: WriteOne, write-output-register\n"); 
    }
  FlagDebugIO = 0;
               
  if( isatty( fileno( stdout)))
    {
      FlagDebugIO = 1;
    } 

  max_device = 0;	
  vector<Controller::Properties>::iterator prop_it;
  for (prop_it = prop.begin(); prop_it != prop.end(); ++prop_it){
	if(prop_it->name == "RootDeviceName"){
      Tango::Database *db = new Tango::Database();
      string root_device_name =prop_it->value.string_prop[0];
      string add = "*";
      string name = root_device_name + add;
      Tango::DbDatum db_datum = db->get_device_exported(name);
      vector<string> str_vec;
      db_datum >> str_vec;  
      int index = 1;
      for(unsigned long l = 0; l < str_vec.size(); l++){
		IORegisterData *ioregister_data_elem = new IORegisterData;
		ioregister_data_elem->tango_device = str_vec[l];
		ioregister_data_elem->device_available = false;
		ioregister_data_elem->proxy = NULL;
		ioregister_data.insert(make_pair(index, ioregister_data_elem));
		max_device++;
		index++;
      }
	}
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
  map<int32_t, IORegisterData*>::iterator ite = ioregister_data.begin();
  for(;ite != ioregister_data.end();ite++)
    {
      if(ite->second->proxy != NULL)
	    delete ite->second->proxy;
      delete ite->second;		
    }		
  ioregister_data.clear();
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
 
  if(idx > max_device){
	TangoSys_OMemStream o;
	o << "The property 'TangoDevices' has no value for index " << idx << ".";
	o << " Please define a valid tango device before adding a new element to this controller"<< ends;
	
	Tango::Except::throw_exception((const char *)"SIS3610Ctrl_BadIndex",o.str(),
                                   (const char *)"SIS3610Ctrl::AddDevice()");
  }
  if(ioregister_data[idx]->device_available == false){
	if(ioregister_data[idx]->proxy == NULL)
      ioregister_data[idx]->proxy = new Tango::DeviceProxy(ioregister_data[idx]->tango_device);
	try{
      ioregister_data[idx]->proxy->ping();
      ioregister_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
      ioregister_data[idx]->device_available = false;
	}
  } 
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
  if(idx > max_device){
	TangoSys_OMemStream o;
	o << "Trying to delete an inexisting element(" << idx << ") from the controller." << ends;
	
	Tango::Except::throw_exception((const char *)"SIS3610Ctrl_BadIndex",o.str(),
                                   (const char *)"SIS3610Ctrl::DeleteDevice()");
  }	
    
  if(ioregister_data[idx]->proxy != NULL){
	delete ioregister_data[idx]->proxy;
	ioregister_data[idx]->proxy = NULL;  
  }
  ioregister_data[idx]->device_available = false;
}

int32_t SIS3610::ReadOne(int32_t idx)
{

  Tango::DeviceAttribute d_out;
  Tango::DevLong read_value;
    
  read_nb++;
    
  if(ioregister_data[idx]->proxy == NULL){
	TangoSys_OMemStream o;
	o << "DGG2Ctrl Device Proxy for idx " << idx << " is NULL" << ends;	
	Tango::Except::throw_exception((const char *)"SIS3610Ctrl_BadCtrlPtr",o.str(),
                                   (const char *)"SIS3610Ctrl::ReadOne()");  
  }
    
  if(ioregister_data[idx]->device_available == false){
	try{
      ioregister_data[idx]->proxy->ping();
      ioregister_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
      ioregister_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "SIS3610Ctrl Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"SIS3610Ctrl_BadCtrlPtr",o.str(),
                                     (const char *)"SIS3610Ctrl::ReadOne()"); 
	}
  }

  d_out = ioregister_data[idx]->proxy->read_attribute("Value");
  d_out >> read_value;
	
	
  return (int32_t)read_value;
}



void SIS3610::WriteOne(int32_t idx, int32_t write_value)
{	
  write_nb++;

  if( FlagDebugIO)
    {
      fprintf( stderr, "SIS3610::WriteOne idx %d value %d\n", idx, write_value); 
    }

  if(ioregister_data[idx]->proxy == NULL){
	TangoSys_OMemStream o;
	o << "DGG2Ctrl Device Proxy for idx " << idx << " is NULL" << ends;	
	Tango::Except::throw_exception((const char *)"SIS3610Ctrl_BadCtrlPtr",o.str(),
                                   (const char *)"SIS3610Ctrl::ReadOne()");  
  }
    
  if(ioregister_data[idx]->device_available == false){
	try{
      ioregister_data[idx]->proxy->ping();
      ioregister_data[idx]->device_available = true;	
	}
	catch(Tango::DevFailed &e){
      ioregister_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "SIS3610Ctrl Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"SIS3610Ctrl_BadCtrlPtr",o.str(),
                                     (const char *)"SIS3610Ctrl::WriteOne()"); 
	}
  }
	
  Tango::DeviceAttribute da("Value", (Tango::DevLong)write_value);

  ioregister_data[idx]->proxy->write_attribute( da);   

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
	
  if(ioregister_data[idx]->proxy == NULL){
	state_tmp = Tango::FAULT;
	return;
  }
    
  state_tmp = ioregister_data[idx]->proxy->state();
    
  ior_info_ptr->state = (int32_t)state_tmp;
  if(state_tmp == Tango::ON){
	ior_info_ptr->status = "IORegister is in ON state";
  } else if (state_tmp == Tango::FAULT){
	ior_info_ptr->status = "IORegister in in FAULT state";
  }
	
}


//-----------------------------------------------------------------------------
//
// method : 		SIS3610::GetExtraAttributePar
// 
// description : 	Get a counter ioregister extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData SIS3610::GetExtraAttributePar(int32_t idx,string &par_name)
{
  Controller::CtrlData par_value;
	
  return par_value;
}

//-----------------------------------------------------------------------------
//
// method : 		SIS3610::SetExtraAttributePar
// 
// description : 	Set extra attribute parameters.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void SIS3610::SetExtraAttributePar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{
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
  string returned_str("Nothing to do");
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


Controller::PropInfo SIS3610_class_prop[] = {
  {"RootDeviceName","Root name for tango devices","DevString"}, 
  NULL};
							  			 
int32_t SIS3610_MaxDevice = 97;

extern "C"
{
	
  Controller *_create_SIS3610(const char *inst,vector<Controller::Properties> &prop)
  {
	return new SIS3610(inst,prop);
  }

}
