#include <iostream>
#include <HasylabDACCtrl.h>
#include <pool/PoolAPI.h>

using namespace std;

//-----------------------------------------------------------------------------
//
// method : 		HasylabDAC::HasylabDAC
// 
// description : 	Controller for DACs
//			It retrieves devices from the DB according 
//                      to the given RootDeviceName
//     
//
//-----------------------------------------------------------------------------

HasylabDAC::HasylabDAC(const char *inst,vector<Controller::Properties> &prop):MotorController(inst)
{
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
	HasylabDACData *dac_data_elem = new HasylabDACData;
	dac_data_elem->tango_device = str_vec[l];
	dac_data_elem->device_available = false;
	dac_data_elem->proxy = NULL;
	dac_data.insert(make_pair(index, dac_data_elem));
	max_device++;
	index++;
      }
    }
  }
  
}

//-----------------------------------------------------------------------------
//
// method : 		HasylabDAC::~HasylabDAC
// 
// description : 	Dtor of the HasylabDAC Controller class
//
//-----------------------------------------------------------------------------

HasylabDAC::~HasylabDAC()
{
  //cout << "[HasylabDAC] class dtor" << endl;	
  map<int32_t, HasylabDACData*>::iterator ite = dac_data.begin();
  for(;ite != dac_data.end();ite++)
    {
      if(ite->second->proxy != NULL)
	delete ite->second->proxy;
      delete ite->second;		
    }		
  dac_data.clear();
}

//-----------------------------------------------------------------------------
//
// method : 		HasylabDAC::AddDevice
// 
// description : 	Register a new device for the controller
//					For the simulated controller, this simply means increment
//					motor count
//
//-----------------------------------------------------------------------------

void HasylabDAC::AddDevice(int32_t idx)
{
  //cout << "[HasylabDAC] Creating a new Motor with index " << idx << " on controller HasylabDAC/" << inst_name << endl;	

  if(idx > max_device){
    TangoSys_OMemStream o;
    o << "The property 'TangoDevices' has no value for index " << idx << ".";
    o << " Please define a valid tango device before adding a new element to this controller"<< ends;
    
    Tango::Except::throw_exception((const char *)"HasylabDAC_BadIndex",o.str(),
				   (const char *)"HasylabDAC::AddDevice()");
  }
  if(dac_data[idx]->device_available == false){
    if(dac_data[idx]->proxy == NULL)
      dac_data[idx]->proxy = new Tango::DeviceProxy(dac_data[idx]->tango_device);
    try{
      dac_data[idx]->proxy->ping();
      dac_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      dac_data[idx]->device_available = false;
    }
  }
}

//-----------------------------------------------------------------------------
//
// method : 		HasylabDAC::DeleteDevice
// 
// description : 	Unregister a new device for the controller
//					For the simulated controller, this simply means decrement
//					motor count
//
//-----------------------------------------------------------------------------

void HasylabDAC::DeleteDevice(int32_t idx)
{
  //cout << "[HasylabDAC] Deleting OneD with index " << idx << " on controller HasylabDAC/" << inst_name << endl;
  if(idx > max_device){
    TangoSys_OMemStream o;
    o << "Trying to delete an inexisting element(" << idx << ") from the controller." << ends;
    
    Tango::Except::throw_exception((const char *)"HasylabDAC_BadIndex",o.str(),
				   (const char *)"HasylabDAC::DeleteDevice()");
  }	
	
  if(dac_data[idx]->proxy != NULL){
    delete dac_data[idx]->proxy;
    dac_data[idx]->proxy = NULL;  
  }
  dac_data[idx]->device_available = false;
}



void  HasylabDAC::AbortOne(int32_t idx)
{
  
  //  cout << "[HasylabDAC] In AbortOne" << endl;

}

void  HasylabDAC::DefinePosition(int32_t idx, double new_pos)
{
  
  //  cout << "[HasylabDAC] In DefinePosition - Set to this value the current position" << endl;
 
  
}


//-----------------------------------------------------------------------------
//
// method : 		HasylabDAC::ReadPosition
// 
// description : 	Read a motor position
//
// arg(s) : - idx : The motor number (starting at 1)
//
// This method returns the motor position
//-----------------------------------------------------------------------------



