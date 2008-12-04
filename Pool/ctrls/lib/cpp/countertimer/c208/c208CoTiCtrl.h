#ifndef _C208COTI_H
#define _C208COTI_H

#include <CoTiCtrl.h>
#include <tango.h>

#define MAX_CHANNELS 12

extern "C"
{
	Controller *_create_c208CoTiController(const char *,vector<Controller::Properties> &);
}


class c208CoTiController:public CoTiController
{
public:
	c208CoTiController(const char *, vector<Controller::Properties> &);
	virtual ~c208CoTiController();

	virtual void AddDevice(int32_t );
	virtual void DeleteDevice(int32_t );

	virtual void LoadOne(int32_t, double );
	virtual void StartOneCT(int32_t );
	virtual void StartAllCT();
	virtual void ReadAll();
	virtual double ReadOne(int32_t );
	virtual void AbortOne(int32_t );
	
	virtual void StateAll();
	virtual void StateOne(int32_t, Controller::CtrlState *);
	
	/*	virtual Controller::CtrlData GetExtraAttributePar(long,string &);
		virtual void SetExtraAttributePar(long,string &,Controller::CtrlData &);    */
	
protected:
	void bad_data_type(string &);
	
	Tango::DeviceProxy *ctr_dev;
	Controller::CtrlState ctr_state;
	string DevName;
	int32_t master_idx;
	int32_t ghostchan, master_started, channels;
	vector<double> values;
};

#endif /* _C208COTI_H */
