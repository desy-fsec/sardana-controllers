#ifndef _HASYLABADCCTRL_H
#define _HASYLABADCCTRL_H

#include <pool/ZeroDCtrl.h>
#include <tango.h>

extern "C"
{
	Controller *_create_HasylabADCCtrl(const char *,vector<Controller::Properties> &);
}


class HasylabADCCtrl:public ZeroDController
{
public:
	HasylabADCCtrl(const char *,vector<Controller::Properties> &);
	virtual ~HasylabADCCtrl();

	virtual void AddDevice(int32_t );
	virtual void DeleteDevice(int32_t );

	virtual double ReadOne(int32_t );	
	virtual void StateOne(int32_t, Controller::CtrlState *);
	

protected:
	void bad_data_type(string &);

	struct ZeroDData 
	{
	  Tango::DeviceProxy	*proxy;
	  bool			device_available;
	  std::string		tango_device;
	};

	std::map<int32_t, ZeroDData*> zerod_data;
	
	int32_t max_device; 
};

#endif /* _HASYLABADCCTRL_H */
