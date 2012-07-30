#ifndef _IK220_H
#define _IK220_H

#include <pool/ZeroDCtrl.h>
#include <tango.h>

extern "C"
{
	Controller *_create_IK220Ctrl(const char *,vector<Controller::Properties> &);
}


class IK220Ctrl:public ZeroDController
{
public:
	IK220Ctrl(const char *,vector<Controller::Properties> &);
	virtual ~IK220Ctrl();

	virtual void AddDevice(int32_t );
	virtual void DeleteDevice(int32_t );

	virtual double ReadOne(int32_t );	
	virtual void StateOne(int32_t, Controller::CtrlState *);
	
	virtual Controller::CtrlData GetExtraAttributePar(int32_t, string &);
	virtual void SetExtraAttributePar(int32_t, string &, Controller::CtrlData &);

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

#endif /* _IK220_H */
