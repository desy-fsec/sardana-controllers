#ifndef _SIS3610CTRL_H_
#define _SIS3610CTRL_H_

#include <tango.h>
#include <pool/IORegisterCtrl.h>

extern "C"
{
	/**
	 * The create controller method for SIS3610 controller.
	 */	
	Controller *_create_SIS3610(const char *,vector<Controller::Properties> &);
}

/**
 * @brief A IORegister controller for SIS3610
 */
class SIS3610:public IORegisterController
{
	double CppComCh_extra_2;	///< dummy property value. Means nothing. For test purposes
	
public:
	/// Constructor
	SIS3610(const char *, vector<Controller::Properties> &);
	/// Destructor
	virtual ~SIS3610();
	
	/**
	 *	@name Management
	 *	Controller add/remove devices related methods
	 */
	//@{
	
	/**
	 * @brief adds (activates) a device in the controller given by the index.
	 * 
	 * @param idx the device index to be added (starts with 1).
	 */
	virtual void AddDevice(int32_t idx);
	
	/**
	 * @brief removes a device in the controller given by the index.
	 * 
	 * @param idx the device index to be removed (starts with 1).
	 */
	virtual void DeleteDevice(int32_t idx);
	//@}
	
	/**
	 * Read data from an input/outpur register. 
	 * 
	 * @param idx - ioregister id
	 *
	 * return the readout value
	 */
	
	virtual int32_t ReadOne(int32_t ); 
	
	
	/**
	 * Write data to an input/output register.
	 * @param idx - ioregister id
	 * @param data  - write value
	 *
	 */
	virtual void WriteOne(int32_t, int32_t); 
	
	
	/**
	 *	@name State
	 *	Controller state related methods.
	 */
	//@{
	/**
	 * @brief StateOne.
	 * 
	 * @param idx         [in] device index (starts with 1).
	 * @param ctrl_state [out] pointer to the state object that will contain the
	 *                         controller state.  
	 */	
	virtual void StateOne(int32_t, Controller::CtrlState *);
	//@}
	
	/**
	 *	@name Extra Attributes
	 *	Extra attributes related methods.
	 */
	//@{
	/** 
	 * @brief Sets the given extra attribute parameter with the given value on
	 *        the given device index.
	 * 
	 * @param idx       [in] device index (starts at 1)
	 * @param attr_name [in] extra attribute name
	 * @param ctrl_data [in] new value reference object
	 */	
	virtual void SetExtraAttributePar(int32_t, string &, Controller::CtrlData &);
	
	/** 
	 * @brief Get the given extra attribute parameter value for the given device
	 *        index.
	 * 
	 * @param idx       [in] device index (starts at 1)
	 * @param attr_name [in] extra attribute name
	 * 
	 * @return a CtrlData object containning the extra attribute value
	 */	
	virtual Controller::CtrlData GetExtraAttributePar(int32_t, string &);
	
	//@}

	/**
	 * @brief Sends the given string to the controller.
	 * 
	 * @param the_str the string to be sent.
	 * 
	 * @return a string with the controller response.
	 */
	virtual string SendToCtrl(string &);
					
protected:	
	struct IORegisterData 
	{
	  Tango::DeviceProxy	*proxy;
	  bool			device_available;
	  std::string		tango_device;
	};

	std::map<int32_t, IORegisterData*> ioregister_data;

	void bad_data_type(string &);
	
	int32_t read_nb;          ///< number of reads invoked on this object
	int32_t write_nb;         ///< number of writes invoked on this object
       	
	int32_t max_device;

	stringstream            convert_stream;

    static int classInit;
    int FlagDebugIO; 
};

#endif /*_SIS3610CTRL_H_*/