double HasylabDAC::ReadOne(int32_t idx)
{
  //  cout << "[HasylabDAC] In ReadOne" << endl;
  
  if(dac_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "HasylabDAC Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"HasylabDACCtrl_BadCtrlPtr",o.str(),
				   (const char *)"HasylabDAC::ReadOne()");  
  }
	
  if(dac_data[idx]->device_available == false){
    try{
      dac_data[idx]->proxy->ping();
      dac_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      dac_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "HasylabDAC Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"HasylabDACCtrl_BadCtrlPtr",o.str(),
				     (const char *)"HasylabDAC::ReadOne()"); 
    }
  }

  Tango::DeviceAttribute d_out;
  Tango::DevDouble value;

  d_out = dac_data[idx]->proxy->read_attribute("Voltage");
  
  d_out >> value; 

  return value;

}


//-----------------------------------------------------------------------------
//
// method : 	       HasylabDAC::PreStartAll
// 
// description : 	Init movement data
//
//-----------------------------------------------------------------------------
	
void HasylabDAC::PreStartAll()
{
	//cout << "[HasylabDAC] PreStartAll on controller HasylabDAC/" << inst_name << " (" << DevName << ")" << endl;
	
	wanted_dac_pos.clear();
	wanted_dac.clear();
}


void  HasylabDAC::StartOne(int32_t idx, double new_pos)
{
  
  //  cout << "[HasylabDAC] In StartOne" << endl;
  
  if(dac_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "HasylabDAC Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"HasylabDACCtrl_BadCtrlPtr",o.str(),
				   (const char *)"HasylabDAC::StartOne()");  
  }
	
  if(dac_data[idx]->device_available == false){
    try{
      dac_data[idx]->proxy->ping();
      dac_data[idx]->device_available = true;	
    }
    catch(Tango::DevFailed &e){
      dac_data[idx]->device_available = false;
      TangoSys_OMemStream o;
      o << "HasylabDAC Device for idx " << idx << " not available" << ends;	
      Tango::Except::throw_exception((const char *)"HasylabDACCtrl_BadCtrlPtr",o.str(),
				     (const char *)"HasylabDAC::StartOne()"); 
    }
  }

  wanted_dac_pos.push_back(new_pos);
  wanted_dac.push_back(idx);

}


void  HasylabDAC::StartAll()
{
  
  //  cout << "[HasylabDAC] In StartAll" << endl;
  

  int32_t nb_mot = wanted_dac.size();
  
  for (int32_t loop = 0;loop < nb_mot;loop++){
    
    int idx = wanted_dac[loop];
    
    if(dac_data[idx]->proxy == NULL){
      TangoSys_OMemStream o;
      o << "HasylabDAC Device Proxy for idx " << idx << " is NULL" << ends;  
      Tango::Except::throw_exception((const char *)"HasylabDACCtrl_BadCtrlPtr",o.str(),
				     (const char *)"HasylabDAC::StartOne()");  
    }
    
    if(dac_data[idx]->device_available == false){
      try{
	dac_data[idx]->proxy->ping();
	dac_data[idx]->device_available = true;	
      }
      catch(Tango::DevFailed &e){
	dac_data[idx]->device_available = false;
	TangoSys_OMemStream o;
	o << "HasylabDAC Device for idx " << idx << " not available" << ends;
	Tango::Except::throw_exception((const char *)"HasylabDACCtrl_BadCtrlPtr",o.str(),
				       (const char *)"HasylabDAC::StartOne()"); 
      }
    }

    Tango::DevDouble position = wanted_dac_pos[loop];
    Tango::DeviceAttribute da("Voltage",position);
    dac_data[idx]->proxy->write_attribute(da);
    
  }
}

//-----------------------------------------------------------------------------
//
// method : 		HasylabDAC::GetState
// 
// description : 	Get one motor status. Motor status means two things :
//					1 - The motor state (Tango sense)
//
// arg(s) : - idx : The motor number (starting at 1)
//			- mot_info_ptr : Pointer to a struct. which will be filled with
//							 motor status
//
//-----------------------------------------------------------------------------

