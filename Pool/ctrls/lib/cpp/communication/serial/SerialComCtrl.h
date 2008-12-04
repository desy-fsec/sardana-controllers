#ifndef _SERIALCOMCTRL_H_
#define _SERIALCOMCTRL_H_

#include <pool/ComCtrl.h>
#include <tango.h>

extern "C"
{
	Controller *_create_PyRemoteTangoSerialController(const char *,vector<Controller::Properties> &);
}
/**
 * A C++ communication controller class that talks to a Serial Line python 
 * device server 
 */
class RemotePyTangoSerialController:public ComController
{
protected:

	struct SerialLineData 
	{
		Tango::DeviceProxy	*proxy;
		bool				device_available;
		std::string			tango_device;
		/*
		Tango::DevShort		baud_rate;
		Tango::DevShort		data_bits;
		string				flow_control;
		Tango::DevShort		input_buffer;
		string				parity;
		string				port;
		Tango::DevShort		stop_bits;
		string				terminator;
		Tango::DevShort		time_out;
		*/
	};
	
	int32_t max_device;
	
	std::map<int32_t, SerialLineData*> sl_data; 
	
public:

	RemotePyTangoSerialController(const char *,std::vector<Controller::Properties> &);
	virtual ~RemotePyTangoSerialController();

	/**
	 * @param idx - communication channel id
	 */
	virtual void OpenOne(int32_t);
	
	/**
	 * @param idx - communication channel id
	 */
	virtual void CloseOne(int32_t);
	

	virtual void AddDevice(int32_t);
	virtual void DeleteDevice(int32_t);

	/**
	 * Atempts to read data into the given buffer. 
	 * The length of the data can be checked by inspecting the buffer.
	 * 
	 * @param idx - communication channel id
	 * @param max_read_len - max length of buff to read.
	 *                        0 empties the read_buff and returns 0.
	 *                       -1 (default value) to read all available data from the channel.
	 */
	virtual std::string &ReadOne(int32_t,int32_t max_read_len = -1); 
	
	/**
	 * Atempts to read data into the given buffer up to a new line character. 
	 * The length of the data can be checked by inspecting the buffer.
	 * 
	 * @param idx - communication channel id
	 */
	virtual std::string &ReadLineOne(int32_t); 
		
	/**
	 * @param idx - communication channel id
	 * @param write_buff - buffer which contains data to be written
	 * @param write_len - length of buffer to write.
	 *                    0 will not write anything
	 *                    -1 (default value) will atempt to write the entire contents of the write_buff
	 * @return the length of the data actually written
	 */
	virtual int32_t WriteOne(int32_t, std::string &,int32_t write_len = -1); 
	
	/**
	 * @param idx - communication channel id
	 * @param write_buff - buffer which contains data to be written
	 * @param write_len - length of buffer to write.
	 *                    0 will not write anything
	 *                    -1 will atempt to write the entire contents of the write_buff
	 * @param max_read_len - max length of buff to read.
	 *                        0 empties the read_buff and returns 0.
	 *                       -1 to read all available data from the channel.
	 * @return the length of the data actually written
	 */
	virtual std::string &WriteReadOne(int32_t, std::string &, int32_t write_len = -1, int32_t max_read_len = -1); 
	
	virtual void StateOne(int32_t, Controller::CtrlState *);
	
	virtual Controller::CtrlData GetExtraAttributePar(int32_t, std::string &);
	virtual void SetExtraAttributePar(int32_t, std::string &, Controller::CtrlData &);
	
	virtual std::string SendToCtrl(std::string &);
					
protected:
	void bad_data_type(std::string &);

};
#endif /*_SERIALCOMCTRL_H_*/
