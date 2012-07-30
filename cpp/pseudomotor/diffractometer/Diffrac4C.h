#ifndef DIFFRAC4C_H_
#define DIFFRAC4C_H_

#include <vector>
#include <pool/PseudoMotCtrl.h>
#include <Diffrac.h>

#define SET_REFLEC_WRONG_PARAMS		"Usage: setor <index> <th> <tth> <h> <k> <l>"

extern "C"
{
	Controller *_create_Diffrac4C(const char *,std::vector<Controller::Properties> &);
}

class Diffrac4C : public Diffrac
{
protected:
	
	hkl::eulerian4C::vertical::Geometry &getGeometry();
	
	virtual hkl::Diffractometer* createDiffractometer();
	virtual const char *setReflection(vector<string> &);
	virtual void setReflections(vector<string> &);
	
	virtual string calcA(vector<string> &);
	virtual string calcHKL(vector<string> &);
	
public:
	Diffrac4C(const char *,std::vector<Controller::Properties> &);
	virtual ~Diffrac4C();
	
	virtual double CalcPhysical(int32_t,std::vector<double> &);
	virtual double CalcPseudo(int32_t,std::vector<double> &);

	/**
	 * Overwritten implementation for efficiency reasons
	 * 
	 * @param	pseudo_pos		[in]	list of pseudo motor positions
	 * @param	physical_pos	[out]	list of physical motor positions
	 * 
	 * @warnning It is crucial that this method is called with physical_pos 
	 *           vector containning the correct number of elements.
	 */ 
	virtual void CalcAllPhysical(std::vector<double> &, std::vector<double> &);
	
	/**
	 * Overwritten implementation for efficiency reasons
	 * 
	 * @param	physical_pos	[in]	list of physical motor positions
	 * @param	pseudo_pos		[out]	list of pseudo motor positions
	 * 
	 * @warnning It is crucial that this method is called with pseudo_pos 
	 *           vector containning the correct number of elements.
	 */ 	
	virtual void CalcAllPseudo(std::vector<double> &, std::vector<double> &);
};

#endif /*DIFFRAC2C_H_*/