void HasylabDAC::StateOne(int32_t idx,Controller::CtrlState *info_ptr)
{
  MotorController::MotorState *mot_info_ptr = static_cast<MotorController::MotorState *>(info_ptr);
  
  if(dac_data[idx]->proxy == NULL){
    mot_info_ptr->state = Tango::FAULT;
    return;
  }
  
  if(dac_data[idx]->device_available == false){
    try
      {
	dac_data[idx]->proxy->ping();
	dac_data[idx]->device_available = true;	
      }
    catch(Tango::DevFailed &e)
      {
	dac_data[idx]->device_available = false;
	mot_info_ptr->state = Tango::FAULT;
	return;
      }
  }
  
  Tango::DevState s = dac_data[idx]->proxy->state();
  Tango::DeviceAttribute d_out;

  if(s == Tango::ON){
    mot_info_ptr->state = Tango::ON;
    mot_info_ptr->status = "DAC is iddle";
  } else if(s == Tango::FAULT){
    mot_info_ptr->state = Tango::FAULT;
    mot_info_ptr->status = "DAC is in error";
  }
  
  mot_info_ptr->switches = 0;
}

//-----------------------------------------------------------------------------
//
// method : 		HasylabDAC::GetPar
// 
// description : 	Get a oned exp channel parameter. Actually, 1 parameters is supported.
//					This is DataLength
//
// arg(s) : - idx : The oned exp channel  number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData HasylabDAC::GetPar(int32_t idx, string &par_name)
{
	//cout << "[HasylabDAC] Getting parameter " << par_name << " for oned exp channel with index " << idx << " on controller HasylabDAC/" << inst_name << " (" << DevName << ")" << endl;

  Controller::CtrlData par_value;
	
  TangoSys_OMemStream o;
  o << "HasylabDAC::GetPar parameter " << par_name << " is not used " << ends;	
  Tango::Except::throw_exception((const char *)"HasylabDACCtrl_BadCtrlPtr",o.str(),
				 (const char *)"HasylabDAC::GetPar()");
  
  return par_value;

}

//-----------------------------------------------------------------------------
//
// method : 		HasylabDAC::SetPar
// 
// description : 	Set a oned parameter. Actually, 1 parameters is supported.
//					This is DataLength
//
// arg(s) : - idx : The oned exp channel number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void HasylabDAC::SetPar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{
  //cout << "[HasylabDAC] Setting parameter " << par_name << " for oned channel with index " << idx << " on controller HasylabDAC/" << inst_name << " (" << DevName << ")" << endl;

 
}


//-----------------------------------------------------------------------------
//
// method : 		HasylabDAC::GetExtraAttributePar
// 
// description : 	Get a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//
// This method returns the parameter value
//-----------------------------------------------------------------------------

Controller::CtrlData HasylabDAC::GetExtraAttributePar(int32_t idx, string &par_name)
{

  Controller::CtrlData par_value;
   
  Tango::DeviceAttribute d_out;
  double par_tmp_db;

  if(dac_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "HasylabDAC Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"HasylabDACCtrl_BadCtrlPtr",o.str(),
				   (const char *)"HasylabDAC::GetExtraAttributePar()");
  }
  
  
  if (par_name == "VoltageMax"){  
    try{
      d_out = dac_data[idx]->proxy->read_attribute("VoltageMax");
      d_out >> par_tmp_db;
      par_value.db_data = par_tmp_db;
      par_value.data_type = Controller::DOUBLE;
    } catch(Tango::DevFailed &e){
      TangoSys_OMemStream o;
      o << "VoltageMax wrong defined or not not available" << ends;	
      Tango::Except::throw_exception((const char *)"HasylabDACCtrl_BadCtrlPtr",o.str(),
				     (const char *)"HasylabDAC::GetExtraAttributePar()"); 
    }
    
  } else if (par_name == "VoltageMin"){
    try{
      d_out = dac_data[idx]->proxy->read_attribute("VoltageMin");
      d_out >> par_tmp_db;
      par_value.db_data = par_tmp_db;
      par_value.data_type = Controller::DOUBLE;
    } catch(Tango::DevFailed &e){
      TangoSys_OMemStream o;
      o << "VoltageMin wrong defined or not not available" << ends;	
      Tango::Except::throw_exception((const char *)"HasylabDACCtrl_BadCtrlPtr",o.str(),
				     (const char *)"HasylabDAC::GetExtraAttributePar()"); 
    }
    
  } else {
    TangoSys_OMemStream o;
    o << "Extra attribute " << par_name << " is unknown for controller ScanVariabvleCtrl/" << get_name()  << ends;
    Tango::Except::throw_exception((const char *)"HasylabDAC_BadCtrlPtr",o.str(),
				   (const char *)"HasylabDAC::GetExtraAttributePar()");
  }
  
  return par_value;
	
}

