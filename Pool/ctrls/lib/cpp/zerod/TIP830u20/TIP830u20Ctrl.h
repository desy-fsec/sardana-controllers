#ifndef _TIP830u20CTRL_H
#define _TIP830u20CTRL_H

#include <pool/ZeroDCtrl.h>
#include <tango.h>

extern "C"
{
	Controller *_create_TIP830u20Ctrl(const char *,vector<Controller::Properties> &);
}


class TIP830u20Ctrl:public ZeroDController
{
public:
	TIP830u20Ctrl(const char *,vector<Controller::Properties> &);
	virtual ~TIP830u20Ctrl();

	virtual void AddDevice(int32_t );
	virtual void DeleteDevice(int32_t );

	virtual double ReadOne(int32_t );	
	virtual void StateOne(int32_t, Controller::CtrlState *);
	

protected:
	void bad_data_type(string &);
	
	string				DevName;
	Tango::DeviceProxy	*adc_ctrl;
};

#endif /* _TIP830u20CTRL_H */
