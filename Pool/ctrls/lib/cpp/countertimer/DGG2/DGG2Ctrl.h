#ifndef _DGG2COTI_H
#define _DGG2COTI_H

#include <pool/CoTiCtrl.h>
#include <tango.h>

extern "C"
{
	Controller *_create_DGG2(const char *,vector<Controller::Properties> &);
}


class DGG2:public CoTiController
{
public:
	DGG2(const char *,vector<Controller::Properties> &);
	virtual ~DGG2();

	virtual void AddDevice(int32_t );
	virtual void DeleteDevice(int32_t );

	virtual double ReadOne(int32_t );
	virtual void AbortOne(int32_t );
	
	virtual void LoadOne(int32_t, double);
	virtual void StartOneCT(int32_t );
	
	virtual void StateOne(int32_t, Controller::CtrlState *);
					
protected:
	
	struct TimerData 
	{
	  Tango::DeviceProxy	*proxy;
	  bool			device_available;
	  std::string		tango_device;
	};

	std::map<int32_t, TimerData*> timer_data;

	int32_t			stop_time_ms;
	int32_t			remain_ms;
	struct timeval	last_read;
       	
	int32_t max_device;

	int 			start_th;
	stringstream            convert_stream;	
};

#endif /* _DGG2COTI_H */