//-----------------------------------------------------------------------------
//
// method : 		HasylabDAC::SetExtraAttributePar
// 
// description : 	Set a counter timer extra attribute parameter.
//
// arg(s) : - idx : The C/T number (starting at 1)
//			- par_name : The parameter name
//			- new_value : The parameter value
//
//-----------------------------------------------------------------------------

void HasylabDAC::SetExtraAttributePar(int32_t idx, string &par_name, Controller::CtrlData &new_value)
{ 

  if(dac_data[idx]->proxy == NULL){
    TangoSys_OMemStream o;
    o << "HasylabDAC Device Proxy for idx " << idx << " is NULL" << ends;	
    Tango::Except::throw_exception((const char *)"HasylabDACCtrl_BadCtrlPtr",o.str(),
				   (const char *)"HasylabDAC::SetExtraAttributePar()");
  }
  
  if (par_name == "VoltageMax"){
    try{
      Tango::DevDouble limit = new_value.db_data;
      Tango::DeviceAttribute da("VoltageMax",limit);
      dac_data[idx]->proxy->write_attribute(da);
    } catch(Tango::DevFailed &e){
      TangoSys_OMemStream o;
      o << "VoltageMax wrong defined or not not available" << ends;	
      Tango::Except::throw_exception((const char *)"HasylabDACCtrl_BadCtrlPtr",o.str(),
				     (const char *)"HasylabDAC::SetExtraAttributePar()");  
      
    }
  } else if (par_name == "VoltageMin"){
    try{
      Tango::DevDouble limit = new_value.db_data;
      Tango::DeviceAttribute da("VoltageMin",limit);
      dac_data[idx]->proxy->write_attribute(da);
    } catch(Tango::DevFailed &e){
      TangoSys_OMemStream o;
      o << "VoltageMin wrong defined or not not available" << ends;	
      Tango::Except::throw_exception((const char *)"HasylabDACCtrl_BadCtrlPtr",o.str(),
				     (const char *)"HasylabDAC::SetExtraAttributePar()");  
    }
  } else {
    TangoSys_OMemStream o;
    o << "Extra attribute " << par_name << " is unknown for controller HasylabDACCtrl/" << get_name() << ends;
    
    Tango::Except::throw_exception((const char *)"HasylabDAC_BadCtrlPtr",o.str(),
				   (const char *)"HasylabDAC::SetExtraAttributePar()");    
  }
  
}


//-----------------------------------------------------------------------------
//
// method : 		HasylabDAC::send_to_ctrl
// 
// description : 	Send a string to the controller
//
// arg(s) : - in_str : the string to send to the ctrl
//
//-----------------------------------------------------------------------------

string HasylabDAC::SendToCtrl(string &in_str)
{
	cout << "[HasylabDAC] I have received the string: " << in_str << endl;
	string returned_str("Nothing to be done");
	return returned_str;	
}

//-----------------------------------------------------------------------------
//
// method : 		HasylabDAC::bad_data_type
// 
// description : 	Throw a bad data type excepton
//
// arg(s) : - par_name : The parameter name
//
//-----------------------------------------------------------------------------

void HasylabDAC::bad_data_type(string &par_name)
{
	TangoSys_OMemStream o;
	o << "A wrong data type has been used to set the parameter " << par_name << ends;

	Tango::Except::throw_exception((const char *)"HasylabDACCtrl_BadParameter",o.str(),
			       			   	   (const char *)"HasylabDAC::SetPar()");
}

//
//===============================================================================================
//

const char *Motor_Ctrl_class_name[] = {"HasylabDAC",NULL};

const char *HasylabDAC_doc = "This is the C++ controller for the HasylabDAC class";
const char *HasylabDAC_gender = "HasylabDAC";
const char *HasylabDAC_model = "HasylabDAC";
const char *HasylabDAC_image = "fake_com.png";
const char *HasylabDAC_organization = "DESY";
const char *HasylabDAC_logo = "ALBA_logo.png";

Controller::ExtraAttrInfo HasylabDAC_ctrl_extra_attributes[] = {
  {"VoltageMax","DevDouble","Read_Write"},
  {"VoltageMin","DevDouble","Read_Write"},
  NULL};

Controller::PropInfo HasylabDAC_class_prop[] = {
  {"RootDeviceName","Root name for tango devices","DevString",NULL},
  NULL};


int32_t HasylabDAC_MaxDevice = 97;

extern "C"
{
	
Controller *_create_HasylabDAC(const char *inst,vector<Controller::Properties> &prop)
{
	return new HasylabDAC(inst,prop);
}

}
