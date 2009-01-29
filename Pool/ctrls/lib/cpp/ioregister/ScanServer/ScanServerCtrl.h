#ifndef _ScanServerCTRL_H_
#define _ScanServerCTRL_H_

#include <tango.h>
#include <pool/IORegisterCtrl.h>

extern "C"
{
	/**
	 * The create controller method for ScanServer controller.
	 */	
	Controller *_create_ScanServer(const char *,vector<Controller::Properties> &);
}

/**
 * @brief A IORegister controller for ScanServer
 */
class ScanServer:public IORegisterController
{
	double CppComCh_extra_2;	///< dummy property value. Means nothing. For test purposes
	
public:
	/// Constructor
	ScanServer(const char *,vector<Controller::Properties> &);
	/// Destructor
	virtual ~ScanServer();

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
	virtual void AddDevice(long idx);
	
	/**
	 * @brief removes a device in the controller given by the index.
	 * 
	 * @param idx the device index to be removed (starts with 1).
	 */
	virtual void DeleteDevice(long idx);
	//@}
	

	/**
	 * Read data from an input/outpur register. 
	 * 
	 * @param idx - ioregister id
	 *
     * return the readout value
	 */

	virtual long ReadOne(long); 
	
		
	/**
	 * Write data to an input/output register.
	 * @param idx - ioregister id
     * @param data  - write value
	 *
	 */
	virtual void WriteOne(long, long); 
	

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
	virtual void StateOne(long, Controller::CtrlState *);
	//@}

	/**
	 * @brief Sends the given string to the controller.
	 * 
	 * @param the_str the string to be sent.
	 * 
	 * @return a string with the controller response.
	 */
	virtual string SendToCtrl(string &);
	string ToString(double);
    double ToDouble(string);
					
protected:

	Tango::DeviceProxy      *scanserver_ctrl;
    string          DevName;
};

#endif /*_ScanServerCTRL_H_*/
