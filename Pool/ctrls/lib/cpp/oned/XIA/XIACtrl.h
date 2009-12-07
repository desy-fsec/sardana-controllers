#ifndef _XIACTRL_H_
#define _XIACTRL_H_

#include <tango.h>
#include <pool/OneDCtrl.h>

extern "C"
{
	/**
	 * The create controller method for XIA controller.
	 */	
	Controller *_create_XIA(const char *,vector<Controller::Properties> &);
}

/**
 * @brief A OneD controller for XIA
 */
class XIA:public OneDController
{
	double CppComCh_extra_2;	///< dummy property value. Means nothing. For test purposes
	
public:
	/// Constructor
	XIA(const char *,vector<Controller::Properties> &);
	/// Destructor
	virtual ~XIA();

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
	virtual void AddDevice(int32_t );
	
	/**
	 * @brief removes a device in the controller given by the index.
	 * 
	 * @param idx the device index to be removed (starts with 1).
	 */
	virtual void DeleteDevice(int32_t );
	//@}
	
    virtual void PreReadOne(int32_t );
	/**
	 * Read data from oned experimental channel. 
	 * 
	 * @param idx - oned id
	 *
     * return the readout value
	 */

	virtual double *ReadOne(int32_t ); 

	virtual void StartOne(int32_t );
	virtual void AbortOne(int32_t );

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

	virtual Controller::CtrlData GetPar(int32_t, string &);
	virtual void SetPar(int32_t, string &, Controller::CtrlData &);
	
	
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
	void bad_data_type(string &);

	struct XIAData 
	{
	  Tango::DeviceProxy	*proxy;
	  bool			device_available;
	  std::string		tango_device;
	};
	
	int32_t max_device;
	
	std::map<int32_t, XIAData*> xia_data; 
	

    stringstream            convert_stream;
};

#endif /*_XIACTRL_H_*/
