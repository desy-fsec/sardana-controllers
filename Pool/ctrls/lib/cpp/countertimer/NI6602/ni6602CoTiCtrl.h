#ifndef _NI6602COTI_H
#define _NI6602COTI_H

#include <pool/CoTiCtrl.h>
#include <tango.h>

#define MAX_CHANNELS 8

extern "C"
{
	Controller *_create_ni6602CoTiController(const char *,vector<Controller::Properties> &);
}


class ni6602CoTiController:public CoTiController
{
public:
	ni6602CoTiController(const char *,vector<Controller::Properties> &);
	virtual ~ni6602CoTiController();

	virtual void AddDevice(int32_t idx);
	virtual void DeleteDevice(int32_t idx);

	virtual void LoadOne(int32_t idx, double new_value);
	virtual void StartOneCT(int32_t idx);
	virtual void StartAllCT();
	virtual void ReadAll();
	virtual double ReadOne(int32_t idx);
	virtual void AbortOne(int32_t idx);
	
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
	int32_t twochans, master_started, channels[MAX_CHANNELS];
	vector<double> values;
};

#endif /* _NI6602COTI_H */
